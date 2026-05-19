# Session 0–1: Setup Môi Trường & Load Dữ Liệu Thô

---

## Trước khi bắt đầu: Lấy dữ liệu thô ở đâu?

Đây là câu hỏi đầu tiên mà ai cũng hỏi. Mình liệt kê từng nguồn, cách lấy, và file cụ thể.

---

### Nguồn 1 — WHO FluNet (Influenza)

**Trang web:** https://www.who.int/tools/flunet

**Cách tải:**
1. Vào trang trên → chọn tab **"Download data"**
2. Chọn: Countries = **All**, Years = **All**, Virus type = **All**
3. Bấm **"Download CSV"**
4. File tải về tên: `VIW_FNT.csv` (khoảng 30–50 MB)

> Hoặc tải trực tiếp qua URL:
> `https://frontdoor-l4uikgap6gz3m.azurefd.net/FLUMART/VIW_FLU_METADATA`

**File dùng trong project:** `Dataset/epidemic/raw/VIW_FNT.csv`

**Cập nhật:** FluNet update hàng tuần — mình tải lần đầu tháng 01/2025, dữ liệu đến tuần 52/2024.

---

### Nguồn 2 — OpenDengue (Dengue)

**Trang web:** https://github.com/OpenDengue/master-repo

**Cách tải:**
1. Vào GitHub repo trên
2. Vào thư mục `data/national_data/`
3. Tải file: **`National_extract_V1_3.csv`** (version 1.3, khoảng 15 MB)

> Hoặc tải thẳng bằng lệnh:
> ```bash
> wget https://github.com/OpenDengue/master-repo/raw/main/data/national_data/National_extract_V1_3.csv
> ```

**File dùng trong project:** `Dataset/epidemic/raw/National_extract_V1_3.csv`

**Lưu ý version:** OpenDengue có nhiều version (V1.0, V1.1, V1.3). Mình dùng **V1.3** — version mới nhất tại thời điểm làm đề tài, có thêm data từ năm 2022.

---

### Nguồn 3 — ERA5 (Dữ liệu khí hậu ECMWF)

ERA5 **không tải thủ công** được vì file quá lớn (6.2 GB). Phải dùng **CDS API**. Xem hướng dẫn chi tiết trong [session_4_era5.md](session_4_era5.md) — phần "Setup CDS API".

**Tóm tắt nhanh:**
1. Đăng ký tài khoản tại https://cds.climate.copernicus.eu/
2. Lấy API key trong profile
3. Cài `cdsapi`: `pip install cdsapi`
4. Tạo file `~/.cdsapirc` với API key
5. Chạy script download trong notebook

**File output sau khi xử lý:** `Dataset/weather/processed/era5_weekly_2010_2019_final.csv`

---

### Nguồn 4 — ECDC Sentinel + ILI (Châu Âu)

**Trang web:** https://www.ecdc.europa.eu/en/seasonal-influenza/data-tools

**Cách tải:**
1. Tải `sentinelTestsDetectionsPositivity.csv` — dữ liệu xét nghiệm cúm sentinel labs
2. Tải `ILIARIRates.csv` — tỷ lệ mắc cúm theo nhóm tuổi

**File dùng trong project:**
- `Dataset/epidemic/raw/sentinelTestsDetectionsPositivity.csv`
- `Dataset/epidemic/raw/ILIARIRates.csv`

**Lưu ý quan trọng:** ECDC chỉ có 30 quốc gia châu Âu và **chỉ có từ năm 2021**. Vì giai đoạn training là 2010–2019, ECDC **không được dùng để training** — chỉ dùng cho validation và dashboard display.

---

### Tổng hợp: File nào → Lấy ở đâu

| File | Nguồn | Cách lấy | Kích thước |
|------|-------|----------|-----------|
| `VIW_FNT.csv` | WHO FluNet | Download CSV từ website | ~40 MB |
| `National_extract_V1_3.csv` | OpenDengue GitHub | Download từ GitHub repo | ~15 MB |
| ERA5 NetCDF (2010–2019) | ECMWF CDS | CDS API (cần đăng ký) | **6.2 GB** |
| `sentinelTestsDetectionsPositivity.csv` | ECDC | Download từ ECDC website | ~5 MB |
| `ILIARIRates.csv` | ECDC | Download từ ECDC website | ~3 MB |
| `era5_weekly_2010_2019_final.csv` | Tự tạo | Chạy Session 4 / scripts/process_era5.py | ~50 MB |
| `master_weekly_2010_2019.csv` | Tự tạo | Chạy Session 5 | ~25 MB |

> **Thứ tự phải làm:** Tải FluNet + OpenDengue + ECDC → Tải ERA5 qua API → Chạy pipeline theo thứ tự session.

---

## Session 0 — Cái cell đầu tiên bạn phải chạy mỗi khi mở notebook

### Tại sao lại có "Session 0"?

Mình làm trên Google Colab — nghĩa là mỗi lần runtime bị restart (hết RAM, mất kết nối, đóng tab), **tất cả biến trong bộ nhớ đều mất**. Nhưng các file CSV đã xử lý vẫn còn trên Google Drive.

Thay vì chạy lại toàn bộ pipeline từ đầu (mất 2–3 tiếng chỉ riêng ERA5), mình tạo "Session 0" ở đầu — chạy 5 cell này là đủ biến cho toàn bộ session tiếp theo.

---

### Cell 0.1 — Mount Google Drive

```python
from google.colab import drive
from pathlib import Path

drive.mount('/content/drive', force_remount=False)

BASE = Path('/content/drive/MyDrive/KLTN')
if BASE.exists():
    print(f"✅ Drive mounted, BASE exists: {BASE}")
else:
    print(f"⚠️ BASE không tồn tại: {BASE}")
```

`force_remount=False` tránh unmount nếu Drive đã được mount từ trước (ví dụ khi chạy lại cell).

---

### Cell 0.2 — Install missing libraries

```python
def ensure_package(import_name, pip_name=None):
    pip_name = pip_name or import_name
    try:
        importlib.import_module(import_name)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name, "-q"])

ensure_package('xgboost')
ensure_package('prophet')
ensure_package('scipy')
ensure_package('sklearn', 'scikit-learn')
ensure_package('joblib')
```

Kiểm tra package trước khi install tránh re-install mất thời gian. Google Colab đã có sẵn `scikit-learn`, `scipy`, `xgboost` — thường chỉ cần install `prophet` (yêu cầu compile C++, lần đầu cài lâu hơn).

---

### Cell 0.3 — Import tất cả thư viện

```python
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import joblib, json
from sklearn.metrics import mean_absolute_error, mean_squared_error
from xgboost import XGBRegressor
# ...
```

Tập trung tất cả import vào một cell duy nhất. Khi Colab restart, chỉ cần chạy lại Session 0 (5 cells) — không cần tìm import rải rác trong các session khác.

---

### Cell 0.4 — Khai báo Paths + Constants

```python
BASE         = Path('/content/drive/MyDrive/KLTN')
RAW          = BASE / 'dataset' / 'epidemic' / 'raw'
PROCESSED    = BASE / 'dataset' / 'processed'
WEATHER_DIR  = BASE / 'dataset' / 'weather' / 'processed'
MODELS_DIR   = BASE / 'models'

ERA5_FILE    = WEATHER_DIR / 'era5_weekly_2010_2019_final.csv'
MASTER_FILE  = PROCESSED   / 'master_weekly_2010_2019.csv'
FLUNET_FILE  = RAW          / 'VIW_FNT.csv'
DENGUE_FILE  = RAW          / 'National_extract_V1_3.csv'
ECDC_ILI     = RAW          / 'ILIARIRates.csv'
ECDC_SENT    = RAW          / 'sentinelTestsDetectionsPositivity.csv'

FILES = {
    'flunet'   : RAW / 'VIW_FNT.csv',
    'flu_meta' : RAW / 'VIW_FLU_METADATA.csv',
    'dengue'   : RAW / 'National_extract_V1_3.csv',
    'ecdc_sen' : RAW / 'sentinelTestsDetectionsPositivity.csv',
    'ecdc_ili' : RAW / 'ILIARIRates.csv',
    'era5'     : ERA5_FILE,
    'master'   : MASTER_FILE,
}

TRAIN_START  = 2010
TRAIN_END    = 2019
VAL_YEAR     = 2022
COVID_YEARS  = [2020, 2021]
TARGET_FLU    = 'inf_log1p'
TARGET_DENGUE = 'dengue_log1p'
LAG_FLU    = [1, 2, 3]
LAG_DENGUE = [6, 8, 10, 12, 14]
WEATHER_VARS = [
    'temp_c', 'dewpoint_c', 'temp_min_c', 'temp_max_c', 'temp_range_c',
    'humidity_pct', 'wind_ms', 'precip_mm', 'conv_precip_mm', 'ls_precip_mm',
    'evap_mm', 'water_vapour', 'solar_wm2', 'uv_wm2', 'thermal_wm2',
    'cloud_cover', 'msl_pa', 'blh_m'
]
```

Lý do tập trung path và constant ở một chỗ: nếu sau này di chuyển file hoặc đổi tên, chỉ sửa một chỗ, không phải đi tìm từng cell.

Hai hằng số cuối — `TARGET_FLU = 'inf_log1p'` và `TARGET_DENGUE = 'dengue_log1p'` — quan trọng nhất. Đây là cột mà model phải học cách dự báo (giải thích kỹ ở Session 5/7).

---

### Cell 0.5 — File Verification

```python
files_to_check = {
    "MASTER_FILE": MASTER_FILE,
    "ERA5_FILE":   ERA5_FILE,
    "FLUNET_FILE": FLUNET_FILE,
    "DENGUE_FILE": DENGUE_FILE,
    "ECDC_ILI":    ECDC_ILI,
    "ECDC_SENT":   ECDC_SENT,
}

for name, path in files_to_check.items():
    if path.exists():
        size_mb = path.stat().st_size / 1024**2
        print(f'✅ {name}: {path.name} ({size_mb:.1f} MB)')
    else:
        print(f'⚠️  {name}: KHÔNG TÌM THẤY -> {path}')
```

Cell này check trước khi vào bất kỳ session nào — biết ngay file nào còn thiếu, không cần chạy đến giữa chừng mới báo lỗi.

---

## Session 1 — Load Dữ Liệu Thô & Nhìn Tổng Quan

### Mục tiêu session này

Không làm gì phức tạp. Mục tiêu duy nhất: **load 5 bộ dữ liệu vào RAM và xem chúng trông như thế nào**. Như lần đầu mở hộp hàng — mình cần biết mình đang có gì trước khi xử lý.

---

### Cell 1.0 — RESTART CELL: Load tất cả raw files

```python
flu      = pd.read_csv(FILES['flunet'], low_memory=False)
flu_meta = pd.read_csv(FILES['flu_meta'], low_memory=False)
dengue   = pd.read_csv(FILES['dengue'], low_memory=False)
ecdc_sen = pd.read_csv(FILES['ecdc_sen'], low_memory=False)
ecdc_ili = pd.read_csv(FILES['ecdc_ili'], low_memory=False)

for name, df in [('flu', flu), ('flu_meta', flu_meta), ('dengue', dengue),
                  ('ecdc_sen', ecdc_sen), ('ecdc_ili', ecdc_ili)]:
    print(f'{name}: shape={df.shape} | cols={list(df.columns[:5])}...')
```

FILES dict đã được define ở SESSION 0. Load tập trung ở đây để các cell inspect [1.1]–[1.4] chỉ cần tham chiếu biến, không load lại.

---

### Cell 1.1 — Inspect FluNet

```python
print(f'Shape: {flu.shape}')
print(f'Columns ({len(flu.columns)}):', list(flu.columns))
print(f'Year range: {flu["ISO_YEAR"].min()}-{flu["ISO_YEAR"].max()}')
print(f'Countries: {flu["COUNTRY_CODE"].nunique()}')
display(flu.head(3))
```

**Output kỳ vọng:** `~(200,000 rows, 53 columns)`, quốc gia: 172, year: 1995–2026

FluNet có 53 cột gồm nhiều subtype chi tiết (AH1N12009, AH3, BVIC...). Các cột quan trọng sẽ dùng: `INF_A`, `INF_B`, `COUNTRY_CODE`, `ISO_YEAR`, `ISO_WEEK`. `RSV` và `RSV_PROCESSED` tồn tại nhưng khác đơn vị — sẽ quyết định giữ/bỏ ở SESSION 2. `PARAINFLUENZA` sẽ bị drop do missing rate cao.

---

### Cell 1.2 — Inspect OpenDengue

```python
print(f'Shape: {dengue.shape}')
print('T_res distribution:')
print(dengue['T_res'].value_counts())
print(f'Year range: {dengue["calendar_start_date"].dropna().iloc[0]} ... '
      f'{dengue["calendar_start_date"].dropna().iloc[-1]}')
display(dengue.head(3))
```

**Output kỳ vọng:** `~(60,000 rows, 15 columns)`, T_res: Week 77.8%, Year 11.7%, Month 10.5%

`T_res` phân ra Week/Month/Year — chỉ dùng Week+Month để đủ granularity cho model tuần. Date format của OpenDengue không nhất quán (MM/DD/YYYY), cần `format='mixed'` khi parse — sẽ xử lý ở SESSION 3 và SESSION 5.

---

### Cell 1.3 — Inspect ECDC Sentinel

```python
print(f'Shape: {ecdc_sen.shape}')
# Pathogen column
pathogen_col = [c for c in ecdc_sen.columns if 'pathogen' in c.lower()]
if pathogen_col:
    print(f'Unique pathogens: {ecdc_sen[pathogen_col[0]].unique()}')
print(f'Countries: {ecdc_sen.iloc[:, 0].nunique()}')
display(ecdc_sen.head(3))
```

**Output kỳ vọng:** ~30 quốc gia châu Âu, có cả SARS-CoV-2 cần filter khi dùng.

ECDC Sentinel chỉ 30 quốc gia châu Âu và chỉ có data từ 2021. Quyết định đã chốt: ECDC chỉ dùng cho validation và dashboard, **không dùng cho training** (vì train period là 2010–2019).

---

### Cell 1.4 — Inspect ECDC ILI

```python
print(f'Shape: {ecdc_ili.shape}')
age_col = [c for c in ecdc_ili.columns if 'age' in c.lower()]
print(f'Age columns: {age_col}')
yr_col = [c for c in ecdc_ili.columns if 'year' in c.lower()]
if yr_col:
    print(f'Year range: {ecdc_ili[yr_col[0]].min()}-{ecdc_ili[yr_col[0]].max()}')
display(ecdc_ili.head(3))
```

ECDC ILI có age groups đầy đủ (0–4, 5–14, 15–64, 65+, total) — hữu ích cho dashboard chi tiết khi hiển thị breakdown theo nhóm tuổi. Cũng chỉ có từ 2021 nên không dùng cho training.

---

### Kết thúc Session 1 — Bạn đã biết gì?

Sau khi chạy xong 5 cell này, bạn có trong tay:
- **FluNet:** ~200k rows, 172 quốc gia, 53 cột, 1995–2026
- **OpenDengue:** ~60k rows, ~60 quốc gia, nhiều granularity (Week/Month/Year)
- **ECDC Sentinel:** ~30 quốc gia châu Âu, từ 2021 (validation only)
- **ECDC ILI:** Age-stratified ILI rates, châu Âu, từ 2021 (validation only)

Chưa làm gì cả. Chỉ xem. Session tiếp theo mình mới bắt đầu hỏi: *dữ liệu này có đáng tin không?*

---

## Key Insights từ Session 0–1

**1. 4 nguồn dữ liệu, 4 "ngôn ngữ" khác nhau**
FluNet báo cáo theo quốc gia–tuần; ERA5 là lưới địa lý 721×1440 điểm; OpenDengue mix Week/Month/Year; ECDC dùng tên quốc gia châu Âu. Không có nguồn nào dùng được trực tiếp — phải chuẩn hóa trước khi merge.

**2. ECDC chỉ có từ 2021 — ràng buộc quyết định train period**
Nếu muốn dùng ECDC cho training, phải cắt train period sau 2021 — quá ít data. Quyết định: ECDC chỉ dùng cho validation và dashboard. Train period 2010–2019 là quyết định xuất phát từ ràng buộc data này.

**3. ERA5 6.2 GB không thể download thủ công**
Đây là lý do tồn tại của SESSION 4. Phải dùng CDS API và xử lý theo từng năm. Ai muốn reproduce pipeline phải đăng ký tài khoản ECMWF trước — đây là "setup cost" duy nhất của project.

**4. OpenDengue có T_res không nhất quán**
77.8% Week, 10.5% Month, 11.7% Year — cùng một file nhưng 3 granularity khác nhau. Chiến lược: giữ Week + resample Month → Week, bỏ Year. Sẽ xử lý ở SESSION 3 và 5.
