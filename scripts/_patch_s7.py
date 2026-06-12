"""Patch notebook v7: fix SESSION 7 cells to use v2 models + trend features."""
import sys, io, json
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

NB = Path('notebooks/KLTN_EpiWeather_ML_v7.ipynb')
nb = json.loads(NB.read_text(encoding='utf-8'))
cells = nb['cells']

# ===== CELL 118 (7.0): load v2 models + inline helper functions =====
NEW_C118 = [
    "# [7.0] Reload models + ERA5 2022 + raw data\n",
    "import joblib, warnings, itertools\n",
    "import json as json_lib\n",
    "import numpy as np\n",
    "import pandas as pd\n",
    "from sklearn.preprocessing import LabelEncoder\n",
    "warnings.filterwarnings('ignore')\n",
    "\n",
    "# Helper functions (inline — khong can chay cell 5.1 truoc)\n",
    "def add_lag_features(df, col, lags, group='iso3'):\n",
    "    d = df.copy()\n",
    "    for lag in lags:\n",
    "        d[f'{col}_lag{lag}'] = d.groupby(group)[col].shift(lag)\n",
    "    return d\n",
    "\n",
    "def add_rolling_features(df, col, windows, group='iso3'):\n",
    "    d = df.copy()\n",
    "    for w in windows:\n",
    "        d[f'{col}_rollmean{w}'] = d.groupby(group)[col].transform(lambda x: x.shift(1).rolling(w).mean())\n",
    "    return d\n",
    "\n",
    "def add_cyclic_week(df, col='iso_week', period=52):\n",
    "    d = df.copy()\n",
    "    d[f'{col}_sin'] = np.sin(2 * np.pi * d[col] / period)\n",
    "    d[f'{col}_cos'] = np.cos(2 * np.pi * d[col] / period)\n",
    "    return d\n",
    "\n",
    "def add_trend_features_flu(df, col='flu_log'):\n",
    "    d = df.copy()\n",
    "    d[f'{col}_velocity'] = d[f'{col}_lag1'] - d[f'{col}_lag2']\n",
    "    d[f'{col}_accel']    = (d[f'{col}_lag1'] - d[f'{col}_lag2']) - (d[f'{col}_lag2'] - d[f'{col}_lag3'])\n",
    "    return d\n",
    "\n",
    "def add_trend_features_dengue(df, col='deng_log'):\n",
    "    d = df.copy()\n",
    "    d[f'{col}_velocity'] = d[f'{col}_lag6']  - d[f'{col}_lag8']\n",
    "    d[f'{col}_accel']    = (d[f'{col}_lag6'] - d[f'{col}_lag8']) - (d[f'{col}_lag8'] - d[f'{col}_lag10'])\n",
    "    return d\n",
    "\n",
    "print('[OK] Helper functions defined')\n",
    "\n",
    "# Load models v2 / classifier v3\n",
    "flu_reg_v2  = joblib.load(MODELS_DIR / 'lgbm_flu_regressor_v2.pkl')\n",
    "deng_reg_v2 = joblib.load(MODELS_DIR / 'rf_dengue_regressor_v2.pkl')\n",
    "flu_clf_v2  = joblib.load(MODELS_DIR / 'xgb_flu_classifier_v3.pkl')\n",
    "deng_clf_v2 = joblib.load(MODELS_DIR / 'xgb_dengue_classifier_v3.pkl')\n",
    "print('[OK] 4 models loaded (regressor v2, classifier v3)')\n",
    "\n",
    "# Load feature lists\n",
    "with open(MODELS_DIR / 'lgbm_flu_regressor_v2_features.json') as f:\n",
    "    FEATURE_COLS_FLU = json_lib.load(f)['features']\n",
    "with open(MODELS_DIR / 'rf_dengue_regressor_v2_features.json') as f:\n",
    "    FEATURE_COLS_DENGUE = json_lib.load(f)['features']\n",
    "print(f'[OK] FEATURE_COLS_FLU    ({len(FEATURE_COLS_FLU)} cols)')\n",
    "print(f'[OK] FEATURE_COLS_DENGUE ({len(FEATURE_COLS_DENGUE)} cols)')\n",
    "\n",
    "# Load ERA5 2022\n",
    "ERA5_2022_FILE = WEATHER_DIR / 'processed/era5_weekly_2022_final.csv'\n",
    "era5_2022 = pd.read_csv(ERA5_2022_FILE)\n",
    "print(f'[OK] ERA5 2022: {era5_2022.shape}')\n",
    "\n",
    "# Load flu raw 2022\n",
    "flu_raw = pd.read_csv(RAW / 'VIW_FNT.csv', low_memory=False)\n",
    "flu_raw['influenza_total'] = flu_raw['INF_A'].fillna(0) + flu_raw['INF_B'].fillna(0)\n",
    "flu_filt = flu_raw[flu_raw['ISO_YEAR'] == 2022].copy()\n",
    "print(f'[OK] Flu 2022 raw: {flu_filt.shape}')\n",
    "\n",
    "# Load dengue raw 2022\n",
    "dengue_raw = pd.read_csv(RAW / 'National_extract_V1_3.csv', low_memory=False)\n",
    "dengue_w = dengue_raw[\n",
    "    (dengue_raw['T_res'] == 'Week') &\n",
    "    (dengue_raw['Year'] == 2022)\n",
    "].copy()\n",
    "print(f'[OK] Dengue 2022 raw: {dengue_w.shape}')\n",
    "\n",
    "# LabelEncoder\n",
    "CLASS_LABELS = ['Low', 'Medium', 'High']\n",
    "le = LabelEncoder().fit(CLASS_LABELS)\n",
    "print('[OK] LabelEncoder ready')\n",
]
cells[118]['source'] = NEW_C118
print('[OK] Cell 118 patched')

# ===== CELL 122 (7.1): them add_trend_features_flu sau add_cyclic_week =====
src122 = ''.join(cells[122]['source'])
OLD = "flu_2022 = pd.get_dummies(flu_2022, columns=['HEMISPHERE'], prefix='HEMISPHERE')"
NEW = "flu_2022 = add_trend_features_flu(flu_2022, 'flu_log')\nflu_2022 = pd.get_dummies(flu_2022, columns=['HEMISPHERE'], prefix='HEMISPHERE')"
src122 = src122.replace(OLD, NEW)
cells[122]['source'] = src122
print('[OK] Cell 122 patched — add_trend_features_flu added')

# ===== CELL 124 (7.2): them add_trend_features_dengue truoc add_cyclic_week =====
src124 = ''.join(cells[124]['source'])
OLD124 = "grid_2022 = add_cyclic_week(grid_2022)"
NEW124 = "grid_2022 = add_trend_features_dengue(grid_2022, 'deng_log')\ngrid_2022 = add_cyclic_week(grid_2022)"
src124 = src124.replace(OLD124, NEW124)
cells[124]['source'] = src124
print('[OK] Cell 124 patched — add_trend_features_dengue added')

# ===== CELL 126 (7.3): doi v1 -> v2 references =====
src126 = ''.join(cells[126]['source'])
src126 = src126.replace('flu_reg_v1.predict', 'flu_reg_v2.predict')
src126 = src126.replace('deng_reg_v1.predict', 'deng_reg_v2.predict')
src126 = src126.replace('LightGBM tuned v1', 'LightGBM tuned v2')
src126 = src126.replace('RandomForest tuned v1', 'RandomForest tuned v2')
src126 = src126.replace('CV R² : 0.9019', 'CV R2 : 0.9017')
src126 = src126.replace('CV R² : 0.9366', 'CV R2 : 0.9380')
cells[126]['source'] = src126
print('[OK] Cell 126 patched')

# ===== CELL 128 (7.4): doi v1 -> v2/v3 references =====
src128 = ''.join(cells[128]['source'])
src128 = src128.replace('flu_clf_v1.predict(', 'flu_clf_v2.predict(')
src128 = src128.replace('flu_clf_v1.predict_proba(', 'flu_clf_v2.predict_proba(')
src128 = src128.replace('deng_clf_v1.predict(', 'deng_clf_v2.predict(')
src128 = src128.replace('deng_clf_v1.predict_proba(', 'deng_clf_v2.predict_proba(')
src128 = src128.replace('XGBClassifier v1', 'XGBClassifier v3')
src128 = src128.replace('XGBClassifier v2', 'XGBClassifier v3')
cells[128]['source'] = src128
print('[OK] Cell 128 patched')

# ===== Save =====
NB.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding='utf-8')
print('\nNotebook saved OK.')

# ===== Verify =====
nb2 = json.loads(NB.read_text(encoding='utf-8'))
c = nb2['cells']
checks = [
    ('Cell118 add_lag_features defined', 'def add_lag_features' in ''.join(c[118]['source'])),
    ('Cell118 flu_reg_v2 loaded',        'flu_reg_v2' in ''.join(c[118]['source'])),
    ('Cell118 lgbm_flu_regressor_v2',    'lgbm_flu_regressor_v2' in ''.join(c[118]['source'])),
    ('Cell122 trend flu',                'add_trend_features_flu' in ''.join(c[122]['source'])),
    ('Cell124 trend dengue',             'add_trend_features_dengue' in ''.join(c[124]['source'])),
    ('Cell126 flu_reg_v2.predict',       'flu_reg_v2.predict' in ''.join(c[126]['source'])),
    ('Cell128 flu_clf_v2.predict',       'flu_clf_v2.predict' in ''.join(c[128]['source'])),
]
print()
all_ok = True
for label, ok in checks:
    status = 'OK' if ok else 'FAIL'
    print(f'  [{status}] {label}')
    if not ok:
        all_ok = False
print()
print('ALL CHECKS PASSED' if all_ok else 'SOME CHECKS FAILED')
