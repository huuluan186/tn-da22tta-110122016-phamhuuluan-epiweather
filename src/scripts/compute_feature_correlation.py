"""
compute_feature_correlation.py — Tính hệ số tương quan Pearson giữa mỗi feature
của model production và log1p số ca (cùng tuần), gộp toàn bộ training set
2010-2019 (mọi quốc gia). Lưu artifact JSON cạnh model để Analytics hiển thị
"chứng minh" feature importance bằng tương quan thực tế.

Output: ml_models/{prefix}_h1_v1_correlation.json
Chạy lại an toàn (ghi đè artifact, không đụng model .pkl).
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE / "ml_models"
PROCESSED = BASE / "data" / "processed"

# (prefix model, csv features, cột target log số ca cùng tuần)
DISEASES = {
    "flu": {
        "prefix": "lgbm_flu_regressor",
        "csv": PROCESSED / "features_flu_v1.csv",
        "log_target": "flu_log",
    },
    "dengue": {
        "prefix": "rf_dengue_regressor",
        "csv": PROCESSED / "features_dengue_v1.csv",
        "log_target": "deng_log",
    },
}


def main():
    for disease, cfg in DISEASES.items():
        features_path = MODELS_DIR / f"{cfg['prefix']}_h1_v1_features.json"
        meta = json.loads(features_path.read_text(encoding="utf-8"))
        feature_cols = meta["features"]

        df = pd.read_csv(cfg["csv"])
        log_target = cfg["log_target"]
        if log_target not in df.columns:
            raise RuntimeError(f"{disease}: thiếu cột target '{log_target}' trong {cfg['csv'].name}")

        correlations = []
        for col in feature_cols:
            if col not in df.columns:
                correlations.append({"feature": col, "pearson_r": None, "n_obs": 0})
                continue
            pair = df[[col, log_target]].replace([np.inf, -np.inf], np.nan).dropna()
            if len(pair) < 30 or pair[col].std() == 0 or pair[log_target].std() == 0:
                correlations.append({"feature": col, "pearson_r": None, "n_obs": int(len(pair))})
                continue
            r = float(np.corrcoef(pair[col].values, pair[log_target].values)[0, 1])
            correlations.append({"feature": col, "pearson_r": round(r, 4), "n_obs": int(len(pair))})

        out = {
            "disease": disease,
            "target": log_target,
            "method": "pearson",
            "scope": "pooled all countries, 2010-2019 training set",
            "n_features": len(feature_cols),
            "correlations": correlations,
        }
        out_path = MODELS_DIR / f"{cfg['prefix']}_h1_v1_correlation.json"
        out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

        ranked = sorted(
            (c for c in correlations if c["pearson_r"] is not None),
            key=lambda c: abs(c["pearson_r"]),
            reverse=True,
        )
        print(f"[{disease}] -> {out_path.name}  ({len(feature_cols)} features)")
        for c in ranked[:5]:
            print(f"    {c['feature']:22s} r = {c['pearson_r']:+.3f}  (n={c['n_obs']:,})")
        print()


if __name__ == "__main__":
    main()
