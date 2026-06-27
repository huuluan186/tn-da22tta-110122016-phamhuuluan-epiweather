"""
load_db_v2.py — Seed DB kltn_epiweather từ artifacts production (LightGBM + RF + XGBClassifier).

Loader chính thức (thay load_db.py cũ đã xoá):
  - Paths: data/processed/, ml_models/ (đổi từ dataset/, models/)
  - Per-model metadata: *_features.json + *_metrics.json (thay vì 1 file tổng)
  - 4 model: lgbm_flu_regressor_v2, rf_dengue_regressor_v2,
             xgb_flu_classifier_v4, xgb_dengue_classifier_v4 (classifier v4 = fix encoding LabelEncoder)
  - Tránh model.get_xgb_params() — gọi __dict__ thông qua to_dict generic
  - Risk level lấy TRỰC TIẾP từ XGBClassifier (nhãn endemic channel Bortman 1999),
    KHÔNG dùng ngưỡng phân vị q33/q67 (đã bỏ hẳn để tránh hai method mâu thuẫn)

Tiền điều kiện:
  1. psql -U postgres -d kltn_epiweather -f scripts/db_init.sql
  2. python scripts/seed_countries.py
  Sau đó:
  3. python scripts/load_db_v2.py
"""

import json
import os
import sys
import warnings
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import joblib
import numpy as np
import pandas as pd
import psycopg2
import psycopg2.extensions
from dotenv import load_dotenv
from psycopg2.extras import execute_values

psycopg2.extensions.register_adapter(np.int64, lambda x: psycopg2.extensions.AsIs(int(x)))
psycopg2.extensions.register_adapter(np.float64, lambda x: psycopg2.extensions.AsIs(float(x)))
psycopg2.extensions.register_adapter(np.bool_, lambda x: psycopg2.extensions.AsIs(bool(x)))

warnings.filterwarnings("ignore")
load_dotenv()

BASE = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE / "ml_models"
PROCESSED = BASE / "data" / "processed"

FLU_FEATURES = PROCESSED / "features_flu_v1.csv"
DENGUE_FEATURES = PROCESSED / "features_dengue_v1.csv"

DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:111111111@localhost:5432/kltn_epiweather",
)

# (disease_code, role) -> stem
ARTIFACTS = {
    ("flu", "regressor"):    "lgbm_flu_regressor_v2",
    ("dengue", "regressor"): "rf_dengue_regressor_v2",
    ("flu", "classifier"):   "xgb_flu_classifier_v4",
    ("dengue", "classifier"): "xgb_dengue_classifier_v4",
}

# Mapping cho disease_cases.raw_count + transformed_value
FEATURE_FILES = {
    "flu":    {"path": FLU_FEATURES,    "raw_col": "influenza_total", "log_col": "flu_log"},
    "dengue": {"path": DENGUE_FEATURES, "raw_col": "dengue_total",    "log_col": "deng_log"},
}


def connect():
    return psycopg2.connect(DB_URL)


def load_artifact(stem: str) -> dict:
    pkl = MODELS_DIR / f"{stem}.pkl"
    feat = MODELS_DIR / f"{stem}_features.json"
    metr = MODELS_DIR / f"{stem}_metrics.json"
    model = joblib.load(pkl)
    with open(feat) as f:
        features = json.load(f)
    metrics = {}
    if metr.exists():
        with open(metr) as f:
            metrics = json.load(f)
    return {"model": model, "features": features, "metrics": metrics}


def safe_hyperparams(model) -> dict:
    """Trích hyperparams an toàn cho LightGBM / sklearn RF / XGBoost."""
    try:
        params = model.get_params()
    except Exception:
        params = {}
    # Convert non-serializable types to str
    cleaned = {}
    for k, v in params.items():
        if isinstance(v, float) and not np.isfinite(v):
            cleaned[k] = None
            continue
        try:
            json.dumps(v, allow_nan=False)
            cleaned[k] = v
        except (TypeError, ValueError):
            cleaned[k] = str(v)
    return cleaned


# ─────────────────────────────────────────────────────────────────────────────
# 1. MODEL VERSIONS + EVALUATIONS
# ─────────────────────────────────────────────────────────────────────────────
def load_model_versions(cur) -> dict:
    """Trả dict {(disease, role): model_version_id}."""
    print("\n[1] Loading model_versions...")
    mv_ids = {}

    for (disease, role), stem in ARTIFACTS.items():
        art = load_artifact(stem)
        cur.execute("SELECT id FROM diseases WHERE code=%s", (disease,))
        row = cur.fetchone()
        if not row:
            raise RuntimeError(f"Disease '{disease}' chưa có trong DB — chạy db_init.sql trước")
        disease_id = row[0]

        meta = art["features"]
        metrics = art["metrics"]
        algorithm = meta.get("model_type", "Unknown")
        version = meta.get("version", "v1")
        version_role = f"{version}-{role}"  # phân biệt regressor/classifier cùng version

        params = safe_hyperparams(art["model"])
        artifact_path = f"ml_models/{stem}.pkl"
        description = f"{role} — {meta.get('note', algorithm)}"

        cur.execute(
            """
            INSERT INTO model_versions
                (disease_id, version, algorithm, description,
                 train_year_start, train_year_end, val_year,
                 feature_config_tag, hyperparams, artifact_path,
                 is_active, is_champion)
            VALUES (%s,%s,%s,%s, %s,%s,%s, %s,%s,%s, TRUE, %s)
            ON CONFLICT (disease_id, version) DO UPDATE SET
                is_active   = TRUE,
                hyperparams = EXCLUDED.hyperparams,
                artifact_path = EXCLUDED.artifact_path,
                description = EXCLUDED.description
            RETURNING id
            """,
            (
                disease_id, version_role, algorithm, description,
                2010, 2019, 2022,
                version, json.dumps(params), artifact_path,
                role == "regressor",  # is_champion chỉ cho regressor
            ),
        )
        mv_id = cur.fetchone()[0]
        mv_ids[(disease, role)] = mv_id

        # Evaluation từ metrics
        if metrics:
            cur.execute(
                """
                INSERT INTO model_evaluations
                    (model_version_id, eval_set, eval_type,
                     r2_score, mae, rmse, n_samples, notes)
                VALUES (%s, 'cv-walk-forward', 'cv', %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
                """,
                (
                    mv_id,
                    metrics.get("r2"),
                    metrics.get("mae"),
                    metrics.get("rmse"),
                    metrics.get("cv_folds"),
                    f"Optuna trials: {metrics.get('optuna_trials', 'n/a')}",
                ),
            )
            t22 = metrics.get("test_2022")
            if t22:
                cur.execute(
                    """
                    INSERT INTO model_evaluations
                        (model_version_id, eval_set, eval_type,
                         r2_score, mae, rmse, n_samples)
                    VALUES (%s, 'holdout_2022', 'holdout', %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                    """,
                    (mv_id, t22.get("r2"), t22.get("mae"), t22.get("rmse"), t22.get("n")),
                )

        print(f"  → {disease}/{role} {version}: id={mv_id}, algorithm={algorithm}")

    return mv_ids


# ─────────────────────────────────────────────────────────────────────────────
# 2. DISEASE CASES (ground truth)
# ─────────────────────────────────────────────────────────────────────────────
def load_disease_cases(cur):
    print("\n[2] Loading disease_cases...")

    src_map = {"flu": "FluNet", "dengue": "WHO_PAHO"}

    for disease, cfg in FEATURE_FILES.items():
        cur.execute("SELECT id FROM diseases WHERE code=%s", (disease,))
        disease_id = cur.fetchone()[0]
        cur.execute("SELECT id FROM data_sources WHERE code=%s", (src_map[disease],))
        source_id = cur.fetchone()[0]

        df = pd.read_csv(cfg["path"], usecols=["iso3", "iso_year", "iso_week", cfg["raw_col"], cfg["log_col"]])
        # Chỉ giữ rows có ground truth (raw_count notna)
        df = df.dropna(subset=[cfg["raw_col"]])

        rows = [
            (
                disease_id, str(r.iso3), source_id,
                int(r.iso_year), int(r.iso_week),
                int(getattr(r, cfg["raw_col"])),
                float(getattr(r, cfg["log_col"])),
                1,
            )
            for r in df.itertuples(index=False)
        ]

        execute_values(
            cur,
            """
            INSERT INTO disease_cases
                (disease_id, iso3, source_id, iso_year, iso_week,
                 raw_count, transformed_value, data_quality)
            VALUES %s
            ON CONFLICT (disease_id, iso3, iso_year, iso_week, source_id) DO NOTHING
            """,
            rows,
            page_size=5000,
        )
        print(f"  → {disease}: {len(rows):,} disease_case rows inserted")


# ─────────────────────────────────────────────────────────────────────────────
# 3. PREDICTIONS (run inference)
# ─────────────────────────────────────────────────────────────────────────────
def load_predictions(cur, mv_ids):
    print("\n[3] Loading predictions (running inference)...")

    for disease, cfg in FEATURE_FILES.items():
        cur.execute("SELECT id FROM diseases WHERE code=%s", (disease,))
        disease_id = cur.fetchone()[0]

        reg_art = load_artifact(ARTIFACTS[(disease, "regressor")])
        cls_art = load_artifact(ARTIFACTS[(disease, "classifier")])
        mv_id_reg = mv_ids[(disease, "regressor")]

        reg_features = reg_art["features"]["features"]
        cls_features = cls_art["features"]["features"]
        cls_classes = cls_art["features"].get("classes", ["Low", "Medium", "High"])

        df = pd.read_csv(cfg["path"])

        # Fill missing feature cols với 0 (idempotent)
        for col in set(reg_features + cls_features):
            if col not in df.columns:
                df[col] = 0.0

        X_reg = df[reg_features].values
        X_cls = df[cls_features].values

        y_pred_log = reg_art["model"].predict(X_reg)
        y_pred_cls_idx = cls_art["model"].predict(X_cls)
        # Robust với numeric labels từ XGBClassifier
        risk_labels = [cls_classes[int(i)] if isinstance(i, (int, np.integer)) else str(i) for i in y_pred_cls_idx]

        rows = []
        for i, r in enumerate(df.itertuples(index=False)):
            pred_log = float(y_pred_log[i])
            pred_cases = float(np.expm1(max(pred_log, 0.0)))
            rows.append(
                (
                    disease_id, str(r.iso3),
                    int(r.iso_year), int(r.iso_week), 1,
                    pred_log, pred_cases,
                    str(risk_labels[i]),
                    mv_id_reg,
                )
            )

        execute_values(
            cur,
            """
            INSERT INTO predictions
                (disease_id, iso3, iso_year, iso_week, horizon_weeks,
                 predicted_value, predicted_cases, risk_level,
                 model_version_id)
            VALUES %s
            ON CONFLICT (disease_id, iso3, iso_year, iso_week, horizon_weeks, model_version_id) DO NOTHING
            """,
            rows,
            page_size=2000,
        )
        print(f"  → {disease}: {len(rows):,} predictions inserted")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("  load_db_v2.py — kltn_epiweather")
    print("=" * 60)

    conn = connect()
    conn.autocommit = False
    cur = conn.cursor()

    try:
        # Verify prerequisite
        cur.execute("SELECT COUNT(*) FROM countries")
        n_countries = cur.fetchone()[0]
        if n_countries == 0:
            raise RuntimeError(
                "Bảng countries trống — chạy `python scripts/seed_countries.py` trước"
            )
        print(f"\nFound {n_countries} countries — OK")

        mv_ids = load_model_versions(cur)
        conn.commit()

        load_disease_cases(cur)
        conn.commit()

        load_predictions(cur, mv_ids)
        conn.commit()

        print("\n[4] Refreshing materialized view...")
        try:
            cur.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY mv_latest_predictions")
            conn.commit()
            print("  → mv_latest_predictions refreshed")
        except psycopg2.Error as e:
            conn.rollback()
            print(f"  ! MV refresh skipped: {e}")

        print("\nVerifying row counts:")
        for table in ["countries", "disease_cases", "model_versions",
                      "model_evaluations", "predictions"]:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            print(f"   {table}: {cur.fetchone()[0]:,}")

        print("\nDone. Start backend: cd backend && uvicorn app.main:app --reload")

    except Exception as e:
        conn.rollback()
        print(f"\nERROR: {e}")
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
