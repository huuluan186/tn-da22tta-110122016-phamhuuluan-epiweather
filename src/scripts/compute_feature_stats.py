"""
compute_feature_stats.py — Tính mean/std mỗi feature của model production trên
training set 2010-2019 (mọi quốc gia, cùng nguồn CSV với compute_feature_correlation.py).

Artifact này để endpoint /analytics/feature-signals tính "chiều tín hiệu tuần này":
direction = sign(pearson_r × (value − mean)). Nếu chỉ dùng sign(pearson_r × value)
thì với feature luôn dương (nhiệt độ, độ ẩm, log số ca) chiều mũi tên cố định qua
mọi tuần — không phản ánh được tuần đang xem cao/thấp so với bình thường.

Output: ml_models/{prefix}_h1_v1_feature_stats.json
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

DISEASES = {
    "flu": {
        "prefix": "lgbm_flu_regressor",
        "csv": PROCESSED / "features_flu_v1.csv",
    },
    "dengue": {
        "prefix": "rf_dengue_regressor",
        "csv": PROCESSED / "features_dengue_v1.csv",
    },
}


def main():
    for disease, cfg in DISEASES.items():
        features_path = MODELS_DIR / f"{cfg['prefix']}_h1_v1_features.json"
        meta = json.loads(features_path.read_text(encoding="utf-8"))
        feature_cols = meta["features"]

        df = pd.read_csv(cfg["csv"])

        stats = {}
        for col in feature_cols:
            if col not in df.columns:
                continue
            vals = df[col].replace([np.inf, -np.inf], np.nan).dropna()
            if len(vals) < 30:
                continue
            stats[col] = {
                "mean": round(float(vals.mean()), 6),
                "std": round(float(vals.std(ddof=0)), 6),
                "n": int(len(vals)),
            }

        out = {
            "disease": disease,
            "scope": "pooled all countries, 2010-2019 training set",
            "n_obs": int(len(df)),
            "n_features": len(stats),
            "stats": stats,
            "note": (
                "Mean/std moi feature tren training set — dung cho direction "
                "theo tuan: sign(pearson_r * (value - mean))"
            ),
        }
        out_path = MODELS_DIR / f"{cfg['prefix']}_h1_v1_feature_stats.json"
        out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

        print(f"[{disease}] -> {out_path.name}  ({len(stats)} features, n={len(df):,})")
        for col, s in list(stats.items())[:5]:
            print(f"    {col:22s} mean={s['mean']:+.3f}  std={s['std']:.3f}")
        print()


if __name__ == "__main__":
    main()
