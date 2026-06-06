"""Cập nhật Cell 112 và Cell 113 trong notebook."""
import json

NB_PATH = r'f:\BAO_CAO\DO_AN_TOT_NGHIEP\KLTN\KLTN_EpiWeather_ML_v6.ipynb'

with open(NB_PATH, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# ===== CELL 112 — Save final models (thêm v2 classifiers với sample_weight) =====
new_cell112 = """\
# [6.10] Save final models
import joblib, json as json_lib
from sklearn.utils.class_weight import compute_sample_weight

# Train cuối trên full data (2010-2018 cho flu, 2015-2018 cho dengue)
flu_full  = flu_feat[flu_feat['iso_year'] <= 2018]
deng_full = deng_feat[deng_feat['iso_year'] <= 2018]

# === 1. Flu Regressor (LightGBM tuned) — v1 không đổi ===
flu_reg = LGBMRegressor(**study_flu.best_params, random_state=42, n_jobs=-1, verbose=-1)
flu_reg.fit(flu_full[FEATURE_COLS_FLU], flu_full['flu_log'])
path = MODELS_DIR / 'lgbm_flu_regressor_v1.pkl'
joblib.dump(flu_reg, path)
json_lib.dump({'features': FEATURE_COLS_FLU, 'target': 'flu_log',
               'version': 'v1', 'date': '2026-05-16',
               'model_type': 'LightGBM', 'tuned': True,
               'best_params': study_flu.best_params},
              open(MODELS_DIR / 'lgbm_flu_regressor_v1_features.json', 'w'), indent=2)
json_lib.dump({'rmse': float(RESULTS['flu']['LightGBM-tuned']['rmse']),
               'mae' : float(RESULTS['flu']['LightGBM-tuned']['mae']),
               'r2'  : float(RESULTS['flu']['LightGBM-tuned']['r2']),
               'cv_folds': 6, 'cv_type': 'walk-forward', 'optuna_trials': 60},
              open(MODELS_DIR / 'lgbm_flu_regressor_v1_metrics.json', 'w'), indent=2)
print(f'[SAVED] {path.name} ({path.stat().st_size/1e3:.0f}KB)')

# === 2. Dengue Regressor (RandomForest tuned) — v1 không đổi ===
deng_reg = RandomForestRegressor(**study_deng.best_params, random_state=42, n_jobs=-1)
deng_reg.fit(deng_full[FEATURE_COLS_DENGUE], deng_full['deng_log'])
path = MODELS_DIR / 'rf_dengue_regressor_v1.pkl'
joblib.dump(deng_reg, path)
json_lib.dump({'features': FEATURE_COLS_DENGUE, 'target': 'deng_log',
               'version': 'v1', 'date': '2026-05-16',
               'model_type': 'RandomForest', 'tuned': True,
               'best_params': study_deng.best_params},
              open(MODELS_DIR / 'rf_dengue_regressor_v1_features.json', 'w'), indent=2)
json_lib.dump({'rmse': float(RESULTS['dengue']['RandomForest-tuned']['rmse']),
               'mae' : float(RESULTS['dengue']['RandomForest-tuned']['mae']),
               'r2'  : float(RESULTS['dengue']['RandomForest-tuned']['r2']),
               'cv_folds': 3, 'cv_type': 'walk-forward', 'optuna_trials': 60},
              open(MODELS_DIR / 'rf_dengue_regressor_v1_metrics.json', 'w'), indent=2)
print(f'[SAVED] {path.name} ({path.stat().st_size/1e6:.1f}MB)')

# === 3. Flu Classifier v2 — có sample_weight balanced ===
flu_clf_v2 = XGBClassifier(n_estimators=300, max_depth=6, learning_rate=0.05,
                            subsample=0.8, colsample_bytree=0.8,
                            objective='multi:softprob', num_class=3,
                            random_state=42, n_jobs=-1, verbosity=0)
y_flu_full = le.transform(flu_full['flu_risk_class'])
sw_flu = compute_sample_weight('balanced', y_flu_full)
flu_clf_v2.fit(flu_full[FEATURE_COLS_FLU], y_flu_full, sample_weight=sw_flu)
path = MODELS_DIR / 'xgb_flu_classifier_v2.pkl'
joblib.dump(flu_clf_v2, path)
json_lib.dump({'features': FEATURE_COLS_FLU, 'target': 'flu_risk_class',
               'classes': CLASS_LABELS, 'version': 'v2', 'date': '2026-06-02',
               'model_type': 'XGBClassifier',
               'note': 'Added sample_weight balanced — High recall 0.60->0.81'},
              open(MODELS_DIR / 'xgb_flu_classifier_v2_features.json', 'w'), indent=2)
json_lib.dump({'macro_f1': float(RESULTS['flu']['XGBClassifier']['macro_f1']),
               'auc_ovr' : float(RESULTS['flu']['XGBClassifier']['auc_ovr']),
               'high_recall_last_fold': 0.81,
               'cv_folds': 6, 'cv_type': 'walk-forward',
               'sample_weight': 'balanced'},
              open(MODELS_DIR / 'xgb_flu_classifier_v2_metrics.json', 'w'), indent=2)
print(f'[SAVED] {path.name} ({path.stat().st_size/1e3:.0f}KB)')

# === 4. Dengue Classifier v2 — có sample_weight balanced ===
deng_clf_v2 = XGBClassifier(n_estimators=300, max_depth=6, learning_rate=0.05,
                             subsample=0.8, colsample_bytree=0.8,
                             objective='multi:softprob', num_class=3,
                             random_state=42, n_jobs=-1, verbosity=0)
y_deng_full = le.transform(deng_full['dengue_risk_class'])
sw_deng = compute_sample_weight('balanced', y_deng_full)
deng_clf_v2.fit(deng_full[FEATURE_COLS_DENGUE], y_deng_full, sample_weight=sw_deng)
path = MODELS_DIR / 'xgb_dengue_classifier_v2.pkl'
joblib.dump(deng_clf_v2, path)
json_lib.dump({'features': FEATURE_COLS_DENGUE, 'target': 'dengue_risk_class',
               'classes': CLASS_LABELS, 'version': 'v2', 'date': '2026-06-02',
               'model_type': 'XGBClassifier',
               'note': 'Added sample_weight balanced — High recall 0.14->0.17, limited by small dataset'},
              open(MODELS_DIR / 'xgb_dengue_classifier_v2_features.json', 'w'), indent=2)
json_lib.dump({'macro_f1': float(RESULTS['dengue']['XGBClassifier']['macro_f1']),
               'auc_ovr' : float(RESULTS['dengue']['XGBClassifier']['auc_ovr']),
               'high_recall_last_fold': 0.17,
               'cv_folds': 3, 'cv_type': 'walk-forward',
               'sample_weight': 'balanced',
               'note': 'High recall thap do dataset nho (37 nuoc, 3 folds) — limitation'},
              open(MODELS_DIR / 'xgb_dengue_classifier_v2_metrics.json', 'w'), indent=2)
print(f'[SAVED] {path.name} ({path.stat().st_size/1e3:.0f}KB)')

print()
print('Tất cả models đã save tại:', MODELS_DIR)
print('Files:')
for f in sorted(MODELS_DIR.glob('*.pkl')):
    print(f'  {f.name}  ({f.stat().st_size/1e3:.0f}KB)')
"""

# ===== CELL 113 — SESSION 6 summary (cập nhật kết quả v2) =====
new_cell113 = """\
---
**KẾT QUẢ SESSION 6** (16/05/2026, cập nhật 02/06/2026)

Mục tiêu: Train + so sánh 5 regression models + 1 classification + Optuna tune top model.

Kết quả chính:

**Regression comparison (mean R² walk-forward CV):**
| Model | Flu R² | Dengue R² |
|---|---|---|
| Naive (baseline) | 0.560 | 0.487 |
| Prophet | 0.429 | -0.282 |
| XGBoost | 0.901 | 0.931 |
| LightGBM | **0.902** (winner) | 0.931 |
| RandomForest | 0.899 | **0.936** (winner) |
| **Best tuned** | **0.902** | **0.937** |

**Classification XGBClassifier — v1 (không có sample_weight) vs v2 (có sample_weight balanced):**
| | Flu macro-F1 | Flu High recall | Dengue macro-F1 | Dengue High recall |
|---|---|---|---|---|
| v1 (default) | 0.5422 | 0.60 | 0.4749 | 0.14 |
| **v2 (balanced)** | **0.5437** | **0.81** | **0.4885** | **0.17** |

Phân tích classification:
- Flu v2: High recall tăng từ 0.60 lên 0.81 — model bắt được 81% tuần dịch bùng phát. Đánh đổi Medium recall giảm (0.76→0.34) — chấp nhận được vì High recall quan trọng hơn cho bài toán cảnh báo.
- Dengue v2: High recall chỉ tăng 0.14→0.17 — sample_weight gần như không có tác dụng. Nguyên nhân cấu trúc: 37 quốc gia, 3 training folds, High class 249 samples/fold — không đủ để model học pattern epidemic. Ghi nhận là limitation trong báo cáo.

**Feature importance Top 3:**
- Flu: flu_log_lag1 (54%), flu_log_lag2 (31%), flu_log_lag3 (8%)
- Dengue: deng_log_rollmean4 (70%), rollmean8 (12%), lag6 (6%)
- AR features dominate (90%+), weather ~5% (khớp CCF findings)

Quyết định đã chốt:
- Flu production: LightGBM tuned v1 (LGBM thắng 6/6 folds vs XGBoost, systematic)
- Dengue production: RandomForest tuned v1 (bagging tốt hơn boosting cho data nhỏ)
- Classifier production: XGBClassifier v2 (có sample_weight balanced) cho cả flu và dengue
- Optuna improvement marginal (+0.04-0.07% R²) — default params gần near-optimal do AR dominant
- Prophet bị loại khỏi production (R² âm với dengue), giữ làm benchmark báo cáo
- Dengue classifier High recall thấp là limitation cơ bản của data — không phải lỗi model

Files tạo ra:
- models/lgbm_flu_regressor_v1.pkl + features.json + metrics.json
- models/rf_dengue_regressor_v1.pkl + features.json + metrics.json
- models/xgb_flu_classifier_v1.pkl (cũ, không có sample_weight — giữ để so sánh)
- models/xgb_flu_classifier_v2.pkl + features.json + metrics.json (production)
- models/xgb_dengue_classifier_v1.pkl (cũ, không có sample_weight — giữ để so sánh)
- models/xgb_dengue_classifier_v2.pkl + features.json + metrics.json (production)

Best result hiện tại:
- Flu regression: LightGBM tuned, R² = 0.9019, RMSE = 0.587 (log scale)
- Dengue regression: RandomForest tuned, R² = 0.9366, RMSE = 0.739 (log scale)
- Flu classification: XGBClassifier v2, macro-F1 = 0.5437, High recall = 0.81
- Dengue classification: XGBClassifier v2, macro-F1 = 0.4885, High recall = 0.17 (limitation do data nhỏ)

Vấn đề còn lại / bước tiếp theo:
- SESSION 7: Validation độc lập 2022 cần chạy lại với classifier v2
- Dengue High recall thấp: ghi nhận là limitation trong báo cáo (geographic concentration + small dataset)
- Update baseline endemic channel rolling 5-year cho production
---\
"""

nb['cells'][112]['source'] = new_cell112
nb['cells'][112]['outputs'] = []
nb['cells'][113]['source'] = new_cell113

with open(NB_PATH, 'w', encoding='utf-8') as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print('Done - Cell 112 va Cell 113 da cap nhat')
print(f'Cell 112 type: {type(nb["cells"][112]["source"])}')
print(f'Cell 113 type: {type(nb["cells"][113]["source"])}')
# Verify key lines
src112 = nb['cells'][112]['source']
for kw in ['sample_weight', 'v2', 'xgb_flu_classifier_v2', 'xgb_dengue_classifier_v2']:
    found = kw in src112
    status = 'OK' if found else 'MISSING'
    print(f'  [{status}] {kw}')
