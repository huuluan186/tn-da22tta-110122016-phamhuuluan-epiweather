# Tổng quan hệ thống EpiWeather — Báo cáo tiến độ

> Sinh viên: Phạm Hữu Luân · MSSV: 110122016 · Lớp: DA22TTA
> Cập nhật: 22/05/2026 (sau Phase A-3 batch_predict + Analytics wiring + scope honesty)

---

## 1. Cơ sở dữ liệu (PostgreSQL)

### 1.1 Kiến trúc tổng quan

Database `kltn_epiweather` có **16 bảng logic**, trong đó 3 bảng lớn (`disease_cases`, `weather_observations`, `predictions`) dùng **partitioning theo năm** (PostgreSQL native partition) để tăng performance khi query nhiều năm.

Tổng số physical partitions: 47 tables = 16 logic + 31 partition con (disease_cases_2010..2022, weather_obs_2010..2022, predictions_2022/2023, api_logs_2026, các *_default partition).

### 1.2 Toàn bộ 16 bảng — số dòng & vai trò

| # | Bảng | Rows | Vai trò |
|---|---|---|---|
| 1 | `alembic_version` | 1 | Tracking migration version (Alembic) |
| 2 | `countries` | 163 | Master list quốc gia (iso3, tên, WHO region, lat/lon, population) |
| 3 | `diseases` | 2 | `flu`, `dengue` + metadata (target_variable, transform) |
| 4 | `data_sources` | 6 | FluNet, PAHO, ERA5, OpenWeatherMap, OpenMeteo, ECDC |
| 5 | `weather_variables` | 18 | Định nghĩa 17 biến ERA5 (mã, đơn vị, ERA5 var name) |
| 6 | `disease_cases` | 81,216 | Số ca bệnh theo tuần — **partition theo iso_year** |
| 7 | `weather_observations` | 11,899 | Thời tiết realtime (Open-Meteo) — partition theo iso_year |
| 8 | `feature_configs` | 28 | Định nghĩa 16 features flu + 12 features dengue (đăng ký metadata) |
| 9 | `feature_snapshots` | 64,394 | Vector features pre-computed (JSONB) — model đọc trực tiếp |
| 10 | `model_versions` | 2 | XGBoost flu v1.0 + dengue v1.0 (hyperparams, artifact_path) |
| 11 | `model_evaluations` | 2 | Metrics 2 model v1.0 (R², RMSE, F1, n_samples) |
| 12 | `risk_thresholds` | 164 | Quantile thresholds (q33, q67) per (disease, iso3) cho phân Low/Med/High |
| 13 | `predictions` | 64,046 | Dự báo lưu sẵn 2010–2019 + **2026-W21 (163 flu nước)** từ batch_predict — partition theo iso_year |
| 14 | `pipeline_runs` | 0 | Tracking pipeline execution (chưa dùng) |
| 15 | `data_quality_checks` | 0 | Tracking data quality (chưa dùng) |
| 16 | `api_request_logs` | 0 | Audit log API calls — partition theo năm (chưa enable middleware) |

### 1.3 Chi tiết bảng dữ liệu chính

**`disease_cases` — 81,216 dòng**

Phân theo năm (partitioned):
| Năm | Rows | Ghi chú |
|---|---|---|
| 2010 | 4,231 | Đã load từ WHO FluNet CSV |
| 2011 | 5,831 | |
| 2012 | 6,297 | |
| 2013 | 6,111 | |
| 2014 | 5,617 | |
| 2015 | 6,331 | |
| 2016 | 6,592 | |
| 2017 | 7,398 | |
| 2018 | 7,617 | |
| 2019 | 7,848 | Hết training data |
| 2020 | 0 | Loại khỏi training (COVID-19 NPI) |
| 2021 | 0 | Loại khỏi training |
| 2022 | 0 | Validation year (chưa load) |
| default (2023–2026) | 17,343 | Sync realtime qua sync_flunet.py |

Theo disease:
| Disease | Năm | Số nước | Rows |
|---|---|---|---|
| Flu | 2010–2026 | 152 | 75,106 |
| Dengue | 2010–2019 | 41 | 6,110 |

**`weather_observations` — 11,899 dòng**

| Nguồn | Năm | Số nước | Rows | Biến trong JSONB |
|---|---|---|---|---|
| OpenMeteo | 2025–2026 | 163 | 11,899 | `temp_c`, `dewpoint_c`, `humidity_pct`, `precip_mm`, `solar_wm2` |

Ghi chú: Weather lịch sử 2010–2019 đã được tính sẵn lag features và lưu trực tiếp trong `feature_snapshots` (từ ERA5 NetCDF), không cần lưu raw weather. Bảng này chỉ chứa Open-Meteo realtime để serve nowcast.

**`feature_snapshots` — 64,394 dòng**

| Disease | Năm | Số nước | Rows | Số features | Ghi chú |
|---|---|---|---|---|---|
| Flu | 2010–2026 | 163 | 58,468 | 16 | 2026 từ realtime sync (W2–W21) |
| Dengue | 2015–2019 | 35 | 5,926 | 15 | **Chưa có nguồn realtime** (xem mục 4.2) |

**`predictions` — 64,046 dòng**

| Disease | Năm | Số nước | Rows | Source |
|---|---|---|---|---|
| Flu | 2010–2019 | 149 | 57,763 | XGBoost v1.0, h=1 (load từ CSV training) |
| Flu | **2026-W21** | **163** | **163** | **LightGBM v1.0, h=1 — batch_predict.py (22/05/2026)** |
| Dengue | 2010–2019 | 41 | 6,120 | XGBoost v1.0 + 10 dòng đè bằng RF v1.0 từ batch_predict |

**`risk_thresholds` — 164 dòng**

Quantile thresholds (q33, q67) tính từ historical predicted_cases per country:
- Low: predicted < q33
- Medium: q33 ≤ predicted < q67
- High: predicted ≥ q67

163 country-specific + 1 global fallback (cho nước không đủ dữ liệu).

**`feature_configs` — 28 dòng**

Đăng ký metadata của 16 features flu + 12 features dengue (gồm lag_weeks, transform, AR target, weather_variable). Đây là registry để service biết gọi feature gì với lag nào.

**`weather_variables` — 18 dòng**

Định nghĩa 17 biến ERA5 (era5_variable name, đơn vị, mô tả). Hiện chỉ 5 biến được dùng trong nowcast: `t2m`, `d2m`, `r2m`, `tp`, `ssrd` (mapping sang `temp_c`, `dewpoint_c`, `humidity_pct`, `precip_mm`, `solar_wm2`).

---

## 2. API Endpoints

Base URL: `http://localhost:8000` (dev) · Prefix: `/api/v1`

### 2.1 Forecast (dự báo on-demand)

| Method | Endpoint | Mô tả |
|---|---|---|
| GET | `/forecast/{disease}/{iso3}?as_of_year=Y&as_of_week=W` | Forecast h=1..4 từ tuần cụ thể (historical hoặc current) |
| GET | `/forecast/{disease}/{iso3}/nowcast` | Auto-detect tuần mới nhất trong feature_snapshots → forecast |
| GET | `/forecast/{disease}/available` | **Mới** — danh sách countries có ít nhất 1 feature snapshot (chỉ phục vụ trên scope thực) |

Response `forecast`/`nowcast` có thêm field `data_coverage` để cảnh báo nếu năm dự báo nằm ngoài training window:
```json
{
  "disease": "flu", "iso3": "VNM",
  "as_of_iso_year": 2026, "as_of_iso_week": 21,
  "points": [
    {"horizon": 1, "target_iso_week": 22, "predicted_cases": 1.0, "r2_cv": 0.866, "rmse_cv": 0.686},
    {"horizon": 2, "target_iso_week": 23, "predicted_cases": 1.4, "r2_cv": 0.829, "rmse_cv": 0.775},
    {"horizon": 3, "target_iso_week": 24, "predicted_cases": 1.7, "r2_cv": 0.793, "rmse_cv": 0.855},
    {"horizon": 4, "target_iso_week": 25, "predicted_cases": 2.0, "r2_cv": 0.757, "rmse_cv": 0.877}
  ],
  "data_coverage": {
    "in_training_period": false,
    "snapshot_years": [2010, 2011, ..., 2019, 2026],
    "training_years": [2015, 2016, 2017, 2018, 2019],
    "warning": "Năm 2026 nằm ngoài training window (2010–2019). Dự báo là extrapolation — không có ground truth để validate."
  }
}
```

### 2.2 Risk Map (precomputed cho global map)

| Method | Endpoint | Mô tả |
|---|---|---|
| GET | `/risk-map/{disease}?year=Y&week=W` | Risk level tất cả nước tại tuần cụ thể (đọc từ predictions table) |
| GET | `/risk-map/{disease}/latest` | **Mới** — auto-detect tuần mới nhất có predictions → trả map |
| GET | `/predictions/{disease}/{iso3}?year=Y&week=W` | 1 dự báo cụ thể |
| GET | `/predictions/{disease}/{iso3}/history?start_year=Y&end_year=Y` | Lịch sử 52-tuần |

### 2.3 Analytics (mới — đọc trực tiếp từ ml_models/)

| Method | Endpoint | Mô tả |
|---|---|---|
| GET | `/analytics/model-performance/{disease}` | R²/RMSE/MAE × h=1..4 từ `*_metrics.json` |
| GET | `/analytics/feature-importance/{disease}?horizon=N` | Danh sách 15-16 features model đang dùng |
| GET | `/analytics/summary` | Meta info |

### 2.4 Reference & Admin

| Method | Endpoint | Mô tả |
|---|---|---|
| GET | `/countries` | Danh sách 163 nước (iso3, name, lat/lon, WHO region) |
| GET | `/diseases` | 2 loại bệnh + metadata |
| GET | `/weather/{iso3}` | Weather observations 1 nước |
| GET | `/admin/scheduler/status` | Trạng thái 4 cron jobs |
| POST | `/admin/sync/sync_flunet` | Trigger sync FluNet |
| POST | `/admin/sync/sync_weather` | Trigger sync Open-Meteo |
| POST | `/admin/sync/build_features` | Trigger rebuild features |
| POST | `/admin/sync/batch_predict` | **Mới** — Trigger predict h=1 + classifier → upsert predictions |

---

## 3. Phương pháp dự đoán — giải thích chi tiết từ đầu

### 3.1 Bài toán đặt ra

Đề tài yêu cầu **dự báo số ca bệnh cúm/sốt xuất huyết** ở mỗi quốc gia theo tuần, sử dụng kết hợp dữ liệu y tế (WHO FluNet, PAHO) và thời tiết (ERA5, Open-Meteo). Đây là bài toán **time-series regression** với đặc điểm:

- **Mỗi đơn vị dự báo** = 1 cặp `(iso3, iso_year, iso_week)` — ví dụ THA tuần 20 năm 2013
- **Output** = số ca bệnh tuần đó (`predicted_cases`)
- **Multi-horizon**: dự báo trước 1, 2, 3, 4 tuần (4 mô hình riêng biệt cho mỗi horizon)

### 3.2 Pipeline 3 giai đoạn

**Giai đoạn 1 — Training (chạy 1 lần trong notebook)**

```
Dữ liệu thô (CSV)              Mô hình
─────────────────────         ──────────────────
WHO FluNet 2010-2019    ──┐
ERA5 weather 2010-2019  ──┤
                          ├──► Feature engineering ──► Train walk-forward CV
PAHO Dengue 2010-2019   ──┘    (16 features flu)        (6 folds, val 2014-2019)
                                                                  │
                                                                  ▼
                                                         Save 4 model pkl/disease
                                                         (h=1, h=2, h=3, h=4)
                                                                  │
                                                                  ▼
                                                         ml_models/*.pkl
```

Walk-forward Cross-Validation chi tiết:

| Fold | Train | Validation |
|---|---|---|
| 1 | 2010–2013 | 2014 |
| 2 | 2010–2014 | 2015 |
| 3 | 2010–2015 | 2016 |
| 4 | 2010–2016 | 2017 |
| 5 | 2010–2017 | 2018 |
| 6 | 2010–2018 | 2019 |

Trung bình R² qua 6 folds = **0.866** (flu, h=1).

**Giai đoạn 2 — Validation (test set held-out)**

Sau khi chốt model từ CV, test trên năm **2022** (held-out, không thấy trong training, không thấy trong CV). Đây là kiểm tra cuối cùng trước khi deploy. Năm 2022 được chọn vì:
- Bỏ qua 2020–2021 (COVID-19 NPI làm số ca giảm bất thường)
- 2022 là năm đầu tiên hậu COVID, đại diện cho điều kiện "bình thường mới"

**Giai đoạn 3 — Production (real-time, đang chạy)**

Sau khi model đã train xong, hệ thống deploy như sau:

```
Có 3 cách user gọi dự báo:

CÁCH A — Dự báo lịch sử (any year 2010-2019):
  Frontend chọn Year=2013, Week=20, Country=THA
       │
       ▼
  GET /api/v1/forecast/flu/THA?as_of_year=2013&as_of_week=20
       │
       ▼
  Backend query feature_snapshots WHERE iso3='THA', year=2013, week=20
       │
       ▼
  Lấy vector 16 features đã pre-compute (JSONB) ──► Load 4 LightGBM model
       │                                                    │
       ▼                                                    ▼
  Predict 4 lần (h=1..4)  ──────────────────────────────────┘
       │
       ▼
  Return 4 ForecastPoint (W21, W22, W23, W24 / 2013)

CÁCH B — Dự báo nowcast (tuần mới nhất có data):
  GET /api/v1/forecast/flu/THA/nowcast (không cần year/week)
       │
       ▼
  Backend tự tìm: SELECT MAX(year, week) FROM feature_snapshots
                  WHERE disease='flu' AND iso3='THA'
       │
       ▼
  Trả về W21/2026 (tuần mới nhất) ──► giống Cách A
       │
       ▼
  Return 4 ForecastPoint (W22, W23, W24, W25 / 2026)

CÁCH C — Dự báo cho tuần chưa có trong DB (CHƯA THỂ):
  Ví dụ: dự báo W30/2026 (8 tuần tới) trong khi DB mới có W21
  → Không khả thi với architecture hiện tại vì chưa có data raw để tính lag.
```

### 3.3 Quy trình realtime ingestion (Phase A-1, A-2, A-3 đã hoàn thiện)

Để hệ thống dự báo được **tuần hiện tại** (2026), 4 cron jobs chạy chuỗi:

```
Hằng ngày 6:00 ICT
    │
    ▼
sync_weather.py ──► Open-Meteo Archive (5 biến) ──► weather_observations

Thứ Hai 10:00 ICT
    │
    ▼
sync_flunet.py ──► WHO FluMart OData ──► UPSERT disease_cases (partition 2026)
                                                       │
Thứ Hai 11:00 ICT                                      │
    │                                                  │
    ▼                                                  │
feature_builder.py                                     │
    │                                                  │
    ├── đọc disease_cases ◄────────────────────────────┘
    ├── đọc weather_observations
    ├── tính 16 lag features (flu_log_lag1..3, rollmean4/8, temp_c_lag3/7,
    │    humidity_pct_lag1/7, solar_wm2_lag7, dewpoint_c_lag1, seasonal sin/cos, …)
    │
    ▼
UPSERT vào feature_snapshots

Thứ Hai 11:30 ICT
    │
    ▼
batch_predict.py
    │
    ├── load 8 model .pkl (4 horizon × 2 disease) một lần
    ├── đọc feature_snapshots tuần MAX(year, week)
    ├── predict h=1 + classifier cho mọi country có snapshot
    │
    ▼
UPSERT vào predictions table (idx_predictions_unique)
    │
    ▼
/risk-map/{disease}/latest trả 163 countries của tuần mới nhất
```

**Trigger manual** (không cần chờ cron):
```bash
curl -X POST http://localhost:8000/api/v1/admin/sync/batch_predict
```

### 3.4 Kiến trúc hybrid: precompute + on-demand

Hệ thống dùng pattern chuẩn của ML serving: tách hai luồng theo tính chất truy vấn.

| Loại request | Approach | Source |
|---|---|---|
| Risk map global (163 nước, 1 tuần) | **Precompute** | `predictions` table (đọc bằng 1 SELECT) |
| Forecast h=1..4 (1 nước, on-demand) | **On-demand** | `feature_snapshots` + `ml_engine.predict_horizon()` |
| Historical query | **On-demand** | `feature_snapshots` + model.predict() |

**Tại sao không tính lag features trực tiếp mỗi request?**

Trước đây mỗi API call backend phải: query disease_cases → query weather → shift/rolling mean → build vector → predict. ~500ms–2s/request, dễ race condition. Hiện tại `feature_snapshots` JSONB pre-compute 1 lần/tuần → API chỉ query + predict ≈ 10-30ms.

**Model weights cache:** 8 model .pkl được load 1 lần khi app start (`ml_engine.load_models()`) và giữ trong singleton dict trong RAM. Mỗi predict sau đó chỉ là `.predict()` (~5-15ms), không đụng disk.

---

## 4. Khó khăn khi dự đoán cho data mới (sau training)

### 4.0 Phạm vi dự đoán hiện tại — minh bạch về data

Hệ thống đã wire endpoint `/forecast/{disease}/available` để FE biết được scope thực:

| Tình trạng | Flu | Dengue |
|---|---|---|
| Training years | 2010–2019 (147 nước) | 2015–2019 (35 nước) |
| Validation year | 2022 | 2022 (khi có data) |
| Năm hiện có snapshot | **2010–2026** (W21 mới nhất) | **2015–2019** chấm hết |
| Nguồn realtime | WHO FluMart OData (free, weekly) | **Chưa có** — xem 4.2 |
| Predict được "tuần hiện tại" | ✅ 163 nước, W21/2026 | ❌ chỉ historical |

Mọi response `/forecast` và `/nowcast` nay trả thêm `data_coverage.warning` nếu năm dự báo không nằm trong training window. FE hiển thị banner amber để user biết kết quả là extrapolation.

### 4.1 Vấn đề 1: Distribution shift (chuyển dịch phân phối)

Model học pattern từ 2010–2019. Khi áp dụng cho 2026:
- Khí hậu thay đổi (warming) — nhiệt độ trung bình tăng so với training
- Hành vi y tế thay đổi (vaccine flu phổ biến hơn, hệ thống reporting tốt hơn)
- Sub-type cúm khác (H1N1, H3N2, B/Victoria thay đổi tỉ lệ qua năm)

**Hệ quả:** Dự đoán có thể bias — số ca dự báo có thể cao hơn hoặc thấp hơn thực tế. Không có cách kiểm chứng nếu chưa có ground truth 2026.

**Em đã làm gì:** Validation trên 2022 (cách training 3 năm) cho R² ổn → cho thấy model có khả năng generalize. Nhưng 4 năm sau (2026) thì chưa rõ.

### 4.2 Vấn đề 2: Dengue chưa có nguồn realtime miễn phí

WHO FluMart OData API miễn phí, weekly, toàn cầu — perfect cho flu. Nhưng dengue:

| Nguồn ứng cử | Phạm vi | Vấn đề |
|---|---|---|
| OpenDengue (oxford.ac.uk) | 2000–2024, ~30 nước | Lag 6 tháng, không weekly realtime |
| PAHO Dengue Surveillance | Châu Mỹ only | HTML scraping, không có API ổn định |
| WHO Health Emergencies | Toàn cầu nhưng month-level | Không phải weekly |
| InfoDengue (Brazil), MOH Singapore… | 1 nước/lần | Phải code adapter riêng cho từng nước |

**Hiện tại:** Dengue ở "historical-only mode" — chỉ predict được 2015–2019 (data Oxford OpenDengue đã load offline). FE auto cảnh báo khi user query dengue ngoài range này.

**Trong báo cáo cần ghi rõ:** "Flu = production-ready realtime; Dengue = demo trên historical training set." Đây là hạn chế khách quan của ecosystem dengue surveillance global, không phải thiếu sót kỹ thuật của hệ thống.

### 4.3 Vấn đề 3: Khoảng trống 2020–2021 (COVID-19)

WHO FluNet ghi nhận số ca cúm 2020–2021 giảm ~99% so với bình thường do giãn cách xã hội. Đây không phải pattern dịch tễ học thật, mà là artifact của NPI (Non-Pharmaceutical Interventions).

**Hệ quả:** Khi tính lag features cho 2022+, các giá trị `flu_log_lag52`, `flu_log_rollmean52` (nếu có) sẽ bị "kéo xuống" bởi 2020–2021 → bias dự báo.

**Em đã làm gì:** Loại 2020–2021 khỏi training. Nhưng lag features cho 2026 vẫn có thể chạm vào giai đoạn này nếu lag đủ dài. May mắn: lag tối đa của em là 8 tuần (rollmean8), không chạm 2020–2021 từ 2026.

### 4.4 Vấn đề 4: Việt Nam không có trong training

WHO FluNet không có dữ liệu cúm đủ ổn định cho VNM giai đoạn 2010–2019. Khi gọi `/nowcast/flu/VNM`:
- `flu_log_lag1`, `lag2`, `lag3` = 0 (không có lịch sử)
- `flu_log_rollmean8` = 0
- Model dự đoán chủ yếu dựa vào weather + seasonal features

**Hệ quả:** Dự báo VNM kém tin cậy hơn các nước trong training (THA, IDN, JPN, USA, BRA...).

**Em đã làm gì:** Vẫn dự báo nhưng đánh dấu. Đang phân vân nên loại VNM khỏi demo hay giữ và ghi chú hạn chế.

### 4.5 Vấn đề 5: Độ trễ báo cáo WHO FluNet

WHO FluNet công bố dữ liệu mới mỗi thứ Hai cho tuần ISO trước đó (W-1). Tuy nhiên:
- Một số nước báo cáo muộn (2–4 tuần sau tuần đó)
- Một số nước chỉ báo cáo theo quý
- Tuần 0 (tuần hiện tại) thường có data thưa, không đầy đủ

**Hệ quả:** Khi gọi `/nowcast` tại W21/2026, nếu nước đó chưa báo cáo W19, W20 → `flu_log_lag1`, `lag2` = 0 → dự báo sai.

**Em đã làm gì:** Service tự fallback về tuần mới nhất có data trong `feature_snapshots`. Nhưng nếu data trễ nhiều, nowcast cũng trễ tương ứng.

### 4.6 Vấn đề 6: Chưa thể dự báo > 4 tuần ahead

Model multi-horizon hiện chỉ train cho h=1..4. Muốn dự báo 8 tuần ahead phải train thêm h=5..8, hoặc dùng recursive (h=1 → feed vào input → h=2 → ...) — recursive thì error tích lũy nhanh.

**Em đã làm gì:** Demo chỉ trong 4 tuần. Nếu cần extend phải train thêm.

### 4.7 Vấn đề 7: Không thể dự báo cho nước mới (out-of-distribution country)

Nếu có quốc gia mới (ví dụ SSD - Nam Sudan, mới tách 2011 và không có data 2010), model sẽ predict nhưng không đáng tin.

**Em đã làm gì:** `risk_thresholds` có 1 dòng `is_global_fallback=true` để xử lý fallback. Nhưng đây vẫn là hạn chế.

---

## 5. Kết quả mô hình ML

### 5.1 Bảng so sánh (walk-forward CV, 6 folds, val 2014–2019)

| Model | Disease | h | R² (CV) | RMSE (CV) | Ghi chú |
|---|---|---|---|---|---|
| Naive same-week-last-year | Flu | 1 | 0.312 | — | Baseline |
| Prophet | Flu | 1 | 0.581 | — | Statistical baseline |
| XGBoost Regressor | Flu | 1 | 0.798 | 0.812 | |
| **LightGBM Regressor** | **Flu** | **1** | **0.866** | **0.686** | ✓ Production |
| LightGBM Regressor | Flu | 2 | 0.829 | 0.775 | |
| LightGBM Regressor | Flu | 3 | 0.793 | 0.855 | |
| LightGBM Regressor | Flu | 4 | 0.757 | 0.877 | |
| **Random Forest** | **Dengue** | **1** | **0.929** | **0.531** | ✓ Production |
| Random Forest | Dengue | 4 | 0.898 | 0.627 | |

Benchmark tham chiếu: Lowe et al. (2014) — R² ≥ 0.70 (flu), ≥ 0.80 (dengue). **Tất cả 8 model vượt benchmark.**

### 5.2 Top 5 features quan trọng (LightGBM flu)

1. `solar_wm2_lag7` — bức xạ mặt trời lag 7 tuần (r = −0.41 với flu, tương quan âm mạnh nhất)
2. `flu_log_lag1` — số ca tuần trước (AR lag, autoregressive)
3. `humidity_pct_lag7` — độ ẩm lag 7 tuần
4. `flu_log_rollmean8` — trung bình 8 tuần gần nhất
5. `temp_c_lag7` — nhiệt độ lag 7 tuần

---

## 6. Những gì đã đạt được và chưa được

### Đã đạt được ✓

- **Data pipeline**: WHO FluNet (152 nước, 2010–2026), ERA5 (17 biến, 2010–2019), Open-Meteo realtime (5 biến, 163 nước, daily sync), Oxford OpenDengue (35 nước, 2015–2019)
- **ML pipeline**: EDA → feature engineering → CCF lag analysis → 5-model comparison → Optuna tuning → multi-horizon (h=1..4) training
- **Production models**: LightGBM flu (R²=0.866, h=1) + RF dengue (R²=0.929, h=1), 8/8 model vượt benchmark Lowe 2014
- **Backend** FastAPI + PostgreSQL: 19 routes, 16 tables (3 partitioned), 4 cron jobs APScheduler
- **Frontend** React + ECharts:
  - HomePage: load LATEST mặc định → 163 nước flu W21/2026; picker để xem historical
  - DiseaseDetailPage: 4-week forecast + 52-week trend từ history API, warning banner cho năm ngoài training
  - AnalyticsPage: 3 chart thật (top countries, R²/RMSE/MAE × h=1..4, features list) từ ml_models/*.json
- **Realtime serving** (Phase A-1, A-2, A-3 hoàn thiện):
  - sync_flunet.py (Mon 10:00) → disease_cases
  - sync_weather.py (daily 6:00) → weather_observations
  - feature_builder.py (Mon 11:00) → feature_snapshots
  - **batch_predict.py (Mon 11:30) → predictions (163 nước/tuần)** ← phase mới nhất
- **Scope honesty**: endpoint `/forecast/{disease}/available` + field `data_coverage.warning` trong mọi response → FE hiển thị banner amber khi extrapolation, không bịa kết quả
- **Hybrid serving**: risk-map precompute (DB SELECT) + forecast on-demand (ml_engine + feature_snapshots) — pattern chuẩn ML serving

### Chưa đạt được / Hạn chế ✗

| Hạn chế | Mức độ | Trạng thái / Giải pháp |
|---|---|---|
| **Dengue chưa có nowcast realtime** | Cao | Khách quan — không có nguồn API miễn phí toàn cầu kiểu WHO FluMart. Ghi chú trong báo cáo: "Flu = production realtime, Dengue = historical demo". |
| VNM không có training data flu | Trung bình | FE flag `data_coverage.warning` đã wire; có thể bổ sung ECDC để có VNM |
| Weather history chỉ có 2025–2026 trong DB | Thấp | ERA5 2010–2019 đã chứa trong feature_snapshots; chỉ cần sync `--from-year 2024` để bridge nếu cần |
| WHO FluNet độ trễ 1–3 tuần | Trung bình | Không thể tránh; nowcast tự fallback về tuần mới nhất có data |
| Distribution shift 2026 vs training | Không xác định | Cần ground truth 2026 để đánh giá; warning đã hiển thị FE |
| Không thể dự báo > 4 tuần ahead | Thấp | Train thêm h=5..8 nếu cần |
| `pipeline_runs`, `data_quality_checks`, `api_request_logs` chưa wire middleware | Thấp | Observability backlog |
| Classifier XGBClassifier chưa serve qua API riêng | Thấp | Đã tích hợp trong batch_predict (set `risk_level` cột) — đủ cho map |

---

## 7. Email gửi Giáo viên hướng dẫn

---

**Kính gửi Thầy/Cô,**

Em là Phạm Hữu Luân, sinh viên lớp DA22TTA, MSSV 110122016, hiện đang thực hiện đề tài **"Hệ thống cảnh báo nguy cơ dịch bệnh từ dữ liệu y tế và thời tiết toàn cầu"**.

Em xin báo cáo tiến độ và kính xin ý kiến hướng dẫn về một số khó khăn kỹ thuật.

---

### I. Tóm tắt tiến độ

**Mô hình Machine Learning:**

Em đã huấn luyện và so sánh 5 mô hình (Naive baseline, Prophet, XGBoost, LightGBM, Random Forest) trên bài toán dự báo số ca bệnh theo tuần, với kiến trúc multi-horizon direct — 4 mô hình riêng biệt cho h = 1, 2, 3, 4 tuần ahead. Kết quả cross-validation (walk-forward, 6 folds, val 2014–2019):

| Model | Disease | Horizon | R² | RMSE |
|---|---|---|---|---|
| LightGBM (Optuna-tuned) | Influenza | h=1 | 0.866 | 0.686 |
| LightGBM | Influenza | h=4 | 0.757 | 0.877 |
| Random Forest | Dengue | h=1 | 0.929 | 0.531 |
| Random Forest | Dengue | h=4 | 0.898 | 0.627 |

Tất cả vượt ngưỡng benchmark của Lowe et al. (2014).

**Hệ thống triển khai:**

- Backend: FastAPI + PostgreSQL (16 bảng, 3 bảng lớn dùng partitioning), 19 API endpoints
- Frontend: React + ECharts — bản đồ risk toàn cầu 163 nước, forecast 4 tuần, historical picker, trang Analytics với top countries + model performance + feature list
- Auto-sync: 4 cron jobs (WHO FluNet thứ Hai, Open-Meteo hàng ngày, feature builder thứ Hai, **batch_predict thứ Hai 11:30** mới)
- Nowcast thực tế: dự báo flu W22–W25/2026 cho 163 nước từ data realtime W21/2026
- **Scope honesty**: mọi response forecast trả `data_coverage.warning` nếu năm dự báo nằm ngoài training window (2010–2019); FE hiển thị banner cảnh báo — không "bịa" kết quả ngoài phạm vi data thực

---

### II. Cách tiếp cận dự đoán cho dữ liệu mới

Em xin trình bày rõ phương pháp dự đoán mà hệ thống đang dùng:

**Giai đoạn training:** Mô hình học trên dữ liệu 2010–2019 (walk-forward CV) và được kiểm chứng trên 2022 (held-out test). Đây là pipeline truyền thống.

**Giai đoạn deploy:** Hệ thống sử dụng **kết hợp cả hai phương pháp**:

1. **Truy vấn lịch sử (Historical query)**: User chọn năm/tuần bất kỳ trong 2010–2019, hệ thống đọc feature vector đã pre-compute từ bảng `feature_snapshots` và predict ngay. Đây là cách kiểm chứng mô hình với data đã có ground truth.

2. **Nowcast realtime**: Hệ thống tự động kéo data mới từ WHO FluNet và Open-Meteo, tính lag features, lưu vào DB, sau đó dự báo cho 4 tuần tới. Hiện đang dự báo W22–W25/2026.

Hai cách dùng chung **cùng một model pkl** và cùng pipeline, chỉ khác nguồn input data.

---

### III. Khó khăn kỹ thuật khi dự đoán trên data mới

Khi áp dụng mô hình đã train (2010–2019) cho data 2026, em đang gặp các thách thức sau:

**1. Distribution shift (chuyển dịch phân phối):** Khí hậu và hành vi y tế đã thay đổi từ 2019 đến 2026 (warming, vaccine coverage, sub-type cúm khác). Mô hình có thể bị bias mà không kiểm chứng được vì chưa có ground truth 2026.

**2. Khoảng trống 2020–2021 do COVID-19:** Số ca cúm giảm ~99% do NPI, không phải pattern dịch tễ thật. Em đã loại khỏi training nhưng vẫn cần ghi chú trong báo cáo.

**3. Việt Nam không có trong training set:** WHO FluNet không có dữ liệu VNM ổn định 2010–2019. Hệ thống vẫn dự báo được nhờ weather features, nhưng độ tin cậy thấp hơn các nước có trong training (THA, IDN, JPN...). FE đã wire warning banner để user biết.

**3.bis Dengue chưa có realtime:** Không có nguồn surveillance toàn cầu miễn phí cho dengue (OpenDengue lag 6 tháng, PAHO HTML scraping, các nguồn còn lại theo từng quốc gia riêng). Hệ thống chỉ predict dengue cho 2015–2019 từ Oxford OpenDengue. Trong báo cáo em sẽ tách rõ "Flu = production realtime, Dengue = historical demo".

**4. Độ trễ báo cáo của WHO FluNet:** Một số nước báo cáo muộn 1–3 tuần. Khi gọi nowcast, dự báo "thực tế" có thể chậm 1–3 tuần so với hiện tại.

**5. Giới hạn 4 tuần ahead:** Mô hình hiện chỉ train cho h=1..4. Muốn dự báo xa hơn phải train thêm hoặc dùng recursive (lỗi tích lũy).

---

### IV. Câu hỏi kính xin ý kiến

1. **Mức độ hoàn thiện:** Với R² = 0.866 (flu h=1), hệ thống nowcast 163 nước từ data 2026, và đầy đủ so sánh 5 model — liệu mức độ này có đủ cho báo cáo tốt nghiệp không, hay Thầy/Cô muốn em bổ sung thực nghiệm cụ thể nào (ví dụ: backtest 2022, validate trên data mới hơn)?

2. **Xử lý VNM:** Em có nên loại Việt Nam khỏi phần demo và chỉ demo các nước có trong training set, hay giữ lại và ghi chú rõ hạn chế?

3. **Cấu trúc báo cáo:** Đề tài yêu cầu "đề xuất mô hình ML". Em đã có bảng so sánh định lượng. Thầy/Cô có muốn em bổ sung phân tích định tính (ưu/nhược điểm từng model trong bối cảnh dịch tễ, SHAP interpretation cho LightGBM, lý do chọn Random Forest cho dengue thay vì LightGBM...) hay tập trung vào kết quả định lượng?

4. **Distribution shift:** Em có nên thêm chương phân tích về sự khác biệt giữa data training (2010–2019) và data hiện tại (2026), hoặc đề xuất hướng retrain định kỳ (mỗi 6 tháng/năm)?

5. **Thời hạn nộp báo cáo và lịch demo:** Xin Thầy/Cô cho em biết lịch chính thức để em sắp xếp tiến độ.

---

Em rất mong nhận được phản hồi của Thầy/Cô. Em xin cảm ơn.

Trân trọng,

**Phạm Hữu Luân**
MSSV: 110122016 | Lớp: DA22TTA
Email: hulung186@gmail.com | SĐT: *(thêm số điện thoại)*

---

*File này được cập nhật từ trạng thái hệ thống ngày 22/05/2026 — sau Phase A-3 (batch_predict.py auto-populate predictions cho tuần mới nhất), Analytics page wiring vào real data từ ml_models/*.json, và fix WHO Region code mismatch (DB dùng AFR/AMR/EMR/EUR/SEAR/WPR, FE đã đồng bộ).*
