# Chi tiết hệ thống EpiWeather — Dataset, DB, Backend, Frontend

> **Sinh viên:** Phạm Hữu Luân — MSSV 110122016 — DA22TTA
> **Đề tài:** Hệ thống cảnh báo nguy cơ dịch bệnh theo mùa dựa trên dữ liệu y tế và thời tiết toàn cầu
> **Mốc tài liệu:** 23/05/2026 — sau khi hoàn thành Phase A (sync realtime) + Phase C (multi-horizon) + Dengue nowcast extension
>
> Mục tiêu file này: GVHD đọc xong **biết hệ thống có gì, mỗi phần làm gì, kết nối với nhau ra sao**, không cần phải tự chạy code.

---

## Mục lục

1. [Tổng quan kiến trúc](#1-tổng-quan-kiến-trúc)
2. [Tầng Dataset — Dữ liệu thô](#2-tầng-dataset)
3. [Tầng Database — PostgreSQL 16 bảng](#3-tầng-database)
4. [Tầng Backend — FastAPI + ML Engine](#4-tầng-backend)
5. [Tầng Frontend — React Dashboard](#5-tầng-frontend)
6. [Tầng MLOps — Scheduler + Pipeline](#6-tầng-mlops)
7. [Bảng tham chiếu nhanh](#7-bảng-tham-chiếu-nhanh)

---

## 1. Tổng quan kiến trúc

```
┌──────────────────────────────────────────────────────────────────────┐
│  NGUỒN DỮ LIỆU (4 nguồn)                                             │
│   WHO FluNet (cúm)  ─────► Realtime API hàng tuần                    │
│   OpenDengue v1.3   ─────► Batch CSV (đến 2023-W36)                  │
│   ERA5 ECMWF        ─────► Historical 2010-2019 (training)           │
│   Open-Meteo Archive─────► Realtime 2020-now (nowcast)               │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│  ETL PIPELINE                                                        │
│   scripts/sync_flunet.py     — Pull FluNet weekly                    │
│   scripts/sync_weather.py    — Pull Open-Meteo weekly                │
│   scripts/feature_builder.py — Compute lag features → snapshot       │
│   scripts/batch_predict.py   — Run ML model → predictions            │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│  DATABASE — PostgreSQL kltn_epiweather (16 bảng, 31 partitions)      │
│   disease_cases (87K) · weather_observations (24K) ·                 │
│   feature_snapshots (75K) · predictions (75K) · countries (163) ·    │
│   model_versions · risk_thresholds · ...                             │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│  BACKEND — FastAPI (Python 3.11) :8000                               │
│   ml_engine: load .pkl, predict realtime                             │
│   8 API endpoints REST: /risk-map /forecast /predictions /analytics  │
│   APScheduler: 4 cron jobs auto-sync                                 │
└──────────────────────────────────────────────────────────────────────┘
                              │  REST JSON
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│  FRONTEND — React + TypeScript + Vite :5173                          │
│   HomePage    → World choropleth + sidebar alerts                    │
│   DiseaseDetail → 4-week forecast chart + 52-week trend              │
│   AnalyticsPage → Model performance + feature importance             │
└──────────────────────────────────────────────────────────────────────┘
```

**Triết lý thiết kế:** mỗi tầng **không phụ thuộc state của tầng cao hơn**:
- Frontend chỉ gọi REST API, không biết model nào đang chạy
- Backend chỉ đọc DB + load model, không biết notebook train ra sao
- ETL ghi DB qua schema cố định, không biết notebook hay backend tiêu thụ
- Notebook chạy độc lập trên Colab, export `.pkl` ra ml_models/

→ Có thể thay tầng nào cũng được mà không vỡ tầng khác.

---

## 2. Tầng Dataset

### 2.1 WHO FluNet — Cúm mùa

| Đặc tính | Giá trị |
|---|---|
| Nguồn | https://app.powerbi.com/view (WHO Global Influenza Programme) |
| Định dạng | CSV export, 1 row = 1 (country, ISO_WEEK) |
| Số dòng raw | 183,000 (toàn thời gian 1995–nay) |
| Filter training | 2010–2019 → 113,000 rows, 189 nước |
| Cột target | `INF_A + INF_B` (subtype A + B) |
| Cột bỏ | `INF_ALL` (missing 44%), `PARAINFLUENZA` (missing 85.5%) |
| Realtime API | `scripts/sync_flunet.py` — pull từ 2024 đến hiện tại |

**Quyết định khoa học:**
- Loại 2020–2021 khỏi training: NPI (giãn cách + đeo khẩu trang) làm flu giảm ~99% giả tạo (không phải do data missing — 2020-2021 vẫn 166-167 nước báo cáo, ngang 2019). Train trên data 2020 sẽ làm model học sai pattern bình thường.
- UK gộp X09–X12: WHO không có mã GBR tổng hợp, mỗi nation con của UK báo cáo riêng.

### 2.2 OpenDengue v1.3 — Sốt xuất huyết

| Đặc tính | Giá trị |
|---|---|
| Nguồn | Clarke et al 2024 Scientific Data, https://opendengue.org |
| Định dạng | CSV global extract |
| Số dòng | 18,000 weekly rows |
| Phạm vi | 82 quốc gia chủ yếu nhiệt đới |
| Brazil dominate | 71% tổng ca toàn cầu → cần log1p transform |
| Training | 2015–2019 (5 năm) — period coverage ổn định nhất |
| Nowcast | 2021–2023-W36 — có ground truth nhưng release batch, không realtime API |
| Loại 2020 | COVID disruption làm dropping case report toàn cầu |

**Tại sao OpenDengue mà không nguồn khác:**
- WHO chưa có dataset dengue global standardized
- Bộ Y tế VN không có API public
- OpenDengue đã merge từ PAHO, MOH các nước, peer-reviewed publish → academic trustworthy

### 2.3 ERA5 — Khí hậu reanalysis (2010-2019)

| Đặc tính | Giá trị |
|---|---|
| Nguồn | ECMWF Copernicus Climate Data Store (CDS) |
| Định dạng | NetCDF, 6.2 GB cho 2010-2019 |
| Lưới spatial | 0.25° × 0.25° → **721 × 1440 = 1,038,240 điểm/timestep** |
| Tần suất raw | Hourly → aggregate weekly (mean/sum theo biến) |
| Số biến | **17 biến khí hậu** (xem 2.5) |
| Mapping → quốc gia | **KD-tree** theo centroid (lat, lon) của country, k=4 nearest grid points |
| Output | `era5_weekly_2010_2019_final.csv` — 197 nước × 522 tuần × 17 biến |

**Tại sao KD-tree centroid (k=4):**
- Đơn giản hơn point-in-polygon, đủ chính xác cho country-level grain
- k=4 vì 1 centroid có thể nằm gần biên giới → trung bình 4 điểm để smooth
- Quốc gia nhỏ (Singapore) hay quốc gia lớn (Russia) đều dùng cùng method → consistent

### 2.4 Open-Meteo Archive — Khí hậu realtime (2020+)

| Đặc tính | Giá trị |
|---|---|
| Nguồn | https://archive-api.open-meteo.com — ERA5 reanalysis underneath, free |
| Format | JSON daily, aggregate weekly trong sync script |
| API key | Không cần (rate limit ~10/min, đã handle qua `--sleep 3.0`) |
| Phạm vi sync hiện tại | 56 dengue countries × 2020-2023 = 4 năm |
| Phạm vi flu | 163 countries × 2024-2026 (1.5 năm warmup + realtime) |
| Realtime job | `scripts/sync_weather.py --weeks-back 12` (daily 6h ICT) |

**Tại sao Open-Meteo Archive thay vì OpenWeatherMap:**
- OWM Historical đắt ($1000+/year cho 10 năm), Open-Meteo free
- Open-Meteo dùng cùng ERA5 reanalysis → consistent với training data
- API stable, không cần auth

### 2.5 Danh sách 17 biến khí hậu (ERA5)

| Mã biến | Đơn vị | Lý do dùng |
|---|---|---|
| `t2m` | K | Nhiệt độ 2m — chính cho cả flu (cold dry) và dengue (warm wet) |
| `d2m` | K | Dewpoint 2m — proxy humidity cho flu transmission |
| `r2_humidity_pct` | % | Relative humidity — mosquito breeding |
| `tp` | mm | Total precipitation — mosquito breeding sites |
| `ssrd` | W/m² | Solar radiation downward — UV inactivation virus |
| `sp` | hPa | Surface pressure — health risk indicator |
| `u10`, `v10` | m/s | Wind components — disease vector dispersion |
| `tcc` | 0-1 | Total cloud cover |
| `tcw`, `tcwv` | mm | Total column water — humidity columnar |
| `lai_lv`, `lai_hv` | m²/m² | Leaf area index (low/high veg) — vector habitat |
| `swvl1`, `swvl2` | m³/m³ | Soil water content — breeding sites stability |
| `skt` | K | Skin temperature — ground heating |
| `e` | mm | Evaporation |

Sau CCF analysis (Session 6), chỉ giữ subset có signal mạnh nhất cho mỗi disease (xem 4.4).

---

## 3. Tầng Database

### 3.1 Tổng quan 16 bảng

| # | Bảng | Rows hiện tại | Vai trò |
|---|---|---|---|
| 1 | `countries` | **163** | Master ISO3, tên, region, lat/lon, population |
| 2 | `diseases` | **2** | flu (id=1) + dengue (id=2) |
| 3 | `data_sources` | **6** | FluNet, PAHO, ERA5, OWM, OpenMeteo, ECDC |
| 4 | `weather_variables` | **18** | 17 ERA5 + 1 derived (humidity_pct) |
| 5 | `disease_cases` | **87,668** | Số ca tuần — partition by `iso_year` |
| 6 | `weather_observations` | **23,603** | Realtime weather Open-Meteo — partition by `iso_year` |
| 7 | `feature_configs` | **28** | Định nghĩa 16 flu features + 12 dengue features (metadata) |
| 8 | `feature_snapshots` | **75,202** | Vector features pre-computed (JSONB), model đọc trực tiếp |
| 9 | `model_versions` | **2** | LGBM flu v1 + RF dengue v1 (hyperparams + artifact path) |
| 10 | `model_evaluations` | **2** | R², RMSE, F1, n_samples |
| 11 | `risk_thresholds` | **164** | Quantile q33/q67 per (disease, iso3) → Low/Med/High |
| 12 | `predictions` | **74,983** | Dự báo lưu sẵn — partition by `iso_year` |
| 13 | `pipeline_runs` | 0 | Tracking pipeline execution (schema ready, chưa dùng) |
| 14 | `pipeline_run_logs` | 0 | Log chi tiết từng step của pipeline |
| 15 | `data_quality_checks` | 0 | Tracking DQ (chưa dùng) |
| 16 | `api_request_logs` | 0 | Audit log (chưa enable middleware) |

**Tổng physical:** 16 logic + 31 partitions = 47 tables.

### 3.2 Chi tiết bảng "máu" của hệ thống

#### `disease_cases` — Dữ liệu nguồn

```sql
CREATE TABLE disease_cases (
    disease_id    SMALLINT REFERENCES diseases(id),
    iso3          CHAR(3)  REFERENCES countries(iso3),
    source_id     SMALLINT REFERENCES data_sources(id),
    iso_year      SMALLINT,
    iso_week      SMALLINT,
    raw_count     INTEGER,
    transformed_value DOUBLE PRECISION, -- log1p(raw_count) đã pre-compute
    PRIMARY KEY (disease_id, iso3, iso_year, iso_week, source_id)
) PARTITION BY RANGE (iso_year);
```

Partitions hiện có: `disease_cases_2010` … `disease_cases_2022`, `disease_cases_default`.

**Tại sao partition theo năm:** queries thường filter theo year range. Partition pruning giảm scan từ 87K rows → ~6K rows/năm.

#### `feature_snapshots` — Cache features

```sql
CREATE TABLE feature_snapshots (
    disease_id      SMALLINT,
    iso3            CHAR(3),
    iso_year        SMALLINT,
    iso_week        SMALLINT,
    feature_version VARCHAR(10),       -- 'v1'
    features        JSONB,             -- {"flu_log_lag1": 4.32, ...}
    PRIMARY KEY (disease_id, iso3, iso_year, iso_week, feature_version)
);
```

**Tại sao JSONB:** flu có 16 cột, dengue 15 cột — schema khác nhau. JSONB cho phép 1 bảng chung. Backend predict load features về dict → feed vào model.predict() trực tiếp.

**Coverage:**
- Flu: 105–141 countries × 52 weeks × 10 years (2010-2019) + 163 × 20 weeks (2026 realtime) = ~58,468 rows
- Dengue: 19–29 countries × 52 weeks × 5 years (2015-2019) + 56 × 52 × 3 + 56 × 36 weeks 2023 = ~13,734 rows

#### `predictions` — Output ML

```sql
CREATE TABLE predictions (
    disease_id        SMALLINT,
    iso3              CHAR(3),
    iso_year          SMALLINT,
    iso_week          SMALLINT,
    horizon_weeks     SMALLINT,        -- 1, 2, 3, 4
    predicted_value   DOUBLE PRECISION, -- log scale
    predicted_cases   DOUBLE PRECISION, -- expm1(predicted_value)
    risk_level        VARCHAR(10),      -- 'Low'|'Medium'|'High' (XGBClassifier.argmax)
    risk_probability  DOUBLE PRECISION, -- P(High) 0..1 từ classifier — FE × 100 = severity score
    risk_q33          DOUBLE PRECISION, -- legacy: threshold low/med (regressor approach, không còn dùng)
    risk_q67          DOUBLE PRECISION, -- legacy
    model_version_id  SMALLINT,
    PRIMARY KEY (disease_id, iso3, iso_year, iso_week, horizon_weeks, model_version_id)
) PARTITION BY RANGE (iso_year);
```

**Coverage hiện tại:**

| disease | iso_year | Weeks | Countries | Total rows |
|---|---|---|---|---|
| flu | 2010-2019 | 52 (44 cho 2010) | 107-147 | ~57,800 |
| flu | 2026 | 20 (W02-W21) | 163 | 3,260 |
| dengue | 2010-2019 | 38-52 | 8-33 | ~6,120 |
| dengue | 2021-2022 | 52 | 56 | 5,824 |
| dengue | 2023 | 36 (cutoff OpenDengue) | 56 | 2,016 |

#### `risk_thresholds` — Phân loại Low/Med/High

```sql
CREATE TABLE risk_thresholds (
    disease_id SMALLINT,
    iso3       CHAR(3),
    q33        DOUBLE PRECISION,  -- 33th percentile log1p(cases) trong 2010-2019
    q67        DOUBLE PRECISION,  -- 67th percentile
    PRIMARY KEY (disease_id, iso3)
);
```

**Logic phân loại:** `predicted_value < q33 → Low; q33 ≤ x < q67 → Medium; x ≥ q67 → High`.

Mỗi quốc gia có ngưỡng riêng vì baseline khác nhau (Brazil 8000 ca/tuần khác Singapore 50 ca/tuần).

### 3.3 Sơ đồ quan hệ tóm tắt

```
countries (163)             diseases (2)              data_sources (6)
    │ iso3                      │ id                       │ id
    │                           │                          │
    └────┬──────────────────────┴─────┬────────────────────┘
         │                            │
    ┌────▼──────────────┐      ┌──────▼─────────────┐    weather_observations
    │ disease_cases     │      │ feature_snapshots  │    (iso3,year,week,JSONB)
    │ (raw + log1p)     │      │ (JSONB features)   │
    └────┬──────────────┘      └──────┬─────────────┘
         │                            │
         │     ┌──────────────────────┘
         │     │
    ┌────▼─────▼──────────┐         model_versions (2)
    │ predictions          │◄──────  model_evaluations (2)
    │ (h=1..4, risk_level) │         risk_thresholds (164)
    └──────────────────────┘

  pipeline_runs (0) ──────< pipeline_run_logs (0)
```

---

## 4. Tầng Backend

### 4.1 Tech stack

| Layer | Tech | Lý do |
|---|---|---|
| Framework | FastAPI 0.115 | Auto OpenAPI docs, async native, type hints |
| ORM | SQLAlchemy 2.0 | Type-safe, declarative models |
| Migration | Alembic | Versioning schema thay đổi |
| ML serving | LightGBM + RF + XGBoost từ `.pkl` joblib | Pre-trained, load 1 lần vào memory |
| Scheduler | APScheduler 3.x AsyncIO | Cron-style jobs trong process FastAPI |
| Logging | Loguru | Cấu hình ngắn, output đẹp |
| Validation | Pydantic v2 | Request/Response schema |

### 4.2 Cấu trúc thư mục

```
backend/app/
├── main.py                  # Entry point, FastAPI app + lifespan
├── core/config.py           # Settings (env vars, paths)
├── api/v1/
│   ├── api.py               # Router aggregator
│   └── endpoints/           # 8 endpoint files (xem 4.3)
├── crud/                    # SQL queries (per-table)
│   ├── countries.py
│   ├── diseases.py
│   ├── predictions.py
│   └── ...
├── services/                # Business logic
│   ├── ml_engine.py         # Load & predict
│   ├── feature_lookup.py    # Query feature_snapshots
│   ├── prediction_service.py
│   ├── risk_service.py
│   ├── analytics_service.py
│   ├── forecast_service.py  # Multi-horizon h=1..4
│   └── scheduler.py         # APScheduler config
├── models/                  # SQLAlchemy ORM classes
├── schemas/                 # Pydantic request/response
└── db/session.py            # Engine + session factory
```

### 4.3 Danh sách 8 API endpoints chính

| Method | Path | Vai trò | Service |
|---|---|---|---|
| GET | `/api/v1/risk-map/{disease}/latest` | Choropleth map mặc định, auto pick latest week | risk_service |
| GET | `/api/v1/risk-map/{disease}?year=&week=` | Choropleth tuần cụ thể | risk_service |
| GET | `/api/v1/predictions/{disease}/{iso3}?year=&week=` | Prediction 1 quốc gia 1 tuần | prediction_service |
| GET | `/api/v1/predictions/{disease}/{iso3}/history?start_year=&end_year=` | History 52 tuần cho chart trend | prediction_service |
| GET | `/api/v1/forecast/{disease}/{iso3}?year=&week=` | 4-week forecast h=1..4 (input cụ thể) | forecast_service |
| GET | `/api/v1/forecast/{disease}/{iso3}/nowcast` | 4-week forecast từ tuần realtime mới nhất | forecast_service |
| GET | `/api/v1/forecast/{disease}/available` | Danh sách country có data nowcast | forecast_service |
| GET | `/api/v1/analytics/summary` | Stats cho dashboard (total countries, regions...) | analytics_service |
| GET | `/api/v1/analytics/model-performance/{disease}` | CV metrics 6 folds | analytics_service |
| GET | `/api/v1/analytics/feature-importance/{disease}` | Top 10 features by gain | analytics_service |
| GET | `/api/v1/countries` / `/{iso3}` | Master country list | countries crud |
| GET | `/api/v1/diseases` | Master disease list | diseases crud |
| GET | `/api/v1/weather/variables` | Master weather var definitions | weather crud |
| POST | `/api/v1/infer` | Ad-hoc inference (feature vector → prediction) | ml_engine |
| GET | `/api/v1/admin/scheduler/status` | APScheduler job status | scheduler |
| POST | `/api/v1/admin/sync/{job_id}` | Manual trigger sync job | scheduler |

### 4.4 ML Engine — `app/services/ml_engine.py`

**Models load vào memory khi startup:**

| Model | File | R² (CV mean) |
|---|---|---|
| flu regressor h=1 | `lgbm_flu_regressor_h1_v1.pkl` | 0.866 |
| flu regressor h=2 | `lgbm_flu_regressor_h2_v1.pkl` | 0.829 |
| flu regressor h=3 | `lgbm_flu_regressor_h3_v1.pkl` | 0.793 |
| flu regressor h=4 | `lgbm_flu_regressor_h4_v1.pkl` | 0.757 |
| dengue regressor h=1 | `rf_dengue_regressor_h1_v1.pkl` | 0.929 |
| dengue regressor h=2 | `rf_dengue_regressor_h2_v1.pkl` | 0.919 |
| dengue regressor h=3 | `rf_dengue_regressor_h3_v1.pkl` | 0.909 |
| dengue regressor h=4 | `rf_dengue_regressor_h4_v1.pkl` | 0.898 |
| flu classifier | `xgb_flu_classifier_v1.pkl` | F1=0.542 |
| dengue classifier | `xgb_dengue_classifier_v1.pkl` | F1=0.475 |

**Predict flow:**
```
GET /forecast/dengue/BRA/nowcast
  → forecast_service.get_nowcast(db, "dengue", "BRA")
  → feature_lookup.get_latest_available_week(...) → (2023, 36)
  → feature_lookup.get_features(...) → {"deng_log_lag6": 8.4, ...}
  → for h in [1,2,3,4]:
      ml_engine.predict_horizon("dengue", h, features)
        → reg_dengue_h.predict([feature_vector])
        → expm1(log_predicted) → predicted_cases
  → feature_lookup.build_data_coverage(...) → DataCoverage{warning, is_nowcast}
  → ForecastResponse{points=[ForecastPoint × 4], data_coverage}
```

**Feature mapping:**

Flu 16 features (max lag=7):
```
flu_log_lag1, flu_log_lag2, flu_log_lag3,
flu_log_rollmean4, flu_log_rollmean8,
temp_c_lag3, temp_c_lag7,
humidity_pct_lag1, humidity_pct_lag7,
solar_wm2_lag7, dewpoint_c_lag1,
iso_week_sin, iso_week_cos, iso_year,
HEMISPHERE_NH, HEMISPHERE_SH
```

Dengue 15 features (max lag=16):
```
deng_log_lag6, deng_log_lag8, deng_log_lag10, deng_log_lag12, deng_log_lag14,
deng_log_rollmean4, deng_log_rollmean8,
temp_c_lag11, dewpoint_c_lag8, precip_mm_lag6,
humidity_pct_lag1, solar_wm2_lag16,
iso_week_sin, iso_week_cos, iso_year
```

### 4.5 Schema response chính

**`ForecastResponse`** (endpoint /forecast):

```json
{
  "disease": "dengue",
  "iso3": "BRA",
  "as_of_iso_year": 2023,
  "as_of_iso_week": 36,
  "points": [
    {"horizon": 1, "target_iso_year": 2023, "target_iso_week": 37,
     "predicted_log": 9.08, "predicted_cases": 8820,
     "r2_cv": 0.929, "rmse_cv": 0.84, "model_version": "dengue_h1_v1"},
    {"horizon": 2, ..., "predicted_cases": 8210, ...},
    {"horizon": 3, ..., "predicted_cases": 7950, ...},
    {"horizon": 4, ..., "predicted_cases": 7100, ...}
  ],
  "data_coverage": {
    "in_training_period": false,
    "is_nowcast": true,
    "snapshot_years": [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023],
    "training_years": [2015, 2016, 2017, 2018, 2019],
    "warning": "Năm 2023 là giai đoạn nowcast dengue (OpenDengue v1.3, đến 2023-W36)..."
  }
}
```

**`RiskMapResponse`** (endpoint /risk-map):

```json
{
  "disease": "flu",
  "iso_year": 2026,
  "iso_week": 21,
  "count": 163,
  "items": [
    {"iso3": "CHN", "country_name": "China",
     "latitude": 35.86, "longitude": 104.19, "who_region": "WPR",
     "predicted_cases": 1081, "risk_level": "High",
     "risk_probability": 0.84,
     "risk_q33": null, "risk_q67": null},
    ...
  ]
}
```

### 4.6 Risk score — cách tính

Mỗi quốc gia trên bản đồ hiển thị **2 thông tin rủi ro tách biệt**:

| Thông tin | Nguồn | Ý nghĩa |
|---|---|---|
| `risk_level` ∈ {Low, Medium, High} | `argmax(classifier.predict_proba(X))` | Class thắng — quyết định **màu** trên choropleth |
| `risk_probability` ∈ [0, 1] | `proba[2]` = P(High) trực tiếp từ classifier | Cường độ rủi ro liên tục — FE × 100 = **severity score 0-100** |

**Lý do dùng P(High) thay vì P(class thắng):**
- Score phải có nghĩa là "mức độ nghiêm trọng", không phải "độ tự tin của model".
- Nước Low với p_low=0.99 → score = 99 (sai về nghĩa, mặc dù model rất confident).
- Nước Low với p_high=0.05 → score = 5 (đúng: rủi ro thấp).
- Nước High với p_high=0.84 → score = 84 (đúng: rủi ro cao và model tin chắc).

**Verified semantic trên DB:**

| risk_level | avg score | n countries |
|---|---|---|
| High | 57.6 | 56 |
| Medium | 17.6 | 43 |
| Low | 9.1 | 120 |

→ Score tăng đơn điệu theo class, đúng dịch tễ.

**KHÔNG dùng hardcode score nữa.** Trước đây FE từng map `{high: 68, medium: 42, low: 18}` cứng, không gắn với output model — đã xóa kể từ migration `a1b2c3d4e5f6_add_risk_probability_to_predictions`.

`risk_q33`/`risk_q67` là **legacy fields** từ approach cũ (quantile threshold trên regressor output) — đã bỏ kể từ khi chuyển hẳn sang classifier. Schema giữ lại NULL để backward-compat.

---

## 5. Tầng Frontend

### 5.1 Tech stack

| Layer | Tech | Lý do |
|---|---|---|
| Framework | React 18 + TypeScript | Type-safe, component reusable |
| Build tool | Vite | Fast HMR, < 1s reload |
| Routing | React Router 6 | Nested routes |
| State global | Zustand | Lightweight (~1KB), persist support |
| State server | TanStack Query | Cache, refetch, loading states |
| HTTP | Axios | Interceptors, baseURL config |
| Map | ECharts (GeoJSON world) | Free, performant, choropleth native |
| Charts | ECharts (LineChart, BarChart) | Cùng lib với map → bundle nhỏ |
| Styling | Tailwind CSS + CSS vars | Dark theme via `:root` vars |

### 5.2 Cấu trúc thư mục

```
frontend/src/
├── main.tsx                  # Entry, QueryClient + Router
├── App.tsx                   # Layout: TopNav + Outlet
├── pages/
│   ├── HomePage.tsx          # Map + sidebar (route /)
│   ├── DiseaseDetailPage.tsx # Detail country (route /detail/:iso3)
│   └── AnalyticsPage.tsx     # Model performance (route /analytics)
├── components/
│   ├── layout/TopNav.tsx
│   ├── map/
│   │   ├── WorldMap.tsx      # ECharts choropleth
│   │   └── MapLegend.tsx
│   ├── sidebar/
│   │   ├── RiskMapSidebar.tsx
│   │   ├── DiseaseTabs.tsx   # Flu / Dengue
│   │   ├── WeekPicker.tsx    # Disease-aware picker
│   │   ├── RegionFilter.tsx  # WHO regions filter
│   │   └── SummaryStats.tsx
│   ├── alerts/
│   │   ├── AlertsSidebar.tsx # Right panel (High/Med countries)
│   │   ├── AlertItem.tsx
│   │   └── Sparkline.tsx
│   ├── detail/
│   │   └── ForecastChart.tsx # 4-week + 52-week trend
│   └── common/
├── api/                      # Axios clients per resource
│   ├── axios.ts
│   ├── countries.ts
│   ├── diseases.ts
│   ├── forecast.ts
│   ├── predictions.ts
│   └── infer.ts
├── hooks/                    # TanStack Query hooks
│   ├── useRiskMap.ts
│   ├── useForecast.ts        # useNowcast() + useForecast(year, week)
│   ├── usePrediction.ts      # usePrediction() + useHistory()
│   ├── useCountries.ts
│   └── useAnalytics.ts
├── store/
│   └── uiStore.ts            # Zustand: disease, year, week, regions, selectedIso3
├── types/
│   ├── api.ts                # ForecastResponse, RiskMapItem, HistoryPoint, ...
│   └── domain.ts             # DiseaseId, RiskLevel
└── constants.ts              # DISEASES, RISK_LEVELS, WHO_REGIONS
```

### 5.3 3 trang chính — luồng UX

#### Page 1: HomePage — Bản đồ risk thế giới

```
[TopNav: EpiWeather | Home · Analytics]
┌──────────────────┬─────────────────────────────────┬─────────────────┐
│ LEFT SIDEBAR     │                                 │ RIGHT ALERTS    │
│                  │   World Choropleth Map          │                 │
│ Disease Tabs     │   (ECharts world GeoJSON)       │ Top 10 High     │
│ [Flu] [Dengue]   │                                 │ Risk Countries  │
│                  │   Risk levels:                  │                 │
│ Week Picker      │   ● High    ● Med    ● Low      │ Sparkline 12wk  │
│ Year:[2026]      │                                 │                 │
│ Week:[21]        │                                 │                 │
│ [Apply]          │   Hover country → tooltip:      │                 │
│                  │   ISO3, predicted_cases, risk   │                 │
│ Region Filter    │   Click country → DetailPage    │                 │
│ [WPR][AFR][...]  │                                 │                 │
│                  │                                 │                 │
│ Summary Stats    │   Legend (bottom right):        │                 │
│ Total: 163       │   Color scale by predicted      │                 │
│ High: 23         │                                 │                 │
└──────────────────┴─────────────────────────────────┴─────────────────┘
```

**Disease-aware behavior:**
- Click `Flu` tab → load `/risk-map/flu/latest` → map render 163 nước, 2026-W21
- Click `Dengue` tab → reset year=2023 week=36 selectedIso3=null → load `/risk-map/dengue/latest` → map render 56 nước, 2023-W36
- Region filter: toggle WHO_REGIONS (AFR, AMR, EMR, EUR, SEAR, WPR) → filter map items

#### Page 2: DiseaseDetailPage — Chi tiết quốc gia

```
[← Back to map]    Country Name (e.g., Brazil)   [Risk Badge: High]
                   Dengue · W36 · 2023

┌──────────────────────────────────────────────────────────────────┐
│ 4-week Forecast · Dengue   ● realtime / ● historical             │
│ As of W36/2023 → W37-W40/2023                                    │
│ [Year][Week][Go]     Historical 2010-2019 hoặc Nowcast 2021-W36  │
│                                                                  │
│ ⚠ Năm 2023 là giai đoạn nowcast dengue (OpenDengue v1.3...)      │
│                                                                  │
│   [ECharts line chart: 4 horizons với confidence interval]       │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│ 52-week Trend · Dengue                                           │
│   [Area chart: cases over time, smooth, gradient fill]           │
└──────────────────────────────────────────────────────────────────┘

┌──────────────┬──────────────┬──────────────┐
│ Predicted    │ Risk Level   │ Disease      │
│ 8,820        │ High         │ DENV         │
└──────────────┴──────────────┴──────────────┘

┌──────────────────────────────────────────────────────────────────┐
│ Top Climate Drivers (feature importance)                         │
│   [TODO: hook /analytics/feature-importance]                     │
└──────────────────────────────────────────────────────────────────┘
```

**API calls:**
- `useNowcast(disease, iso3)` → `/forecast/{disease}/{iso3}/nowcast` (latest realtime)
- `useForecast(disease, iso3, year, week)` → khi user pick historical year/week
- `useHistory(disease, iso3, 2010, 2019)` → 52-week trend
- `usePrediction(disease, iso3, year, week)` → risk badge

#### Page 3: AnalyticsPage — Model performance

```
Model Performance Comparison

┌──────────────────────────────────────────────────────────────────┐
│ Multi-horizon R² Cross-Validation                                │
│   [Bar chart] h=1 h=2 h=3 h=4 cho cả flu + dengue                │
│   Flu (LGBM):    0.866 → 0.829 → 0.793 → 0.757                   │
│   Dengue (RF):   0.929 → 0.919 → 0.909 → 0.898                   │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│ Feature Importance · {Flu | Dengue}                              │
│   [Horizontal bar chart top 10 features]                         │
│   AR features dominate ~90%, weather ~5%                         │
└──────────────────────────────────────────────────────────────────┘
```

### 5.4 State management — Zustand store

```typescript
// store/uiStore.ts
type UIState = {
  disease: DiseaseId;          // 'flu' | 'dengue'
  year: number;                // 2026 (flu) hoặc 2023 (dengue) default
  week: number;                // 21 (flu) hoặc 36 (dengue) default
  regions: WhoRegion[];        // filter [], [] = tất cả
  selectedIso3: string | null; // country đã click trên map

  setDisease: (d: DiseaseId) => void;  // RESET year/week/selectedIso3
  setYear: (y: number) => void;
  setWeek: (w: number) => void;
  setRegions: (rs: WhoRegion[]) => void;
  setSelectedIso3: (iso3: string | null) => void;
};
```

**DISEASE_DEFAULTS** per-disease (sau session 23/05):
```typescript
{
  flu:    { year: 2026, week: 21 },   // latest realtime
  dengue: { year: 2023, week: 36 },   // OpenDengue cutoff
}
```

### 5.5 Data fetching — TanStack Query

| Hook | Endpoint | Cache key |
|---|---|---|
| `useRiskMap(disease, year, week)` | `/risk-map/{disease}?year=&week=` | `['risk-map', disease, year, week]` |
| `useNowcast(disease, iso3)` | `/forecast/{disease}/{iso3}/nowcast` | `['nowcast', disease, iso3]` |
| `useForecast(disease, iso3, y, w)` | `/forecast/{disease}/{iso3}?year=&week=` | `['forecast', disease, iso3, y, w]` |
| `usePrediction(disease, iso3, y, w)` | `/predictions/{disease}/{iso3}?year=&week=` | `['prediction', ...]` |
| `useHistory(disease, iso3, sy, ey)` | `/predictions/{disease}/{iso3}/history` | `['history', ...]` |
| `useAnalytics()` | `/analytics/summary` | `['analytics']` |

**Stale time**: 5 phút (data update hằng tuần, không cần refresh nhiều).

---

## 6. Tầng MLOps

### 6.1 APScheduler — 4 cron jobs

| Job ID | Schedule (ICT) | Script | Mục đích |
|---|---|---|---|
| `sync_flunet` | Thứ Hai 10:00 | `sync_flunet.py --from-year 2024` | Pull WHO FluNet weekly |
| `sync_weather` | Hằng ngày 6:00 | `sync_weather.py --weeks-back 12` | Pull Open-Meteo 12 tuần |
| `build_features` | Thứ Hai 11:00 | `feature_builder.py --disease flu --from-year {cur}` + `--disease dengue` | Rebuild snapshots năm hiện tại |
| `batch_predict` | Thứ Hai 11:30 | `batch_predict.py` | Predict latest week → predictions table |

**Manual triggers** (qua admin endpoint):
- `POST /admin/sync/sync_flunet` — trigger ngay
- `POST /admin/sync/build_features_dengue_nowcast` — đặc biệt: rebuild dengue 2020-2023 sau khi load OpenDengue batch release mới

### 6.2 Sync workflow tổng thể

```
Monday 06:00 ICT — daily weather already running last 6 days
                   sync_weather.py pulls Open-Meteo W21 data → weather_observations

Monday 10:00 ICT — sync_flunet.py
                   GET WHO FluNet 2024-now → diff with disease_cases → UPSERT new rows
                   163 countries × 1 week = 163 new rows typical

Monday 11:00 ICT — build_features (cả 2 bệnh)
                   feature_builder reads disease_cases + weather_observations
                   computes 16 flu features + 15 dengue features → UPSERT feature_snapshots
                   ~163 + 56 = 219 new rows

Monday 11:30 ICT — batch_predict
                   load 10 models → for each disease:
                     fetch latest snapshots from DB
                     predict h=1 (regressor) + risk (classifier)
                     UPSERT predictions
                   → frontend /risk-map/{disease}/latest returns new week
```

### 6.3 Pipeline error handling

- Subprocess timeout 1800s (30 phút) cho mỗi script
- Failed job log lưu stdout_tail + stderr_tail (500 chars) qua Loguru
- Admin endpoint trả 500 nếu returncode != 0 — user gọi `/admin/scheduler/status` để xem job lần cuối thành công khi nào

### 6.4 Audit trail vào DB — `pipeline_runs` (Phase 1, 25/05/2026)

Mỗi pipeline run được persist vào bảng `pipeline_runs` qua context manager `track_run()` ở [`scripts/_pipeline_logger.py`](scripts/_pipeline_logger.py). Hoạt động độc lập với FastAPI — script tự kết nối Postgres qua psycopg2.

**Pattern dùng trong scripts:**

```python
from _pipeline_logger import track_run

with track_run("sync_flunet", trigger_type="scheduled") as stats:
    # ...do work...
    stats["rows_processed"] = 29575
    stats["rows_inserted"] = 17384
# Tự động UPDATE status='success', completed_at=NOW() khi block thoát
# Nếu exception → status='failed', errors = JSON traceback, re-raise
```

**Columns được populate:**

| Column | Nguồn |
|---|---|
| `run_id` | UUID auto-gen |
| `pipeline_name` | sync_flunet / sync_weather / build_features_flu / build_features_dengue / batch_predict |
| `trigger_type` | manual / scheduled / api / event (qua CLI flag `--trigger`) |
| `status` | running → success / failed / partial |
| `started_at` | NOW() khi enter |
| `completed_at` | NOW() khi exit |
| `duration_sec` | GENERATED column: EPOCH(completed_at - started_at) |
| `rows_processed`, `rows_inserted`, `rows_updated`, `rows_skipped` | Script tự update vào stats dict |
| `errors` | JSONB array: traceback + per-iso3 errors |
| `metadata` | JSONB: args runtime (from_year, dry_run, ...) |

**Query mẫu cho dashboard MLOps:**

```sql
-- Latest 10 runs
SELECT pipeline_name, trigger_type, status, started_at, duration_sec, rows_inserted
FROM pipeline_runs
ORDER BY started_at DESC LIMIT 10;

-- Success rate per pipeline last 7 days
SELECT pipeline_name,
       COUNT(*) FILTER (WHERE status='success') * 100.0 / COUNT(*) AS success_pct,
       AVG(duration_sec) FILTER (WHERE status='success') AS avg_dur_sec
FROM pipeline_runs
WHERE started_at >= NOW() - INTERVAL '7 days'
GROUP BY 1;
```

### 6.5 Cron — Windows Task Scheduler (production)

APScheduler trong FastAPI process chỉ chạy khi backend uvicorn alive. Để pipeline tiếp tục chạy **kể cả khi backend down**, đăng ký Task Scheduler ở Windows:

```powershell
# Mở PowerShell as Administrator
cd F:\BAO_CAO\DO_AN_TOT_NGHIEP\KLTN
.\scripts\setup_windows_task.ps1
```

Task `EpiWatch-DailyPipeline`:
- Schedule: hằng ngày **00:00 ICT**
- Account: SYSTEM (chạy 24/7 không cần user login)
- Command: `cmd /c "python.exe scripts/run_daily_pipeline.py >> logs/daily_pipeline_<date>.log 2>&1"`
- Settings: timeout 2h, retry 2 lần cách 10 phút, start when available (catch up nếu miss)
- Master script `run_daily_pipeline.py` chain 5 jobs với `--trigger scheduled` → mỗi job tự log vào `pipeline_runs`

**Alternative không cần admin:** `setup_windows_task_user.ps1` (user-level, chỉ chạy khi user logged in).

Verify task chạy:

```powershell
Get-ScheduledTaskInfo -TaskName "EpiWatch-DailyPipeline"
```

```sql
-- Audit trail từ DB
SELECT * FROM pipeline_runs
WHERE trigger_type='scheduled'
  AND started_at >= CURRENT_DATE
ORDER BY started_at DESC;
```

---

## 7. Bảng tham chiếu nhanh

### 7.1 Số liệu khoa học

| Metric | Flu | Dengue |
|---|---|---|
| Train years | 2010-2019 (skip 2020-2021) | 2015-2019 |
| Train countries | 143 | 35 |
| Realtime/nowcast | 2026-W02 → W21 (163 countries) | 2021-2023-W36 (56 countries) |
| R² h=1 (CV) | **0.866** (LightGBM) | **0.929** (Random Forest) |
| R² h=4 (CV) | 0.757 | 0.898 |
| Classifier macro-F1 | 0.542 | 0.475 |
| Features | 16 (max lag 7w) | 15 (max lag 16w) |
| Best params | Optuna 60 trials | Optuna 60 trials |

### 7.2 Endpoints quick reference

| URL | Trả về |
|---|---|
| `GET /api/v1/risk-map/flu/latest` | Map 163 nước, 2026-W21 |
| `GET /api/v1/risk-map/dengue/latest` | Map 56 nước, 2023-W36 |
| `GET /api/v1/forecast/dengue/BRA/nowcast` | 4-week forecast Brazil dengue từ W36/2023 |
| `GET /api/v1/predictions/flu/VNM/history?start_year=2010&end_year=2019` | 52-week trend Vietnam flu |
| `GET /api/v1/analytics/summary` | Stats tổng dashboard |
| `POST /api/v1/admin/sync/sync_flunet` | Trigger pull WHO data manual |
| `GET /docs` | OpenAPI Swagger UI (FastAPI auto) |

### 7.3 Frontend routes

| Path | Component |
|---|---|
| `/` | HomePage — world risk map |
| `/detail/:iso3` | DiseaseDetailPage — country detail |
| `/analytics` | AnalyticsPage — model metrics |

### 7.4 File quan trọng để demo / debug

| File | Khi nào mở |
|---|---|
| `KLTN_EpiWeather_ML_v6.ipynb` | Khi GVHD hỏi về training, CV folds, feature importance |
| `docs/presentation/kich_ban_thuyet_trinh.md` | Trước khi thuyết trình — học thuộc câu mở đầu |
| `docs/presentation/session_*.md` | Khi GVHD đào sâu từng phần |
| `docs/session_summaries/2026-05-23_session_summary.md` | Update tiến độ gần nhất |
| `ml_models/*_metrics.json` | Khi GVHD hỏi "model này train ra sao" |
| `backend/app/services/ml_engine.py` | Khi GVHD hỏi "predict realtime hoạt động ra sao" |
| `frontend/src/store/uiStore.ts` | Khi GVHD hỏi "switch disease state ra sao" |

### 7.5 Lệnh chạy hệ thống local

```powershell
# Terminal 1 — Backend
cd backend
.\.venv\Scripts\uvicorn.exe app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 — Frontend
cd frontend
npm run dev   # http://localhost:5173

# Postgres: assume running on localhost:5432
# Database: kltn_epiweather, user: postgres, pass: 111111111

# Optional — trigger sync manual
curl -X POST http://localhost:8000/api/v1/admin/sync/sync_flunet
```

---

**Tóm tắt 1 câu cho thầy cô:**

> "Hệ thống là một pipeline ML production-grade end-to-end: 4 nguồn dữ liệu → ETL ghi vào PostgreSQL có partition → 10 model multi-horizon (LightGBM flu + RandomForest dengue + XGBoost classifier) serve qua FastAPI với APScheduler tự động sync hàng tuần → React dashboard cho phép user xem bản đồ choropleth toàn cầu, click vào quốc gia thấy forecast 4 tuần, và analytics page so sánh model performance."
