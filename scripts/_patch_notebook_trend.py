"""Patch notebook: thêm velocity + acceleration trend features vào SESSION 5 và 6."""
import json

NB_PATH = r'f:\BAO_CAO\DO_AN_TOT_NGHIEP\KLTN\KLTN_EpiWeather_ML_v6.ipynb'
with open(NB_PATH, encoding='utf-8') as f:
    nb = json.load(f)
cells = nb['cells']


# ── Cell 78: thêm 2 helper functions ─────────────────────────────────────────
old78 = ''.join(cells[78]['source'])
trend_helpers = '''

def add_trend_features_flu(df, col='flu_log', group_col='iso3'):
    """
    Velocity và acceleration từ log-scale lags (lag1, lag2, lag3).
    velocity = lag1 - lag2: log-ratio xap xi tuần-over-tuần growth rate.
    accel    = velocity_t - velocity_(t-1): toc do thay doi cua growth rate.
    Tinh AFTER add_lag_features da co lag1/lag2/lag3.
    """
    df = df.copy()
    df[f'{col}_velocity'] = df[f'{col}_lag1'] - df[f'{col}_lag2']
    df[f'{col}_accel']    = (df[f'{col}_lag1'] - df[f'{col}_lag2']) - (df[f'{col}_lag2'] - df[f'{col}_lag3'])
    return df


def add_trend_features_dengue(df, col='deng_log', group_col='iso3'):
    """
    Velocity va acceleration cho dengue (lags 6, 8, 10 tuan).
    velocity = lag6 - lag8: 2-tuan growth rate.
    accel    = (lag6 - lag8) - (lag8 - lag10).
    """
    df = df.copy()
    df[f'{col}_velocity'] = df[f'{col}_lag6']  - df[f'{col}_lag8']
    df[f'{col}_accel']    = (df[f'{col}_lag6'] - df[f'{col}_lag8']) - (df[f'{col}_lag8'] - df[f'{col}_lag10'])
    return df'''
cells[78]['source'] = old78 + trend_helpers
print('[OK] Cell 78 -- add_trend_features_flu / add_trend_features_dengue')


# ── Cell 80: flu trend features + FEATURE_COLS_FLU update ────────────────────
src80 = ''.join(cells[80]['source'])
src80 = src80.replace(
    "flu = pd.get_dummies(flu, columns=['HEMISPHERE'], prefix='HEMISPHERE')",
    "flu = pd.get_dummies(flu, columns=['HEMISPHERE'], prefix='HEMISPHERE')\nflu = add_trend_features_flu(flu, 'flu_log')"
)
src80 = src80.replace(
    "    'flu_log_rollmean4', 'flu_log_rollmean8',",
    "    'flu_log_rollmean4', 'flu_log_rollmean8',\n    'flu_log_velocity', 'flu_log_accel',   # trend features v2"
)
cells[80]['source'] = src80
print('[OK] Cell 80 -- flu trend features')


# ── Cell 82: dengue trend features + FEATURE_COLS_DENGUE update ──────────────
src82 = ''.join(cells[82]['source'])
src82 = src82.replace(
    'grid = add_cyclic_week(grid)',
    "grid = add_cyclic_week(grid)\ngrid = add_trend_features_dengue(grid, 'deng_log')"
)
src82 = src82.replace(
    "    'deng_log_rollmean4', 'deng_log_rollmean8',",
    "    'deng_log_rollmean4', 'deng_log_rollmean8',\n    'deng_log_velocity', 'deng_log_accel',   # trend features v2"
)
cells[82]['source'] = src82
print('[OK] Cell 82 -- dengue trend features')


# ── Cell 86: save v2 files ────────────────────────────────────────────────────
src86 = ''.join(cells[86]['source'])
src86 = src86.replace('features_flu_v1.csv', 'features_flu_v2.csv')
src86 = src86.replace('features_dengue_v1.csv', 'features_dengue_v2.csv')
cells[86]['source'] = src86
print('[OK] Cell 86 -- save paths -> v2')


# ── Cell 90: reload v2 files ──────────────────────────────────────────────────
src90 = ''.join(cells[90]['source'])
src90 = src90.replace('features_flu_v1.csv', 'features_flu_v2.csv')
src90 = src90.replace('features_dengue_v1.csv', 'features_dengue_v2.csv')
cells[90]['source'] = src90
print('[OK] Cell 90 -- reload paths -> v2')


# ── Cell 112: regressors v1->v2, classifiers v2->v3 ──────────────────────────
src112 = ''.join(cells[112]['source'])

# Flu regressor v1 -> v2
src112 = src112.replace("'lgbm_flu_regressor_v1.pkl'", "'lgbm_flu_regressor_v2.pkl'")
src112 = src112.replace("'lgbm_flu_regressor_v1_features.json'", "'lgbm_flu_regressor_v2_features.json'")
src112 = src112.replace("'lgbm_flu_regressor_v1_metrics.json'", "'lgbm_flu_regressor_v2_metrics.json'")

# Dengue regressor v1 -> v2
src112 = src112.replace("'rf_dengue_regressor_v1.pkl'", "'rf_dengue_regressor_v2.pkl'")
src112 = src112.replace("'rf_dengue_regressor_v1_features.json'", "'rf_dengue_regressor_v2_features.json'")
src112 = src112.replace("'rf_dengue_regressor_v1_metrics.json'", "'rf_dengue_regressor_v2_metrics.json'")

# Flu classifier v2 -> v3
src112 = src112.replace("'xgb_flu_classifier_v2.pkl'", "'xgb_flu_classifier_v3.pkl'")
src112 = src112.replace("'xgb_flu_classifier_v2_features.json'", "'xgb_flu_classifier_v3_features.json'")
src112 = src112.replace("'xgb_flu_classifier_v2_metrics.json'", "'xgb_flu_classifier_v3_metrics.json'")

# Dengue classifier v2 -> v3
src112 = src112.replace("'xgb_dengue_classifier_v2.pkl'", "'xgb_dengue_classifier_v3.pkl'")
src112 = src112.replace("'xgb_dengue_classifier_v2_features.json'", "'xgb_dengue_classifier_v3_features.json'")
src112 = src112.replace("'xgb_dengue_classifier_v2_metrics.json'", "'xgb_dengue_classifier_v3_metrics.json'")

# Update version + date + note strings
src112 = src112.replace(
    "'version': 'v1', 'date': '2026-05-16',\n               'model_type': 'LightGBM', 'tuned': True,",
    "'version': 'v2', 'date': '2026-06-06',\n               'model_type': 'LightGBM', 'tuned': True,\n               'note': 'Added flu_log_velocity + flu_log_accel trend features',"
)
src112 = src112.replace(
    "'version': 'v1', 'date': '2026-05-16',\n               'model_type': 'RandomForest', 'tuned': True,",
    "'version': 'v2', 'date': '2026-06-06',\n               'model_type': 'RandomForest', 'tuned': True,\n               'note': 'Added deng_log_velocity + deng_log_accel trend features',"
)
src112 = src112.replace(
    "'version': 'v2', 'date': '2026-06-02',\n               'model_type': 'XGBClassifier',\n               'note': 'Added sample_weight balanced — High recall 0.60->0.81'",
    "'version': 'v3', 'date': '2026-06-06',\n               'model_type': 'XGBClassifier',\n               'note': 'velocity+accel features + sample_weight balanced'"
)
src112 = src112.replace(
    "'version': 'v2', 'date': '2026-06-02',\n               'model_type': 'XGBClassifier',\n               'note': 'Added sample_weight balanced — High recall 0.14->0.17, limited by small dataset'",
    "'version': 'v3', 'date': '2026-06-06',\n               'model_type': 'XGBClassifier',\n               'note': 'velocity+accel features + sample_weight balanced'"
)
cells[112]['source'] = src112
print('[OK] Cell 112 -- regressor v1->v2, classifier v2->v3')


# ── Save ──────────────────────────────────────────────────────────────────────
with open(NB_PATH, 'w', encoding='utf-8') as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)
print('\nNotebook saved OK.')

# Verify
with open(NB_PATH, encoding='utf-8') as f:
    nb2 = json.load(f)
c78  = ''.join(nb2['cells'][78]['source'])
c80  = ''.join(nb2['cells'][80]['source'])
c82  = ''.join(nb2['cells'][82]['source'])
c86  = ''.join(nb2['cells'][86]['source'])
c90  = ''.join(nb2['cells'][90]['source'])
c112 = ''.join(nb2['cells'][112]['source'])

checks = [
    ('Cell78 velocity func',  'add_trend_features_flu' in c78),
    ('Cell78 accel func',     'add_trend_features_dengue' in c78),
    ('Cell80 call trend',     "add_trend_features_flu(flu, 'flu_log')" in c80),
    ('Cell80 velocity feat',  'flu_log_velocity' in c80),
    ('Cell80 accel feat',     'flu_log_accel' in c80),
    ('Cell82 call trend',     "add_trend_features_dengue(grid, 'deng_log')" in c82),
    ('Cell82 velocity feat',  'deng_log_velocity' in c82),
    ('Cell82 accel feat',     'deng_log_accel' in c82),
    ('Cell86 v2 flu',         'features_flu_v2.csv' in c86),
    ('Cell86 v2 dengue',      'features_dengue_v2.csv' in c86),
    ('Cell90 v2 flu',         'features_flu_v2.csv' in c90),
    ('Cell90 v2 dengue',      'features_dengue_v2.csv' in c90),
    ('Cell112 regressor v2',  'lgbm_flu_regressor_v2.pkl' in c112),
    ('Cell112 dengue reg v2', 'rf_dengue_regressor_v2.pkl' in c112),
    ('Cell112 clf v3',        'xgb_flu_classifier_v3.pkl' in c112),
]
print('\nVerification:')
all_ok = True
for label, ok in checks:
    status = 'OK' if ok else 'FAIL'
    print(f'  [{status}] {label}')
    if not ok:
        all_ok = False
print(f'\n{"ALL CHECKS PASSED" if all_ok else "SOME CHECKS FAILED"}')
