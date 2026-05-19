# Session 9: Đánh Giá 2022, Risk Classification & Export

---

## Tại sao 2022 là năm validation?

Model train trên 2010–2019. Mình bỏ 2020–2021 vì COVID. Năm 2022 là năm đầu tiên sau COVID mà pattern dịch bệnh bắt đầu phục hồi gần bình thường.

Đây là **post-COVID generalization test** — câu hỏi thực chất là: *Model học từ thế giới trước COVID, có áp dụng được cho thế giới sau COVID không?*

Nếu được → model capture được seasonal pattern cơ bản của dịch, không chỉ overfitting vào giai đoạn 2010–2019.

---

## Cell 9.0 — RESTART CELL: Load Models + Features

```python
xgb_flu    = joblib.load(MODEL_FLU_FILE)
xgb_dengue = joblib.load(MODEL_DENGUE_FILE)
features_flu    = pd.read_csv(FEATURES_FLU_FILE)
features_dengue = pd.read_csv(FEATURES_DENGUE_FILE)

FEATURE_COLS_FLU    = [c for c in features_flu.columns
                       if c not in EXCLUDE_COLS and not c.startswith('dengue_lag')]
FEATURE_COLS_DENGUE = [c for c in features_dengue.columns
                       if c not in EXCLUDE_COLS and not c.startswith('inf_lag')]
```

Sau khi chạy cell này, toàn bộ Session 9 có thể chạy độc lập không cần Session 7 hay 8.

---

## Cell 9.0b — Download + Process ERA5 2022

```python
ERA5_2022_FILE = WEATHER_DIR / 'era5_weekly_2022_final.csv'

if ERA5_2022_FILE.exists():
    weather_2022 = pd.read_csv(ERA5_2022_FILE)
    USE_REAL_WEATHER = True
else:
    # Step 1: Download từ CDS API
    c_api = cdsapi.Client()
    c_api.retrieve('reanalysis-era5-single-levels-monthly-means', {
        'product_type': 'monthly_averaged_reanalysis',
        'variable': VARS_ALL,
        'year': '2022',
        'month': [f'{m:02d}' for m in range(1, 13)],
        'data_format': 'netcdf',
        ...
    }, str(nc_file))

    # Step 2: Unzip tách instant/accumulated variables
    # Step 3: Aggregate theo KD-tree grid (giống SESSION 4)
    # Step 4: Expand monthly → weekly bằng forward fill
    weather_2022.to_csv(ERA5_2022_FILE, index=False)
    USE_REAL_WEATHER = True
```

**Quan trọng:** Mình dùng **ERA5 thực tế năm 2022**, không dùng giá trị trung bình training (2010–2019). Tại sao?

Trong production (FastAPI phục vụ thực tế), weather data đến từ API thực — không phải từ training mean. Nếu validate bằng training mean, metrics sẽ cao hơn thực tế nhưng không phản ánh hiệu năng production.

**Trade-off:** Năm 2022 có **La Niña** — hiện tượng khí hậu làm nhiệt độ và mưa lệch khỏi bình thường. Điều này làm Flu R² giảm từ 0.811 (training mean) xuống 0.791 (ERA5 thực). −2% là noise chấp nhận được vì ta đổi lấy tính nhất quán với production pipeline.

Pipeline: (1) Download NetCDF từ CDS API → (2) Unzip tách instant/accum → (3) Aggregate theo KD-tree grid giống [4.x] → (4) Expand monthly → weekly bằng forward fill.

---

## Cell 9.1 — Build Features 2022 + Predict + Metrics

```python
# CCF lags phải khớp với SESSION 7 [7.5]
WEATHER_LAGS_FLU = {'temp_c': 4, 'humidity_pct': 8, 'solar_wm2': 8, 'dewpoint_c': 2}
WEATHER_LAGS_DEN = {'temp_c': 0, 'humidity_pct': 2, 'dewpoint_c': 0, 'precip_mm': 0}

# 1. Load FluNet + Dengue raw (2010-2022, bỏ 2020-2021)
# 2. Merge weather: ưu tiên ERA5 2022 thật, fallback về per-country training mean
# 3. Feature engineering: AR lags, rolling, weather lags, sin/cos, who_region_enc
# 4. Filter val_flu = rows có iso_year == 2022, dropna
# 5. Predict

preds_flu    = np.maximum(xgb_flu.predict(val_flu[FEATURE_COLS_FLU]), 0)
preds_dengue = np.maximum(xgb_dengue.predict(val_dengue[FEATURE_COLS_DENGUE]), 0)

# Metrics in log1p space
r2_flu   = r2_score(y_flu_true, preds_flu)
mae_flu  = mean_absolute_error(y_flu_true, preds_flu)
r2_den   = r2_score(y_dengue_true, preds_dengue)
mae_den  = mean_absolute_error(y_dengue_true, preds_dengue)

print(f'Influenza - MAE(log): {mae_flu:.4f} | R2: {r2_flu:.3f}')
print(f'Dengue    - MAE: {mae_den:.3f} | R2: {r2_den:.3f}')
```

**Chú ý quan trọng:** Mình bỏ 2020–2021 khỏi training set, nhưng vẫn cần dữ liệu 2020–2021 để tính AR lags cho 2022. Ví dụ `inf_lag1w` của tuần 1/2022 = ca bệnh tuần 52/2021. Không thể bỏ hoàn toàn 2020–2021 khỏi feature computation.

**Kết quả validation 2022:**
```
Flu   - MAE(log): ~0.41 | R² = 0.7906
Dengue - MAE:     ~0.28 | R² = 0.8494
```

**`expm1()` để đánh giá trên raw scale:** Nếu model dự báo `inf_log1p = 3.5`, số ca thực = `expm1(3.5) = e^3.5 - 1 ≈ 32.1 ca`. Mình evaluate trên cả log scale (fair comparison) và raw scale (ý nghĩa thực tế).

---

## Cell 9.2 — Prediction vs Actual: Global Aggregate 2022

```python
flu_agg = val_flu.groupby('iso_week')[[TARGET_FLU, 'pred']].sum()

axes[0].plot(flu_agg.index, flu_agg[TARGET_FLU], label='Actual', lw=2)
axes[0].plot(flu_agg.index, flu_agg['pred'], label='Predicted', ls='--', lw=2)
axes[0].set_title(f'Influenza 2022 — Global Aggregate (R²={r2_flu:.3f})')
```

Biểu đồ Actual vs Predicted theo tuần. Nếu prediction bắt được seasonal peak (Influenza: tháng 12–2, Dengue: tháng 6–10 tùy vùng) → model có seasonality tốt.

---

## Cell 9.3 — Risk Classification: Vấn đề Global Quantile

```python
def classify_risk(pred_series, train_preds):
    low_q  = np.quantile(train_preds, 0.33)
    high_q = np.quantile(train_preds, 0.67)
    return pd.cut(pred_series, bins=[-np.inf, low_q, high_q, np.inf],
                  labels=['Low', 'Medium', 'High'])

# Flu risk classification report
print(classification_report(risk_true_flu, risk_pred_flu,
      target_names=['Low','Medium','High']))
```

**Vấn đề với global quantile:** 73% tuần flu = 0 → global Q33 = Q67 = 0 → Medium band biến mất.

```
Risk: [predicted <= 0] = Low, [predicted > 0] = High
Medium không tồn tại → Medium F1 = 0.06
```

---

## Cell 9.3b — Per-Country Quantile Thresholds: Fix Medium F1

```python
MIN_NONZERO = 8

train_nz_flu = flu_df[
    flu_df['iso_year'].between(TRAIN_START, TRAIN_END) &
    (flu_df['inf_log1p'] > 0)
][['iso3', 'inf_log1p']]

country_q = (
    train_nz_flu.groupby('iso3')['inf_log1p']
    .quantile([0.33, 0.67])
    .unstack()
    .rename(columns={0.33: 'q33', 0.67: 'q67'})
)
n_obs = train_nz_flu.groupby('iso3')['inf_log1p'].count()
country_q = country_q[n_obs >= MIN_NONZERO]

# Global fallback cho countries < 8 non-zero weeks
global_q33 = train_nz_flu['inf_log1p'].quantile(0.33)
global_q67 = train_nz_flu['inf_log1p'].quantile(0.67)

def flu_risk_pc(iso3, val):
    if iso3 in country_q.index:
        q33, q67 = country_q.loc[iso3, 'q33'], country_q.loc[iso3, 'q67']
    else:
        q33, q67 = global_q33, global_q67
    if val <= q33:  return 'Low'
    if val <= q67:  return 'Medium'
    return 'High'

print(classification_report(tmp['risk_true'], tmp['risk_pred'],
                            labels=['Low','Medium','High']))
```

**Logic:** Thay vì so sánh Vietnam với USA (không công bằng), mình so sánh **Vietnam với chính Vietnam**:
- "Ca thấp" = thấp hơn 33% các tuần có dịch của Vietnam trong quá khứ
- "Ca cao" = cao hơn 67% các tuần có dịch của Vietnam trong quá khứ

**Ví dụ thresholds:**
```
Vietnam: Q33=1.2, Q67=3.5  (log1p scale)
USA:     Q33=6.8, Q67=9.2
Nigeria: Q33=0.7, Q67=1.8
```

**Kết quả sau per-country thresholds:**

| Metric | Global Quantile | Per-Country Quantile |
|--------|----------------|---------------------|
| Flu Medium F1 | 0.06 | **0.52** |
| Flu Macro F1 | 0.40 | **0.72** |
| Flu Accuracy | 0.42 | **0.81** |
| Dengue Macro F1 | 0.85 | 0.85 (không đổi) |

Dengue không cần fix vì endemic countries ít zero hơn — global quantile đã ổn.

---

## Cell 9.4 — Summary Table

```python
summary = pd.DataFrame([
    {'model': 'XGBoost Influenza', 'target': TARGET_FLU, 'val_year': VAL_YEAR,
     'val_MAE': mae_flu, 'val_RMSE': rmse_flu,
     'n_features': len(FEATURE_COLS_FLU), 'n_countries': val_flu['iso3'].nunique()},
    {'model': 'XGBoost Dengue', 'target': TARGET_DENGUE, 'val_year': VAL_YEAR,
     'val_MAE': mae_den, 'val_RMSE': rmse_den,
     'n_features': len(FEATURE_COLS_DENGUE), 'n_countries': val_dengue['iso3'].nunique()},
])
print(f'Influenza R²: {r2_flu:.3f}')
print(f'Dengue    R²: {r2_den:.3f}')
```

---

## Cell 9.4b — Export model_metrics.json

```python
model_metrics = {
    'flu': {
        'version': 'v1.0',
        'algorithm': 'XGBRegressor',
        'holdout': {
            'eval_set': 'val_2022',
            'r2_score': 0.7906,
            'mae': ...,
            'risk_macro_f1': 0.7161,
            'risk_accuracy': ...,
            'notes': 'ERA5 2022 real weather, holdout never touched in training',
        }
    },
    'dengue': {
        'holdout': {
            'r2_score': 0.8494,
            'risk_macro_f1': 0.8476,
            ...
        }
    }
}
with open(metrics_file, 'w') as f:
    json.dump(model_metrics, f, indent=2)
```

**Kết quả thực tế đã xác nhận:**
- **Flu:** R² = 0.7906 | Macro F1 = 0.7161
- **Dengue:** R² = 0.8494 | Macro F1 = 0.8476

File này là **single source of truth** cho `load_db.py` — thay vì hardcode từng giá trị, script đọc trực tiếp từ file này, đảm bảo số liệu trong DB luôn khớp với kết quả thực tế.

---

## Cell 9.5 — Export Artifacts cho FastAPI

```python
# Feature list (cho FastAPI inference)
feature_export = {
    'flu': {
        'target': TARGET_FLU,
        'features': FEATURE_COLS_FLU,
        'weather_lags': WEATHER_LAGS_FLU,
        ...
    },
    'dengue': { ... },
    'meta': {
        'train_period': f'{TRAIN_START}-{TRAIN_END}',
        'val_year': VAL_YEAR,
        'exclude_years': COVID_YEARS,
    }
}
with open(FEATURE_LIST_FILE, 'w') as f:
    json.dump(feature_export, f, indent=2)

# Per-country flu risk thresholds
thresh_export = pd.concat([
    country_q.reset_index(),
    pd.DataFrame({"iso3": ["_global"], "q33": [global_q33], "q67": [global_q67]})
], ignore_index=True)
thresh_export.to_csv(risk_thresh_file, index=False)
print(f"{len(country_q)} country-specific + 1 global fallback")
```

**3 artifacts này** là tất cả những gì FastAPI cần để phục vụ dự báo:
- `xgb_flu_final.pkl` — model
- `xgb_dengue_final.pkl` — model
- `feature_list.json` — contract features giữa ML và API
- `model_metrics.json` — metrics để hiển thị trên dashboard
- `flu_risk_thresholds.csv` — per-country quantile thresholds

Không cần access training data, không cần Colab.

---

## Kết thúc Session 9 và Toàn Pipeline

```
Raw data (3 nguồn: FluNet, OpenDengue, ERA5)
    ↓ SESSION 0–1: Load, inspect
    ↓ SESSION 2–3: Data quality + EDA + seasonality
    ↓ SESSION 4: ERA5 → bảng quốc gia (KD-tree)
    ↓ SESSION 5: Merge thành master dataset
    ↓ SESSION 6: CCF analysis → optimal lags
    ↓ SESSION 7: Feature engineering (AR, rolling, weather lag, seasonal, WHO region)
    ↓ SESSION 8: XGBoost + Optuna tuning + walk-forward CV + Prophet baseline
    ↓ SESSION 9: Validate 2022 (ERA5 real), risk classification, export
         ↓
    5 files: xgb_flu.pkl, xgb_dengue.pkl, feature_list.json,
             model_metrics.json, flu_risk_thresholds.csv
         ↓
    FastAPI backend phục vụ dashboard
```

**Kết quả cuối cùng:**
- **Flu:** R² = 0.791, Macro F1 = 0.72
- **Dengue:** R² = 0.849, Macro F1 = 0.85

Xem file [hanh_trinh_cai_thien.md](hanh_trinh_cai_thien.md) để hiểu tại sao từ R²=0.488 lên 0.791.

---

## Key Insights từ Session 9

**1. R²=0.791 trên holdout 2022 post-COVID là generalization thực sự**
Model train 2010–2019, skip 2020–2021, test 2022. Đây không chỉ là out-of-sample — là **out-of-distribution**: pattern dịch bệnh 2022 khác 2019 vì COVID đã thay đổi hành vi lây truyền, tập miễn dịch cộng đồng, hành vi con người. R²=0.791 trong điều kiện đó là kết quả đáng tin cậy để báo cáo.

**2. Global quantile → Medium F1=0.06, per-country quantile → Medium F1=0.52**
Đây là insight quan trọng nhất của risk classification. Với 73% zero rows trong flu, global Q33=Q67≈0 — không có không gian cho Medium class. Giải pháp per-country "so sánh Vietnam với chính Vietnam" về mặt khoa học đúng hơn: high risk không phải là nhiều hơn USA, mà là nhiều hơn bình thường của Vietnam.

**3. ERA5 2022 thực tế (La Niña) giảm R² 2% — đây là trade-off có chủ ý**
Dùng weather thực tế (−2% R²) thay vì training mean (giả vờ weather "trung bình") để đảm bảo pipeline nhất quán với production. Validation phản ánh đúng hiệu năng FastAPI sẽ có khi serve thực tế.

**4. Dengue R²=0.849 cao hơn Flu R²=0.791 vì pattern seasonal rõ hơn**
Dengue endemic countries có dịch rõ ràng theo mùa mưa, ít "nhiễu nền" hơn Flu (77.8% Week data đã sạch hơn). Mặt khác, training chỉ 1,435 rows nhưng pattern rất consistent → model học tốt trên ít data hơn.

**5. 5 artifacts là toàn bộ những gì FastAPI cần — không cần access training data**
`xgb_flu.pkl`, `xgb_dengue.pkl`, `feature_list.json`, `model_metrics.json`, `flu_risk_thresholds.csv`. Tách biệt hoàn toàn ML pipeline khỏi inference pipeline — đây là thiết kế MLOps cơ bản: model được "đóng gói" và deploy độc lập.
