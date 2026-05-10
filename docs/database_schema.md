# PostgreSQL Schema — EpiWeather ML System (MLOps-ready)

Tài liệu thiết kế cơ sở dữ liệu cho hệ thống cảnh báo nguy cơ dịch bệnh.
Dùng cho **Chương 3 — Thiết kế hệ thống**.

Nguyên tắc thiết kế:
- **Full DB** — lưu raw data, processed data, predictions, model versions
- **MLOps extensibility** — model versioning, pipeline run tracking
- **Audit trail** — mọi prediction có thể trace về model version và data source
- Dùng `iso3` (ISO 3166-1 alpha-3) làm khóa định danh quốc gia xuyên suốt

---

## ERD Overview

```
countries (master)
    │
    ├──< flu_cases          (raw + processed flu data)
    ├──< dengue_cases       (raw + processed dengue data)
    ├──< era5_weather       (17-variable ERA5 weather, weekly)
    ├──< predictions        (output của ML model, mọi disease)
    └──< flu_risk_thresholds (per-country Q33/Q67)

model_versions (catalog)
    └──< predictions        (FK: mỗi prediction biết dùng model nào)

data_pipeline_runs (monitoring)
    └──< pipeline_run_logs  (chi tiết log từng bước)
```

---

## DDL — Tạo bảng

```sql
-- ============================================================
-- 1. COUNTRIES — master reference table
-- ============================================================
CREATE TABLE countries (
    iso3            CHAR(3)         PRIMARY KEY,
    iso2            CHAR(2),
    country_name    VARCHAR(100)    NOT NULL,
    who_region      VARCHAR(10),                    -- AFR, AMR, EMR, EUR, SEAR, WPR
    who_region_enc  SMALLINT,                       -- ordinal: 0-5 (giữ để tránh encode lại khi serve)
    latitude        DOUBLE PRECISION,               -- centroid dùng cho KD-tree ERA5 mapping
    longitude       DOUBLE PRECISION,
    population      BIGINT,
    is_flu_country  BOOLEAN DEFAULT TRUE,           -- 197 countries in ERA5 flu coverage
    is_dengue_country BOOLEAN DEFAULT FALSE,        -- 41 countries in dengue coverage
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- 2. FLU_CASES — dữ liệu cúm theo tuần (FluNet source)
-- ============================================================
CREATE TABLE flu_cases (
    id              BIGSERIAL       PRIMARY KEY,
    iso3            CHAR(3)         NOT NULL REFERENCES countries(iso3),
    iso_year        SMALLINT        NOT NULL,        -- ISO week year (e.g., 2019)
    iso_week        SMALLINT        NOT NULL,        -- ISO week number 1-53
    inf_a           INTEGER,                         -- Influenza A confirmed cases
    inf_b           INTEGER,                         -- Influenza B confirmed cases
    inf_cases       INTEGER,                         -- inf_a + inf_b (computed/stored)
    inf_log1p       DOUBLE PRECISION,                -- log1p(inf_cases) — target variable
    source          VARCHAR(20) DEFAULT 'FluNet',
    ingested_at     TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (iso3, iso_year, iso_week)
);

CREATE INDEX idx_flu_cases_iso3_year ON flu_cases (iso3, iso_year, iso_week);
CREATE INDEX idx_flu_cases_year_week ON flu_cases (iso_year, iso_week);

-- ============================================================
-- 3. DENGUE_CASES — dữ liệu sốt xuất huyết theo tuần (WHO PAHO source)
-- ============================================================
CREATE TABLE dengue_cases (
    id              BIGSERIAL       PRIMARY KEY,
    iso3            CHAR(3)         NOT NULL REFERENCES countries(iso3),
    iso_year        SMALLINT        NOT NULL,
    iso_week        SMALLINT        NOT NULL,
    dengue_total    INTEGER,                         -- total confirmed + suspected cases
    dengue_log1p    DOUBLE PRECISION,                -- log1p(dengue_total) — target variable
    source          VARCHAR(30) DEFAULT 'WHO_PAHO',
    ingested_at     TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (iso3, iso_year, iso_week)
);

CREATE INDEX idx_dengue_cases_iso3_year ON dengue_cases (iso3, iso_year, iso_week);

-- ============================================================
-- 4. ERA5_WEATHER — 17 biến ERA5 theo tuần, mỗi quốc gia
-- ============================================================
-- Tần suất: weekly (ISO week mean của daily ERA5)
-- Source: ECMWF ERA5 via CDS API, KD-tree centroid mapping
-- Coverage: 197 countries (flu) / 41 countries (dengue)
CREATE TABLE era5_weather (
    id              BIGSERIAL       PRIMARY KEY,
    iso3            CHAR(3)         NOT NULL REFERENCES countries(iso3),
    iso_year        SMALLINT        NOT NULL,
    iso_week        SMALLINT        NOT NULL,
    -- Temperature variables
    temp_c          DOUBLE PRECISION,               -- 2m temperature (°C)
    temp_min_c      DOUBLE PRECISION,               -- daily min temp (°C)
    temp_max_c      DOUBLE PRECISION,               -- daily max temp (°C)
    dewpoint_c      DOUBLE PRECISION,               -- 2m dewpoint (°C)
    -- Humidity & precipitation
    humidity_pct    DOUBLE PRECISION,               -- relative humidity (%)
    precip_mm       DOUBLE PRECISION,               -- total precipitation (mm)
    -- Solar radiation
    solar_wm2       DOUBLE PRECISION,               -- surface solar radiation (W/m²)
    -- Wind
    wind_u_ms       DOUBLE PRECISION,               -- U-component wind (m/s)
    wind_v_ms       DOUBLE PRECISION,               -- V-component wind (m/s)
    wind_speed_ms   DOUBLE PRECISION,               -- |wind| magnitude (m/s)
    -- Pressure & boundary layer
    pressure_hpa    DOUBLE PRECISION,               -- surface pressure (hPa)
    blh_m           DOUBLE PRECISION,               -- boundary layer height (m)
    -- Soil & surface moisture
    soil_temp_c     DOUBLE PRECISION,               -- soil temperature (°C)
    total_water_col DOUBLE PRECISION,               -- total column water vapour (kg/m²)
    -- Additional
    cape_jkg        DOUBLE PRECISION,               -- CAPE (J/kg)
    snowfall_m      DOUBLE PRECISION,               -- snowfall (m of water equivalent)
    source          VARCHAR(20) DEFAULT 'ERA5',
    ingested_at     TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (iso3, iso_year, iso_week)
);

CREATE INDEX idx_era5_iso3_year ON era5_weather (iso3, iso_year, iso_week);
CREATE INDEX idx_era5_year_week ON era5_weather (iso_year, iso_week);

-- ============================================================
-- 5. MODEL_VERSIONS — catalog model đã train
-- ============================================================
CREATE TABLE model_versions (
    id              SERIAL          PRIMARY KEY,
    disease         VARCHAR(10)     NOT NULL CHECK (disease IN ('flu', 'dengue')),
    version         VARCHAR(30)     NOT NULL,        -- e.g., 'v1.0.0', 'v1.1-optuna'
    description     TEXT,
    train_year_start SMALLINT       NOT NULL,        -- e.g., 2010
    train_year_end  SMALLINT        NOT NULL,        -- e.g., 2019
    val_year        SMALLINT,                        -- holdout year (e.g., 2022)
    n_features      SMALLINT,
    feature_cols    JSONB,                           -- list of feature column names
    hyperparams     JSONB,                           -- XGBoost params (Optuna output, etc.)
    -- Performance metrics
    r2_score        DOUBLE PRECISION,
    mae             DOUBLE PRECISION,
    smape_nonzero   DOUBLE PRECISION,
    risk_macro_f1   DOUBLE PRECISION,
    -- Artifact
    artifact_path   VARCHAR(255),                    -- path đến .pkl file
    is_active       BOOLEAN DEFAULT FALSE,           -- model đang dùng để serve
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (disease, version)
);

-- ============================================================
-- 6. FLU_RISK_THRESHOLDS — per-country Q33/Q67 risk levels
-- ============================================================
CREATE TABLE flu_risk_thresholds (
    iso3            CHAR(3)         PRIMARY KEY,     -- '_global' cho global fallback
    q33             DOUBLE PRECISION NOT NULL,        -- threshold Low/Medium (log1p scale)
    q67             DOUBLE PRECISION NOT NULL,        -- threshold Medium/High (log1p scale)
    n_nonzero_weeks INTEGER,                         -- số tuần non-zero trong training
    is_global_fallback BOOLEAN DEFAULT FALSE,        -- TRUE nếu đây là global record
    model_version_id INTEGER REFERENCES model_versions(id),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- 7. PREDICTIONS — output ML model (mọi disease)
-- ============================================================
CREATE TABLE predictions (
    id              BIGSERIAL       PRIMARY KEY,
    iso3            CHAR(3)         NOT NULL REFERENCES countries(iso3),
    disease         VARCHAR(10)     NOT NULL CHECK (disease IN ('flu', 'dengue')),
    iso_year        SMALLINT        NOT NULL,
    iso_week        SMALLINT        NOT NULL,
    horizon_weeks   SMALLINT DEFAULT 1,              -- h=1 (current) hoặc h=2,3,4 (multi-horizon)
    -- Predictions
    predicted_log1p DOUBLE PRECISION,                -- raw model output (log1p scale)
    predicted_cases DOUBLE PRECISION,                -- expm1(predicted_log1p)
    -- Risk classification
    risk_level      VARCHAR(10) CHECK (risk_level IN ('Low', 'Medium', 'High')),
    risk_q33        DOUBLE PRECISION,                -- threshold dùng tại thời điểm predict
    risk_q67        DOUBLE PRECISION,
    -- Metadata
    model_version_id INTEGER REFERENCES model_versions(id),
    confidence      DOUBLE PRECISION,                -- optional: prediction interval width
    features_snapshot JSONB,                         -- snapshot features tại thời điểm predict (MLOps audit)
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (iso3, disease, iso_year, iso_week, horizon_weeks, model_version_id)
);

CREATE INDEX idx_predictions_iso3 ON predictions (iso3, disease, iso_year, iso_week);
CREATE INDEX idx_predictions_risk ON predictions (disease, iso_year, iso_week, risk_level);
CREATE INDEX idx_predictions_model ON predictions (model_version_id);

-- ============================================================
-- 8. DATA_PIPELINE_RUNS — MLOps: tracking ETL & scoring runs
-- ============================================================
CREATE TABLE data_pipeline_runs (
    run_id          UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_name   VARCHAR(50)     NOT NULL,        -- 'era5_ingest', 'flu_ingest', 'score_flu', etc.
    trigger         VARCHAR(20)     DEFAULT 'manual', -- 'manual', 'scheduled', 'api'
    status          VARCHAR(20)     NOT NULL CHECK (status IN ('running', 'success', 'failed', 'partial')),
    iso_year        SMALLINT,                        -- năm dữ liệu được xử lý
    iso_week        SMALLINT,                        -- tuần dữ liệu được xử lý
    started_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    completed_at    TIMESTAMPTZ,
    duration_sec    DOUBLE PRECISION GENERATED ALWAYS AS
                    (EXTRACT(EPOCH FROM (completed_at - started_at))) STORED,
    rows_processed  INTEGER,
    rows_inserted   INTEGER,
    rows_updated    INTEGER,
    errors          JSONB,                           -- list of error dicts nếu status='partial'/'failed'
    metadata        JSONB                            -- extra context (file paths, API params, etc.)
);

CREATE INDEX idx_pipeline_runs_name_status ON data_pipeline_runs (pipeline_name, status);
CREATE INDEX idx_pipeline_runs_started ON data_pipeline_runs (started_at DESC);

-- ============================================================
-- 9. PIPELINE_RUN_LOGS — chi tiết log từng step
-- ============================================================
CREATE TABLE pipeline_run_logs (
    id              BIGSERIAL       PRIMARY KEY,
    run_id          UUID            NOT NULL REFERENCES data_pipeline_runs(run_id) ON DELETE CASCADE,
    step_name       VARCHAR(100)    NOT NULL,
    level           VARCHAR(10)     DEFAULT 'INFO' CHECK (level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR')),
    message         TEXT,
    logged_at       TIMESTAMPTZ     DEFAULT NOW()
);

CREATE INDEX idx_run_logs_run_id ON pipeline_run_logs (run_id, logged_at);
```

---

## Quan hệ giữa các bảng (ERD text)

```
countries (1) ──< (N) flu_cases
countries (1) ──< (N) dengue_cases
countries (1) ──< (N) era5_weather
countries (1) ──< (N) predictions
countries (1) ──  (1) flu_risk_thresholds [iso3 PK]

model_versions (1) ──< (N) predictions
model_versions (1) ──< (N) flu_risk_thresholds

data_pipeline_runs (1) ──< (N) pipeline_run_logs
```

---

## Ghi chú thiết kế

### Tại sao lưu `inf_log1p` và `dengue_log1p` trực tiếp?
Đây là target variable của model — lưu vào DB để phục vụ retraining không cần recompute. Đảm bảo consistency giữa pipeline offline và online serving.

### Tại sao `features_snapshot JSONB` trong predictions?
MLOps best practice: mỗi prediction phải có khả năng tái tạo — biết chính xác features đã dùng tại thời điểm predict. Quan trọng khi detect data drift hoặc debug model degradation.

### Tại sao `model_versions` là bảng riêng?
- Cho phép A/B testing giữa model versions
- `is_active = TRUE` đánh dấu model đang serve
- Hyperparams lưu dạng JSONB → không bị tied vào schema cứng, dễ extend

### `data_pipeline_runs` — scope MLOps
Khi scale lên production, mọi ETL job (ERA5 ingest, FluNet scrape, scoring) đều cần:
- Idempotency check (đã xử lý tuần này chưa?)
- Failure recovery (partial status → retry từ row nào?)
- Monitoring (thời gian chạy, số rows, error rate)

### Dengue weather coverage
41/197 countries trong ERA5 dengue coverage — các quốc gia không có ERA5 dengue data sẽ không có row trong `era5_weather` cho `is_dengue_country=FALSE`.

---

## Indexes quan trọng

| Index | Lý do |
|---|---|
| `flu_cases(iso3, iso_year, iso_week)` | Query theo quốc gia + tuần (JOIN với weather) |
| `era5_weather(iso3, iso_year, iso_week)` | JOIN với cases khi build feature matrix |
| `predictions(disease, iso_year, iso_week, risk_level)` | Dashboard filter theo tuần + risk |
| `predictions(model_version_id)` | Audit trail — prediction nào dùng model nào |
| `data_pipeline_runs(pipeline_name, status)` | Monitor health của từng pipeline |

---

## Data Volume Estimate

| Bảng | Rows/năm | 10 năm (2010-2019) | Ghi chú |
|---|---|---|---|
| flu_cases | ~9,000 | ~90,000 | 197 countries × 52 weeks (partial) |
| dengue_cases | ~2,000 | ~20,000 | 41 countries × 52 weeks (partial) |
| era5_weather | ~10,000 | ~100,000 | 197 countries × 52 weeks |
| predictions | ~10,000/run | — | Per scoring run |
| model_versions | ~10 total | — | Ít update |
| data_pipeline_runs | ~100-500/năm | — | Tùy lịch chạy |
