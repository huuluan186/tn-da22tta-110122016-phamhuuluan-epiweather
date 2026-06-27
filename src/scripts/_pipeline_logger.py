"""
_pipeline_logger.py — Context manager ghi log mỗi pipeline run vào DB.

Dùng được cho mọi script trong scripts/ (sync_flunet, sync_weather,
feature_builder, batch_predict). Không phụ thuộc FastAPI — chỉ cần psycopg2
và DATABASE_URL trong .env.

Usage:
    from _pipeline_logger import track_run

    with track_run("sync_flunet", trigger_type="scheduled",
                   iso_year=2026, iso_week=21) as stats:
        # ...do work...
        stats["rows_processed"] = 1000
        stats["rows_inserted"] = 800
        stats["rows_updated"] = 200

Khi block exit:
- Không exception → status='success', completed_at=NOW()
- Có exception → status='failed', errors=JSON([str(e)]), re-raise

Nếu DB không reach được khi enter → context manager vẫn yield một dict trống
(silent fallback) để script tiếp tục chạy. Script không bị block vì logging.
"""
import json
import os
import sys
import traceback
import uuid
from contextlib import contextmanager
from datetime import datetime

import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:111111111@localhost:5432/kltn_epiweather",
)

# trigger_type CHECK: ('manual', 'scheduled', 'api', 'event')
VALID_TRIGGERS = {"manual", "scheduled", "api", "event"}


def _connect():
    try:
        return psycopg2.connect(DB_URL, connect_timeout=5)
    except Exception as e:
        print(f"[pipeline_logger] WARN: DB không reach được — bỏ qua log: {e}",
              file=sys.stderr)
        return None


def _insert_running(conn, pipeline_name, trigger_type, iso_year, iso_week, meta):
    run_id = str(uuid.uuid4())
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO pipeline_runs
            (run_id, pipeline_name, trigger_type, status,
             iso_year, iso_week, started_at, metadata)
        VALUES (%s, %s, %s, 'running', %s, %s, NOW(), %s)
        """,
        (run_id, pipeline_name, trigger_type, iso_year, iso_week,
         json.dumps(meta) if meta else None),
    )
    conn.commit()
    cur.close()
    return run_id


def _finalize(conn, run_id, status, stats, errors):
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE pipeline_runs SET
            status         = %s,
            completed_at   = NOW(),
            rows_processed = %s,
            rows_inserted  = %s,
            rows_updated   = %s,
            rows_skipped   = %s,
            errors         = %s
        WHERE run_id = %s
        """,
        (
            status,
            stats.get("rows_processed"),
            stats.get("rows_inserted"),
            stats.get("rows_updated"),
            stats.get("rows_skipped"),
            json.dumps(errors) if errors else None,
            run_id,
        ),
    )
    conn.commit()
    cur.close()


@contextmanager
def track_run(
    pipeline_name: str,
    trigger_type: str = "scheduled",
    iso_year: int | None = None,
    iso_week: int | None = None,
    metadata: dict | None = None,
):
    """
    Context manager: ghi run vào pipeline_runs.

    Yields một dict stats mà script body update các field:
        rows_processed, rows_inserted, rows_updated, rows_skipped, errors (list)

    Status được tự động set:
        - không exception                       → 'success'
        - exception bình thường                 → 'failed' (kèm traceback)
        - stats['errors'] có item nhưng OK      → 'partial'
    """
    if trigger_type not in VALID_TRIGGERS:
        trigger_type = "manual"

    started_wall = datetime.now()
    print(f"[pipeline_logger] {pipeline_name} start "
          f"(trigger={trigger_type}, week={iso_year}-W{iso_week or 0:02d}) "
          f"at {started_wall.strftime('%Y-%m-%d %H:%M:%S')}")

    conn = _connect()
    run_id: str | None = None
    if conn is not None:
        try:
            run_id = _insert_running(
                conn, pipeline_name, trigger_type, iso_year, iso_week, metadata,
            )
            print(f"[pipeline_logger] run_id={run_id}")
        except Exception as e:
            print(f"[pipeline_logger] WARN insert failed: {e}", file=sys.stderr)
            run_id = None

    stats: dict = {
        "rows_processed": None,
        "rows_inserted": None,
        "rows_updated": None,
        "rows_skipped": None,
        "errors": [],
    }

    try:
        yield stats
    except Exception as exc:
        tb = traceback.format_exc()
        errors_list = stats.get("errors") or []
        errors_list.append({"type": type(exc).__name__, "message": str(exc), "traceback": tb[-2000:]})
        if conn is not None and run_id is not None:
            try:
                _finalize(conn, run_id, "failed", stats, errors_list)
            except Exception as e:
                print(f"[pipeline_logger] WARN finalize failed: {e}", file=sys.stderr)
        elapsed = (datetime.now() - started_wall).total_seconds()
        print(f"[pipeline_logger] {pipeline_name} FAILED in {elapsed:.1f}s: {exc}",
              file=sys.stderr)
        raise
    else:
        final_status = "partial" if stats.get("errors") else "success"
        if conn is not None and run_id is not None:
            try:
                _finalize(conn, run_id, final_status, stats, stats.get("errors"))
            except Exception as e:
                print(f"[pipeline_logger] WARN finalize failed: {e}", file=sys.stderr)
        elapsed = (datetime.now() - started_wall).total_seconds()
        print(f"[pipeline_logger] {pipeline_name} {final_status.upper()} "
              f"in {elapsed:.1f}s "
              f"(processed={stats.get('rows_processed')}, "
              f"inserted={stats.get('rows_inserted')}, "
              f"updated={stats.get('rows_updated')})")
    finally:
        if conn is not None:
            conn.close()
