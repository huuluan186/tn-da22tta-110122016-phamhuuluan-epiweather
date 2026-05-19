# Session 8: Huấn Luyện Model XGBoost + Optuna

---

## Tại sao chọn XGBoost?

**Bài toán của mình có đặc điểm:**
- Dữ liệu **tabular** (bảng), không phải ảnh hay văn bản
- **Nhiều quốc gia** với pattern khác nhau — model phải học được điều kiện địa lý
- Dữ liệu có **missing values** (weather của 14 quốc gia đảo nhỏ)
- Cần **interpretability** — giải thích được feature nào quan trọng

XGBoost thống trị các bài toán tabular data. Nó xử lý missing values natively, không cần scale features (tree-based), và feature importance dễ hiểu.

---

## Cell 8.0 — RESTART CELL: Load Feature Files

```python
features_flu    = pd.read_csv(FEATURES_FLU_FILE)
features_dengue = pd.read_csv(FEATURES_DENGUE_FILE)

FEATURE_COLS_FLU    = [c for c in features_flu.columns
                       if c not in ['iso3','iso_year','iso_week',TARGET_FLU]]
FEATURE_COLS_DENGUE = [c for c in features_dengue.columns
                       if c not in ['iso3','iso_year','iso_week',TARGET_DENGUE]]

print(f'✅ flu:    {features_flu.shape}  | features: {len(FEATURE_COLS_FLU)}')
print(f'✅ dengue: {features_dengue.shape} | features: {len(FEATURE_COLS_DENGUE)}')
```

**Output xác nhận:**
- Flu: ~44,035 rows, 11 features (AR lag ngắn 1–3 tuần + rolling 4w + 4 weather lags)
- Dengue: ~1,435 rows, 13 features (AR lag dài 6–14 tuần + rolling + 4 weather lags)

Dengue ít rows hơn nhiều (1,435 vs 44,035) là bình thường — chỉ endemic countries có `dengue > 0` và cần đủ 14 tuần lịch sử để tạo lag dài nhất.

---

## Cell 8.1 — Feature Column Definition (Auto-detect)

```python
EXCLUDE_COLS = {'iso3', 'iso_year', 'iso_week', TARGET_FLU, TARGET_DENGUE,
                'rsv_cases', 'dengue_total', 'dengue_log1p', 'malaria_cases', 'malaria_log1p'}

FEATURE_COLS_FLU = [c for c in features_flu.columns
                    if c not in EXCLUDE_COLS and not c.startswith('dengue_lag')]
FEATURE_COLS_DENGUE = [c for c in features_dengue.columns
                       if c not in EXCLUDE_COLS and not c.startswith('inf_lag')]
```

Cross-exclude: `dengue_lag*` bị loại khỏi flu model, `inf_lag*` bị loại khỏi dengue model. Nếu sau này ai thêm cột mới vào feature file, cell này tự động lọc đúng theo từng model.

---

## Cell 8.2 — Walk-Forward Cross-Validation Function

```python
def walk_forward_cv(df, feature_cols, target, val_years=range(2014, 2020)):
    results = []
    for val_year in val_years:
        train_mask = df['iso_year'] < val_year
        val_mask   = df['iso_year'] == val_year
        X_train = df.loc[train_mask, feature_cols]
        y_train = df.loc[train_mask, target]
        X_val   = df.loc[val_mask, feature_cols]
        y_val   = df.loc[val_mask, target]
        model = XGBRegressor(
            n_estimators=300, learning_rate=0.05, max_depth=6,
            subsample=0.8, colsample_bytree=0.8, random_state=42, verbosity=0
        )
        model.fit(X_train, y_train)
        preds = np.maximum(model.predict(X_val), 0)
        mae   = mean_absolute_error(y_val, preds)
        rmse  = np.sqrt(mean_squared_error(y_val, preds))
        smape = 100 * np.mean(2*np.abs(y_val-preds)/(np.abs(y_val)+np.abs(preds)+1e-8))
        results.append({'fold': val_year, 'mae': mae, 'rmse': rmse, 'smape': smape,
                        'n_train': train_mask.sum(), 'n_val': val_mask.sum()})
    return pd.DataFrame(results)
```

**Đây là điểm then chốt về methodology mà nhiều project ML làm sai.**

Tại sao không dùng random train/test split? Dữ liệu thời gian có tính **temporal dependency** — ca bệnh tuần này phụ thuộc tuần trước. Nếu split ngẫu nhiên, test set có thể bao gồm tuần 50/2016 trong khi train set có tuần 51/2016 — model "thấy tương lai" trong training.

**Walk-Forward CV:**
```
Fold 1: Train 2010–2013 | Validate 2014
Fold 2: Train 2010–2014 | Validate 2015
Fold 3: Train 2010–2015 | Validate 2016
Fold 4: Train 2010–2016 | Validate 2017
Fold 5: Train 2010–2017 | Validate 2018
Fold 6: Train 2010–2018 | Validate 2019
```

Mỗi fold chỉ dùng **dữ liệu quá khứ** để validate **dữ liệu tương lai**. **sMAPE thay MAPE:** khi `y=0` và `ŷ>0` nhỏ, MAPE → ∞; sMAPE chỉ → 200% — an toàn hơn với 73% zero rows của Influenza.

---

## Cell 8.3 — Prophet Baseline: Influenza

```python
from prophet import Prophet

def prophet_walk_forward(df, target, val_years=range(2014, 2020)):
    global_df = df.groupby(['iso_year','iso_week'])[target].sum().reset_index()
    global_df['ds'] = pd.to_datetime(...)
    global_df = global_df.rename(columns={target: 'y'})
    # Walk-forward: train trên tất cả năm trước val_year
    for val_year in val_years:
        m = Prophet(yearly_seasonality=True, weekly_seasonality=False, daily_seasonality=False)
        m.fit(train_df)
        fc = m.predict(val_df[['ds']])
        # Tính MAE, RMSE, sMAPE
        ...
    return pd.DataFrame(results)

cv_prophet_flu = prophet_walk_forward(features_flu, TARGET_FLU)
print(f'Mean MAE:  {cv_prophet_flu["mae"].mean():,.0f}')
print(f'Mean sMAPE: {cv_prophet_flu["smape"].mean():.1f}%')
```

**Output kỳ vọng:**
- Mean MAE: ~1,967 | sMAPE: ~43.5%
- Fold tệ nhất: 2018 (sMAPE 82.9%) — mùa cúm 2018 bất thường toàn cầu

Prophet train trên **global aggregate** (tổng tất cả quốc gia mỗi tuần), không dùng per-country features hay weather — chỉ có trend + yearly seasonality. Đây là **lower bound** — XGBoost phải làm tốt hơn.

Lưu ý: MAE Prophet (~1,967) và XGBoost (~16 per country-week) **không so sánh trực tiếp được** vì khác granularity (global vs per-country). Dùng sMAPE để so sánh fair.

---

## Cell 8.4 — Prophet Baseline: Dengue

```python
cv_prophet_dengue = prophet_walk_forward(features_dengue, TARGET_DENGUE)
print(f'Mean sMAPE: {cv_prophet_dengue["smape"].mean():.1f}%')
```

**Output kỳ vọng:** sMAPE ~93.4%

sMAPE cao vì dengue data sparse — global aggregate có nhiều tuần zero, khi đó sMAPE → 200% và kéo mean lên cao. XGBoost cần đạt sMAPE thấp hơn nhiều trên per-country level để justify complexity.

---

## Cell 8.5 — Walk-Forward CV: XGBoost Influenza

```python
cv_flu = walk_forward_cv(features_flu, FEATURE_COLS_FLU, TARGET_FLU)
print(cv_flu.to_string(index=False))
print(f'Mean MAE:  {cv_flu["mae"].mean():.2f}')
print(f'Mean sMAPE: {cv_flu["smape"].mean():.1f}%')
```

**Output kỳ vọng:**
- Mean MAE: ~16.55 per country-week
- sMAPE all-rows: ~97.9% (bị inflate bởi 73% zero rows)
- **sMAPE non-zero rows: ~51.4%** — con số thực phản ánh chất lượng model

---

## Cell 8.5b — Optuna Hyperparameter Tuning (60 trials)

```python
import optuna

def objective(trial):
    params = {
        'n_estimators'     : trial.suggest_int('n_estimators', 200, 1000, step=50),
        'max_depth'        : trial.suggest_int('max_depth', 3, 8),
        'learning_rate'    : trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
        'subsample'        : trial.suggest_float('subsample', 0.6, 1.0),
        'colsample_bytree' : trial.suggest_float('colsample_bytree', 0.5, 1.0),
        'min_child_weight' : trial.suggest_int('min_child_weight', 1, 10),
        'reg_alpha'        : trial.suggest_float('reg_alpha', 0.0, 1.0),
        'reg_lambda'       : trial.suggest_float('reg_lambda', 0.5, 5.0),
        'early_stopping_rounds': 30, 'eval_metric': 'mae',
        'random_state': 42, 'n_jobs': -1, 'tree_method': 'hist',
    }
    return walk_forward_cv_score(params)  # Returns mean CV MAE

study = optuna.create_study(direction='minimize',
    sampler=optuna.samplers.TPESampler(seed=42))
study.optimize(objective, n_trials=60, show_progress_bar=True)

print(f'Best MAE (log1p): {study.best_value:.4f}')
```

**Optuna** là framework Bayesian optimization — nó học từ các trial trước để đề xuất trial tiếp theo thông minh hơn. Hiệu quả hơn grid search và random search.

**Tại sao 60 trials?** Thực nghiệm cho thấy 60 trials đủ để explore không gian tham số. Ít hơn (20-30) chưa đủ; nhiều hơn (100+) tốn thời gian nhưng cải thiện ít dần. 60 trials mất khoảng **30–45 phút** trên Colab GPU.

**CV MAE cải thiện:** 0.460 → **0.4508** (−2%)

Cải thiện khiêm tốn 2% là tín hiệu tốt — xác nhận model ở [8.5] đã được cấu hình hợp lý. Bộ params tìm được thường có `learning_rate` rất thấp (~0.03) đi kèm `n_estimators` lớn (~650) — chiến lược **slow-learning / many-trees**, phù hợp với flu data có nhiều noise.

---

## Cell 8.6 — Train Final XGBoost Flu với Optuna Params

```python
best_flu_params = {**study.best_params, 'random_state': 42, 'n_jobs': -1, 'tree_method': 'hist'}
best_flu_params.pop('early_stopping_rounds', None)

train_full = features_flu.dropna(subset=FEATURE_COLS_FLU + [TARGET_FLU])
xgb_flu_tuned = xgb.XGBRegressor(**best_flu_params)
xgb_flu_tuned.fit(train_full[FEATURE_COLS_FLU], train_full[TARGET_FLU])

# In-sample check
preds_is = np.maximum(xgb_flu_tuned.predict(train_full[FEATURE_COLS_FLU]), 0)
print(f'In-sample MAE (log1p): {mean_absolute_error(train_full[TARGET_FLU], preds_is):.4f}')
print(f'In-sample R2         : {r2_score(train_full[TARGET_FLU], preds_is):.4f}')

xgb_flu = xgb_flu_tuned  # Replace xgb_flu để SESSION 9 dùng model mới
```

Train final model trên **toàn bộ 2010–2019** — không chia val fold để tận dụng tối đa data. In-sample MAE/R² chỉ để xác nhận model fit bình thường — thước đo thật là holdout 2022 (SESSION 9).

---

## Cell 8.7 — Walk-Forward CV: XGBoost Dengue

```python
cv_dengue = walk_forward_cv(features_dengue, FEATURE_COLS_DENGUE, TARGET_DENGUE)
print(f'Mean MAE:  {cv_dengue["mae"].mean():.3f}')
print(f'Mean sMAPE: {cv_dengue["smape"].mean():.1f}%')
```

**Output kỳ vọng:**
- Mean MAE: ~0.275 (log scale) | sMAPE: **~7.2%**

XGBoost thắng Prophet rõ ràng (7.2% vs 93.4% sMAPE) — per-country AR lags và weather features bắt được pattern mùa mưa nhiệt đới tốt hơn nhiều. Tuy nhiên chỉ có 1,435 training rows — kết quả tốt có thể phản ánh overfitting; SESSION 9 validate trên 2022 sẽ xác nhận.

---

## Cell 8.8 — Save Final Model PKL Artifacts

```python
# Flu: dùng xgb_flu đã có từ [8.6] (Optuna-tuned) — không retrain lại
joblib.dump(xgb_flu, MODEL_FLU_FILE)
print(f"Saved xgb_flu (Optuna-tuned, {len(FEATURE_COLS_FLU)} features)")

# Dengue: train trên full 2010-2019 (default params — Optuna chưa chạy cho dengue)
xgb_dengue = XGBRegressor(
    n_estimators=300, learning_rate=0.05, max_depth=6,
    subsample=0.8, colsample_bytree=0.8, random_state=42, verbosity=0
)
xgb_dengue.fit(X_train_dengue, y_train_dengue)
joblib.dump(xgb_dengue, MODEL_DENGUE_FILE)
```

**Lưu ý:** Optuna chỉ chạy cho **Flu**. Dengue dùng default params vì dataset nhỏ (1,435 rows) và Optuna 60 trials trên dataset nhỏ dễ overfit vào CV folds.

---

## Cell 8.8b — XGBClassifier: Risk Classification Trực Tiếp

```python
from xgboost import XGBClassifier

def make_risk_labels(series, low_q=0.33, high_q=0.67):
    low_t  = series.quantile(low_q)
    high_t = series.quantile(high_q)
    return pd.cut(series, bins=[-np.inf, low_t, high_t, np.inf],
                  labels=["Low", "Medium", "High"])

# Train XGBClassifier cho cả Flu và Dengue
xgb_cls_flu = XGBClassifier(n_estimators=200, max_depth=5, ...)
xgb_cls_flu.fit(flu_train_cls[FEATURE_COLS_FLU], y_cls_flu)

print(f"Flu classes:    {le_flu.classes_}")
print(f"Dengue classes: {le_dengue.classes_}")
```

Cách tiếp cận song song: thay vì regression → threshold, train thẳng **classifier** với nhãn Low/Medium/High. Quantile-based label đảm bảo 3 class cân bằng (~⅓ mỗi class). Precision/Recall/F1 của cả 2 approach sẽ được đo và so sánh ở SESSION 9 [9.3].

---

## Cell 8.9 — Feature Importance

```python
for model, feature_cols, title in [
    (xgb_flu, FEATURE_COLS_FLU, 'Influenza — Top 15 Features'),
    (xgb_dengue, FEATURE_COLS_DENGUE, 'Dengue — Top 15 Features'),
]:
    imp = pd.Series(model.feature_importances_, index=feature_cols)
    top15 = imp.nlargest(15).sort_values()
    top15.plot(kind='barh', ...)
```

**Top features cho Flu:**

| Rank | Feature | Importance |
|------|---------|-----------|
| 1 | `inf_lag1w` | ~47% |
| 2 | `inf_lag2w` | ~27% |
| 3 | `inf_roll4w` | ~13% |
| ... | weather features | ~0% |

**Top features cho Dengue:**

| Rank | Feature | Importance |
|------|---------|-----------|
| 1 | `dengue_roll4w` | ~77% |
| 2 | `dengue_lag6w/8w` | ~14% |
| ... | weather features | ~0% |

**Điều này có nghĩa gì?**

Cả 2 model hoạt động như **AR model với seasonal correction** từ `sin/cos_week` — không phải weather-driven. AR momentum lag ngắn mạnh hơn nhiều, `sin/cos_week` đã encode seasonality ngầm nên weather không thêm được signal mới.

Weather importance ≈ 0 **không có nghĩa** weather vô ích về mặt dịch tễ — chỉ bị lấn át bởi AR ở short-term prediction. Cần giải thích rõ trong báo cáo.

---

## Cell 8.10 — So sánh Prophet vs XGBoost

```python
comparison = pd.DataFrame([
    {'Model':'Prophet','Disease':'Influenza','sMAPE(%)':43.5,'Scope':'Global aggregate'},
    {'Model':'XGBoost','Disease':'Influenza','sMAPE(%)':51.4,'Scope':'Per-country (non-zero)'},
    {'Model':'Prophet','Disease':'Dengue','sMAPE(%)':93.4,'Scope':'Global aggregate'},
    {'Model':'XGBoost','Disease':'Dengue','sMAPE(%)':7.2,'Scope':'Per-country'},
])
```

**Tóm tắt:**
- **Dengue:** XGBoost thắng rõ ràng (7.2% vs 93.4% sMAPE)
- **Influenza:** gần ngang nhau (51.4% vs 43.5%) — AR momentum đã capture phần lớn seasonal signal

SARIMA và LSTM là **future work**: SARIMA phù hợp per-country nhưng chậm với 172 model riêng; LSTM cần nhiều data và dengue 1,435 rows hiện tại chưa đủ.

---

## Kết thúc Session 8

Sau session này bạn có:
- `xgb_flu_final.pkl` — XGBoost Flu model (Optuna-tuned, train 2010–2019)
- `xgb_dengue_final.pkl` — XGBoost Dengue model (default params)

Session 9 sẽ **kiểm tra thực tế**: model có dự báo đúng cho năm 2022 không?

---

## Key Insights từ Session 8

**1. Walk-forward CV không phải tùy chọn — là bắt buộc với time-series**
Random split cho time-series = model thấy tương lai trong training. Với flu data, ca bệnh tuần này cao correlate với tuần trước — nếu split ngẫu nhiên, AR lags sẽ leak thông tin future vào training. Walk-forward là phương pháp duy nhất đúng.

**2. Optuna 60 trials chỉ cải thiện 2% CV MAE → model baseline đã được cấu hình hợp lý**
Cải thiện nhỏ là tín hiệu tốt, không phải xấu. Nếu Optuna cải thiện 30–40%, nghĩa là default params quá tệ. 2% xác nhận XGBoost với params hợp lý đã gần optimal. Thời gian 30–45 phút Optuna đáng đầu tư một lần.

**3. AR features chiếm 70–90% importance — model hoạt động như AR + seasonal correction**
`inf_lag1w` ~47%, `inf_lag2w` ~27%, `inf_roll4w` ~13% — top 3 features đã chiếm ~87%. Weather features ~0%. Đây không phải failure của weather features — AR momentum ngắn hạn mạnh hơn bất kỳ signal nào khác ở weekly prediction. Weather sẽ quan trọng hơn ở horizon dài hơn (4+ tuần ahead).

**4. Prophet thắng trên Flu sMAPE (43.5% vs 51.4%) nhưng thua trên Dengue (93.4% vs 7.2%)**
Sự khác biệt này cho thấy Dengue cần per-country AR features rõ ràng — global aggregate Prophet không capture được sự đa dạng mùa vụ. Flu thì global aggregate vẫn capture được seasonal pattern vì đồng bộ theo bán cầu.

**5. Dengue không chạy Optuna là quyết định đúng**
1,435 training rows / 6 CV folds ≈ 240 rows mỗi fold. Optuna 60 trials trên dataset này dễ overfit vào noise của CV folds. Default params với conservative hyperparams (max_depth=6, subsample=0.8) an toàn hơn.
