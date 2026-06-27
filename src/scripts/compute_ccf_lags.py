"""
compute_ccf_lags.py — Tính lại khoảng trễ tối ưu (CCF) giữa biến khí hậu và số ca.

Tái lập đúng phương pháp ở cell [4.4] của notebook KLTN_EpiWeather_ML_v7.ipynb:
avg Pearson r theo từng quốc gia của weather(t-k) vs disease(t), target log1p,
quét lag k = 0..16 tuần, lấy lag có |r| lớn nhất.

Dùng để kiểm chứng/đồng bộ Bảng 3.4 trong báo cáo với số thật.

Chạy: python scripts/compute_ccf_lags.py
"""

from pathlib import Path

import numpy as np
import pandas as pd

MASTER = Path(__file__).resolve().parent.parent / "data/processed/master_weekly_v1.csv"
WEATHER = ["temp_c", "humidity_pct", "precip_mm", "solar_wm2", "dewpoint_c"]
MAX_LAG = 16
MIN_OBS = 30


def avg_ccf(df, target, wcol, max_lag=MAX_LAG, min_obs=MIN_OBS):
    """Avg Pearson r theo lag, trung bình qua các quốc gia (như notebook [4.4])."""
    corrs = {k: [] for k in range(max_lag + 1)}
    for _, g in df.dropna(subset=[target]).groupby("iso3"):
        g = g.sort_values(["iso_year", "iso_week"])
        y = g[target].values
        x = g[wcol].values
        for k in range(max_lag + 1):
            xx, yy = (x, y) if k == 0 else (x[:-k], y[k:])
            if len(xx) >= min_obs and np.std(xx) > 0 and np.std(yy) > 0:
                r = np.corrcoef(xx, yy)[0, 1]
                if not np.isnan(r):
                    corrs[k].append(r)
    return {k: (np.mean(v) if v else np.nan) for k, v in corrs.items()}


def best_lag(curve):
    return max(curve, key=lambda k: abs(curve[k]) if not np.isnan(curve[k]) else 0)


def main():
    m = pd.read_csv(MASTER)
    m["flu_log"] = np.log1p(m["influenza_total"].clip(lower=0))
    m["deng_log"] = np.log1p(m["dengue_total"].clip(lower=0))
    train = m[m.iso_year.between(2010, 2019)]

    for name, tgt in [("CÚM", "flu_log"), ("SỐT XUẤT HUYẾT", "deng_log")]:
        print(f"\n=== {name} (2010-2019) — lag tối ưu theo |r| max ===")
        for w in WEATHER:
            c = avg_ccf(train, tgt, w)
            k = best_lag(c)
            print(f"  {w:14s} lag={k:2d}  r={c[k]:+.3f}")


if __name__ == "__main__":
    main()
