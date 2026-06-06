"""
Bootstrap a fresh Docker PostgreSQL database with the project seed data.

Intended usage:
  docker compose run --rm scheduler python scripts/bootstrap_db.py
"""

import subprocess
import sys
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

import os

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:111111111@localhost:5432/kltn_epiweather",
)


def execute_sql(path: Path) -> None:
    sql = path.read_text(encoding="utf-8")
    conn = psycopg2.connect(DB_URL)
    conn.autocommit = False
    cur = conn.cursor()
    try:
        cur.execute(sql)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def run_script(name: str) -> None:
    cmd = [sys.executable, str(PROJECT_ROOT / "scripts" / name)]
    print(f"[bootstrap] running: {' '.join(cmd)}", flush=True)
    subprocess.run(cmd, cwd=PROJECT_ROOT, check=True)


def main() -> None:
    print("[bootstrap] applying feature_snapshots migration", flush=True)
    execute_sql(PROJECT_ROOT / "scripts" / "db_migrate_feature_snapshots.sql")
    print("[bootstrap] applying predictions risk_probability migration", flush=True)
    execute_sql(PROJECT_ROOT / "scripts" / "db_migrate_predictions_risk_probability.sql")

    run_script("seed_countries.py")
    run_script("load_db_v2.py")
    run_script("load_features.py")
    print("[bootstrap] done", flush=True)


if __name__ == "__main__":
    main()
