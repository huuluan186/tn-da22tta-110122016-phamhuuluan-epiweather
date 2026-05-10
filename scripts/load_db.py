"""
load_db.py — Load toàn bộ data từ CSV/pkl vào DB kltn_epiweather
Chạy 1 lần sau khi tạo schema bằng db_init.sql

Thứ tự load:
  1. countries
  2. feature_configs (từ feature_list.json)
  3. model_versions + model_evaluations
  4. risk_thresholds (flu)
  5. disease_cases (flu + dengue từ feature CSV)
  6. predictions (chạy inference trên feature CSV)
  7. REFRESH materialized view
"""

import json
import sys
import warnings
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import joblib
import numpy as np
import pandas as pd
import psycopg2
import psycopg2.extensions
from psycopg2.extras import execute_values

# Cho psycopg2 tự convert numpy types sang Python native
psycopg2.extensions.register_adapter(np.int64,   lambda x: psycopg2.extensions.AsIs(int(x)))
psycopg2.extensions.register_adapter(np.float64, lambda x: psycopg2.extensions.AsIs(float(x)))
psycopg2.extensions.register_adapter(np.bool_,   lambda x: psycopg2.extensions.AsIs(bool(x)))

warnings.filterwarnings("ignore")

# ── Paths ──────────────────────────────────────────────────────────────────
BASE = Path(__file__).parent.parent
MODELS_DIR   = BASE / "models"
PROCESSED    = BASE / "dataset" / "processed"
RAW          = BASE / "dataset" / "epidemic" / "raw"

FLU_FEATURES   = PROCESSED / "features_flu_2010_2019.csv"
DENGUE_FEATURES = PROCESSED / "features_dengue_2010_2019.csv"
FLUNET_FILE    = RAW / "VIW_FNT.csv"
FEATURE_JSON   = MODELS_DIR / "feature_list.json"
METRICS_JSON   = MODELS_DIR / "model_metrics.json"
THRESHOLDS_CSV = MODELS_DIR / "flu_risk_thresholds.csv"

# ── DB connection ───────────────────────────────────────────────────────────
DB_CONFIG = {
    "dbname":   "kltn_epiweather",
    "user":     "postgres",
    "password": "111111111",
    "host":     "localhost",
    "port":     5432,
}

REGION_MAP = {"AFR": 0, "AMR": 1, "EMR": 2, "EUR": 3, "SEAR": 4, "WPR": 5}


def load_configs():
    """Load feature_list.json và model_metrics.json — single source of truth."""
    with open(FEATURE_JSON) as f:
        features = json.load(f)
    with open(METRICS_JSON) as f:
        metrics = json.load(f)

    # Parse train period từ feature_list.json: "2010-2019" → (2010, 2019)
    train_start, train_end = map(int, features["meta"]["train_period"].split("-"))
    val_year = int(features["meta"]["val_year"])

    # Derive model file paths từ artifact field trong model_metrics.json
    model_paths = {
        disease: MODELS_DIR / cfg["artifact"]
        for disease, cfg in metrics.items()
    }

    return features, metrics, train_start, train_end, val_year, model_paths


def connect():
    return psycopg2.connect(**DB_CONFIG)


# ─────────────────────────────────────────────────────────────────────────────
# 1. COUNTRIES
# ─────────────────────────────────────────────────────────────────────────────
def load_countries(cur):
    print("\n[1] Loading countries...")
    flu_df = pd.read_csv(FLU_FEATURES, usecols=["iso3", "who_region_enc"])
    den_df = pd.read_csv(DENGUE_FEATURES, usecols=["iso3", "who_region_enc"])
    all_iso = pd.concat([flu_df, den_df]).drop_duplicates("iso3")

    # Get country names + who_region string from VIW_FNT
    vfw = pd.read_csv(FLUNET_FILE,
                      usecols=["COUNTRY_CODE", "COUNTRY_AREA_TERRITORY", "WHOREGION"],
                      low_memory=False)
    vfw = (vfw.drop_duplicates("COUNTRY_CODE")
              .rename(columns={
                  "COUNTRY_CODE": "iso3",
                  "COUNTRY_AREA_TERRITORY": "country_name",
                  "WHOREGION": "who_region",
              }))

    countries = all_iso.merge(vfw, on="iso3", how="left")
    countries["who_region"] = countries["who_region"].fillna("UNK")
    rows = [
        (r.iso3, r.country_name if pd.notna(r.country_name) else r.iso3,
         r.who_region, int(r.who_region_enc))
        for _, r in countries.iterrows()
    ]
    execute_values(cur, """
        INSERT INTO countries (iso3, country_name, who_region, who_region_enc)
        VALUES %s
        ON CONFLICT (iso3) DO UPDATE SET
            country_name   = EXCLUDED.country_name,
            who_region     = EXCLUDED.who_region,
            who_region_enc = EXCLUDED.who_region_enc
    """, rows)
    print(f"  → {len(rows)} countries inserted/updated")


# ─────────────────────────────────────────────────────────────────────────────
# 2. FEATURE CONFIGS
# ─────────────────────────────────────────────────────────────────────────────
def load_feature_configs(cur):
    print("\n[2] Loading feature_configs...")
    fj, metrics_cfg, _, _, _, _ = load_configs()

    cur.execute("SELECT id FROM diseases WHERE code='flu'")
    flu_id = cur.fetchone()[0]
    cur.execute("SELECT id FROM diseases WHERE code='dengue'")
    den_id = cur.fetchone()[0]

    rows = []
    for disease_id, key in [(flu_id, "flu"), (den_id, "dengue")]:
        cfg = fj[key]
        version_tag = metrics_cfg[key]["version"]   # từ model_metrics.json
        for feat in cfg["features"]:
            if "lag" in feat and ("inf_" in feat or "dengue_" in feat):
                src = "ar_lag"
            elif any(w in feat for w in ["temp", "humidity", "solar", "dewpoint", "precip"]):
                src = "weather"
            elif feat in ("sin_week", "cos_week", "quarter"):
                src = "calendar"
            else:
                src = "geographic"

            rows.append((disease_id, feat, src, version_tag))

    execute_values(cur, """
        INSERT INTO feature_configs (disease_id, feature_name, source_type, version_tag)
        VALUES %s
        ON CONFLICT (disease_id, feature_name, version_tag) DO NOTHING
    """, rows)
    print(f"  → {len(rows)} feature configs inserted")


# ─────────────────────────────────────────────────────────────────────────────
# 3. MODEL VERSIONS + EVALUATIONS
# ─────────────────────────────────────────────────────────────────────────────
def load_model_versions(cur):
    print("\n[3] Loading model_versions...")
    _, metrics_cfg, train_start, train_end, val_year, model_paths = load_configs()

    model_ids = {}
    for disease_code, mcfg in metrics_cfg.items():
        cur.execute("SELECT id FROM diseases WHERE code=%s", (disease_code,))
        disease_id = cur.fetchone()[0]

        # Hyperparams từ pkl — không hardcode
        model = joblib.load(model_paths[disease_code])
        params = model.get_xgb_params()
        params["n_estimators"] = int(model.n_estimators)

        version       = mcfg["version"]
        algorithm     = mcfg["algorithm"]
        description   = mcfg["description"]
        artifact_path = f"models/{mcfg['artifact']}"
        holdout       = mcfg["holdout"]

        cur.execute("""
            INSERT INTO model_versions
                (disease_id, version, algorithm, description,
                 train_year_start, train_year_end, val_year,
                 feature_config_tag, hyperparams, artifact_path,
                 is_active, is_champion)
            VALUES (%s,%s,%s,%s, %s,%s,%s, %s,%s,%s, TRUE, TRUE)
            ON CONFLICT (disease_id, version) DO UPDATE SET
                is_active   = TRUE,
                is_champion = TRUE,
                hyperparams = EXCLUDED.hyperparams
            RETURNING id
        """, (disease_id, version, algorithm, description,
              train_start, train_end, val_year,
              version, json.dumps(params), artifact_path))
        mv_id = cur.fetchone()[0]
        model_ids[disease_code] = mv_id

        # Evaluation metrics — từ model_metrics.json
        cur.execute("""
            INSERT INTO model_evaluations
                (model_version_id, eval_set, eval_type,
                 r2_score, mae, smape_nonzero,
                 risk_macro_f1, risk_accuracy,
                 risk_low_f1, risk_medium_f1, risk_high_f1,
                 n_samples, notes)
            VALUES (%s,%s,'holdout', %s,%s,%s, %s,%s, %s,%s,%s, %s,%s)
            ON CONFLICT DO NOTHING
        """, (mv_id,
              holdout["eval_set"],
              holdout.get("r2_score"),    holdout.get("mae"), holdout.get("smape_nonzero"),
              holdout.get("risk_macro_f1"), holdout.get("risk_accuracy"),
              holdout.get("risk_low_f1"),   holdout.get("risk_medium_f1"), holdout.get("risk_high_f1"),
              holdout.get("n_samples"),   holdout.get("notes")))

        print(f"  → {disease_code} {version}: id={mv_id}, R²={holdout.get('r2_score')}")

    return model_ids


# ─────────────────────────────────────────────────────────────────────────────
# 4. RISK THRESHOLDS (flu)
# ─────────────────────────────────────────────────────────────────────────────
def load_risk_thresholds(cur, model_ids):
    print("\n[4] Loading risk_thresholds...")
    cur.execute("SELECT id FROM diseases WHERE code='flu'")
    flu_id = cur.fetchone()[0]
    mv_id  = model_ids["flu"]

    thresh = pd.read_csv(THRESHOLDS_CSV)
    rows = [
        (flu_id, str(r.iso3), float(r.q33), float(r.q67),
         int(r.get("n_nonzero_weeks", 0)) if "n_nonzero_weeks" in thresh.columns else None,
         bool(str(r.iso3) == "_global"), mv_id)
        for _, r in thresh.iterrows()
    ]
    execute_values(cur, """
        INSERT INTO risk_thresholds
            (disease_id, iso3, q33, q67, n_nonzero_weeks, is_global_fallback, model_version_id)
        VALUES %s
        ON CONFLICT (disease_id, iso3) DO UPDATE SET
            q33 = EXCLUDED.q33,
            q67 = EXCLUDED.q67,
            model_version_id = EXCLUDED.model_version_id
    """, rows)
    print(f"  → {len(rows)} thresholds inserted (flu)")

    # Dengue: global quantile từ feature CSV
    cur.execute("SELECT id FROM diseases WHERE code='dengue'")
    den_id = cur.fetchone()[0]
    den_df = pd.read_csv(DENGUE_FEATURES, usecols=["dengue_log1p"])
    nz = den_df[den_df["dengue_log1p"] > 0]["dengue_log1p"]
    cur.execute("""
        INSERT INTO risk_thresholds (disease_id, iso3, q33, q67, is_global_fallback, model_version_id)
        VALUES (%s,'_global',%s,%s, TRUE,%s)
        ON CONFLICT (disease_id, iso3) DO UPDATE SET q33=EXCLUDED.q33, q67=EXCLUDED.q67
    """, (den_id, float(nz.quantile(0.33)), float(nz.quantile(0.67)), model_ids["dengue"]))
    print(f"  → 1 global threshold inserted (dengue)")


# ─────────────────────────────────────────────────────────────────────────────
# 5. DISEASE CASES
# ─────────────────────────────────────────────────────────────────────────────
def load_disease_cases(cur):
    print("\n[5] Loading disease_cases...")
    cur.execute("SELECT id FROM diseases WHERE code='flu'")
    flu_id = cur.fetchone()[0]
    cur.execute("SELECT id FROM diseases WHERE code='dengue'")
    den_id = cur.fetchone()[0]
    cur.execute("SELECT id FROM data_sources WHERE code='FluNet'")
    flu_src = cur.fetchone()[0]
    cur.execute("SELECT id FROM data_sources WHERE code='WHO_PAHO'")
    den_src = cur.fetchone()[0]

    # Flu cases
    flu_df = pd.read_csv(FLU_FEATURES, usecols=["iso3", "iso_year", "iso_week", "inf_log1p"])
    flu_rows = [
        (flu_id, r.iso3, flu_src, int(r.iso_year), int(r.iso_week),
         None, float(r.inf_log1p), 1)
        for _, r in flu_df.iterrows()
    ]
    execute_values(cur, """
        INSERT INTO disease_cases
            (disease_id, iso3, source_id, iso_year, iso_week, raw_count, transformed_value, data_quality)
        VALUES %s
        ON CONFLICT (disease_id, iso3, iso_year, iso_week, source_id) DO NOTHING
    """, flu_rows, page_size=5000)
    print(f"  → {len(flu_rows):,} flu case rows inserted")

    # Dengue cases
    den_df = pd.read_csv(DENGUE_FEATURES, usecols=["iso3", "iso_year", "iso_week", "dengue_log1p"])
    den_rows = [
        (den_id, r.iso3, den_src, int(r.iso_year), int(r.iso_week),
         None, float(r.dengue_log1p), 1)
        for _, r in den_df.iterrows()
    ]
    execute_values(cur, """
        INSERT INTO disease_cases
            (disease_id, iso3, source_id, iso_year, iso_week, raw_count, transformed_value, data_quality)
        VALUES %s
        ON CONFLICT (disease_id, iso3, iso_year, iso_week, source_id) DO NOTHING
    """, den_rows, page_size=5000)
    print(f"  → {len(den_rows):,} dengue case rows inserted")


# ─────────────────────────────────────────────────────────────────────────────
# 6. PREDICTIONS (run inference trên toàn feature CSV)
# ─────────────────────────────────────────────────────────────────────────────
def load_predictions(cur, model_ids):
    print("\n[6] Loading predictions (running inference)...")
    fj, _, _, _, _, model_paths = load_configs()

    xgb_flu    = joblib.load(model_paths["flu"])
    xgb_dengue = joblib.load(model_paths["dengue"])
    thresh_df  = pd.read_csv(THRESHOLDS_CSV).set_index("iso3")
    global_q33 = thresh_df.loc["_global", "q33"]
    global_q67 = thresh_df.loc["_global", "q67"]

    def flu_risk(iso3, val):
        if iso3 in thresh_df.index:
            q33, q67 = thresh_df.loc[iso3, "q33"], thresh_df.loc[iso3, "q67"]
        else:
            q33, q67 = global_q33, global_q67
        if val <= q33:   return "Low",    q33, q67
        if val <= q67:   return "Medium", q33, q67
        return "High", q33, q67

    cur.execute("SELECT id FROM diseases WHERE code='flu'")
    flu_disease_id = cur.fetchone()[0]
    cur.execute("SELECT id FROM diseases WHERE code='dengue'")
    den_disease_id = cur.fetchone()[0]

    # ── Flu predictions ──
    flu_df = pd.read_csv(FLU_FEATURES)
    flu_feat_cols = fj["flu"]["features"]
    X_flu = flu_df[flu_feat_cols].values
    y_pred_flu = xgb_flu.predict(X_flu)

    flu_rows = []
    for i, (_, r) in enumerate(flu_df.iterrows()):
        pred_log1p = float(y_pred_flu[i])
        pred_cases = float(np.expm1(pred_log1p))
        risk, q33, q67 = flu_risk(r.iso3, pred_log1p)
        flu_rows.append((
            flu_disease_id, r.iso3, int(r.iso_year), int(r.iso_week), 1,
            pred_log1p, pred_cases, risk, q33, q67,
            model_ids["flu"]
        ))

    execute_values(cur, """
        INSERT INTO predictions
            (disease_id, iso3, iso_year, iso_week, horizon_weeks,
             predicted_value, predicted_cases, risk_level, risk_q33, risk_q67,
             model_version_id)
        VALUES %s
        ON CONFLICT (disease_id, iso3, iso_year, iso_week, horizon_weeks, model_version_id) DO NOTHING
    """, flu_rows, page_size=2000)
    print(f"  → {len(flu_rows):,} flu predictions inserted")

    # ── Dengue predictions ──
    den_df = pd.read_csv(DENGUE_FEATURES)
    den_feat_cols = fj["dengue"]["features"]

    # Dengue global quantile
    nz = den_df[den_df["dengue_log1p"] > 0]["dengue_log1p"]
    den_q33, den_q67 = float(nz.quantile(0.33)), float(nz.quantile(0.67))

    X_den = den_df[den_feat_cols].values
    y_pred_den = xgb_dengue.predict(X_den)

    den_rows = []
    for i, (_, r) in enumerate(den_df.iterrows()):
        pred_log1p = float(y_pred_den[i])
        pred_cases = float(np.expm1(pred_log1p))
        if pred_log1p <= den_q33:   risk = "Low"
        elif pred_log1p <= den_q67: risk = "Medium"
        else:                       risk = "High"
        den_rows.append((
            den_disease_id, r.iso3, int(r.iso_year), int(r.iso_week), 1,
            pred_log1p, pred_cases, risk, den_q33, den_q67,
            model_ids["dengue"]
        ))

    execute_values(cur, """
        INSERT INTO predictions
            (disease_id, iso3, iso_year, iso_week, horizon_weeks,
             predicted_value, predicted_cases, risk_level, risk_q33, risk_q67,
             model_version_id)
        VALUES %s
        ON CONFLICT (disease_id, iso3, iso_year, iso_week, horizon_weeks, model_version_id) DO NOTHING
    """, den_rows, page_size=2000)
    print(f"  → {len(den_rows):,} dengue predictions inserted")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("  DB Loader — kltn_epiweather")
    print("=" * 60)

    conn = connect()
    conn.autocommit = False
    cur = conn.cursor()

    try:
        load_countries(cur)
        conn.commit()

        load_feature_configs(cur)
        conn.commit()

        model_ids = load_model_versions(cur)
        conn.commit()

        load_risk_thresholds(cur, model_ids)
        conn.commit()

        load_disease_cases(cur)
        conn.commit()

        load_predictions(cur, model_ids)
        conn.commit()

        print("\n[7] Refreshing materialized view...")
        cur.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY mv_latest_predictions")
        conn.commit()
        print("  → mv_latest_predictions refreshed")

        print("\nDone! Verifying row counts...")
        for table in ["countries", "disease_cases", "model_versions",
                      "risk_thresholds", "predictions", "feature_configs"]:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            print(f"   {table}: {cur.fetchone()[0]:,} rows")

    except Exception as e:
        conn.rollback()
        print(f"\nERROR: {e}")
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
