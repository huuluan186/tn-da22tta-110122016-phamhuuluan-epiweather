# notebook_workflow.md — Quy trình làm việc Notebook

## Nguyên tắc cốt lõi

1. **1 notebook duy nhất** cho toàn bộ pipeline ML
2. **Session independence**: mỗi session đọc/ghi CSV — không phụ thuộc biến session trước
3. **Idempotent**: chạy lại cell không bị lỗi, không tạo duplicate
4. **Check-before-process**: kiểm tra file tồn tại trước khi xử lý nặng

## Session Structure

```
SESSION 0  — Setup & Load (chạy khi mở lại Colab)
SESSION 1  — Load & Sanity Check raw data
SESSION 2  — ERA5 Process (nặng, chạy 1 lần)
SESSION 3  — Merge All -> master_weekly.csv
SESSION 4  — EDA trên master file
SESSION 5  — Feature Engineering
SESSION 6  — Model Training (XGBoost + LightGBM + RF + Prophet + Classifier + Optuna)
SESSION 7  — Evaluation & Export
```

## Pattern: Check-before-process

```python
# Pattern chuẩn cho mọi bước xử lý nặng
OUTPUT_FILE = Path('data/processed/era5_weekly.csv')

if OUTPUT_FILE.exists():
    print(f'✅ File đã có: {OUTPUT_FILE.name} — load từ disk')
    df = pd.read_csv(OUTPUT_FILE)
else:
    print(f'⏳ Chưa có — bắt đầu process...')
    df = heavy_processing()
    df.to_csv(OUTPUT_FILE, index=False)
    print(f'💾 Saved: {OUTPUT_FILE}')
```

## Pattern: Session 0 Restart

```python
# [SESSION 0] Chạy cell này khi mở lại notebook
# Load tất cả file đã có từ disk — không reprocess

from pathlib import Path
import pandas as pd, numpy as np

DATA_DIR = Path('data')
flu    = pd.read_csv(DATA_DIR / 'raw/VIW_FNT.csv', low_memory=False)
dengue = pd.read_csv(DATA_DIR / 'raw/National_extract_V1_3.csv', low_memory=False)
era5   = pd.read_csv(DATA_DIR / 'processed/era5_weekly_2010_2019_final.csv')
master = pd.read_csv(DATA_DIR / 'processed/master_weekly_2010_2019.csv')  # nếu đã có

TRAIN_START, TRAIN_END = 2010, 2019
VAL_YEAR = 2022

print(f'✅ FluNet : {flu.shape}')
print(f'✅ Dengue : {dengue.shape}')
print(f'✅ ERA5   : {era5.shape}')
```

## Khi nào cần chạy lại gì

| Tình huống | Cần chạy |
|---|---|
| Mở lại Colab sau khi tắt | SESSION 0 (30 giây) + restart cell session đang làm |
| Muốn bắt đầu SESSION 6 | SESSION 0 → [6.0] load features → chạy tiếp |
| Muốn xem lại EDA | SESSION 0 → [4.0] load master → chạy tiếp |
| Thay đổi features | SESSION 5 trở đi |
| Thêm model mới | SESSION 6 trở đi |
| master.csv chưa có | SESSION 0 → SESSION 3 |
| ERA5 chưa có | SESSION 0 → SESSION 2 đầy đủ |

## Ghi chú Markdown cell

Format chuẩn sau mỗi code cell:
```markdown
📌 **[x.x]** Giải thích ngắn gọn lý do làm bước này, quyết định rút ra,
hoặc cảnh báo kỹ thuật. Có thể dùng bullet nếu cần liệt kê nhiều điểm.
Không dùng heading `#` vì sẽ to hơn session header.
```

## Workflow với Claude

```
1. Claude gửi code cell trong chat
2. Người dùng copy vào notebook → chạy
3. Paste output (text + screenshot nếu có plot) vào chat
4. Claude phân tích → gửi ghi chú markdown
5. Người dùng thêm markdown cell vào notebook
6. Claude gửi cell tiếp theo
```

**Sau mỗi session:**
- Claude đánh giá xem session đủ chưa hay cần thêm gì
- Update Notion nếu có quyết định quan trọng
