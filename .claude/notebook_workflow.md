# notebook_workflow.md — Quy trình làm việc Notebook

## Nguyên tắc cốt lõi

1. **1 notebook duy nhất** cho toàn bộ pipeline ML
2. **Session independence**: mỗi session đọc/ghi CSV — không phụ thuộc biến session trước
3. **Idempotent**: chạy lại cell không bị lỗi, không tạo duplicate
4. **Check-before-process**: kiểm tra file tồn tại trước khi xử lý nặng

## Session Structure

```
SESSION 0  — Setup & Load (nhẹ, luôn chạy khi restart)
SESSION 1  — Load & Inspect raw data
SESSION 2  — Data quality check
SESSION 3  — EDA: Seasonality & Trends
SESSION 3.5 — ERA5 Download & Process (NẶNG — chạy 1 lần, lưu CSV)
SESSION 4  — Preprocessing & Merge → master_weekly.csv
SESSION 5  — Correlation Analysis
SESSION 6  — Feature Engineering
SESSION 7  — Model Training & Comparison
SESSION 8  — Kết luận & Bước tiếp theo
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
| Mở notebook lại sau khi tắt | SESSION 0 (load từ CSV) |
| Thay đổi ERA5 variables | SESSION 3.5 (xóa CSV cũ trước) |
| Thay đổi merge logic | SESSION 4 (xóa master CSV cũ) |
| Thêm feature mới | SESSION 6 trở đi |
| Thay đổi model | SESSION 7 trở đi |

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
