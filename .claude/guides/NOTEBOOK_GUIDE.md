# NOTEBOOK_GUIDE.md — Hướng dẫn viết KLTN_EpiWeather_ML.ipynb

> File này dành cho Claude, đọc trước khi viết hoặc sửa bất kỳ cell nào trong notebook.
> Cập nhật lần cuối: 2026-04-28

---

## 1. NGUYÊN TẮC BẤT BIẾN

### 1.1 Môi trường
- **ML pipeline (notebook):** Google Colab + Google Drive
- **Backend/Frontend:** Local VSCode + Python venv
- **Export flow:** Sau SESSION 7, download .pkl + features.json + thresholds.json
  từ Drive về local → copy vào backend/models/ → FastAPI load khi startup

### 1.2 Cấu trúc thư mục trên Google Drive
```
MyDrive/KLTN/
├── Dataset/
│   ├── epidemic/
│   │   ├── raw/                  ← FluNet, OpenDengue, ECDC CSVs
│   │   └── processed/            ← Output của mỗi session
│   └── weather/
│       ├── era5_raw/             ← NetCDF files ERA5 (2010–2019)
│       └── era5_weekly_2010_2019_final.csv
├── models/                       ← Model .pkl sau khi train
├── outputs/                      ← Plots, figures
└── KLTN_EpiWeather_ML.ipynb
```

### 1.3 Các hằng số đã chốt (KHÔNG thay đổi)
```python
TRAIN_START  = 2010       # Coverage ổn định từ đây
TRAIN_END    = 2019       # Tránh COVID disruption
COVID_YEARS  = [2020, 2021]
VAL_YEAR     = 2022       # Test generalization post-COVID
TARGET_FLU   = 'influenza_total'   # INF_A + INF_B (không dùng INF_ALL vì missing 44%)
TARGET_DENGUE = 'dengue_log'       # log1p(dengue_total) vì Brazil dominated 70%
LAG_FLU      = [1, 2, 3]          # tuần — incubation + reporting delay
LAG_DENGUE   = [6, 8, 10, 12, 14] # tuần — mosquito breeding cycle
ERA5_VARS    = 17                  # biến khí hậu (đủ theo lý thuyết hô hấp + vector-borne)
```

---

## 2. KIẾN TRÚC NOTEBOOK — 8 SESSIONS

Nguyên tắc: merge sớm nhất có thể → EDA trên master file → không EDA riêng lẻ.

```
SESSION 0  — SETUP & RESTART CELL       <- luôn chạy đầu tiên khi mở lại
SESSION 1  — LOAD RAW DATA & SANITY     <- check shape/dtypes/missing, nhanh
SESSION 2  — ERA5 PROCESS               <- nặng, chạy 1 lần, có idempotent guard
SESSION 3  — MERGE ALL -> master.csv    <- disease + weather, key: iso3 x ISO_WEEK
SESSION 4  — EDA TRÊN MASTER FILE       <- đây là EDA thật (trên dữ liệu tích hợp)
SESSION 5  — FEATURE ENGINEERING        <- lag, rolling, seasonal encoding
SESSION 6  — MODEL TRAINING & CV        <- 4 Regressors + 1 Classifier + Optuna
SESSION 7  — EVALUATION & EXPORT        <- validate 2022, so sánh, xuất .pkl
```

Tại sao merge trước EDA:
- EDA riêng lẻ không thấy được relationship weather <-> disease
- Thesis cần EDA trên dữ liệu tích hợp, không phải trên raw files
- Data đã download + process xong, không cần kiểm tra riêng lẻ nữa

SESSION INDEPENDENCE — MỖI SESSION TỰ LOAD TỪ DISK:
Mở lại Colab → chạy SESSION 0 → nhảy thẳng đến session cần làm.
Không cần chạy session 1-2-3... trước. Mỗi session bắt đầu bằng
restart cell đọc CSV từ Drive. Không phụ thuộc biến từ session trước.

---

## 3. PATTERN BẮT BUỘC

### 3.1 SESSION 0 — Restart Cell (QUAN TRỌNG NHẤT)

SESSION 0 là cell duy nhất cần chạy khi mở lại notebook sau khi tắt Colab.
Nó phải làm đủ 4 việc: (1) cài thư viện nếu thiếu, (2) mount Drive,
(3) import tất cả, (4) define tất cả paths + constants.

```python
# ════════════════════════════════════════════════════════════════
# SESSION 0 — SETUP & RESTART CELL
# Chạy cell này mỗi khi mở lại notebook. Không cần chạy lại SESSION khác
# vì data đã được lưu vào CSV trên Drive.
# ════════════════════════════════════════════════════════════════

# [0.1] Mount Google Drive
from google.colab import drive
drive.mount('/content/drive', force_remount=False)
print('✅ Drive mounted')

# [0.2] Cài thư viện còn thiếu (idempotent — pip tự bỏ qua nếu đã cài)
import subprocess, sys
PACKAGES = ['xgboost', 'lightgbm', 'optuna', 'prophet', 'shap',
            'cdsapi', 'netcdf4', 'xarray', 'scipy']
for pkg in PACKAGES:
    try:
        __import__(pkg.replace('-','_'))
    except ImportError:
        print(f'📦 Installing {pkg}...')
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', pkg, '-q'])
print('✅ Libraries OK')

# [0.3] Import tất cả thư viện
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from pathlib import Path
from sklearn.metrics import mean_absolute_error, mean_squared_error
import warnings
warnings.filterwarnings('ignore')

plt.rcParams['figure.figsize'] = (14, 5)
plt.rcParams['font.size'] = 12
sns.set_style('whitegrid')
print('✅ Imports OK')

# [0.4] Paths tập trung — TẤT CẢ paths đều khai báo ở đây, không khai báo lại ở session khác
BASE         = Path('/content/drive/MyDrive/KLTN')
RAW          = BASE / 'Dataset/epidemic/raw'
PROCESSED    = BASE / 'Dataset/epidemic/processed'
WEATHER_DIR  = BASE / 'Dataset/weather'
ERA5_RAW     = WEATHER_DIR / 'era5_raw'
ERA5_FILE    = WEATHER_DIR / 'era5_weekly_2010_2019_final.csv'
MASTER_FILE  = PROCESSED / 'master_weekly_2010_2019.csv'
MODELS_DIR   = BASE / 'models'
OUTPUTS_DIR  = BASE / 'outputs'

# Tạo thư mục output nếu chưa có
for d in [PROCESSED, MODELS_DIR, OUTPUTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# [0.5] Constants đã chốt
TRAIN_START   = 2010
TRAIN_END     = 2019
COVID_YEARS   = [2020, 2021]
VAL_YEAR      = 2022
TARGET_FLU    = 'influenza_total'
TARGET_DENGUE = 'dengue_log'       # log1p(dengue_total)
LAG_FLU       = [1, 2, 3]
LAG_DENGUE    = [6, 8, 10, 12, 14]

# Models to compare
MODELS_REGRESSION = ['Prophet', 'Naive', 'XGBoost', 'LightGBM', 'RandomForest']
MODELS_CLASSIFICATION = ['XGBClassifier']
OPTUNA_TRIALS = 60  # chỉ tune top 1-2 model

# [0.6] Kiểm tra files quan trọng
FILES = {
    'flunet'   : RAW / 'VIW_FNT.csv',
    'flu_meta' : RAW / 'VIW_FLU_METADATA.csv',
    'dengue'   : RAW / 'National_extract_V1_3.csv',
    'ecdc_sen' : RAW / 'sentinelTestsDetectionsPositivity.csv',
    'ecdc_ili' : RAW / 'ILIARIRates.csv',
    'era5'     : ERA5_FILE,
    'master'   : MASTER_FILE,
}
print('\nKiểm tra files:')
for name, path in FILES.items():
    status = '✅' if path.exists() else '⚠️  chưa có'
    print(f'  {status}  {name:12s} → {path.name}')
```

### 3.2 Idempotent Guard — Bắt buộc cho mọi bước xử lý nặng

```python
# ĐÚNG — luôn kiểm tra trước khi process
OUTPUT_FILE = PROCESSED / 'master_weekly_2010_2019.csv'

if OUTPUT_FILE.exists():
    print(f'✅ File đã có: {OUTPUT_FILE.name} — load từ disk, bỏ qua process')
    master = pd.read_csv(OUTPUT_FILE)
else:
    print('⏳ Chưa có — bắt đầu process...')
    master = _do_heavy_processing()
    master.to_csv(OUTPUT_FILE, index=False)
    print(f'💾 Saved {len(master):,} rows → {OUTPUT_FILE.name}')

print(f'Shape: {master.shape}')
```

### 3.3 Load từ disk ở đầu mỗi session (Session Restart Cell)

Mỗi session lớn bắt đầu bằng 1 cell load data từ disk.
Nhờ đó người dùng có thể chạy từ session bất kỳ sau khi restart.

```python
# ── RESTART: chạy cell này để load lại biến sau khi kernel restart ──
# Yêu cầu: SESSION 0 đã chạy (paths và imports đã có)
flu    = pd.read_csv(FILES['flunet'],  low_memory=False)
dengue = pd.read_csv(FILES['dengue'],  low_memory=False)
print(f'✅ FluNet {flu.shape} | Dengue {dengue.shape}')
```

---

## 4. FORMAT CELL — QUY TẮC VIẾT

### 4.1 Header Session (Markdown cell)
```markdown
---
# 🔬 SESSION X — TÊN SESSION
> **Mục tiêu:** Một câu mô tả mục tiêu của session này.
> **Input:** Đọc từ file nào
> **Output:** Ghi ra file nào (nếu có)
> **Có thể skip nếu:** Điều kiện nào cho phép bỏ qua
```

### 4.2 Header bước con (Markdown cell)
```markdown
## X.Y — Tên bước con
```

### 4.3 Code cell — Comment đầu cell BẮT BUỘC
```python
# [X.Y] Tên ngắn gọn — 1 dòng mô tả MỤC ĐÍCH
# Không phải mô tả "làm gì" mà mô tả "tại sao làm"
```

### 4.4 Format annotation sau mỗi code cell

Format chuẩn — viết như thuyết trình cho người mới:

---
**[x.x] Tên bước**

Mục đích: tại sao cần làm bước này.

Kết quả:
- Metric A = giá trị (so sánh: baseline = giá trị cũ, cải thiện x%)
- Metric B = giá trị (nhận xét: tốt/xấu so với literature)

Phân tích: giải thích ý nghĩa thực tế của kết quả.
Nếu có biểu đồ: mô tả rõ pattern — peak ở đâu, anomaly gì, trend gì.

Quyết định: dựa vào kết quả này, bước tiếp theo sẽ làm gì.
---

Quy tắc:
- Không dùng emoji, icon, hay symbol đặc biệt
- Không dùng heading # (giữ nhỏ hơn session header)
- Mỗi plot phải có lý do — không vẽ cho có
- Đọc biểu đồ kỹ: ghi rõ peak tại week/month nào, country nào outlier
- Ghi rõ best result hiện tại để so sánh khi cải thiện

### 4.5 Kết luận session (Markdown cell cuối mỗi session)

Dùng block "KET QUA SESSION X" theo format chuẩn trong CLAUDE.md
(không emoji, ghi đủ con số, files tạo ra, best result hiện tại).

---

## 5. CHI TIẾT TỪNG SESSION

### SESSION 0 — SETUP & RESTART CELL
Xem pattern đầy đủ ở mục 3.1. Không cần thêm gì.

---

### SESSION 1 — LOAD RAW DATA & SANITY
**Mục tiêu:** Load nhanh các file raw, sanity check shape/dtypes/missing.

Các bước con:
- `[1.1]` Load FluNet (VIW_FNT.csv) — shape, columns, năm, quốc gia
- `[1.2]` Load OpenDengue (National_extract_V1_3.csv) — parse date format mixed
- `[1.3]` Load ERA5 weekly nếu đã có
- `[1.4]` Sanity: số quốc gia, năm coverage, missing rate sơ bộ

**Quyết định đã chốt (không hỏi lại):**
- Bỏ `PARAINFLUENZA` vì missing >85%
- Bỏ `RSV_PROCESSED` vì corr=0.729 với `RSV` nhưng khác đơn vị
- Dùng `INF_A + INF_B` thay vì `INF_ALL` vì INF_ALL missing 44%
- `fillna(0)` cho INF_A, INF_B vì missing = không báo cáo ≠ 0 ca thực

---

### SESSION 2 — ERA5 PROCESS
**Mục tiêu:** Download ERA5 từ CDS API, chuyển NetCDF sang weekly CSV theo iso3.
**NẶNG — chạy 1 lần, có idempotent guard ở đầu.**

Các bước con:
- `[2.0]` Idempotent check — nếu `ERA5_FILE` đã tồn tại thì skip toàn session
- `[2.1]` Setup CDS API credentials (từ `~/.cdsapirc`)
- `[2.2]` Download ERA5 NetCDF từ CDS (17 biến, 2010–2019)
- `[2.3]` KD-tree spatial mapping: lưới ERA5 → iso3 centroid (Natural Earth 50m)
- `[2.4]` Aggregate theo ISO week → weekly mean/sum
- `[2.5]` Save ra `ERA5_FILE` (idempotent)

```python
# [2.0] Idempotent guard — phải ở ĐẦU session 2
if ERA5_FILE.exists():
    print(f'ERA5 đã có: {ERA5_FILE.name} ({ERA5_FILE.stat().st_size/1e6:.1f} MB)')
    print('   -> Bỏ qua toàn bộ SESSION 2 — chạy SESSION 3')
else:
    print('Chưa có ERA5 — bắt đầu download và process...')
    # ... code download ERA5 ...
```

---

### SESSION 3 — MERGE ALL -> master.csv
**Mục tiêu:** Chuẩn hóa các nguồn về cùng key `iso3 + ISO_YEAR + ISO_WEEK`,
merge → `master_weekly_v1.csv`.

Các bước con:
- `[3.0]` Idempotent check + load tất cả data từ disk
- `[3.1]` FluNet → chuẩn hóa: filter 2010–2019, tính `influenza_total = INF_A + INF_B`
- `[3.2]` OpenDengue → parse date, tính ISO week, group theo iso3+week, tính `dengue_log`
- `[3.3]` ERA5 → rename cols về merge key chung
- `[3.4]` Merge: FluNet ⋈ ERA5 ⋈ Dengue (LEFT JOIN — FluNet là anchor)
- `[3.5]` UK special case: gộp X09–X12 (WHO không có mã GBR tổng hợp)
- `[3.6]` Sanity check: shape, missing rate sau merge, số quốc gia
- `[3.7]` Save `master_weekly_v1.csv` (idempotent, versioned)

**Merge logic quan trọng:**
```python
master = flu_proc.merge(era5_proc, on=['iso3','ISO_YEAR','ISO_WEEK'], how='left')
master = master.merge(dengue_proc, on=['iso3','ISO_YEAR','ISO_WEEK'], how='left')
master['dengue_total'] = master['dengue_total'].fillna(0)
master['dengue_log']   = master['dengue_log'].fillna(0)
```

---

### SESSION 4 — EDA TRÊN MASTER FILE
Mục tiêu: Phân tích toàn diện trên dữ liệu đã tích hợp.
Input: master_weekly_2010_2019.csv
Output: Plots lưu vào OUTPUTS_DIR, kết luận lag times, quyết định features

Các bước con:
- [4.0] Restart cell: load master file từ disk
- [4.1] Coverage: heatmap country x year, bao nhiêu nước có data mỗi năm
- [4.2] Distribution: case counts + weather vars, histogram + boxplot
- [4.3] Seasonality decomposition (STL): flu global, dengue endemic countries
- [4.4] Correlation heatmap: weather vars x disease targets
- [4.5] CCF lag analysis: xác định lag time weather -> disease
        Influenza: temp/humidity/solar vs flu, lag 0-12 weeks
        Dengue: precip/temp vs dengue, lag 0-16 weeks
- [4.6] Top countries deep-dive: seasonal pattern, weather relationship
- [4.7] Kết luận: chốt lag windows, chốt important features

---

### SESSION 5 — FEATURE ENGINEERING
**Mục tiêu:** Tạo feature matrix đầu vào cho model từ master file.

Các bước con:
- `[5.0]` Load master file (restart cell)
- `[5.1]` Lag features bệnh: `influenza_total_lag{1,2,3}`, `dengue_log_lag{6,8,10,12,14}`
- `[5.2]` Rolling mean features: window 4 và 8 tuần (shift trước để tránh data leakage)
- `[5.3]` Seasonal encoding: `sin_week`, `cos_week`, `quarter`
- `[5.4]` Weather lag features: top 5 ERA5 vars với lag từ CCF analysis (SESSION 4)
- `[5.5]` Loại bỏ NaN do lag, verify không có data leakage
- `[5.6]` Save feature matrix: `features_flu_v1.csv` và `features_dengue_v1.csv`

**Chống data leakage:**
```python
# ĐÚNG: shift trước khi rolling
df_feat[f'flu_roll{w}'] = (
    df_feat.groupby('iso3')[TARGET_FLU]
    .transform(lambda x: x.shift(1).rolling(w).mean())
)
# SAI: x.rolling(w).mean() — dùng giá trị hiện tại (t) → leakage
```

---

### SESSION 6 — MODEL TRAINING & WALK-FORWARD CV
Mục tiêu: Train, so sánh, tune. Ra kết quả cuối cùng.

Walk-forward CV: 6 folds (val_year 2014-2019), expanding window.

Các bước con:
- [6.0] Restart cell: load feature matrix
- [6.1] Baseline: Prophet (global aggregate, seasonality benchmark)
- [6.2] Baseline: Naive same-week-last-year
- [6.3] XGBoost Regressor — walk-forward CV
- [6.4] LightGBM Regressor — walk-forward CV (cùng features, cùng scheme)
- [6.5] Random Forest Regressor — walk-forward CV
- [6.6] Bảng so sánh regression: RMSE, MAE, R² — chọn top 1-2
- [6.7] Optuna tuning cho top model(s): 60 trials, ghi before/after
- [6.8] Endemic channel label generation per (iso3, week_of_year)
- [6.9] XGBClassifier (multi:softprob) — walk-forward CV — macro-F1, AUC
- [6.10] Bảng tổng hợp: regression vs classification, chốt model cho production
- [6.11] KET QUA SESSION 6: block tổng kết (format chuẩn, xem CLAUDE.md)

Lưu ý:
- LightGBM cần pip install lightgbm trong SESSION 0
- Random Forest dùng sklearn, không cần cài thêm
- Optuna cần pip install optuna trong SESSION 0
- Mỗi model dùng CÙNG feature set, CÙNG CV folds — so sánh fair
- Mỗi model save .pkl với hậu tố version: xgb_flu_regressor_v1.pkl
- KHÔNG ghi đè file cũ — tạo version mới (v2, v3...) khi cải thiện
- Kèm theo mỗi .pkl phải có _features.json và _metrics.json

Restart cell cho SESSION 6:
```python
# [6.0] RESTART — Load feature matrix
# Yêu cầu: SESSION 0 đã chạy
flu_feat = pd.read_csv(PROCESSED / 'features_flu_v1.csv')
dengue_feat = pd.read_csv(PROCESSED / 'features_dengue_v1.csv')
FEATURE_COLS_FLU = [c for c in flu_feat.columns if c not in ['iso3','ISO_YEAR','ISO_WEEK', TARGET_FLU]]
FEATURE_COLS_DEN = [c for c in dengue_feat.columns if c not in ['iso3','ISO_YEAR','ISO_WEEK', TARGET_DENGUE]]
print(f'Flu features: {flu_feat.shape}, {len(FEATURE_COLS_FLU)} features')
print(f'Dengue features: {dengue_feat.shape}, {len(FEATURE_COLS_DEN)} features')
```

---

### SESSION 7 — EVALUATION & EXPORT
Mục tiêu: Validate trên 2022, so sánh tất cả approaches, xuất artifacts.

Các bước con:
- [7.0] Train final models trên toàn bộ 2010-2019 (dùng best hyperparams từ Optuna)
- [7.1] Validate regression trên 2022: RMSE, MAE, R² per model
- [7.2] Validate classification trên 2022: macro-F1, AUC, confusion matrix
- [7.3] Cross-compare: Regressor+threshold vs Classifier trực tiếp
        -> bảng so sánh F1: approach nào cho kết quả tốt hơn?
- [7.4] Feature importance: SHAP values cho best regression + classification model
- [7.5] Predicted vs Actual plots (2022): time series overlay
- [7.6] Endemic channel risk map: sample week visualization
- [7.7] Export artifacts (versioned, KHONG ghi de file cu):
        models/xgb_flu_regressor_vN.pkl (N = version cao nhat)
        models/xgb_flu_regressor_vN_features.json
        models/xgb_flu_regressor_vN_metrics.json
        models/xgb_flu_classifier_v1.pkl
        models/xgb_dengue_regressor_vN.pkl
        models/xgb_dengue_classifier_v1.pkl
        models/thresholds.json (endemic channel per iso3 x week)
- [7.8] Bang tong ket versions + metrics, model nao dung cho muc dich gi
- [7.9] KET QUA SESSION 7: block tong ket cuoi cung (best results, all files created)

Restart cell cho SESSION 7:
```python
# [7.0] RESTART — Load best models + validation data
# Yêu cầu: SESSION 0 đã chạy, SESSION 6 đã hoàn thành
import joblib
flu_feat = pd.read_csv(PROCESSED / 'features_flu_v1.csv')
# ... load model từ pkl nếu đã save ở SESSION 6
```

---

## 6. QUY TẮC CHẠY LẠI — PHÒNG NGỪA LỖI RESTART

### Bảng quyết định khi mở lại notebook

| Tình huống | Cần chạy |
|---|---|
| Mở lại sau khi tắt Colab | SESSION 0 (30 giây) + restart cell session đang làm |
| Muốn bắt đầu SESSION 6 | SESSION 0 → [6.0] load features → chạy tiếp |
| Muốn xem lại EDA | SESSION 0 → [4.0] load master → chạy tiếp |
| Thay đổi features | SESSION 5 trở đi |
| Thêm model mới | SESSION 6 trở đi |
| master.csv chưa có | SESSION 0 → SESSION 3 |
| ERA5 chưa có | SESSION 0 → SESSION 2 đầy đủ |

### Nguyên tắc không bị lỗi khi chạy lại

1. **Không dùng biến cross-session** — mỗi session khai báo lại biến nó cần từ disk
2. **Không import lại** — tất cả import nằm ở [0.3], sessions sau không import thêm
3. **Không redefine path** — tất cả path từ `BASE` ở [0.4], không hardcode trong cell
4. **Idempotent guard** ở mọi bước write file và process nặng
5. **Session restart cell** ở đầu mỗi session: 1 cell load data từ CSV

### Các lỗi thường gặp và cách tránh

```python
# ❌ SAI — biến từ session trước có thể không tồn tại sau restart
flu_train = flu[flu['ISO_YEAR'] >= 2010]  # 'flu' chưa được load

# ✅ ĐÚNG — mỗi session tự load từ disk
flu = pd.read_csv(FILES['flunet'], low_memory=False)  # [restart cell đầu session]
flu_train = flu[flu['ISO_YEAR'] >= 2010]

# ❌ SAI — path hardcode
era5 = pd.read_csv('/content/drive/MyDrive/KLTN/Dataset/weather/era5_weekly.csv')

# ✅ ĐÚNG — dùng constant từ SESSION 0
era5 = pd.read_csv(ERA5_FILE)

# ❌ SAI — install trong cell giữa chừng làm notebook lộn xộn
!pip install xgboost

# ✅ ĐÚNG — kiểm tra + install tập trung ở [0.2]
# (xem pattern ở SESSION 0)
```

---

## 7. QUY TẮC VIẾT ANNOTATION (MARKDOWN CELL)

### Nên viết gì trong annotation
- **Lý do kỹ thuật**: tại sao dùng approach này thay vì cách khác
- **Quyết định đã chốt**: con số, threshold, lựa chọn cụ thể và lý do
- **Cảnh báo kỹ thuật**: pitfalls, edge cases, data quirks cần biết
- **Kết quả mong đợi**: số lượng rows, countries, range giá trị hợp lý

### Không viết gì trong annotation
- Tóm tắt "code làm gì" — tên biến và comment trong code đã đủ
- Mô tả từng dòng code
- Hướng dẫn copy-paste hay chạy cell
- TODO hay task list (để trong chat, không trong notebook)

### Ví dụ annotation TỐT vs XẤU

```markdown
❌ XẤU:
📌 [4.2] Cell này tính influenza_total bằng cách cộng INF_A và INF_B,
sau đó fillna bằng 0.

✅ TỐT:
📌 **[4.2]** Dùng `INF_A + INF_B` thay vì `INF_ALL` vì INF_ALL missing 44% theo phân tích
[2.1]. `fillna(0)` ở đây không có nghĩa là "không có ca bệnh" mà là "quốc gia không báo cáo
tuần đó" — WHO FluNet cho phép quốc gia báo cáo gián đoạn. Nếu sau này cần phân biệt
"missing" vs "0 thật", cần thêm cột flag riêng.
```

---

## 8. WORKFLOW VỚI CLAUDE

```
1. Claude gửi 1 code cell trong chat (kèm comment [x.x])
2. Người dùng copy vào notebook → chạy
3. Paste output (text) hoặc chụp màn hình (nếu có plot) vào chat
4. Claude phân tích output → gửi markdown annotation cho cell đó
5. Người dùng thêm markdown cell vào notebook ngay dưới code cell
6. Claude gửi cell tiếp theo
```

**Claude KHÔNG:**
- Gửi nhiều cell một lúc rồi mới phân tích
- Viết annotation trước khi thấy kết quả thực tế (trừ khi kết quả đơn giản)
- Thay đổi các quyết định đã chốt trong bảng Decisions ở CLAUDE.md

**Claude NÊN:**
- Đặt câu hỏi khi output bất thường (ví dụ: shape khác kỳ vọng)
- Ghi chú rõ khi cell có thể chạy lâu (>5 phút)
- Đề xuất lưu plot ra `OUTPUTS_DIR` để có trong Drive sau khi Colab hết session

---

## 9. CẬP NHẬT NOTION

Sau mỗi session hoàn chỉnh:
- Update Master Notebook page với code và annotation đã confirm
- Nếu có quyết định kỹ thuật mới → update bảng Decisions trong CLAUDE.md
- Session summary (kết quả số liệu quan trọng) → tạo trang mới trong Notion

Notion pages:
- Master Notebook: `3463e0d7-9ba5-816f-9475-d1bfb6e94a5f`
- Đề cương: `3463e0d7-9ba5-8140-8fda-c2f646ec28f0`
- Pipeline Tasks DB: `c7aa3ba9-3ef9-44e2-8935-66b49796f295`
