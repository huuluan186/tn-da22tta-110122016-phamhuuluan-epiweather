"""
feature_builder.py — Tính lag features từ disease_cases + weather_observations
→ UPSERT feature_snapshots.

Phase A-2: bridge giữa raw realtime data (Phase A-1) và /forecast endpoint (Phase C-2).

Flu features (16):
  flu_log_lag1,2,3  flu_log_rollmean4,8
  temp_c_lag3,7  humidity_pct_lag1,7  solar_wm2_lag7  dewpoint_c_lag1
  iso_week_sin  iso_week_cos  iso_year  HEMISPHERE_NH  HEMISPHERE_SH

Dengue features (15):
  deng_log_lag6,8,10,12,14  deng_log_rollmean4,8
  temp_c_lag11  dewpoint_c_lag8  precip_mm_lag6  humidity_pct_lag1  solar_wm2_lag16
  iso_week_sin  iso_week_cos  iso_year

Usage:
  python scripts/feature_builder.py --disease flu --from-year 2020
  python scripts/feature_builder.py --disease dengue --countries BRA,IDN,COL --from-year 2024
  python scripts/feature_builder.py --disease flu --weeks-back 12 --countries VNM,THA,IDN --dry-run
"""

import argparse
import math
import os
import sys
from datetime import date, timedelta
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import numpy as np
import pandas as pd
import psycopg2
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _pipeline_logger import track_run  # noqa: E402
from psycopg2.extras import execute_values, Json

load_dotenv()

DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:111111111@localhost:5432/kltn_epiweather",
)

# ── Feature definitions ───────────────────────────────────────────────────────

FLU_FEATURES = [
    "flu_log_lag1", "flu_log_lag2", "flu_log_lag3",
    "flu_log_rollmean4", "flu_log_rollmean8",
    "flu_log_velocity", "flu_log_accel",
    "temp_c_lag3", "temp_c_lag7",
    "humidity_pct_lag1", "humidity_pct_lag7",
    "solar_wm2_lag7", "dewpoint_c_lag1",
    "iso_week_sin", "iso_week_cos", "iso_year",
    "HEMISPHERE_NH", "HEMISPHERE_SH",
]

DENGUE_FEATURES = [
    "deng_log_lag6", "deng_log_lag8", "deng_log_lag10",
    "deng_log_lag12", "deng_log_lag14",
    "deng_log_rollmean4", "deng_log_rollmean8",
    "deng_log_velocity", "deng_log_accel",
    "temp_c_lag11", "dewpoint_c_lag8", "precip_mm_lag6",
    "humidity_pct_lag1", "solar_wm2_lag16",
    "iso_week_sin", "iso_week_cos", "iso_year",
]

WEATHER_VARS = ["temp_c", "dewpoint_c", "humidity_pct", "precip_mm", "solar_wm2"]

# Warmup = số tuần tối thiểu cần trước target_week để tính đủ lags
FLU_WARMUP = 10    # max(rollmean8=8, weather_lag7=7) + buffer
DENGUE_WARMUP = 18  # max(deng_lag14=14, solar_lag16=16) + buffer
DENGUE_LATEST_VALID_DATE = date.fromisocalendar(2023, 36, 1)


# ── Helpers ───────────────────────────────────────────────────────────────────

def yw_to_int(y: int, w: int) -> int:
    """Encode (year, week) as YYYYWW int — order-preserving."""
    return y * 100 + w


def first_monday_on_or_after(d: date) -> date:
    days_ahead = (7 - d.weekday()) % 7
    return d + timedelta(days=days_ahead)


def build_dense_df(
    cur,
    disease_id: int,
    iso3: str,
    disease_col: str,
    start_date: date,
    end_date: date,
) -> pd.DataFrame:
    """
    Xây dựng DataFrame tuần liên tục (dense) từ start_date đến end_date.

    Columns: disease_col + temp_c, dewpoint_c, humidity_pct, precip_mm, solar_wm2
    Disease: fill 0 nếu không có record (không báo cáo = 0 ca).
    Weather: NaN nếu không có.
    Index: Python date (Monday của ISO week), sorted asc.
    """
    # All Mondays in [start_date, end_date]
    mondays = []
    d = first_monday_on_or_after(start_date)
    while d <= end_date:
        mondays.append(d)
        d += timedelta(weeks=1)

    if not mondays:
        return pd.DataFrame()

    start_yw = yw_to_int(*date.fromisoformat(str(start_date)).isocalendar()[:2])
    end_yw = yw_to_int(*date.fromisoformat(str(end_date)).isocalendar()[:2])

    # ── Disease cases ──────────────────────────────────────────────────────────
    cur.execute(
        """
        SELECT iso_year, iso_week, COALESCE(SUM(raw_count), 0) AS rc
        FROM disease_cases
        WHERE disease_id = %s AND iso3 = %s
          AND (iso_year * 100 + iso_week) BETWEEN %s AND %s
        GROUP BY iso_year, iso_week
        """,
        (disease_id, iso3, start_yw, end_yw),
    )
    dis_map: dict[date, float] = {}
    for iso_year, iso_week, rc in cur.fetchall():
        try:
            dis_map[date.fromisocalendar(int(iso_year), int(iso_week), 1)] = math.log1p(max(0, rc or 0))
        except (ValueError, TypeError):
            pass

    # ── Weather observations ───────────────────────────────────────────────────
    cur.execute(
        """
        SELECT iso_year, iso_week, data
        FROM weather_observations
        WHERE iso3 = %s
          AND (iso_year * 100 + iso_week) BETWEEN %s AND %s
        """,
        (iso3, start_yw, end_yw),
    )
    wea_map: dict[date, dict] = {}
    for iso_year, iso_week, data in cur.fetchall():
        try:
            wea_map[date.fromisocalendar(int(iso_year), int(iso_week), 1)] = data or {}
        except (ValueError, TypeError):
            pass

    # ── Assemble DataFrame ─────────────────────────────────────────────────────
    df = pd.DataFrame({"date": mondays})
    df.set_index("date", inplace=True)

    df[disease_col] = [dis_map.get(d, 0.0) for d in mondays]
    for var in WEATHER_VARS:
        df[var] = pd.to_numeric(
            [wea_map.get(d, {}).get(var) for d in mondays],
            errors="coerce",
        )

    return df


def compute_features(
    df: pd.DataFrame,
    disease_col: str,
    feature_names: list[str],
    hemisphere_nh: float,
    hemisphere_sh: float,
) -> pd.DataFrame:
    """
    Tính tất cả các cột lag/rollmean/seasonal cần thiết.
    Trả về df với thêm các feature columns.
    """
    d = df.copy()

    # ── Disease lags ──────────────────────────────────────────────────────────
    needed_dis_lags = [
        int(c.split("_lag")[1]) for c in feature_names
        if c.startswith(disease_col + "_lag")
    ]
    for lag in set(needed_dis_lags):
        d[f"{disease_col}_lag{lag}"] = d[disease_col].shift(lag)

    # rollmean: shift(1) rồi rolling(K).mean() → mean của lag1..lagK
    if f"{disease_col}_rollmean4" in feature_names:
        d[f"{disease_col}_rollmean4"] = d[disease_col].shift(1).rolling(4).mean()
    if f"{disease_col}_rollmean8" in feature_names:
        d[f"{disease_col}_rollmean8"] = d[disease_col].shift(1).rolling(8).mean()

    # Trend features: velocity = log growth rate, accel = change in growth rate
    if f"{disease_col}_velocity" in feature_names:
        if disease_col.startswith("flu"):
            # flu: dùng lag1, lag2, lag3
            d[f"{disease_col}_velocity"] = d[f"{disease_col}_lag1"] - d[f"{disease_col}_lag2"]
            d[f"{disease_col}_accel"]    = (d[f"{disease_col}_lag1"] - d[f"{disease_col}_lag2"]) - (d[f"{disease_col}_lag2"] - d[f"{disease_col}_lag3"])
        else:
            # dengue: dùng lag6, lag8, lag10
            d[f"{disease_col}_velocity"] = d[f"{disease_col}_lag6"]  - d[f"{disease_col}_lag8"]
            d[f"{disease_col}_accel"]    = (d[f"{disease_col}_lag6"] - d[f"{disease_col}_lag8"]) - (d[f"{disease_col}_lag8"] - d[f"{disease_col}_lag10"])

    # ── Weather lags ──────────────────────────────────────────────────────────
    for var in WEATHER_VARS:
        needed_w_lags = [
            int(c.split(f"{var}_lag")[1]) for c in feature_names
            if c.startswith(f"{var}_lag")
        ]
        for lag in set(needed_w_lags):
            d[f"{var}_lag{lag}"] = d[var].shift(lag)

    # ── Seasonal ──────────────────────────────────────────────────────────────
    cal = [(dt.isocalendar()[0], dt.isocalendar()[1]) for dt in d.index]
    years = [y for y, _ in cal]
    weeks = [w for _, w in cal]

    d["iso_year"] = years
    d["iso_week_sin"] = [math.sin(2 * math.pi * w / 52.18) for w in weeks]
    d["iso_week_cos"] = [math.cos(2 * math.pi * w / 52.18) for w in weeks]

    # ── Hemisphere ────────────────────────────────────────────────────────────
    d["HEMISPHERE_NH"] = hemisphere_nh
    d["HEMISPHERE_SH"] = hemisphere_sh

    return d


def extract_feature_dicts(
    df: pd.DataFrame,
    feature_names: list[str],
    target_dates: set[date],
) -> dict[tuple[int, int], dict]:
    """
    Trả về {(iso_year, iso_week): feature_dict} chỉ cho target_dates,
    bỏ qua rows có NaN trong bất kỳ feature nào.
    """
    results = {}
    for dt, row in df.iterrows():
        if dt not in target_dates:
            continue
        cal = dt.isocalendar()
        iso_year, iso_week = cal[0], cal[1]
        feat = {}
        valid = True
        for f in feature_names:
            val = row.get(f)
            if val is None or (isinstance(val, float) and math.isnan(val)):
                valid = False
                break
            feat[f] = float(val)
        if valid:
            results[(iso_year, iso_week)] = feat
    return results


def upsert_feature_snapshots(
    cur,
    disease_id: int,
    iso3: str,
    feature_dicts: dict[tuple[int, int], dict],
    feature_version: str = "v1",
    dry_run: bool = False,
) -> int:
    if not feature_dicts:
        return 0

    rows = [
        (disease_id, iso3, y, w, Json(feat), feature_version)
        for (y, w), feat in feature_dicts.items()
    ]

    if dry_run:
        print(f"    [DRY-RUN] {iso3}: would upsert {len(rows)} feature snapshots")
        if rows:
            (y, w), feat = next(iter(feature_dicts.items()))
            print(f"    Sample {iso3} W{w}/{y}: {feat}")
        return 0

    execute_values(
        cur,
        """
        INSERT INTO feature_snapshots
            (disease_id, iso3, iso_year, iso_week, features, feature_version)
        VALUES %s
        ON CONFLICT (disease_id, iso3, iso_year, iso_week, feature_version)
        DO UPDATE SET
            features   = EXCLUDED.features,
            updated_at = NOW()
        """,
        rows,
        page_size=500,
    )
    return len(rows)


def process_country(
    cur,
    disease_id: int,
    iso3: str,
    disease_col: str,
    feature_names: list[str],
    warmup_weeks: int,
    hemisphere_nh: float,
    hemisphere_sh: float,
    target_weeks: list[tuple[int, int]],
    dry_run: bool = False,
) -> int:
    if not target_weeks:
        return 0

    # Date range cho dense build (warmup + target window)
    target_dates = {date.fromisocalendar(y, w, 1) for y, w in target_weeks}
    earliest_target = min(target_dates)
    latest_target = max(target_dates)

    start_date = earliest_target - timedelta(weeks=warmup_weeks)
    end_date = latest_target  # target week itself (lag cols go back, not forward)

    df = build_dense_df(cur, disease_id, iso3, disease_col, start_date, end_date)
    if df.empty:
        return 0

    df = compute_features(df, disease_col, feature_names, hemisphere_nh, hemisphere_sh)

    feature_dicts = extract_feature_dicts(df, feature_names, target_dates)
    n = upsert_feature_snapshots(cur, disease_id, iso3, feature_dicts, dry_run=dry_run)
    return n


def main():
    ap = argparse.ArgumentParser(description="Build feature snapshots từ disease_cases + weather_observations")
    ap.add_argument("--disease", required=True, choices=["flu", "dengue"],
                    help="Disease: flu hoặc dengue")
    ap.add_argument("--from-year", type=int, default=2020,
                    help="Bắt đầu từ năm này (default 2020)")
    ap.add_argument("--to-year", type=int, default=None,
                    help="Kết thúc năm này (default: năm hiện tại)")
    ap.add_argument("--weeks-back", type=int, default=None,
                    help="Override: chỉ build N tuần gần nhất")
    ap.add_argument("--countries", type=str, default=None,
                    help="Comma-separated iso3 codes (default: tất cả)")
    ap.add_argument("--dry-run", action="store_true",
                    help="Preview, không UPSERT")
    ap.add_argument("--feature-version", type=str, default="v1",
                    help="Feature version tag (default v1)")
    ap.add_argument("--trigger", type=str, default="manual",
                    choices=["manual", "scheduled", "api", "event"])
    args = ap.parse_args()

    # Disease config
    if args.disease == "flu":
        disease_col = "flu_log"
        feature_names = FLU_FEATURES
        warmup_weeks = FLU_WARMUP
        disease_code = "flu"
    else:
        disease_col = "deng_log"
        feature_names = DENGUE_FEATURES
        warmup_weeks = DENGUE_WARMUP
        disease_code = "dengue"

    # Target week range
    today = date.today()
    if args.weeks_back:
        end_date = today
        start_date = today - timedelta(weeks=args.weeks_back)
    else:
        end_year = args.to_year or today.year
        start_date = date(args.from_year, 1, 1)
        end_date = min(date(end_year, 12, 31), today)

    # Dengue: OpenDengue v1.3 hiện chỉ hợp lệ tới 2023-W36.
    # Không build feature cho các tuần sau mốc này, kể cả khi DB còn dòng sinh thừa.
    if args.disease == "dengue" and not args.weeks_back:
        end_date = min(end_date, DENGUE_LATEST_VALID_DATE)

    # Dengue: nếu user không override to-year thì vẫn lấy thêm năm cuối có trong DB,
    # nhưng không vượt quá cutoff hợp lệ phía trên.
    if args.disease == "dengue" and not args.weeks_back and args.to_year is None:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        try:
            cur.execute(
                """
                SELECT MAX(dc.iso_year)
                FROM disease_cases dc
                JOIN diseases d ON d.id = dc.disease_id
                WHERE d.code = %s
                """,
                ("dengue",),
            )
            max_year = cur.fetchone()[0]
            if max_year:
                end_date = min(end_date, date(int(max_year), 12, 31), DENGUE_LATEST_VALID_DATE)
        finally:
            cur.close()
            conn.close()

    if start_date > end_date:
        print("=" * 60)
        print(f"  feature_builder.py — {disease_code} features → feature_snapshots")
        print("=" * 60)
        print(f"  Không có tuần hợp lệ để build: {start_date} > {end_date}")
        return

    # Enumerate target weeks in range
    target_weeks = []
    d = first_monday_on_or_after(start_date)
    while d <= end_date:
        cal = d.isocalendar()
        target_weeks.append((cal[0], cal[1]))
        d += timedelta(weeks=1)

    print("=" * 60)
    print(f"  feature_builder.py — {disease_code} features → feature_snapshots")
    print("=" * 60)
    print(f"  Date range:      {start_date} → {end_date} ({len(target_weeks)} tuần)")
    print(f"  Feature version: {args.feature_version}")
    print(f"  Features ({len(feature_names)}): {feature_names[:4]}...")
    print(f"  Dry run:         {args.dry_run}")
    if args.countries:
        print(f"  Countries:       {args.countries}")
    print()

    with track_run(
        f"build_features_{disease_code}",
        trigger_type=args.trigger,
        metadata={"disease": disease_code, "start": str(start_date), "end": str(end_date),
                  "n_weeks": len(target_weeks), "feature_version": args.feature_version,
                  "dry_run": args.dry_run},
    ) as stats:
        conn = psycopg2.connect(DB_URL)
        conn.autocommit = False
        cur = conn.cursor()

        try:
            cur.execute("SELECT id FROM diseases WHERE code = %s", (disease_code,))
            row = cur.fetchone()
            if not row:
                raise RuntimeError(f"Disease '{disease_code}' chưa có trong DB — chạy db_init.sql trước")
            disease_id = row[0]

            wanted = None
            if args.countries:
                wanted = {c.strip().upper() for c in args.countries.split(",")}

            cur.execute(
                "SELECT iso3, latitude FROM countries WHERE latitude IS NOT NULL ORDER BY iso3"
            )
            all_countries = cur.fetchall()
            if disease_code == "dengue" and not wanted:
                cur.execute(
                    "SELECT DISTINCT iso3 FROM disease_cases WHERE disease_id = %s",
                    (disease_id,),
                )
                dengue_iso3 = {r[0] for r in cur.fetchall()}
                all_countries = [c for c in all_countries if c[0] in dengue_iso3]
            if wanted:
                all_countries = [c for c in all_countries if c[0] in wanted]
            print(f"  Countries to process: {len(all_countries)}")
            stats["rows_processed"] = len(all_countries) * len(target_weeks)

            total_upserted = 0
            skipped_no_weather = 0

            for i, (iso3, lat) in enumerate(all_countries, 1):
                nh = 1.0 if (lat or 0) >= 0 else 0.0
                sh = 1.0 - nh

                n = process_country(
                    cur=cur,
                    disease_id=disease_id,
                    iso3=iso3,
                    disease_col=disease_col,
                    feature_names=feature_names,
                    warmup_weeks=warmup_weeks,
                    hemisphere_nh=nh,
                    hemisphere_sh=sh,
                    target_weeks=target_weeks,
                    dry_run=args.dry_run,
                )

                if not args.dry_run and n > 0:
                    conn.commit()

                total_upserted += n
                if n == 0:
                    skipped_no_weather += 1

                if n > 0 or args.dry_run:
                    print(f"  [{i:3d}/{len(all_countries)}] {iso3}: {n} snapshots")
                elif i % 20 == 0:
                    print(f"  [{i:3d}/{len(all_countries)}] ... (skipped {skipped_no_weather} so far, no data)")

            stats["rows_inserted"] = total_upserted
            stats["rows_skipped"] = skipped_no_weather

            print()
            print(f"  Tổng: {total_upserted:,} feature snapshots upserted")
            print(f"  Skipped (no data): {skipped_no_weather}")

            if not args.dry_run:
                cur.execute(
                    """
                    SELECT MIN(iso_year), MAX(iso_year), COUNT(DISTINCT iso3), COUNT(*)
                    FROM feature_snapshots
                    WHERE disease_id = %s AND feature_version = %s
                    """,
                    (disease_id, args.feature_version),
                )
                r = cur.fetchone()
                print(f"\n  DB feature_snapshots ({disease_code} v{args.feature_version[-1]}): "
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
