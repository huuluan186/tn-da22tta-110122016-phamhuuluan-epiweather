"""
load_features.py — Load pre-computed features từ CSV vào bảng feature_snapshots.

Cần chạy SAU:
  1. psql -f scripts/db_init.sql                     (tạo schema)
  2. psql -f scripts/db_migrate_feature_snapshots.sql (tạo bảng features)
  3. python scripts/seed_countries.py                 (seed countries)

Sau bước này, API /forecast có thể query features theo (disease, iso3, year, week).
"""

import json
import os
import sys
import warnings
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import numpy as np
import pandas as pd
import psycopg2
import psycopg2.extensions
from dotenv import load_dotenv
from psycopg2.extras import execute_values

psycopg2.extensions.register_adapter(np.int64, lambda x: psycopg2.extensions.AsIs(int(x)))
psycopg2.extensions.register_adapter(np.float64, lambda x: psycopg2.extensions.AsIs(float(x)))

warnings.filterwarnings("ignore")
load_dotenv()

BASE = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE / "ml_models"
PROCESSED = BASE / "data" / "processed"

DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:111111111@localhost:5432/kltn_epiweather",
)

# Mỗi disease: file CSV + feature columns lấy từ regressor v1 features.json
FEATURE_FILES = {
    "flu":    PROCESSED / "features_flu_v1.csv",
    "dengue": PROCESSED / "features_dengue_v1.csv",
}

# Lấy feature columns từ regressor h1 metadata (model production backend load
# để forecast). Set h1 (flu 16 / dengue 15 cột) khớp đúng cột trong CSV training.
# Không dùng base v2 vì v2 thêm velocity/accel — hai cột này CSV không có.
FEATURE_META = {
    "flu":    MODELS_DIR / "lgbm_flu_regressor_h1_v1_features.json",
    "dengue": MODELS_DIR / "rf_dengue_regressor_h1_v1_features.json",
}


def load_feature_columns(disease: str) -> list[str]:
    with open(FEATURE_META[disease]) as f:
        meta = json.load(f)
    return meta["features"]


def load_disease_features(cur, disease: str, feature_cols: list[str]):
    cur.execute("SELECT id FROM diseases WHERE code=%s", (disease,))
    row = cur.fetchone()
    if not row:
        raise RuntimeError(f"Disease '{disease}' chưa có trong DB — chạy db_init.sql trước")
    disease_id = row[0]

    df = pd.read_csv(FEATURE_FILES[disease])

    # Verify tất cả feature columns có trong DataFrame
    missing = [c for c in feature_cols if c not in df.columns]
    if missing:
        raise RuntimeError(f"Thiếu cột trong {FEATURE_FILES[disease]}: {missing}")

    print(f"  {disease}: {len(df):,} rows × {len(feature_cols)} features")

    # Build rows for INSERT
    rows = []
    for r in df.itertuples(index=False):
        features_dict = {col: float(getattr(r, col)) for col in feature_cols}
        rows.append((
            disease_id,
            str(r.iso3),
            int(r.iso_year),
            int(r.iso_week),
            json.dumps(features_dict),
            "v1",
        ))

    # Batch insert
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
        page_size=2000,
    )
    print(f"  {disease}: inserted/updated {len(rows):,} feature_snapshots")


def main():
    print("=" * 60)
    print("  load_features.py — feature_snapshots")
    print("=" * 60)

    conn = psycopg2.connect(DB_URL)
    conn.autocommit = False
    cur = conn.cursor()

    try:
        # Sanity check: bảng tồn tại?
        cur.execute("""
            SELECT 1 FROM information_schema.tables
            WHERE table_name = 'feature_snapshots'
        """)
        if not cur.fetchone():
            raise RuntimeError(
                "Bảng feature_snapshots chưa tồn tại — chạy:\n"
                "  psql -U postgres -d kltn_epiweather -f scripts/db_migrate_feature_snapshots.sql"
            )

        for disease in ["flu", "dengue"]:
            feature_cols = load_feature_columns(disease)
            print(f"\n[{disease}] features: {feature_cols[:5]}... ({len(feature_cols)} cols)")
            load_disease_features(cur, disease, feature_cols)
            conn.commit()

        print("\nVerifying:")
        cur.execute("""
            SELECT d.code, COUNT(*) AS n_rows,
                   MIN(iso_year) AS min_year, MAX(iso_year) AS max_year,
                   COUNT(DISTINCT iso3) AS n_countries
            FROM feature_snapshots fs
            JOIN diseases d ON d.id = fs.disease_id
            GROUP BY d.code
            ORDER BY d.code
        """)
        for r in cur.fetchall():
            print(f"  {r[0]}: {r[1]:,} rows, {r[2]}-{r[3]}, {r[4]} countries")

        print("\nDone. API /forecast giờ có thể query features từ DB.")

    except Exception as e:
        conn.rollback()
        print(f"\nERROR: {e}")
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
