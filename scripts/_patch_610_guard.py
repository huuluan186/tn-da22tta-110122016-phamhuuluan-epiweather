"""Bọc phần regressor refit trong cell 6.10 bằng try/except để không bắt buộc chạy 6.9."""
import sys, io, json
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

NB = Path('notebooks/KLTN_EpiWeather_ML_v7.ipynb')
nb = json.loads(NB.read_text(encoding='utf-8'))
cells = nb['cells']

idx = None
for i, c in enumerate(cells):
    if c['cell_type'] == 'code' and '[6.10] Save final models' in ''.join(c['source']):
        idx = i
        break

src = ''.join(cells[idx]['source'])

# Bọc khối regressor (tu '# === 1.' den het '# === 2.' ... truoc '# === 3 & 4.')
OLD_REG_START = "flu_full  = flu_feat[flu_feat['iso_year'] <= 2018]"
NEW_REG_START = (
    "flu_full  = flu_feat[flu_feat['iso_year'] <= 2018]\n"
    "deng_full = deng_feat[deng_feat['iso_year'] <= 2018]\n\n"
    "# Regressor v2 KHONG doi — chi refit + save neu da chay 6.9 (co study_flu/study_deng).\n"
    "# Neu chua chay 6.9, bo qua (file v2 da co san), chi luu classifier v4.\n"
    "if 'study_flu' in dir() and 'study_deng' in dir():"
)
src = src.replace(OLD_REG_START + "\ndeng_full = deng_feat[deng_feat['iso_year'] <= 2018]", NEW_REG_START)

# Indent toan bo khoi regressor (tu '# === 1.' den truoc '# === 3 & 4.')
marker_start = "# === 1. Flu Regressor"
marker_end = "# === 3 & 4. Classifiers v4"
i0 = src.index(marker_start)
i1 = src.index(marker_end)
block = src[i0:i1]
indented = '\n'.join(('    ' + ln if ln.strip() else ln) for ln in block.split('\n'))
src = src[:i0] + indented + src[i1:]

# Them else nhanh thong bao
src = src.replace(
    marker_end,
    "else:\n"
    "    print('[SKIP] Chua chay 6.9 (Optuna) -> bo qua refit regressor, giu file v2 san co.')\n\n"
    + marker_end
)

cells[idx]['source'] = src
NB.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding='utf-8')
print('[OK] Cell 6.10 guarded — regressor refit optional')

# Verify
nb2 = json.loads(NB.read_text(encoding='utf-8'))
s = ''.join(nb2['cells'][idx]['source'])
print('  [%s] has guard if study_flu' % ('OK' if "if 'study_flu' in dir()" in s else 'FAIL'))
print('  [%s] has skip msg' % ('OK' if '[SKIP] Chua chay 6.9' in s else 'FAIL'))
print('  [%s] classifier v4 still present' % ('OK' if 'xgb_flu_classifier_v4' in s else 'FAIL'))
# In thu 60 dong dau de kiem tra indent
print('\n--- preview ---')
for ln in s.split('\n')[:40]:
    print(ln)
