"""
sync_flunet.py — Pull WHO FluNet realtime → INSERT/UPDATE bảng disease_cases.

Source: WHO FluMart public OData API (free, không cần API key).
  https://xmart-api-public.who.int/FLUMART/VIW_FNT

Mục đích Phase A-1: bổ sung data 2020-current vào DB để model có lag features
cho nowcast tuần hiện tại.

Usage:
  python scripts/sync_flunet.py --from-year 2020
  python scripts/sync_flunet.py --from-year 2024 --dry-run   # preview, không INSERT
  python scripts/sync_flunet.py --from-year 2024 --countries VNM,THA,IDN

Cron schedule (production):
  Chạy mỗi thứ Hai 8:00 ICT (WHO publish FluNet weekly thứ Hai).
"""

import argparse
import json
import math
import os
import sys
import warnings
from pathlib import Path
from typing import Iterable

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import numpy as np
import pandas as pd
import psycopg2
import requests
from dotenv import load_dotenv
from psycopg2.extras import execute_values

# Local import: pipeline_runs DB logger (cùng thư mục)
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _pipeline_logger import track_run  # noqa: E402

warnings.filterwarnings("ignore")
load_dotenv()

BASE = Path(__file__).resolve().parent.parent
DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:111111111@localhost:5432/kltn_epiweather",
)

FLUMART_URL = "https://xmart-api-public.who.int/FLUMART/VIW_FNT"
PAGE_SIZE = 5000  # OData $top per request

# Columns ta cần từ VIW_FNT
NEEDED_COLUMNS = {"COUNTRY_CODE", "ISO_YEAR", "ISO_WEEK", "INF_A", "INF_B"}


def fetch_flunet_batch(from_year: int, skip: int = 0, top: int = PAGE_SIZE) -> list[dict]:
    """Fetch 1 batch từ FluMart OData endpoint.

    NOTE: Phải build URL thủ công — requests tự encode '$' → '%24' làm OData API trả 400.
    """
    # Không dùng $format — API trả JSON mặc định, $format=json bị từ chối với 400
    url = (
        f"{FLUMART_URL}"
        f"?$top={top}"
        f"&$skip={skip}"
        f"&$filter=ISO_YEAR%20ge%20{from_year}"
        f"&$select=COUNTRY_CODE,ISO_YEAR,ISO_WEEK,INF_A,INF_B"
    )
    r = requests.get(url, timeout=120)
    r.raise_for_status()
    return r.json().get("value", [])


def fetch_all(from_year: int) -> pd.DataFrame:
    """Pull tất cả data từ FluMart kể từ from_year, paginate."""
    print(f"  Fetching FluMart from year {from_year}...")
    all_rows: list[dict] = []
    skip = 0
    while True:
        batch = fetch_flunet_batch(from_year, skip=skip, top=PAGE_SIZE)
        if not batch:
            break
        all_rows.extend(batch)
        print(f"    +{len(batch):,} rows (total {len(all_rows):,})")
        if len(batch) < PAGE_SIZE:
            break
        skip += PAGE_SIZE

    df = pd.DataFrame(all_rows)
    if df.empty:
        return df

    missing = NEEDED_COLUMNS - set(df.columns)
    if missing:
        raise RuntimeError(f"FluMart response thiếu columns: {missing}")
    return df


def compute_inf_total(df: pd.DataFrame) -> pd.DataFrame:
    """
    Tính inf_total = INF_A + INF_B (decision CLAUDE.md — không dùng INF_ALL).
    Dedup bằng groupby — FluNet có thể trả nhiều dòng cho cùng (country, year, week).
    """
    df = df.copy()
    df["INF_A"] = pd.to_numeric(df["INF_A"], errors="coerce").fillna(0)
    df["INF_B"] = pd.to_numeric(df["INF_B"], errors="coerce").fillna(0)

    # Aggregate trước: sum theo (COUNTRY_CODE, ISO_YEAR, ISO_WEEK)
    df = (
        df.groupby(["COUNTRY_CODE", "ISO_YEAR", "ISO_WEEK"], as_index=False)
        .agg(INF_A=("INF_A", "sum"), INF_B=("INF_B", "sum"))
    )

    df["inf_total"] = (df["INF_A"] + df["INF_B"]).astype(int)
    df["transformed_value"] = np.log1p(df["inf_total"]).astype(float)
    return df


def upsert_disease_cases(
    cur,
    df: pd.DataFrame,
    disease_id: int,
    source_id: int,
    countries_in_db: set[str],
    dry_run: bool = False,
) -> int:
    """UPSERT df vào disease_cases. Trả về số rows upserted."""
    # Filter countries có trong DB (master list từ seed_countries.py)
    before = len(df)
    df = df[df["COUNTRY_CODE"].isin(countries_in_db)]
    skipped = before - len(df)
    if skipped > 0:
        print(f"    Skipped {skipped:,} rows — country không có trong DB master")

    if df.empty:
        return 0

    rows = []
    for r in df.itertuples(index=False):
        rows.append((
            disease_id,
            str(r.COUNTRY_CODE),
            source_id,
            int(r.ISO_YEAR),
            int(r.ISO_WEEK),
            int(r.inf_total),
            float(r.transformed_value),
            1,  # data_quality
        ))

    if dry_run:
        print(f"    [DRY-RUN] Would upsert {len(rows):,} rows")
        print(f"    Sample (3 rows): {rows[:3]}")
        return 0

    execute_values(
        cur,
        """
        INSERT INTO disease_cases
            (disease_id, iso3, source_id, iso_year, iso_week,
             raw_count, transformed_value, data_quality)
        VALUES %s
        ON CONFLICT (disease_id, iso3, iso_year, iso_week, source_id)
        DO UPDATE SET
            raw_count         = EXCLUDED.raw_count,
            transformed_value = EXCLUDED.transformed_value,
            data_quality      = EXCLUDED.data_quality
        """,
        rows,
        page_size=2000,
    )
    return len(rows)


def main():
    ap = argparse.ArgumentParser(description="Sync WHO FluNet → DB disease_cases")
    ap.add_argument("--from-year", type=int, default=2020,
                    help="Pull data từ năm này trở đi (default 2020)")
    ap.add_argument("--countries", type=str, default=None,
                    help="Comma-separated iso3 codes để filter (default tất cả)")
    ap.add_argument("--dry-run", action="store_true",
                    help="Không INSERT, chỉ preview")
    ap.add_argument("--trigger", type=str, default="manual",
                    choices=["manual", "scheduled", "api", "event"],
                    help="Loại trigger ghi vào pipeline_runs")
    args = ap.parse_args()

    print("=" * 60)
    print("  sync_flunet.py — WHO FluMart → disease_cases")
    print("=" * 60)
    print(f"  from_year: {args.from_year}")
    print(f"  dry_run:   {args.dry_run}")
    if args.countries:
        print(f"  countries: {args.countries}")
    print()

    with track_run(
        "sync_flunet",
        trigger_type=args.trigger,
        metadata={"from_year": args.from_year, "dry_run": args.dry_run,
                  "countries": args.countries},
    ) as stats:
        # ── Fetch ──
        df = fetch_all(args.from_year)
        if df.empty:
            print("Không có data trả về — kết thúc.")
            stats["rows_processed"] = 0
            return
        print(f"  Total raw rows: {len(df):,}")
        stats["rows_processed"] = len(df)

        if args.countries:
            wanted = {c.strip().upper() for c in args.countries.split(",")}
            df = df[df["COUNTRY_CODE"].isin(wanted)]
            print(f"  After country filter: {len(df):,}")

        df = compute_inf_total(df)
        print(f"  inf_total: min={df['inf_total'].min()}, max={df['inf_total'].max()}, "
              f"mean={df['inf_total'].mean():.1f}")

        conn = psycopg2.connect(DB_URL)
        conn.autocommit = False
        cur = conn.cursor()

        try:
            cur.execute("SELECT id FROM diseases WHERE code='flu'")
            row = cur.fetchone()
            if not row:
                raise RuntimeError("Disease 'flu' chưa có trong DB — chạy db_init.sql trước")
            flu_id = row[0]

            cur.execute("SELECT id FROM data_sources WHERE code='FluNet'")
            row = cur.fetchone()
            if not row:
                raise RuntimeError("Data source 'FluNet' chưa có — chạy db_init.sql trước")
            source_id = row[0]

            cur.execute("SELECT iso3 FROM countries")
            countries_in_db = {r[0] for r in cur.fetchall()}
            print(f"  Countries trong DB: {len(countries_in_db)}")

            n_upserted = upsert_disease_cases(
                cur, df, flu_id, source_id, countries_in_db, dry_run=args.dry_run,
            )
            stats["rows_inserted"] = n_upserted

            if not args.dry_run:
                conn.commit()
                print(f"\n  Upserted {n_upserted:,} rows vào disease_cases.")
                cur.execute("""
                    SELECT MIN(iso_year), MAX(iso_year), COUNT(DISTINCT iso3), COUNT(*)
                    FROM disease_cases WHERE disease_id=%s AND source_id=%s
                """, (flu_id, source_id))
                r = cur.fetchone()
                print(f"  DB disease_cases flu: {r[0]}-{r[1]}, {r[2]} countries, {r[3]:,} rows total")
            else:
                conn.rollback()
                print("\n  [DRY-RUN] Không commit.")
        except Exception as e:
            conn.rollback()
            print(f"\nERROR: {e}")
            raise
        finally:
            cur.close()
            conn.close()


if __name__ == "__main__":
    main()
