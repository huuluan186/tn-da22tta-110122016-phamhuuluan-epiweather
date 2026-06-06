"""
Revert v6 ve nguyen ban, tao v7 = v6 + trend feature improvements.
"""
import json, shutil, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from pathlib import Path

NB_V6 = Path(r'f:\BAO_CAO\DO_AN_TOT_NGHIEP\KLTN\KLTN_EpiWeather_ML_v6.ipynb')
NB_V7 = Path(r'f:\BAO_CAO\DO_AN_TOT_NGHIEP\KLTN\KLTN_EpiWeather_ML_v7.ipynb')

# ── Bước 1: Revert v6 về nguyên bản ──────────────────────────────────────────
with open(NB_V6, encoding='utf-8') as f:
    nb = json.load(f)
cells = nb['cells']

# Cell 78 — xóa 2 hàm trend feature đã thêm
src78 = ''.join(cells[78]['source'])
cutoff = src78.find('\n\ndef add_trend_features_flu(')
if cutoff != -1:
    cells[78]['source'] = src78[:cutoff]
    print('[REVERT] Cell 78 — xóa trend helper functions')
else:
    print('[SKIP]   Cell 78 — không tìm thấy trend functions, bỏ qua')

# Cell 80 — xóa call + velocity/accel trong FEATURE_COLS_FLU
src80 = ''.join(cells[80]['source'])
src80 = src80.replace(
    "\nflu = add_trend_features_flu(flu, 'flu_log')", ""
).replace(
    "\n    'flu_log_velocity', 'flu_log_accel',   # trend features v2", ""
)
cells[80]['source'] = src80
print('[REVERT] Cell 80 — flu trend features')

# Cell 82 — xóa call + velocity/accel trong FEATURE_COLS_DENGUE
src82 = ''.join(cells[82]['source'])
src82 = src82.replace(
    "\ngrid = add_trend_features_dengue(grid, 'deng_log')", ""
).replace(
    "\n    'deng_log_velocity', 'deng_log_accel',   # trend features v2", ""
)
cells[82]['source'] = src82
print('[REVERT] Cell 82 — dengue trend features')

# Cell 86 — v2 -> v1
src86 = ''.join(cells[86]['source'])
src86 = src86.replace('features_flu_v2.csv', 'features_flu_v1.csv')
src86 = src86.replace('features_dengue_v2.csv', 'features_dengue_v1.csv')
cells[86]['source'] = src86
print('[REVERT] Cell 86 — save paths v2->v1')

# Cell 90 — v2 -> v1
src90 = ''.join(cells[90]['source'])
src90 = src90.replace('features_flu_v2.csv', 'features_flu_v1.csv')
src90 = src90.replace('features_dengue_v2.csv', 'features_dengue_v1.csv')
cells[90]['source'] = src90
print('[REVERT] Cell 90 — reload paths v2->v1')

# Cell 112 — regressor v2->v1, classifier v3->v2
src112 = ''.join(cells[112]['source'])
src112 = src112.replace("'lgbm_flu_regressor_v2.pkl'",    "'lgbm_flu_regressor_v1.pkl'")
src112 = src112.replace("'lgbm_flu_regressor_v2_features.json'", "'lgbm_flu_regressor_v1_features.json'")
src112 = src112.replace("'lgbm_flu_regressor_v2_metrics.json'",  "'lgbm_flu_regressor_v1_metrics.json'")
src112 = src112.replace("'rf_dengue_regressor_v2.pkl'",   "'rf_dengue_regressor_v1.pkl'")
src112 = src112.replace("'rf_dengue_regressor_v2_features.json'","'rf_dengue_regressor_v1_features.json'")
src112 = src112.replace("'rf_dengue_regressor_v2_metrics.json'", "'rf_dengue_regressor_v1_metrics.json'")
src112 = src112.replace("'xgb_flu_classifier_v3.pkl'",    "'xgb_flu_classifier_v2.pkl'")
src112 = src112.replace("'xgb_flu_classifier_v3_features.json'", "'xgb_flu_classifier_v2_features.json'")
src112 = src112.replace("'xgb_flu_classifier_v3_metrics.json'",  "'xgb_flu_classifier_v2_metrics.json'")
src112 = src112.replace("'xgb_dengue_classifier_v3.pkl'", "'xgb_dengue_classifier_v2.pkl'")
src112 = src112.replace("'xgb_dengue_classifier_v3_features.json'","'xgb_dengue_classifier_v2_features.json'")
src112 = src112.replace("'xgb_dengue_classifier_v3_metrics.json'", "'xgb_dengue_classifier_v2_metrics.json'")

# revert version/date/note strings
src112 = src112.replace(
    "'version': 'v2', 'date': '2026-06-06',\n               'model_type': 'LightGBM', 'tuned': True,\n               'note': 'Added flu_log_velocity + flu_log_accel trend features',",
    "'version': 'v1', 'date': '2026-05-16',\n               'model_type': 'LightGBM', 'tuned': True,"
)
src112 = src112.replace(
    "'version': 'v2', 'date': '2026-06-06',\n               'model_type': 'RandomForest', 'tuned': True,\n               'note': 'Added deng_log_velocity + deng_log_accel trend features',",
    "'version': 'v1', 'date': '2026-05-16',\n               'model_type': 'RandomForest', 'tuned': True,"
)
src112 = src112.replace(
    "'version': 'v3', 'date': '2026-06-06',\n               'model_type': 'XGBClassifier',\n               'note': 'velocity+accel features + sample_weight balanced'",
    "'version': 'v2', 'date': '2026-06-02',\n               'model_type': 'XGBClassifier',\n               'note': 'Added sample_weight balanced — High recall 0.60->0.81'"
)
cells[112]['source'] = src112
print('[REVERT] Cell 112 — regressor v2->v1, classifier v3->v2')

with open(NB_V6, 'w', encoding='utf-8') as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)
print('\n[OK] v6 reverted và saved.\n')

# Verify v6 sạch
with open(NB_V6, encoding='utf-8') as f:
    nb6 = json.load(f)
checks_v6 = [
    ('v6 Cell78 no velocity func', 'add_trend_features_flu' not in ''.join(nb6['cells'][78]['source'])),
    ('v6 Cell80 no velocity feat', 'flu_log_velocity'       not in ''.join(nb6['cells'][80]['source'])),
    ('v6 Cell82 no velocity feat', 'deng_log_velocity'      not in ''.join(nb6['cells'][82]['source'])),
    ('v6 Cell86 uses v1 csv',      'features_flu_v1.csv'    in     ''.join(nb6['cells'][86]['source'])),
    ('v6 Cell90 uses v1 csv',      'features_flu_v1.csv'    in     ''.join(nb6['cells'][90]['source'])),
    ('v6 Cell112 regressor v1',    'lgbm_flu_regressor_v1.pkl' in  ''.join(nb6['cells'][112]['source'])),
]
all_ok = True
for label, ok in checks_v6:
    print(f'  {"[OK]" if ok else "[FAIL]"} {label}')
    if not ok: all_ok = False
if not all_ok:
    print('\nERROR: v6 revert incomplete — dừng lại')
    exit(1)

# ── Bước 2: Copy v6 -> v7 rồi apply patches ───────────────────────────────────
print()
shutil.copy2(NB_V6, NB_V7)
print(f'[OK] Copied v6 -> v7 ({NB_V7.stat().st_size/1e6:.1f}MB)')

with open(NB_V7, encoding='utf-8') as f:
    nb7 = json.load(f)
cells7 = nb7['cells']

# ── Patch Cell 78: thêm 2 helper functions ────────────────────────────────────
trend_helpers = '''

def add_trend_features_flu(df, col='flu_log', group_col='iso3'):
    """
    Velocity va acceleration tu log-scale lags (lag1, lag2, lag3).
    velocity = lag1 - lag2: log-ratio xap xi tuan-over-tuan growth rate.
    accel    = velocity_t - velocity_(t-1): toc do thay doi cua growth rate.
    Ly thuyet: tuong duong log(Rt) trong mo hinh lan truyen dich.
    Phai tinh AFTER add_lag_features da co lag1/lag2/lag3.
    """
    df = df.copy()
    df[f'{col}_velocity'] = df[f'{col}_lag1'] - df[f'{col}_lag2']
    df[f'{col}_accel']    = (df[f'{col}_lag1'] - df[f'{col}_lag2']) - (df[f'{col}_lag2'] - df[f'{col}_lag3'])
    return df


def add_trend_features_dengue(df, col='deng_log', group_col='iso3'):
    """
    Velocity va acceleration cho dengue (lags 6, 8, 10 tuan).
    Dengue dung longer lags do chu ky vector mosquito dai hon flu.
    velocity = lag6 - lag8: 2-tuan growth rate tai cua so 6-8 tuan.
    accel    = (lag6 - lag8) - (lag8 - lag10).
    """
    df = df.copy()
    df[f'{col}_velocity'] = df[f'{col}_lag6']  - df[f'{col}_lag8']
    df[f'{col}_accel']    = (df[f'{col}_lag6'] - df[f'{col}_lag8']) - (df[f'{col}_lag8'] - df[f'{col}_lag10'])
    return df'''

cells7[78]['source'] = ''.join(cells7[78]['source']) + trend_helpers
print('[PATCH v7] Cell 78 — thêm add_trend_features_flu/dengue')

# ── Patch Cell 80: flu velocity/accel ─────────────────────────────────────────
src80 = ''.join(cells7[80]['source'])
src80 = src80.replace(
    "flu = pd.get_dummies(flu, columns=['HEMISPHERE'], prefix='HEMISPHERE')",
    "flu = pd.get_dummies(flu, columns=['HEMISPHERE'], prefix='HEMISPHERE')\nflu = add_trend_features_flu(flu, 'flu_log')"
)
src80 = src80.replace(
    "    'flu_log_rollmean4', 'flu_log_rollmean8',",
    "    'flu_log_rollmean4', 'flu_log_rollmean8',\n    'flu_log_velocity', 'flu_log_accel',   # v2: trend — log growth rate + acceleration"
)
cells7[80]['source'] = src80
print('[PATCH v7] Cell 80 — flu trend features')

# ── Patch Cell 82: dengue velocity/accel ──────────────────────────────────────
src82 = ''.join(cells7[82]['source'])
src82 = src82.replace(
    'grid = add_cyclic_week(grid)',
    "grid = add_cyclic_week(grid)\ngrid = add_trend_features_dengue(grid, 'deng_log')"
)
src82 = src82.replace(
    "    'deng_log_rollmean4', 'deng_log_rollmean8',",
    "    'deng_log_rollmean4', 'deng_log_rollmean8',\n    'deng_log_velocity', 'deng_log_accel',   # v2: trend — log growth rate + acceleration"
)
cells7[82]['source'] = src82
print('[PATCH v7] Cell 82 — dengue trend features')

# ── Patch Cell 86: save v2 files ──────────────────────────────────────────────
src86 = ''.join(cells7[86]['source'])
src86 = src86.replace('features_flu_v1.csv', 'features_flu_v2.csv')
src86 = src86.replace('features_dengue_v1.csv', 'features_dengue_v2.csv')
cells7[86]['source'] = src86
print('[PATCH v7] Cell 86 — save v2 CSVs')

# ── Patch Cell 90: reload v2 files ────────────────────────────────────────────
src90 = ''.join(cells7[90]['source'])
src90 = src90.replace('features_flu_v1.csv', 'features_flu_v2.csv')
src90 = src90.replace('features_dengue_v1.csv', 'features_dengue_v2.csv')
cells7[90]['source'] = src90
print('[PATCH v7] Cell 90 — reload v2 CSVs')

# ── Patch Cell 112: version bump ──────────────────────────────────────────────
src112 = ''.join(cells7[112]['source'])
src112 = src112.replace("'lgbm_flu_regressor_v1.pkl'",    "'lgbm_flu_regressor_v2.pkl'")
src112 = src112.replace("'lgbm_flu_regressor_v1_features.json'", "'lgbm_flu_regressor_v2_features.json'")
src112 = src112.replace("'lgbm_flu_regressor_v1_metrics.json'",  "'lgbm_flu_regressor_v2_metrics.json'")
src112 = src112.replace("'rf_dengue_regressor_v1.pkl'",   "'rf_dengue_regressor_v2.pkl'")
src112 = src112.replace("'rf_dengue_regressor_v1_features.json'","'rf_dengue_regressor_v2_features.json'")
src112 = src112.replace("'rf_dengue_regressor_v1_metrics.json'", "'rf_dengue_regressor_v2_metrics.json'")
src112 = src112.replace("'xgb_flu_classifier_v2.pkl'",    "'xgb_flu_classifier_v3.pkl'")
src112 = src112.replace("'xgb_flu_classifier_v2_features.json'", "'xgb_flu_classifier_v3_features.json'")
src112 = src112.replace("'xgb_flu_classifier_v2_metrics.json'",  "'xgb_flu_classifier_v3_metrics.json'")
src112 = src112.replace("'xgb_dengue_classifier_v2.pkl'", "'xgb_dengue_classifier_v3.pkl'")
src112 = src112.replace("'xgb_dengue_classifier_v2_features.json'","'xgb_dengue_classifier_v3_features.json'")
src112 = src112.replace("'xgb_dengue_classifier_v2_metrics.json'", "'xgb_dengue_classifier_v3_metrics.json'")
src112 = src112.replace(
    "'version': 'v1', 'date': '2026-05-16',\n               'model_type': 'LightGBM', 'tuned': True,",
    "'version': 'v2', 'date': '2026-06-06',\n               'model_type': 'LightGBM', 'tuned': True,\n               'note': 'Added flu_log_velocity + flu_log_accel (trend features)',"
)
src112 = src112.replace(
    "'version': 'v1', 'date': '2026-05-16',\n               'model_type': 'RandomForest', 'tuned': True,",
    "'version': 'v2', 'date': '2026-06-06',\n               'model_type': 'RandomForest', 'tuned': True,\n               'note': 'Added deng_log_velocity + deng_log_accel (trend features)',"
)
src112 = src112.replace(
    "'version': 'v2', 'date': '2026-06-02',\n               'model_type': 'XGBClassifier',\n               'note': 'Added sample_weight balanced — High recall 0.60->0.81'",
    "'version': 'v3', 'date': '2026-06-06',\n               'model_type': 'XGBClassifier',\n               'note': 'velocity+accel trend features + sample_weight balanced'"
)
src112 = src112.replace(
    "'version': 'v2', 'date': '2026-06-02',\n               'model_type': 'XGBClassifier',\n               'note': 'Added sample_weight balanced — High recall 0.14->0.17, limited by small dataset'",
    "'version': 'v3', 'date': '2026-06-06',\n               'model_type': 'XGBClassifier',\n               'note': 'velocity+accel trend features + sample_weight balanced'"
)
cells7[112]['source'] = src112
print('[PATCH v7] Cell 112 — regressor v1->v2, classifier v2->v3')

# ── Lưu v7 ───────────────────────────────────────────────────────────────────
with open(NB_V7, 'w', encoding='utf-8') as f:
    json.dump(nb7, f, ensure_ascii=False, indent=1)
print(f'\n[OK] v7 saved: {NB_V7.name} ({NB_V7.stat().st_size/1e6:.1f}MB)')

# ── Verify v7 ─────────────────────────────────────────────────────────────────
with open(NB_V7, encoding='utf-8') as f:
    nb7v = json.load(f)
checks_v7 = [
    ('v7 Cell78 has velocity func',  'add_trend_features_flu'             in ''.join(nb7v['cells'][78]['source'])),
    ('v7 Cell80 flu_log_velocity',   'flu_log_velocity'                   in ''.join(nb7v['cells'][80]['source'])),
    ('v7 Cell80 flu_log_accel',      'flu_log_accel'                      in ''.join(nb7v['cells'][80]['source'])),
    ('v7 Cell82 deng_log_velocity',  'deng_log_velocity'                  in ''.join(nb7v['cells'][82]['source'])),
    ('v7 Cell82 deng_log_accel',     'deng_log_accel'                     in ''.join(nb7v['cells'][82]['source'])),
    ('v7 Cell86 v2 flu csv',         'features_flu_v2.csv'                in ''.join(nb7v['cells'][86]['source'])),
    ('v7 Cell86 v2 dengue csv',      'features_dengue_v2.csv'             in ''.join(nb7v['cells'][86]['source'])),
    ('v7 Cell90 v2 flu csv',         'features_flu_v2.csv'                in ''.join(nb7v['cells'][90]['source'])),
    ('v7 Cell112 regressor v2',      'lgbm_flu_regressor_v2.pkl'          in ''.join(nb7v['cells'][112]['source'])),
    ('v7 Cell112 classifier v3',     'xgb_flu_classifier_v3.pkl'          in ''.join(nb7v['cells'][112]['source'])),
]
print('\nVerify v7:')
all_ok = True
for label, ok in checks_v7:
    print(f'  {"[OK]" if ok else "[FAIL]"} {label}')
    if not ok: all_ok = False

print(f'\n{"ALL CHECKS PASSED" if all_ok else "SOME CHECKS FAILED"}')
print(f'\nTong cells v7: {len(nb7v["cells"])} (bang v6: {len(nb["cells"])})')
