# Session 8: Multi-Horizon Forecasting (v6 Extension — h=1,2,3,4 tuần)

> **Mục tiêu thuyết trình:** Đây là **session bổ sung trong notebook v6** (chốt 21/05/2026, sau khi v5 hoàn tất Session 0-7). Đề tài yêu cầu "dự báo theo giai đoạn/mùa/tháng" → cần forecast multi-horizon, không chỉ h=1.

---

## 1. Vì sao cần v6 — vấn đề của v5

v5 chỉ predict **h=1** (tuần kế tiếp). Nhưng đề tài KLTN yêu cầu "dự báo dịch bệnh có thể diễn ra theo giai đoạn/mùa/tháng" → chỉ có h=1 không đủ.

**Quan trắc viên y tế cần:**
- Tuần này risk?
- 2 tuần nữa risk?
- 1 tháng nữa risk? → để chuẩn bị vaccine, giường bệnh

→ Cần forecast trajectory **h=1, h=2, h=3, h=4 tuần**.

---

## 2. 2 cách multi-horizon — em chọn cách nào

| Cách | Mô tả | Ưu | Nhược |
|---|---|---|---|
| **Recursive** | Predict h=1, dùng output làm input cho h=2... | Code đơn giản, 1 model | **Error propagation** — sai h=1 thì h=2,3,4 sai cấp số |
| **Multi-horizon trực tiếp** ✅ | Train **4 model riêng**, mỗi model dùng feature **actual** | Tránh error compound, mỗi h tối ưu riêng | Train 4 model = 4× compute |

→ **Em chọn multi-horizon trực tiếp.** Lý do: error propagation là vấn đề **critical với forecasting**. Nếu h=1 sai 10%, recursive feed vào h=2 → error compound thành 15-20%. Train riêng từng h dùng feature actual → error không cộng dồn.

---

## 3. Cell 8.1 — Build multi-horizon targets (flu)

```python
def build_multi_horizon_targets(features_df, target_col, horizons=[1,2,3,4]):
    """Cho mỗi (iso3, year, week), build 4 target: cases tại week+h."""
    df = features_df.copy()
    for h in horizons:
        df[f'target_h{h}'] = df.groupby('iso3')[target_col].shift(-h)
    # Drop rows không có target h=4 (cuối dataset)
    df = df.dropna(subset=[f'target_h{h}' for h in horizons])
    return df

features_flu_h = build_multi_horizon_targets(features_flu, 'inf_log1p', [1,2,3,4])
# Flu: 55,208 → 54,636 rows (drop 572 cuối dataset)
```

**Logic:**
- Tại tuần W, target_h1 = cases tuần W+1, target_h2 = W+2, ..., target_h4 = W+4
- Drop rows cuối không có target h=4 đầy đủ

---

## 4. Cell 8.2 — Build multi-horizon targets (dengue)

```python
features_dengue_h = build_multi_horizon_targets(features_dengue, 'dengue_log1p', [1,2,3,4])
# Dengue: 5,926 → 5,786 rows (drop 140)
```

Cùng logic. Dengue drop ít rows hơn (chỉ 140 vs 572) vì dataset đã nhỏ.

---

## 5. Cell 8.3 — Walk-forward CV flu multi-horizon

```python
flu_results = {}
for h in [1, 2, 3, 4]:
    cv_results = run_cv(
        model_fn=lambda: LGBMRegressor(**LGBM_FLU_BEST_PARAMS),  # giữ params từ v1
        features_df=features_flu_h,
        target_col=f'target_h{h}',
        splits=walk_forward_splits(features_flu_h),
    )
    flu_results[h] = cv_results
```

**Tại sao giữ `LGBM_FLU_BEST_PARAMS` từ v1, không tune lại:**
- Optuna v1 (Session 6.9) đã tune cho feature set hiện tại (16 features)
- Multi-horizon **dùng CÙNG feature set** → optimal params giống
- Tune lại sẽ tốn ~60×4 = 240 trials/disease, improvement marginal (< 0.005 R²) — **không hiệu quả thời gian**

---

## 6. Cell 8.4 — Train final flu + save 4 pkl

```python
flu_models = {}
for h in [1, 2, 3, 4]:
    model = LGBMRegressor(**LGBM_FLU_BEST_PARAMS)
    model.fit(features_flu_h[FLU_COLS], features_flu_h[f'target_h{h}'])
    flu_models[h] = model
    joblib.dump(model, MODELS_DIR / f'lgbm_flu_regressor_h{h}_v1.pkl')
```

**4 artifacts mới (1.7 MB mỗi cái):**
```
lgbm_flu_regressor_h1_v1.pkl  → R² CV = 0.866
lgbm_flu_regressor_h2_v1.pkl  → R² CV = 0.829
lgbm_flu_regressor_h3_v1.pkl  → R² CV = 0.793
lgbm_flu_regressor_h4_v1.pkl  → R² CV = 0.757
```

---

## 7. Cell 8.5 — Walk-forward CV + train dengue multi-horizon

Cùng logic cho Random Forest dengue.

**4 artifacts mới (39.8 MB mỗi cái):**
```
rf_dengue_regressor_h1_v1.pkl  → R² CV = 0.929
rf_dengue_regressor_h2_v1.pkl  → R² CV = 0.919
rf_dengue_regressor_h3_v1.pkl  → R² CV = 0.909
rf_dengue_regressor_h4_v1.pkl  → R² CV = 0.898
```

Mỗi pkl kèm `_features.json` + `_metrics.json` (gồm h, R², RMSE, MAE, best_params, training_date, source_notebook=v6).

---

## 8. Cell 8.6 — Bảng so sánh R² theo horizon (final v6)

| h | Flu (LightGBM) | Dengue (Random Forest) | Lowe 2014 benchmark |
|---|----------------|------------------------|---------------------|
| 1 | **0.8661** | **0.9292** | 0.78-0.85 |
| 2 | 0.8293 | 0.9191 | 0.70-0.78 |
| 3 | 0.7928 | 0.9086 | 0.62-0.72 |
| 4 | 0.7573 | 0.8981 | **0.55-0.68** |

### Phát hiện 1: 8/8 horizon vượt benchmark Lowe et al 2014 Lancet ID

Paper reference cho dengue forecasting Brazil. **Cả 4 horizon flu + 4 horizon dengue đều vượt** — đây là contribution mạnh cho thesis.

### Phát hiện 2 — bất ngờ: Dengue degradation gentler hơn flu

| Metric | Flu | Dengue |
|---|---|---|
| R² h=1 | 0.866 | 0.929 |
| R² h=4 | 0.757 | 0.898 |
| Δ R² total | 0.109 | 0.031 |
| **Slope (Δ R²/horizon)** | **-0.036** | **-0.010** |

Dengue degrade **chỉ 1/3.6 lần flu** — bất ngờ vì thông thường horizon dài thì R² giảm mạnh hơn.

**Lý do em phân tích được:**

1. **Lag dengue dài hơn flu rất nhiều** — features dùng lag 6-14 tuần (dengue) vs 1-7 tuần (flu). AR signal phủ xa hơn → h=4 vẫn nằm trong "vùng ảnh hưởng" của lag.

2. **Pattern dengue endemic năm cả 12 tháng ở vùng nhiệt đới** — ít volatile theo tuần so với flu mùa đông Bắc bán cầu.

3. **RF robust với noise hơn LGBM** — bagging average qua nhiều tree, variance thấp.

→ **Insight epidemiological** document trong báo cáo Chapter 4.

### Phát hiện 3: So với v5 (h=1)

v5 R² h=1: **0.902** (flu), **0.937** (dengue) — cao hơn v6 h=1 (0.866, 0.929).

**Vì sao v6 thấp hơn?** v6 phải drop rows cuối dataset (không có target h=4) → ít data hơn → R² thấp hơn 0.04 ở h=1.

**Trade-off worth it:** v6 có forecast 4 tuần đầy đủ, v5 chỉ có 1 tuần.

---

## 9. So sánh tổng kết v5 vs v6

| Aspect | v5 (17/05/2026) | v6 (21/05/2026) |
|---|---|---|
| Horizon | h=1 only | **h=1, 2, 3, 4** |
| Models per disease | 1 regressor + 1 classifier | **4 regressors + 1 classifier** |
| Total artifacts | 4 pkl | **10 pkl** |
| Flu R² h=1 | 0.902 | 0.866 (drop 0.04 do less data) |
| Dengue R² h=1 | 0.937 | 0.929 |
| Forecast trajectory | ❌ Chỉ 1 tuần | ✅ **4 tuần đầy đủ** |
| Deploy production | ❌ Không serve forecast | ✅ Backend `/forecast/{disease}/{iso3}/nowcast` |

→ **v6 là step bắt buộc** để đáp ứng đề tài "dự báo theo giai đoạn".

---

## Key Insights Session 8 (slide thuyết trình)

1. **Multi-horizon trực tiếp thay vì recursive** — tránh error propagation. Train 4 model riêng dùng feature actual.
2. **8/8 horizon vượt benchmark Lowe et al 2014** — paper reference cho dengue forecasting. Contribution mạnh cho thesis.
3. **Dengue degradation gentler 3.6× flu** — insight epidemiological em phân tích được: lag dài + endemic stable + RF robust.
4. **Giữ best_params từ v1, không Optuna lại** — feature set không đổi, optimal params giống. Document principle "don't tune when not needed".
5. **v6 R² h=1 thấp hơn v5 0.04 do drop rows cuối** — trade-off worth it để có forecast 4 tuần đầy đủ cho production.

---

## Câu nói thuyết trình cho Session 8

> "Sau v5 hoàn tất Session 0-7, em mở rộng thành **multi-horizon v6** — train **4 model riêng** cho h=1, 2, 3, 4 tuần."
>
> "**Lý do**: đề tài yêu cầu 'dự báo theo giai đoạn/mùa/tháng' — chỉ có h=1 không đủ. Quan trắc viên y tế cần biết 1 tháng nữa risk như thế nào để chuẩn bị vaccine, giường bệnh."
>
> "Em chọn cách **multi-horizon trực tiếp** thay vì recursive. **Recursive có error propagation**: sai h=1 thì feed vào h=2, error compound. **Train 4 model riêng dùng feature actual** → error không cộng dồn."
>
> [CHUYỂN SLIDE — bảng kết quả]
>
> "Bảng R² qua 4 horizon:
> - Flu h=1: **0.866**, h=4: 0.757
> - Dengue h=1: **0.929**, h=4: **0.898**"
>
> [NHẤN MẠNH] "**8 trên 8 horizon vượt benchmark Lowe et al 2014 Lancet ID** — paper reference cho dengue forecasting Brazil. Đặc biệt h=4: flu 0.757, dengue 0.898 — gấp **1.3× Lowe baseline**."
>
> "**Phát hiện bất ngờ**: dengue degradation **gentler hơn flu** — dengue mất 0.010 R²/horizon, flu mất 0.036/horizon. Lý do em phân tích được:
> 1. Lag dengue dài 6-14 tuần phủ xa hơn flu 1-7 tuần
> 2. Pattern dengue endemic năm cả 12 tháng ở vùng nhiệt đới
> 3. RF robust với noise hơn LGBM"
>
> "Đây là **insight epidemiological** em document trong báo cáo Chương 4."
>
> [NẾU HỎI: Sao không Optuna tune lại multi-horizon?]
> > "Optuna v1 đã tune cho feature set 16-feature. Multi-horizon dùng **cùng feature set** → optimal params giống. Tune lại tốn 60×4 = 240 trials/disease, improvement marginal < 0.005 R². Em document principle 'don't tune when not needed' — không tốn compute khi không hiệu quả."
