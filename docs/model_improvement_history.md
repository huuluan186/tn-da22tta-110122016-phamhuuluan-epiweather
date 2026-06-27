# Model Improvement History — KLTN EpiWeather ML

Lịch sử toàn bộ các lần cải thiện model theo thứ tự thời gian.
Dùng để so sánh kết quả và viết Chương 4 (Thực nghiệm & Kết quả).

---

## Baseline — Trước SESSION 5 (≤ 03/05/2026)

**Setup:** XGBoost với raw `inf_cases` target, 12 features (không có hemisphere, không có WHO region), ERA5 training mean làm weather 2022.

| Model | R² | MAE | sMAPE non-zero | Ghi chú |
|---|---|---|---|---|
| XGBoost Flu | 0.488 | 47.97 (raw) | 62.9% | Target: raw inf_cases |
| XGBoost Dengue | ~0.80 | — | — | log1p từ trước |

**Bottleneck:** Long-tail distribution của flu cases (USA/India/Brazil dominate → MSE loss bị kéo về peak lớn).

---

## Cải tiến #1 — log1p transform cho flu target
**Ngày:** 05/05/2026 | **Session:** 5 | **Effort:** ~1 cell

**What:** Đổi `TARGET_FLU` từ `inf_cases` sang `inf_log1p = log1p(INF_A + INF_B)`. Cập nhật toàn bộ pipeline: AR lags, walk-forward CV, validation.

**Why:** log1p compress long-tail → MSE loss phân bổ đều hơn giữa các quốc gia, không bị dominated bởi peak USA/India.

**How:** `flu_df['inf_log1p'] = np.log1p(flu_df['inf_cases'])` → set `TARGET_FLU = 'inf_log1p'` → cập nhật [7.5], [8.5], [9.1].

**Result:**

| Metric | Trước | Sau | Δ |
|---|---|---|---|
| Flu R² | 0.488 | **0.811** | +0.323 (+66%) |
| Flu MAE | 47.97 (raw) | 0.41 (log1p) | — |
| Flu sMAPE non-zero | 62.9% | 73.4% | +10.5% (artifact of scale) |

**Verdict:** ✅ **Cải tiến lớn nhất trong toàn pipeline.** Đây là root cause fix thực sự — không phải hyperparameter hay model architecture.

---

## Cải tiến #2 — Hemisphere + Climate zone features
**Ngày:** 05/05/2026 | **Session:** 5 | **Effort:** ~2 cells

**What:** Thêm `hemisphere_enc` (North=1, South=-1, Equatorial=0) và `climate_zone_enc` (5 zones từ latitude) vào feature set.

**Why:** Flu season ngược nhau giữa 2 bán cầu — kỳ vọng model phân biệt được winter/summer theo địa lý.

**How:** Tính từ latitude country centroid, merge vào feature DataFrame.

**Result:**

| Metric | Trước | Sau | Δ |
|---|---|---|---|
| Flu R² (validation 2022) | 0.811 | 0.811 | 0 |
| Feature importance hemisphere | — | ~1–2% | Không đáng kể |

**Verdict:** ❌ **Revert.** XGBoost tự học được hemisphere effect thông qua AR lags (winter/summer pattern đã có trong historical cases). Geographic label tường minh không thêm thông tin.

---

## Cải tiến #3 — Optuna hyperparameter tuning (60 trials)
**Ngày:** 05/05/2026 | **Session:** 5 | **Effort:** ~30 phút runtime

**What:** Bayesian optimization (TPE sampler) cho XGBoost flu, 60 trials, optimize CV MAE trên walk-forward 6 folds (2014–2019).

**Why:** Default params (n_estimators=300, lr=0.05, max_depth=6) chưa được tune — có thể có cải thiện.

**How:** `optuna.create_study(direction='minimize')`, objective = cross-val MAE trên log1p flu.

**Best params tìm được:**
```
n_estimators: ~400-500, learning_rate: ~0.03-0.04, max_depth: 5-7,
subsample: ~0.7-0.9, colsample_bytree: ~0.6-0.8, ...
```

**Result:**

| Metric | Default params | Optuna params | Δ |
|---|---|---|---|
| CV MAE (log1p) | ~0.460 | **0.4508** | -0.009 (-2%) |
| Flu R² validation 2022 | 0.791 | 0.791 | 0 |

**Verdict:** ✅ **Giữ Optuna params** nhưng cải tiến nhỏ. Bottleneck xác nhận là distribution shift (immunity debt 2022), không phải hyperparameter. Optuna model được save vào pkl.

---

## Cải tiến #4 — ERA5 2022 weather thực tế (thay training mean)
**Ngày:** 07/05/2026 | **Session:** — | **Effort:** 1 buổi (download + process)

**What:** Thay per-country training mean bằng ERA5 weather thực tế năm 2022 cho validation. Cùng pipeline KD-tree mapping với training 2010–2019.

**Why:** Nhất quán pipeline giữa training và serving — production sẽ dùng weather thực tế, không phải mean. Training mean là "lazy baseline" không đại diện real-world deployment.

**How:** Download ERA5 2022 qua CDS API, process với cùng script `process_era5.py`, merge vào validation features.

**Result:**

| Metric | Training mean (cũ) | ERA5 2022 thực tế | Δ |
|---|---|---|---|
| Flu R² | 0.811 | **0.791** | -0.020 |
| Dengue R² | 0.858 | **0.836** | -0.022 |

**Verdict:** ✅ **Giữ ERA5 2022.** Giảm nhẹ ~2% phản ánh noise La Niña kéo dài năm 2022 (model chưa thấy pattern này trong training). Đây là tradeoff chấp nhận được — production consistency quan trọng hơn metric trên validation inflated bởi mean.

**Báo cáo metric chính thức từ đây:** Flu R²=0.791, Dengue R²=0.836.

---

## Cải tiến #5 — WHO Region encoding feature
**Ngày:** 09/05/2026 | **Session:** — | **Effort:** ~1 cell ([7.1b])

**What:** Thêm `who_region_enc` (ordinal: AFR=0, AMR=1, EMR=2, EUR=3, SEAR=4, WPR=5) vào feature set. Flu: 12→13 features, Dengue: 14→15 features.

**Why:** GV góp ý — model thiếu thông tin geographic grouping. Dengue có baseline endemic rất khác nhau giữa regions (AMR/SEAR/WPR chiếm >95% ca toàn cầu). Flu AR lags đã capture regional seasonality nhưng dengue cần explicit region signal.

**How:** Extract từ `WHOREGION` column trong `VIW_FNT.csv` (FluNet metadata) → ordinal encode → merge vào feature DataFrame. Coverage: 172/172 flu countries (100%).

**Result:**

| Metric | Trước | Sau | Δ |
|---|---|---|---|
| Flu R² | 0.791 | **0.791** | 0 |
| Dengue R² | 0.836 | **0.849** | +0.013 |
| Flu feature importance | — | who_region_enc ~2% | Marginal |
| Dengue feature importance | — | who_region_enc **~19% (rank #2)** | Significant |

**Verdict:** ✅ **Giữ.** Dengue cải thiện rõ ràng. Flu không tổn hại. Feature importance xác nhận giả thuyết: regional baseline là signal quan trọng cho vector-borne disease nhưng không cần thiết cho flu (AR lags đã đủ).

**Báo cáo metric từ đây:** Flu R²=0.791, Dengue R²=0.849.

---

## Cải tiến #6 — Per-country quantile risk thresholds
**Ngày:** 09/05/2026 | **Session:** — | **Effort:** ~30 phút ([9.3b])

**What:** Thay global quantile thresholds bằng per-country Q33/Q67 tính từ non-zero training rows (MIN_NONZERO=8). 162/170 flu countries có threshold riêng, 8 dùng global fallback.

**Why:** Global quantile collapse: 73% flu rows = 0 → Q33 global = 0, vùng Medium = band cực hẹp → model gần như không predict Medium. Flu Medium F1 = 0.06 không thể dùng trong production.

**How:**
```python
country_q = train_nz_flu.groupby('iso3')['inf_log1p'].quantile([0.33, 0.67]).unstack()
country_q = country_q[n_obs >= 8]
# Fallback: global Q33/Q67 cho countries có < 8 non-zero weeks
```
Export `flu_risk_thresholds.csv` (163 rows = 162 countries + 1 global) vào [9.5].

**Result:**

| Class | F1 global | F1 per-country | Δ |
|---|---|---|---|
| Low | 0.81 | **0.90** | +0.09 |
| Medium | 0.06 | **0.52** | +0.46 |
| High | 0.34 | **0.72** | +0.38 |
| **Macro F1** | 0.40 | **0.72** | +0.32 |
| Accuracy | 0.42 | **0.81** | +0.39 |

Dengue: không cần fix (global quantile cho macro F1 = 0.85 — đã tốt vì ít zero rows).

**Verdict:** ✅ **Cải tiến lớn cho risk classification.** Medium F1 từ gần 0 lên 0.52 — đủ để dùng trong dashboard. Artifact cần export: `flu_risk_thresholds.csv`.

---

## Tổng kết trajectory

| Cải tiến | Flu R² | Dengue R² | Flu Macro F1 | Dengue Macro F1 |
|---|---|---|---|---|
| Baseline | 0.488 | ~0.80 | — | — |
| +log1p | **0.811** | ~0.80 | — | — |
| +Hemisphere | 0.811 | ~0.80 | — | — |
| -Hemisphere (revert) | 0.811 | ~0.80 | — | — |
| +Optuna | 0.811 | ~0.80 | — | — |
| +ERA5 2022 real | 0.791 | **0.836** | — | — |
| +WHO region | 0.791 | **0.849** | — | — |
| +Per-country quantile | 0.791 | 0.849 | **0.72** | **0.85** |

**Final (09/05/2026):** Flu R²=**0.791**, Dengue R²=**0.849**, Flu macro F1=**0.72**, Dengue macro F1=**0.85**

---

## Pending improvements

| # | Cải tiến | Expected gain | Effort | Status |
|---|---|---|---|---|
| Tier 2.4 | LightGBM comparison table | Defensive cho thesis | 1 buổi | ⏳ |
| Tier 2.5 | 4-week-ahead forecasting | Story mạnh hơn | 1–2 buổi | ⏳ |
| GV Task 2 | PCA on weather features | R² +0.01–0.02? | 1 buổi | ⏳ |
| GV Task 3 | ERA5 bi-weekly split | Intra-month variation | 1 buổi | ⏳ |
| Dengue Optuna | Hyperparameter tuning dengue | CV MAE -2–5% | ~30 phút | ⏳ |
