"""Patch notebook v7: thêm confusion matrix vào cell 7.4 + markdown giải thích imbalanced."""
import sys, io, json
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

NB = Path('notebooks/KLTN_EpiWeather_ML_v7.ipynb')
nb = json.loads(NB.read_text(encoding='utf-8'))
cells = nb['cells']

# ===== CELL 128 (7.4): thêm confusion matrix sau classification reports =====
APPEND_C128 = """
# === Confusion Matrix ===
from sklearn.metrics import confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

fig, axes = plt.subplots(1, 2, figsize=(12, 5))

for ax, y_true, y_pred, title in [
    (axes[0], y_flu_clf,  yhat_flu_clf,  'FLU — XGBClassifier v3 (2022 holdout)'),
    (axes[1], y_deng_clf, yhat_deng_clf, 'DENGUE — XGBClassifier v3 (2022 holdout)'),
]:
    cm = confusion_matrix(y_true, y_pred)
    cm_norm = confusion_matrix(y_true, y_pred, normalize='true')  # recall per class
    annot = [[f'{cm[i,j]}\\n({cm_norm[i,j]:.0%})' for j in range(3)] for i in range(3)]

    sns.heatmap(
        cm_norm, ax=ax, annot=annot, fmt='', cmap='Blues',
        xticklabels=CLASS_LABELS, yticklabels=CLASS_LABELS,
        vmin=0, vmax=1, linewidths=0.5,
    )
    ax.set_xlabel('Predicted', fontsize=11)
    ax.set_ylabel('Actual', fontsize=11)
    ax.set_title(title, fontsize=12, pad=10)

plt.suptitle('Confusion Matrix — Normalized by Actual (Recall per class)', fontsize=13, y=1.02)
plt.tight_layout()
plt.savefig('confusion_matrix_2022.png', dpi=150, bbox_inches='tight')
plt.show()
print('[OK] Confusion matrix saved: confusion_matrix_2022.png')

# === Summary: per-class recall ===
print()
print('Per-class Recall (diagonal):')
for label, cm, y_true, y_pred in [
    ('FLU',    confusion_matrix(y_flu_clf, yhat_flu_clf, normalize='true'),  y_flu_clf,  yhat_flu_clf),
    ('DENGUE', confusion_matrix(y_deng_clf, yhat_deng_clf, normalize='true'), y_deng_clf, yhat_deng_clf),
]:
    print(f'  {label}:  Low={cm[0,0]:.0%}  Medium={cm[1,1]:.0%}  High={cm[2,2]:.0%}')
"""

src128 = ''.join(cells[128]['source'])
src128 = src128 + APPEND_C128
cells[128]['source'] = src128
print('[OK] Cell 128 patched — confusion matrix added')

# ===== INSERT markdown cell sau cell 128 (index 129): giải thích imbalanced =====
MARKDOWN_IMBALANCED = """**[7.4 — Giải thích xử lý Imbalanced Data]**

**Vấn đề:** Dataset classification bị mất cân bằng nhãn nghiêm trọng.
Phân phối nhãn flu training (2010-2018): Low ~55%, Medium ~32%, High ~13%.
Nếu không xử lý, model sẽ thiên về dự đoán Low/Medium, bỏ sót High outbreak.

**Phương pháp đã chọn: `compute_sample_weight('balanced', y_train)`**

Ý tưởng: gán trọng số ngược tỷ lệ xuất hiện cho từng mẫu khi train.
Nhãn hiếm (High) được tính loss nặng hơn → model chú ý nhiều hơn vào class này.

Công thức: `weight_c = n_samples / (n_classes × n_samples_c)`

**Tại sao không dùng các phương pháp khác:**

- **SMOTE / ADASYN** (tạo synthetic samples): không phù hợp với time-series.
  Tạo mẫu tổng hợp giữa 2 tuần dịch bệnh thực tế không có ý nghĩa về mặt dịch tễ học,
  và có nguy cơ leakage nếu không áp dụng đúng trong walk-forward CV.

- **Oversampling / Undersampling** thuần túy: với walk-forward CV 6 folds,
  oversampling làm tăng kích thước training không đồng đều giữa các fold,
  undersampling làm mất thông tin ở majority class.

- **class_weight trong XGBoost** (`scale_pos_weight`): chỉ hỗ trợ binary classification,
  không áp dụng được cho bài toán 3 class (Low/Medium/High).

**Kết quả:** High recall flu tăng từ ~0.30 (không xử lý) lên 0.71 (có sample_weight).
Đánh đổi: precision High thấp (0.22) → nhiều false alarm, nhưng trong hệ thống
cảnh báo dịch bệnh, bỏ sót outbreak nguy hiểm hơn báo nhầm (recall-oriented).

**Áp dụng đúng chỗ:** `compute_sample_weight` tính trên `y_train` của từng fold,
sau khi đã split train/val — không có data leakage.
"""

new_md_cell = {
    "cell_type": "markdown",
    "metadata": {},
    "source": MARKDOWN_IMBALANCED
}

# Insert sau cell 128 (index 128), trước cell 129 (markdown 7.5)
cells.insert(129, new_md_cell)
print('[OK] Markdown cell inserted at index 129 — giai thich imbalanced')

# ===== Save =====
NB.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding='utf-8')
print()
print(f'Notebook saved OK. Total cells: {len(cells)}')

# ===== Verify =====
nb2 = json.loads(NB.read_text(encoding='utf-8'))
c = nb2['cells']
checks = [
    ('Cell128 confusion_matrix import', 'confusion_matrix' in ''.join(c[128]['source'])),
    ('Cell128 sns.heatmap',             'sns.heatmap' in ''.join(c[128]['source'])),
    ('Cell128 saved png',               'confusion_matrix_2022.png' in ''.join(c[128]['source'])),
    ('Cell129 markdown imbalanced',     'sample_weight' in ''.join(c[129]['source'])),
    ('Cell129 SMOTE explanation',       'SMOTE' in ''.join(c[129]['source'])),
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
