"""
Patch lon: sua bug LabelEncoder (High=0 alphabetical) + them thi nghiem 3 tang
xu ly imbalanced (Algorithm -> Resampling -> Threshold).

Thay LabelEncoder bang RISK_MAP tuong minh: Low=0, Medium=1, High=2 (ordinal).
Sau fix: proba[0]=P(Low), proba[1]=P(Medium), proba[2]=P(High) -> dung voi ml_engine.
Classifier bump v3 -> v4.
"""
import sys, io, json
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

NB = Path('notebooks/KLTN_EpiWeather_ML_v7.ipynb')
nb = json.loads(NB.read_text(encoding='utf-8'))
cells = nb['cells']


def find_cell(substr, ctype='code'):
    for i, c in enumerate(cells):
        if c['cell_type'] == ctype and substr in ''.join(c['source']):
            return i
    raise ValueError(f'Khong tim thay cell chua: {substr}')


def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": text}


def code(text):
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": text}


# ===================================================================
# 1. CELL 6.8 (code) — rewrite: encoding fix + 3-tier experiment framework
# ===================================================================
idx_68 = find_cell('[6.8] XGBClassifier')
NEW_68 = r'''# [6.8] XGBClassifier + xu ly Imbalanced Data — thi nghiem 3 tang
# ===================================================================
# FIX BUG: truoc day dung LabelEncoder().fit(['Low','Medium','High']) -> sort alphabet
# -> High=0, Low=1, Medium=2 (SAI thu tu). Gio dung mapping tuong minh ordinal.
# ===================================================================
from xgboost import XGBClassifier
from sklearn.utils.class_weight import compute_sample_weight
from sklearn.metrics import precision_recall_fscore_support

# Mapping tuong minh — thu tu ordinal tang dan muc do nguy hiem
RISK_MAP    = {'Low': 0, 'Medium': 1, 'High': 2}
RISK_INV    = {0: 'Low', 1: 'Medium', 2: 'High'}
CLASS_LABELS = ['Low', 'Medium', 'High']   # index = gia tri encoded
# Sau fix: proba[:,0]=P(Low), proba[:,1]=P(Medium), proba[:,2]=P(High)

XGB_PARAMS = dict(n_estimators=300, max_depth=6, learning_rate=0.05,
                  subsample=0.8, colsample_bytree=0.8,
                  objective='multi:softprob', num_class=3,
                  random_state=42, n_jobs=-1, verbosity=0)


def random_oversample(X, y, seed=42):
    """Oversample cac class thieu len bang class nhieu nhat (random duplicate).
    Thay cho SMOTE — khong tao synthetic, phu hop time-series, khong leak."""
    rng = np.random.RandomState(seed)
    classes, counts = np.unique(y, return_counts=True)
    target_n = counts.max()
    parts = []
    for c in classes:
        idx = np.where(y == c)[0]
        if len(idx) < target_n:
            extra = rng.choice(idx, size=target_n - len(idx), replace=True)
            idx = np.concatenate([idx, extra])
        parts.append(idx)
    allidx = np.concatenate(parts); rng.shuffle(allidx)
    return X.iloc[allidx], y[allidx]


def fit_classifier(X_tr, y_tr, strategy='balanced', custom_weights=None):
    """Train 1 XGBClassifier theo chien luoc xu ly imbalanced.
    strategy: 'none' | 'balanced' | 'custom' | 'oversample'."""
    sw = None
    if strategy == 'balanced':
        sw = compute_sample_weight('balanced', y_tr)
    elif strategy == 'custom':
        wmap = custom_weights or {0: 1, 1: 2, 2: 4}
        sw = np.array([wmap[c] for c in y_tr], dtype=float)
    elif strategy == 'oversample':
        X_tr, y_tr = random_oversample(X_tr, y_tr)
    mdl = XGBClassifier(**XGB_PARAMS)
    mdl.fit(X_tr, y_tr, sample_weight=sw)
    return mdl


def eval_clf_strategy(df, feat_cols, target_col, folds,
                      strategy='balanced', custom_weights=None, threshold_high=None):
    """Walk-forward CV — tra ve macro_f1 + recall/precision cho High va Medium."""
    macro_f1s, hi_rec, hi_prec, med_rec, med_prec = [], [], [], [], []
    for train_years, val_year in folds:
        tr = df[df['iso_year'].isin(list(train_years))]
        vl = df[df['iso_year'] == val_year]
        if len(vl) == 0:
            continue
        X_tr, y_tr = tr[feat_cols], tr[target_col].map(RISK_MAP).values
        X_vl, y_vl = vl[feat_cols], vl[target_col].map(RISK_MAP).values
        mdl = fit_classifier(X_tr, y_tr, strategy, custom_weights)
        proba = mdl.predict_proba(X_vl)
        if threshold_high is not None:
            # P(High) >= nguong -> High; nguoc lai argmax giua Low/Medium
            y_pred = np.where(proba[:, 2] >= threshold_high, 2, np.argmax(proba[:, :2], axis=1))
        else:
            y_pred = np.argmax(proba, axis=1)
        macro_f1s.append(f1_score(y_vl, y_pred, average='macro'))
        p, r, f, _ = precision_recall_fscore_support(y_vl, y_pred, labels=[0, 1, 2], zero_division=0)
        hi_rec.append(r[2]); hi_prec.append(p[2]); med_rec.append(r[1]); med_prec.append(p[1])
    return {'macro_f1': np.mean(macro_f1s), 'high_recall': np.mean(hi_rec),
            'high_prec': np.mean(hi_prec), 'med_recall': np.mean(med_rec),
            'med_prec': np.mean(med_prec)}


# ── Phan phoi nhan (bang chung imbalanced) ────────────────────────────────────
print('=== Phan phoi nhan (class distribution) ===')
for name, df_, tcol in [('FLU', flu_feat, 'flu_risk_class'),
                        ('DENGUE', deng_feat, 'dengue_risk_class')]:
    vc = df_[tcol].value_counts()
    tot = vc.sum()
    print(f'{name}: ' + '  '.join(f'{k}={vc.get(k,0)} ({vc.get(k,0)/tot*100:.1f}%)'
                                   for k in CLASS_LABELS))

# ── Tang 1 (Algorithm) + Tang 2 (Resampling): so sanh 4 chien luoc ────────────
STRATEGIES = [
    ('none (baseline)',     dict(strategy='none')),
    ('balanced (algo)',     dict(strategy='balanced')),
    ('custom 1/2/4 (algo)', dict(strategy='custom', custom_weights={0: 1, 1: 2, 2: 4})),
    ('oversample (resamp)', dict(strategy='oversample')),
]

CLF_COMPARE = {}
for disease, df_, feats, folds, tcol in [
    ('flu',    flu_feat,  FEATURE_COLS_FLU,    FOLDS_FLU,    'flu_risk_class'),
    ('dengue', deng_feat, FEATURE_COLS_DENGUE, FOLDS_DENGUE, 'dengue_risk_class'),
]:
    rows = []
    for sname, kw in STRATEGIES:
        m = eval_clf_strategy(df_, feats, tcol, folds, **kw)
        rows.append({'strategy': sname, **{k: round(v, 4) for k, v in m.items()}})
    tbl = pd.DataFrame(rows)
    CLF_COMPARE[disease] = tbl
    print(f'\n=== {disease.upper()} — Tang 1+2 (Algorithm vs Resampling) ===')
    print(tbl.to_string(index=False))

print('\n[OK] CLF_COMPARE da luu — dung de chon chien luoc o cell 6.10')
'''
cells[idx_68]['source'] = NEW_68
print(f'[OK] Cell {idx_68} (6.8) rewritten — encoding fix + strategy comparison')

# Update markdown 6.8 title
idx_68md = find_cell('## 6.8', ctype='markdown')
cells[idx_68md]['source'] = (
    "## 6.8 — XGBClassifier + xu ly Imbalanced Data (3 tang)\n\n"
    "Branch B cua hybrid approach: classification muc do nguy hiem Low/Medium/High.\n\n"
    "**FIX BUG quan trong:** Truoc day dung `LabelEncoder().fit(['Low','Medium','High'])` "
    "nhung LabelEncoder sap xep theo alphabet -> High=0, Low=1, Medium=2 (SAI thu tu gia dinh). "
    "Gio thay bang mapping tuong minh `Low=0, Medium=1, High=2` -> `proba[2]=P(High)` dung voi backend.\n\n"
    "**Thi nghiem 3 tang xu ly imbalanced** (theo thu tu chuan: Algorithm -> Resampling -> Threshold):\n"
    "- Tang 1 (Algorithm): `sample_weight='balanced'` vs custom weight `{Low:1, Med:2, High:4}`\n"
    "- Tang 2 (Resampling): `RandomOverSampler` (thay SMOTE vi time-series)\n"
    "- Tang 3 (Threshold): sweep nguong `P(High)` (cell 6.8c)\n\n"
    "So sanh tren walk-forward CV, chon chien luoc tot nhat cho v4."
)
print(f'[OK] Cell {idx_68md} (6.8 md) updated')

# ===================================================================
# 2. INSERT cell 6.8c — threshold sweep (Tang 3) truoc 6.9
# ===================================================================
idx_69md = find_cell('## 6.9', ctype='markdown')

MD_68C = (
    "## 6.8c — Tang 3: Threshold tuning cho class High\n\n"
    "Sau khi chon chien luoc Algorithm/Resampling tot nhat, tinh chinh nguong quyet dinh.\n"
    "Mac dinh model dung `argmax(proba)` (tuong duong nguong 0.5). "
    "Ha nguong `P(High)` xuong giup bat them ca High that (tang recall) — "
    "danh doi precision giam. Trong he thong canh bao dich, recall quan trong hon.\n\n"
    "Sweep nguong 0.15 -> 0.55, ve recall/precision/macro-F1 de chon diem can bang."
)

CODE_68C = r'''# [6.8c] Threshold sweep cho class High (Tang 3)
import matplotlib.pyplot as plt

# Base strategy cho threshold sweep — dung 'balanced' lam goc (co the doi)
BASE_KW = {'flu':    dict(strategy='balanced'),
           'dengue': dict(strategy='balanced')}

THRESHOLDS = [0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.55]

fig, axes = plt.subplots(1, 2, figsize=(13, 5))
for ax, disease, df_, feats, folds, tcol in [
    (axes[0], 'flu',    flu_feat,  FEATURE_COLS_FLU,    FOLDS_FLU,    'flu_risk_class'),
    (axes[1], 'dengue', deng_feat, FEATURE_COLS_DENGUE, FOLDS_DENGUE, 'dengue_risk_class'),
]:
    rows = []
    for t in THRESHOLDS:
        m = eval_clf_strategy(df_, feats, tcol, folds, threshold_high=t, **BASE_KW[disease])
        rows.append({'threshold': t, **m})
    sweep = pd.DataFrame(rows)
    ax.plot(sweep['threshold'], sweep['high_recall'], 'o-', label='High recall', color='C0')
    ax.plot(sweep['threshold'], sweep['high_prec'],   's-', label='High precision', color='C1')
    ax.plot(sweep['threshold'], sweep['macro_f1'],    '^-', label='macro-F1', color='C2')
    ax.axvline(0.5, ls='--', color='gray', alpha=0.5, label='default (0.5)')
    ax.set_xlabel('Nguong P(High)'); ax.set_ylabel('Score')
    ax.set_title(f'{disease.upper()} — Threshold sweep'); ax.legend(); ax.grid(alpha=0.3)
    print(f'=== {disease.upper()} threshold sweep ===')
    print(sweep.to_string(index=False, float_format=lambda x: f'{x:.4f}'))
    print()

plt.tight_layout()
plt.savefig('threshold_sweep.png', dpi=150, bbox_inches='tight')
plt.show()
print('[OK] threshold_sweep.png saved')
'''

cells.insert(idx_69md, code(CODE_68C))
cells.insert(idx_69md, md(MD_68C))
print(f'[OK] Inserted 6.8c (md+code) tai index {idx_69md}')

# ===================================================================
# 3. CELL 6.10 (save) — fix encoding + bump v4 + use chosen strategy
# ===================================================================
idx_610 = find_cell('[6.10] Save final models')
NEW_610 = r'''# [6.10] Save final models — classifier v4 (encoding fix + chien luoc tot nhat)
import joblib, json as json_lib

# ── Cau hinh classifier chon tu thi nghiem 6.8 (chinh tay sau khi xem bang) ───
# strategy: 'none'|'balanced'|'custom'|'oversample';  threshold: None hoac 0..1
CLF_CFG = {
    'flu':    {'strategy': 'balanced', 'custom_weights': {0: 1, 1: 2, 2: 4}, 'threshold': None},
    'dengue': {'strategy': 'custom',   'custom_weights': {0: 1, 1: 2, 2: 4}, 'threshold': None},
}

flu_full  = flu_feat[flu_feat['iso_year'] <= 2018]
deng_full = deng_feat[deng_feat['iso_year'] <= 2018]

# === 1. Flu Regressor (LightGBM tuned) — v2 khong doi ===
flu_reg = LGBMRegressor(**study_flu.best_params, random_state=42, n_jobs=-1, verbose=-1)
flu_reg.fit(flu_full[FEATURE_COLS_FLU], flu_full['flu_log'])
path = MODELS_DIR / 'lgbm_flu_regressor_v2.pkl'
joblib.dump(flu_reg, path)
json_lib.dump({'features': FEATURE_COLS_FLU, 'target': 'flu_log',
               'version': 'v2', 'date': '2026-06-06', 'model_type': 'LightGBM', 'tuned': True,
               'note': 'Added flu_log_velocity + flu_log_accel (trend features)',
               'best_params': study_flu.best_params},
              open(MODELS_DIR / 'lgbm_flu_regressor_v2_features.json', 'w'), indent=2)
json_lib.dump({'rmse': float(RESULTS['flu']['LightGBM-tuned']['rmse']),
               'mae': float(RESULTS['flu']['LightGBM-tuned']['mae']),
               'r2': float(RESULTS['flu']['LightGBM-tuned']['r2']),
               'cv_folds': 6, 'cv_type': 'walk-forward', 'optuna_trials': 60},
              open(MODELS_DIR / 'lgbm_flu_regressor_v2_metrics.json', 'w'), indent=2)
print(f'[SAVED] {path.name}')

# === 2. Dengue Regressor (RandomForest tuned) — v2 khong doi ===
deng_reg = RandomForestRegressor(**study_deng.best_params, random_state=42, n_jobs=-1)
deng_reg.fit(deng_full[FEATURE_COLS_DENGUE], deng_full['deng_log'])
path = MODELS_DIR / 'rf_dengue_regressor_v2.pkl'
joblib.dump(deng_reg, path)
json_lib.dump({'features': FEATURE_COLS_DENGUE, 'target': 'deng_log',
               'version': 'v2', 'date': '2026-06-06', 'model_type': 'RandomForest', 'tuned': True,
               'note': 'Added deng_log_velocity + deng_log_accel (trend features)',
               'best_params': study_deng.best_params},
              open(MODELS_DIR / 'rf_dengue_regressor_v2_features.json', 'w'), indent=2)
json_lib.dump({'rmse': float(RESULTS['dengue']['RandomForest-tuned']['rmse']),
               'mae': float(RESULTS['dengue']['RandomForest-tuned']['mae']),
               'r2': float(RESULTS['dengue']['RandomForest-tuned']['r2']),
               'cv_folds': 3, 'cv_type': 'walk-forward', 'optuna_trials': 60},
              open(MODELS_DIR / 'rf_dengue_regressor_v2_metrics.json', 'w'), indent=2)
print(f'[SAVED] {path.name}')

# === 3 & 4. Classifiers v4 — encoding dung (Low=0,Med=1,High=2) + chien luoc chon ===
for disease, df_full, feats, tcol, fname in [
    ('flu',    flu_full,  FEATURE_COLS_FLU,    'flu_risk_class',    'xgb_flu_classifier_v4'),
    ('dengue', deng_full, FEATURE_COLS_DENGUE, 'dengue_risk_class', 'xgb_dengue_classifier_v4'),
]:
    cfg = CLF_CFG[disease]
    y_full = df_full[tcol].map(RISK_MAP).values
    clf = fit_classifier(df_full[feats], y_full, cfg['strategy'], cfg['custom_weights'])
    path = MODELS_DIR / f'{fname}.pkl'
    joblib.dump(clf, path)
    cv_folds = 6 if disease == 'flu' else 3
    json_lib.dump({'features': feats, 'target': tcol,
                   'classes': CLASS_LABELS, 'class_order': RISK_INV,
                   'risk_map': RISK_MAP, 'version': 'v4', 'date': '2026-06-07',
                   'model_type': 'XGBClassifier',
                   'strategy': cfg['strategy'], 'custom_weights': cfg['custom_weights'],
                   'high_threshold': cfg['threshold'],
                   'note': 'FIX encoding Low=0/Med=1/High=2; imbalanced strategy chon tu 6.8'},
                  open(MODELS_DIR / f'{fname}_features.json', 'w'), indent=2)
    # ghi metrics tu CLF_COMPARE (chon dong co strategy khop prefix)
    row = CLF_COMPARE[disease][
        CLF_COMPARE[disease]['strategy'].str.startswith(cfg['strategy'])].iloc[0]
    json_lib.dump({'macro_f1': float(row['macro_f1']),
                   'high_recall': float(row['high_recall']),
                   'high_prec': float(row['high_prec']),
                   'med_recall': float(row['med_recall']),
                   'cv_folds': cv_folds, 'cv_type': 'walk-forward',
                   'strategy': cfg['strategy'], 'high_threshold': cfg['threshold']},
                  open(MODELS_DIR / f'{fname}_metrics.json', 'w'), indent=2)
    print(f'[SAVED] {path.name} — strategy={cfg["strategy"]}, '
          f'macro_f1={row["macro_f1"]:.4f}, high_recall={row["high_recall"]:.4f}')

print('\nTat ca models da save tai:', MODELS_DIR)
'''
cells[idx_610]['source'] = NEW_610
print(f'[OK] Cell {idx_610} (6.10) rewritten — classifier v4 + encoding fix')

# Update 6.10 markdown
idx_610md = find_cell('## 6.10', ctype='markdown')
cells[idx_610md]['source'] = (
    "## 6.10 — Save final models (regressor v2, classifier v4)\n\n"
    "Refit tuned models tren FULL training data (flu 2010-2018, dengue 2015-2018).\n\n"
    "- Regressor: v2 (khong doi — trend features)\n"
    "- Classifier: **v4** — fix encoding (Low=0/Med=1/High=2) + chien luoc imbalanced chon tu 6.8.\n"
    "  Metadata luu `risk_map`, `class_order`, `strategy`, `high_threshold` de backend doc dung."
)
print(f'[OK] Cell {idx_610md} (6.10 md) updated')

# ===================================================================
# 4. CELL 7.0 (118) — fix LabelEncoder + load classifier v4
# ===================================================================
idx_70 = find_cell('[7.0] Reload models')
src70 = ''.join(cells[idx_70]['source'])
src70 = src70.replace("xgb_flu_classifier_v3.pkl", "xgb_flu_classifier_v4.pkl")
src70 = src70.replace("xgb_dengue_classifier_v3.pkl", "xgb_dengue_classifier_v4.pkl")
src70 = src70.replace(
    "from sklearn.preprocessing import LabelEncoder\n",
    "")
src70 = src70.replace(
    "CLASS_LABELS = ['Low', 'Medium', 'High']\nle = LabelEncoder().fit(CLASS_LABELS)\nprint('[OK] LabelEncoder ready')",
    "RISK_MAP = {'Low': 0, 'Medium': 1, 'High': 2}\n"
    "RISK_INV = {0: 'Low', 1: 'Medium', 2: 'High'}\n"
    "CLASS_LABELS = ['Low', 'Medium', 'High']\n"
    "print('[OK] RISK_MAP ready (Low=0, Medium=1, High=2)')")
cells[idx_70]['source'] = src70
print(f'[OK] Cell {idx_70} (7.0) fixed — v4 classifier + RISK_MAP')

# ===================================================================
# 5. CELL 7.4 (128) — fix le.transform -> map(RISK_MAP); confusion matrix dung
# ===================================================================
idx_74 = find_cell('[7.4] Classification 2022 evaluation')
src74 = ''.join(cells[idx_74]['source'])
src74 = src74.replace("le.transform(flu_2022_eval['flu_risk_class'])",
                      "flu_2022_eval['flu_risk_class'].map(RISK_MAP).values")
src74 = src74.replace("le.transform(deng_2022_eval['dengue_risk_class'])",
                      "deng_2022_eval['dengue_risk_class'].map(RISK_MAP).values")
src74 = src74.replace('flu_clf_v2', 'flu_clf_v4')
src74 = src74.replace('deng_clf_v2', 'deng_clf_v4')
src74 = src74.replace('XGBClassifier v3', 'XGBClassifier v4')
cells[idx_74]['source'] = src74
print(f'[OK] Cell {idx_74} (7.4) fixed — map(RISK_MAP) + v4')

# Cung sua bien load model trong 7.0 -> ten flu_clf_v4
src70b = ''.join(cells[idx_70]['source'])
src70b = src70b.replace('flu_clf_v2  = joblib.load', 'flu_clf_v4  = joblib.load')
src70b = src70b.replace('deng_clf_v2 = joblib.load', 'deng_clf_v4 = joblib.load')
cells[idx_70]['source'] = src70b
print(f'[OK] Cell {idx_70} (7.0) var rename -> flu_clf_v4/deng_clf_v4')

# ===================================================================
# SAVE
# ===================================================================
NB.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding='utf-8')
print(f'\nNotebook saved. Total cells: {len(cells)}')

# ===================================================================
# VERIFY
# ===================================================================
nb2 = json.loads(NB.read_text(encoding='utf-8'))
c = nb2['cells']
allsrc = '\n'.join(''.join(x['source']) for x in c)
checks = [
    ('RISK_MAP defined',        "RISK_MAP    = {'Low': 0" in allsrc or "RISK_MAP = {'Low': 0" in allsrc),
    ('eval_clf_strategy',       'def eval_clf_strategy' in allsrc),
    ('random_oversample',       'def random_oversample' in allsrc),
    ('threshold sweep cell',    'threshold_sweep.png' in allsrc),
    ('classifier v4 save',      'xgb_flu_classifier_v4' in allsrc),
    ('7.0 loads v4',            'xgb_flu_classifier_v4.pkl' in allsrc),
    ('7.4 uses map(RISK_MAP)',  "flu_2022_eval['flu_risk_class'].map(RISK_MAP)" in allsrc),
    ('no le.transform left',    'le.transform' not in allsrc),
]
print('\nVerification:')
all_ok = True
for label, ok in checks:
    print(f'  [{"OK" if ok else "FAIL"}] {label}')
    if not ok:
        all_ok = False
print('\n' + ('ALL CHECKS PASSED' if all_ok else 'SOME CHECKS FAILED'))
