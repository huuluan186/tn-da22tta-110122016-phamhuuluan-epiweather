"""
backfill_model_evaluations.py — Đồng bộ model_versions + model_evaluations trong DB
từ các file metrics JSON cuối cùng (ml_models/*_metrics.json).

Lý do: DB hiện còn giữ số của model cũ v1.0 (trước khi sửa bug LabelEncoder) và
chưa backfill regressor v2 / classifier v4 — số dùng trong báo cáo Chương 4.
Script này nạp đúng số từ artifact training để dashboard khớp báo cáo.

Nguồn số (đã đối chiếu khớp báo cáo):
  - Regressor single-step CV: *_regressor_v2_metrics.json
  - Regressor hold-out 2022:  *_regressor_v1_metrics.json -> test_2022
  - Regressor đa chân trời:    *_regressor_h{1..4}_v1_metrics.json
  - Classifier walk-forward CV: xgb_*_classifier_v4_metrics.json

Chạy:
  python scripts/backfill_model_evaluations.py            # dry-run, chỉ in ra
  python scripts/backfill_model_evaluations.py --commit   # ghi thật vào DB

Idempotent: upsert model_versions theo (disease_id, version); với mỗi model_version
sẽ XÓA các eval cũ rồi chèn lại, nên chạy nhiều lần không sinh dòng trùng.
"""

import argparse
import json
import os
import sys
from pathlib import Path

import psycopg2

# Tránh lỗi UnicodeEncodeError khi in tiếng Việt trên console Windows (cp1252)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/kltn_epiweather"
)
ML_DIR = Path(__file__).resolve().parent.parent / "ml_models"

# Cấu hình từng bệnh: file artifact + thuật toán champion
DISEASES = {
    "flu": {
        "reg_algo": "LightGBM",
        "reg_v2": "lgbm_flu_regressor_v2_metrics.json",
        "reg_v1": "lgbm_flu_regressor_v1_metrics.json",
        "reg_h": "lgbm_flu_regressor_h{h}_v1_metrics.json",
        "reg_artifact": "lgbm_flu_regressor_v2.pkl",
        "clf_v4": "xgb_flu_classifier_v4_metrics.json",
        "clf_artifact": "xgb_flu_classifier_v4.pkl",
    },
    "dengue": {
        "reg_algo": "RandomForest",
        "reg_v2": "rf_dengue_regressor_v2_metrics.json",
        "reg_v1": "rf_dengue_regressor_v1_metrics.json",
        "reg_h": "rf_dengue_regressor_h{h}_v1_metrics.json",
        "reg_artifact": "rf_dengue_regressor_v2.pkl",
        "clf_v4": "xgb_dengue_classifier_v4_metrics.json",
        "clf_artifact": "xgb_dengue_classifier_v4.pkl",
    },
}

TRAIN_START, TRAIN_END, VAL_YEAR = 2010, 2019, 2022


def load_json(name: str) -> dict:
    path = ML_DIR / name
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def f1_from(prec, recall):
    """Tính F1 từ precision và recall (an toàn khi mẫu số = 0)."""
    if prec is None or recall is None or (prec + recall) == 0:
        return None
    return round(2 * prec * recall / (prec + recall), 4)


def upsert_model_version(cur, disease_id, version, algorithm, artifact, is_champion):
    """Upsert model_versions theo (disease_id, version). Trả về id."""
    cur.execute(
        """
        INSERT INTO model_versions
            (disease_id, version, algorithm, description,
             train_year_start, train_year_end, val_year, artifact_path,
             is_active, is_champion)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, TRUE, %s)
        ON CONFLICT (disease_id, version) DO UPDATE SET
            algorithm   = EXCLUDED.algorithm,
            artifact_path = EXCLUDED.artifact_path,
            is_active   = TRUE,
            is_champion = EXCLUDED.is_champion
        RETURNING id
        """,
        (disease_id, version, algorithm,
         f"Champion {algorithm} — backfill từ metrics JSON",
         TRAIN_START, TRAIN_END, VAL_YEAR, artifact, is_champion),
    )
    return cur.fetchone()[0]


def replace_evals(cur, model_version_id, rows):
    """Xóa eval cũ của model_version rồi chèn lại (idempotent)."""
    cur.execute(
        "DELETE FROM model_evaluations WHERE model_version_id = %s",
        (model_version_id,),
    )
    for r in rows:
        cur.execute(
            """
            INSERT INTO model_evaluations
                (model_version_id, eval_set, eval_type,
                 r2_score, mae, rmse,
                 risk_macro_f1, risk_high_f1,
                 n_samples, notes)
            VALUES (%(mv)s, %(set)s, %(type)s,
                    %(r2)s, %(mae)s, %(rmse)s,
                    %(macro_f1)s, %(high_f1)s,
                    %(n)s, %(notes)s)
            """,
            {"mv": model_version_id, **r},
        )


def eval_row(eval_set, eval_type, *, r2=None, mae=None, rmse=None,
             macro_f1=None, high_f1=None, n=None, notes=None):
    return {"set": eval_set, "type": eval_type, "r2": r2, "mae": mae,
            "rmse": rmse, "macro_f1": macro_f1, "high_f1": high_f1,
            "n": n, "notes": notes}


def build_regressor_evals(cfg):
    rows = []
    v2 = load_json(cfg["reg_v2"])
    rows.append(eval_row("cv-single-step", "cv",
                         r2=v2["r2"], mae=v2["mae"], rmse=v2["rmse"],
                         notes="Regressor v2 (single-step), walk-forward CV"))
    v1 = load_json(cfg["reg_v1"])
    t = v1.get("test_2022")
    if t:
        rows.append(eval_row("holdout_2022", "holdout",
                             r2=t["r2"], mae=t["mae"], rmse=t["rmse"],
                             n=t.get("n"),
                             notes="Hold-out 2022 (regressor v1 — bản đã lưu test riêng)"))
    for h in (1, 2, 3, 4):
        hj = load_json(cfg["reg_h"].format(h=h))
        rows.append(eval_row(f"cv-h{h}", "cv",
                             r2=hj.get("r2"), mae=hj.get("mae"), rmse=hj.get("rmse"),
                             notes=f"Multi-horizon h={h}, walk-forward CV"))
    return rows


def build_classifier_evals(cfg):
    c = load_json(cfg["clf_v4"])
    high_f1 = f1_from(c.get("high_prec"), c.get("high_recall"))
    notes = (f"Classifier v4, walk-forward CV; high_recall={c.get('high_recall')}, "
             f"high_prec={c.get('high_prec')}, med_recall={c.get('med_recall')}, "
             f"strategy={c.get('strategy')}")
    return [eval_row("cv-walk-forward", "cv",
                     macro_f1=c.get("macro_f1"), high_f1=high_f1, notes=notes)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--commit", action="store_true",
                    help="Ghi thật vào DB (mặc định chỉ dry-run)")
    args = ap.parse_args()

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    for code, cfg in DISEASES.items():
        cur.execute("SELECT id FROM diseases WHERE code = %s", (code,))
        row = cur.fetchone()
        if not row:
            print(f"[BỎ QUA] Không tìm thấy disease code={code}")
            continue
        disease_id = row[0]

        reg_id = upsert_model_version(
            cur, disease_id, "v2-regressor", cfg["reg_algo"],
            cfg["reg_artifact"], is_champion=True)
        reg_evals = build_regressor_evals(cfg)
        replace_evals(cur, reg_id, reg_evals)

        clf_id = upsert_model_version(
            cur, disease_id, "v4-classifier", "XGBClassifier",
            cfg["clf_artifact"], is_champion=False)
        clf_evals = build_classifier_evals(cfg)
        replace_evals(cur, clf_id, clf_evals)

        print(f"[{code}] regressor mv_id={reg_id}: {len(reg_evals)} eval; "
              f"classifier mv_id={clf_id}: {len(clf_evals)} eval")
        for r in reg_evals + clf_evals:
            print(f"    {r['set']:16s} r2={r['r2']} mae={r['mae']} "
                  f"rmse={r['rmse']} macroF1={r['macro_f1']} highF1={r['high_f1']}")

    if args.commit:
        conn.commit()
        print("\n[COMMIT] Đã ghi vào DB.")
    else:
        conn.rollback()
        print("\n[DRY-RUN] Chưa ghi. Chạy lại với --commit để áp dụng.")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
