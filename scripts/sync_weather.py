"""
sync_weather.py — Pull weather từ Open-Meteo Archive → bảng weather_observations.

Source: Open-Meteo Archive API (free, no key, dùng ERA5 reanalysis dưới underneath).
  https://archive-api.open-meteo.com/v1/archive

Variables pulled (khớp 5 weather features model dùng):
  - temperature_2m         → temp_c
  - dew_point_2m           → dewpoint_c
  - relative_humidity_2m   → humidity_pct
  - precipitation          → precip_mm
  - shortwave_radiation    → solar_wm2

Aggregation: hourly raw → weekly mean per (iso3, iso_year, iso_week).

Usage:
  python scripts/sync_weather.py --from-year 2020 --to-year 2026
  python scripts/sync_weather.py --countries VNM,THA,IDN --from-year 2024 --dry-run
  python scripts/sync_weather.py --weeks-back 12     # chỉ pull 12 tuần gần nhất

Cron schedule: hằng ngày 6:00 ICT (Open-Meteo cập nhật daily).
"""

import argparse
import os
import sys
import time
import warnings
from datetime import date, timedelta
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import numpy as np
import pandas as pd
import psycopg2
import requests
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _pipeline_logger import track_run  # noqa: E402
from psycopg2.extras import execute_values, Json

warnings.filterwarnings("ignore")
load_dotenv()

DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:111111111@localhost:5432/kltn_epiweather",
)

OPEN_METEO_URL = "https://archive-api.open-meteo.com/v1/archive"

# Mapping Open-Meteo var → tên feature model dùng
VAR_MAP = {
    "temperature_2m":       "temp_c",
    "dew_point_2m":         "dewpoint_c",
    "relative_humidity_2m": "humidity_pct",
    "precipitation":        "precip_mm",
    "shortwave_radiation":  "solar_wm2",
}


def fetch_country_weather(
    lat: float,
    lon: float,
    start_date: str,
    end_date: str,
    timeout: int = 60,
) -> pd.DataFrame:
    """Pull hourly weather 1 quốc gia từ Open-Meteo Archive."""
    params = {
        "latitude":  lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date":   end_date,
        "hourly": ",".join(VAR_MAP.keys()),
        "timezone": "UTC",
    }
    r = requests.get(OPEN_METEO_URL, params=params, timeout=timeout)
    r.raise_for_status()
    payload = r.json()
    hourly = payload.get("hourly")
    if not hourly:
        return pd.DataFrame()

    df = pd.DataFrame(hourly)
    df["time"] = pd.to_datetime(df["time"])
    return df


def aggregate_weekly(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate hourly → weekly mean. Trả về df có (iso_year, iso_week, ... features)."""
    if df.empty:
        return df
    df = df.copy()
    iso = df["time"].dt.isocalendar()
    df["iso_year"] = iso["year"].astype(int)
    df["iso_week"] = iso["week"].astype(int)

    feature_cols = list(VAR_MAP.keys())
    weekly = df.groupby(["iso_year", "iso_week"])[feature_cols].mean().reset_index()
    weekly = weekly.rename(columns=VAR_MAP)
    return weekly


def ensure_open_meteo_source(cur) -> int:
    """Tạo data_source 'OpenMeteo' nếu chưa có. Trả về id."""
    cur.execute("SELECT id FROM data_sources WHERE code='OpenMeteo'")
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute(
        """
        INSERT INTO data_sources (code, source_type, update_frequency, spatial_coverage, description)
        VALUES ('OpenMeteo', 'weather', 'daily', 'global', 'Open-Meteo Archive API (ERA5 reanalysis)')
        RETURNING id
        """
    )
    return cur.fetchone()[0]


def upsert_weather(
    cur,
    iso3: str,
    weekly: pd.DataFrame,
    source_id: int,
    dry_run: bool = False,
) -> int:
    if weekly.empty:
        return 0

    rows = []
    feature_cols = list(VAR_MAP.values())  # temp_c, dewpoint_c, ...
    for r in weekly.itertuples(index=False):
        data = {col: float(getattr(r, col)) for col in feature_cols if not pd.isna(getattr(r, col))}
        if not data:
            continue
        rows.append((iso3, source_id, int(r.iso_year), int(r.iso_week), Json(data)))

    if dry_run:
        if rows:
            print(f"    [DRY-RUN] {iso3}: would upsert {len(rows)} weeks, sample: {rows[0]}")
        return 0

    execute_values(
        cur,
        """
        INSERT INTO weather_observations (iso3, source_id, iso_year, iso_week, data)
        VALUES %s
        ON CONFLICT (iso3, source_id, iso_year, iso_week) DO UPDATE SET data = EXCLUDED.data
        """,
        rows,
        page_size=500,
    )
    return len(rows)


def main():
    ap = argparse.ArgumentParser(description="Sync Open-Meteo Archive → weather_observations")
    ap.add_argument("--from-year", type=int, default=2020)
    ap.add_argument("--to-year",   type=int, default=date.today().year)
    ap.add_argument("--weeks-back", type=int, default=None,
                    help="Override: chỉ pull N tuần gần nhất (bỏ qua --from-year / --to-year)")
    ap.add_argument("--countries", type=str, default=None,
                    help="Comma-separated iso3 codes")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--sleep", type=float, default=0.3,
                    help="Sleep giây giữa API calls (avoid rate limit)")
    ap.add_argument("--trigger", type=str, default="manual",
                    choices=["manual", "scheduled", "api", "event"])
    args = ap.parse_args()

    # Determine date range
    if args.weeks_back:
        end = date.today()
        start = end - timedelta(weeks=args.weeks_back)
    else:
        start = date(args.from_year, 1, 1)
        end   = min(date(args.to_year, 12, 31), date.today() - timedelta(days=1))

    print("=" * 60)
    print("  sync_weather.py — Open-Meteo Archive → weather_observations")
    print("=" * 60)
    print(f"  Date range: {start} → {end}")
    print(f"  dry_run:    {args.dry_run}")
    if args.countries:
        print(f"  countries:  {args.countries}")
    print()

    with track_run(
        "sync_weather",
        trigger_type=args.trigger,
        metadata={"start": str(start), "end": str(end), "dry_run": args.dry_run,
                  "weeks_back": args.weeks_back},
    ) as stats:
        conn = psycopg2.connect(DB_URL)
        conn.autocommit = False
        cur = conn.cursor()

        try:
            source_id = ensure_open_meteo_source(cur)
            conn.commit()

            wanted = None
            if args.countries:
                wanted = {c.strip().upper() for c in args.countries.split(",")}

            cur.execute(
                """SELECT iso3, country_name, latitude, longitude FROM countries
                   WHERE latitude IS NOT NULL AND longitude IS NOT NULL
                   ORDER BY iso3"""
            )
            all_countries = cur.fetchall()
            if wanted:
                all_countries = [c for c in all_countries if c[0] in wanted]
            print(f"  Countries to sync: {len(all_countries)}")
            stats["rows_processed"] = len(all_countries)

            start_str, end_str = start.isoformat(), end.isoformat()
            total_upserted = 0
            failures: list = []

            for i, (iso3, name, lat, lon) in enumerate(all_countries, 1):
                try:
                    raw = fetch_country_weather(lat, lon, start_str, end_str)
                    weekly = aggregate_weekly(raw)
                    n = upsert_weather(cur, iso3, weekly, source_id, dry_run=args.dry_run)
                    total_upserted += n
                    if not args.dry_run:
                        conn.commit()
                    print(f"  [{i:3d}/{len(all_countries)}] {iso3} ({name[:30]}): {n} weeks")
                except Exception as e:
                    conn.rollback()
                    failures.append({"iso3": iso3, "error": str(e)[:200]})
                    print(f"  [{i:3d}/{len(all_countries)}] {iso3}: ERROR — {str(e)[:80]}")

                time.sleep(args.sleep)

            stats["rows_inserted"] = total_upserted
            stats["rows_skipped"] = len(failures)
            if failures:
                stats["errors"] = failures

            print(f"\n  Total upserted: {total_upserted:,} weather observations")
            if failures:
                print(f"  Failures ({len(failures)}):")
                for f in failures[:10]:
                    print(f"    {f['iso3']}: {f['error'][:80]}")

            if not args.dry_run:
                cur.execute("""
                    SELECT MIN(iso_year), MAX(iso_year), COUNT(DISTINCT iso3), COUNT(*)
                    FROM weather_observations WHERE source_id=%s
                """, (source_id,))
                r = cur.fetchone()
                print(f"  DB weather_observations (OpenMeteo): "
                      f"{r[0]}-{r[1]}, {r[2]} countries, {r[3]:,} rows total")

        except Exception as e:
            conn.rollback()
            print(f"\nERROR: {e}")
            raise
        finally:
            cur.close()
            conn.close()


if __name__ == "__main__":
    main()
