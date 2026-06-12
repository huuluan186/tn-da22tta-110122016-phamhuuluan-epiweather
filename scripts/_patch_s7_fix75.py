"""Patch cell 7.5: fix model labels v1->v2/v3 + correct CV metrics + fix conclusion text."""
import sys, io, json
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

NB = Path('notebooks/KLTN_EpiWeather_ML_v7.ipynb')
nb = json.loads(NB.read_text(encoding='utf-8'))
cells = nb['cells']

# Cell 7.5 = index 130 (sau khi insert markdown cell 129)
# Tim cell co '7.5' hoac 'Bảng so sánh tổng hợp'
target_idx = None
for i, c in enumerate(cells):
    src = ''.join(c['source'])
    if '[7.5]' in src and 'reg_compare' in src:
        target_idx = i
        break

print(f'Found cell 7.5 at index {target_idx}')

NEW_C75 = [
    "# [7.5] Bang so sanh tong hop CV vs 2022 hold-out\n",
    "import pandas as pd\n",
    "\n",
    "# Regression comparison — dung metrics chinh xac tu v2\n",
    "reg_compare = pd.DataFrame({\n",
    "    'Disease'        : ['Flu', 'Dengue'],\n",
    "    'Model'          : ['LightGBM tuned v2', 'RandomForest tuned v2'],\n",
    "    'CV_R2'          : [0.9017, 0.9380],\n",
    "    'Test_2022_R2'   : [RESULTS_2022['flu']['r2'], RESULTS_2022['dengue']['r2']],\n",
    "    'Delta_R2'       : [RESULTS_2022['flu']['r2']-0.9017, RESULTS_2022['dengue']['r2']-0.9380],\n",
    "    'CV_RMSE'        : [0.5876, 0.7319],\n",
    "    'Test_2022_RMSE' : [RESULTS_2022['flu']['rmse'], RESULTS_2022['dengue']['rmse']],\n",
    "    'N_test'         : [RESULTS_2022['flu']['n'], RESULTS_2022['dengue']['n']],\n",
    "})\n",
    "\n",
    "# Classification comparison — dung metrics chinh xac tu v3\n",
    "clf_compare = pd.DataFrame({\n",
    "    'Disease'        : ['Flu', 'Dengue'],\n",
    "    'Model'          : ['XGBClassifier v3', 'XGBClassifier v3'],\n",
    "    'CV_F1'          : [0.5437, 0.4842],\n",
    "    'Test_2022_F1'   : [RESULTS_2022['flu']['macro_f1'], RESULTS_2022['dengue']['macro_f1']],\n",
    "    'Delta_F1'       : [RESULTS_2022['flu']['macro_f1']-0.5437, RESULTS_2022['dengue']['macro_f1']-0.4842],\n",
    "    'CV_AUC'         : [0.7360, 0.7248],\n",
    "    'Test_2022_AUC'  : [RESULTS_2022['flu']['auc_ovr'], RESULTS_2022['dengue']['auc_ovr']],\n",
    "})\n",
    "\n",
    "print('=== REGRESSION: CV (2014-2019) vs Hold-out 2022 ===')\n",
    "print(reg_compare.to_string(index=False, float_format=lambda x: f'{x:.4f}'))\n",
    "print()\n",
    "print('=== CLASSIFICATION: CV vs Hold-out 2022 ===')\n",
    "print(clf_compare.to_string(index=False, float_format=lambda x: f'{x:.4f}'))\n",
    "print()\n",
    "print('=== Ket luan tom tat ===')\n",
    "print('Regression: Generalize xuat sac (Flu delta=+0.0003, Dengue delta=-0.0183) -> production-ready')\n",
    "print('Flu classifier: High recall=71% (tot cho canh bao), nhung precision thap (22%) do post-COVID distribution shift')\n",
    "print('Dengue classifier: High recall=23% (han che) do dataset nho 37 nuoc x 5 nam, SMOTE khong phu hop time-series')\n",
    "print('AR features (lag1/lag2/lag3) chiem >90% gain importance -> chinh la goc cua predictive power')\n",
    "print('Limitation: can update Bortman baseline dinh ky moi nam de classification on dinh hon')\n",
]

cells[target_idx]['source'] = NEW_C75
print(f'[OK] Cell {target_idx} (7.5) patched')

NB.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding='utf-8')
print('Notebook saved OK.')

# Verify
nb2 = json.loads(NB.read_text(encoding='utf-8'))
src = ''.join(nb2['cells'][target_idx]['source'])
checks = [
    ('v2 regressor label', 'LightGBM tuned v2' in src),
    ('v3 classifier label', 'XGBClassifier v3' in src),
    ('correct flu CV_RMSE 0.5876', '0.5876' in src),
    ('correct dengue CV_RMSE 0.7319', '0.7319' in src),
    ('correct flu CV_F1 0.5437', '0.5437' in src),
    ('correct dengue CV_F1 0.4842', '0.4842' in src),
]
all_ok = True
for label, ok in checks:
    status = 'OK' if ok else 'FAIL'
    print(f'  [{status}] {label}')
    if not ok:
        all_ok = False
print()
print('ALL CHECKS PASSED' if all_ok else 'SOME CHECKS FAILED')
