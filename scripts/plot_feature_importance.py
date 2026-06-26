"""
Ve Hinh 4.11 - feature importance cua dung model production trong ml_models/.

Output:
  docs/diagrams/hinh_4_11a_feature_importance_flu_lgbm.png
  docs/diagrams/hinh_4_11b_feature_importance_dengue_rf.png
"""
import json
import math
from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = ROOT / "ml_models"
OUT_DIR = ROOT / "docs" / "diagrams"
OUT_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams["font.family"] = "DejaVu Sans"

JOBS = [
    {
        "stem": "lgbm_flu_regressor_v2",
        "title": "Top 12 đặc trưng quan trọng nhất - mô hình cúm LightGBM (tuned)",
        "color": "#3B6FA0",
        "out": "hinh_4_11a_feature_importance_flu_lgbm.png",
    },
    {
        "stem": "rf_dengue_regressor_v2",
        "title": "Top 12 đặc trưng quan trọng nhất - mô hình sốt xuất huyết Random Forest (tuned)",
        "color": "#C0504D",
        "out": "hinh_4_11b_feature_importance_dengue_rf.png",
    },
]


def load_feature_importance(job: dict) -> pd.DataFrame:
    model = joblib.load(MODELS_DIR / f"{job['stem']}.pkl")
    with open(MODELS_DIR / f"{job['stem']}_features.json", encoding="utf-8") as f:
        features = json.load(f)["features"]

    imp = model.feature_importances_.astype(float)
    if len(imp) != len(features):
        raise ValueError(f"{job['stem']}: model has {len(imp)} importances but {len(features)} features")
    if imp.sum() <= 0:
        raise ValueError(f"{job['stem']}: feature importances sum to zero")

    pct = imp / imp.sum() * 100.0
    return (
        pd.DataFrame({"feature": features, "importance": imp, "pct": pct})
        .sort_values("importance", ascending=True)
        .tail(12)
    )


def plot_feature_importance(job: dict, fi: pd.DataFrame) -> Path:
    xmax = max(10, math.ceil(fi["pct"].max() * 1.2 / 5) * 5)

    fig, ax = plt.subplots(figsize=(10.5, 6.2))
    bars = ax.barh(fi["feature"], fi["pct"], color=job["color"], height=0.72)
    ax.set_xlabel("Tỷ trọng (%) trên tổng mức quan trọng của mô hình", fontsize=11)
    ax.set_title(job["title"], fontsize=13, fontweight="bold", pad=10)
    ax.set_xlim(0, xmax)
    ax.xaxis.set_major_locator(MultipleLocator(5))
    ax.grid(axis="x", alpha=0.25, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(axis="x", labelsize=10)
    ax.tick_params(axis="y", labelsize=10)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    for bar, p in zip(bars, fi["pct"]):
        w = bar.get_width()
        y = bar.get_y() + bar.get_height() / 2
        ax.text(
            w + xmax * 0.015,
            y,
            f"{p:.1f}%",
            va="center",
            ha="left",
            color="black",
            fontweight="bold",
            fontsize=10,
            clip_on=False,
        )

    fig.tight_layout(pad=1.0)
    out_path = OUT_DIR / job["out"]
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return out_path


for job in JOBS:
    fi = load_feature_importance(job)
    out_path = plot_feature_importance(job, fi)
    print(f"[OK] {out_path.name}")
    print(fi.iloc[::-1][["feature", "pct"]].to_string(index=False))
    print()
