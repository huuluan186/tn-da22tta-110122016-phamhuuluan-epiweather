# PostgreSQL Schema v2 — Generalized & Production-Ready

**Nguyên tắc thiết kế lại:**
- **Catalog-driven** — thêm bệnh/biến thời tiết/nguồn dữ liệu = INSERT vào catalog, không ALTER TABLE
- **JSONB cho flexible data** — weather observations và feature snapshots không bị tied vào column cứng
- **Partitioning** — time-series data chia theo năm, không bị slow query khi data lớn
- **MLOps native** — model versioning, experiment tracking, data quality gate tích hợp vào schema

---

## Kiến trúc tổng quan

```
┌─────────────────── CATALOG (config-driven) ──────────────────┐
│  diseases  │  data_sources  │  weather_variables              │
└──────────────────────────────────────────────────────────────┘
                    │ FK
┌─────────────── OBSERVATIONS (generic, partitioned) ──────────┐
│  disease_cases (partitioned by year)                         │
│  weather_observations (partitioned by year, JSONB data)      │
└──────────────────────────────────────────────────────────────┘
                    │ feed
┌────────────────── ML PIPELINE ───────────────────────────────┐
│  model_versions  │  feature_configs  │  risk_thresholds      │
│  predictions (partitioned by year)   │  model_evaluations    │
└──────────────────────────────────────────────────────────────┘
                    │ monitor
┌───────────────── MLOPS / OPS ────────────────────────────────┐
│  pipeline_runs   │  pipeline_run_logs  │  data_quality_checks │
│  api_request_logs (production monitoring)                    │
└──────────────────────────────────────────────────────────────┘
```

---

## DDL

### LAYER 0 — Master geography

```sql
CREATE TABLE countries (
    iso3              CHAR(3)          PRIMARY KEY,
    iso2              CHAR(2),
    country_name      VARCHAR(100)     NOT NULL,
    who_region        VARCHAR(10),     -- AFR, AMR, EMR, EUR, SEAR, WPR
    who_region_enc    SMALLINT,        -- ordinal 0-5, cached để tránh JOIN khi serve
    latitude          DOUBLE PRECISION,
    longitude         DOUBLE PRECISION,
    population        BIGINT,
    created_at        TIMESTAMPTZ      DEFAULT NOW()
);
```

---

### LAYER 1 — CATALOG (config-driven, không hardcode)

```sql
-- 1a. Diseases — thêm bệnh mới = INSERT 1 row
CREATE TABLE diseases (
    id                SERIAL           PRIMARY KEY,
    code              VARCHAR(20)      NOT NULL UNIQUE,  -- 'flu', 'dengue', 'covid', 'mpox'
    display_name      VARCHAR(100)     NOT NULL,
    target_variable   VARCHAR(50)      NOT NULL,         -- tên cột raw: 'inf_cases', 'dengue_total'
    target_transform  VARCHAR(20)      DEFAULT 'log1p'   -- 'log1p', 'none', 'sqrt'
                      CHECK (target_transform IN ('log1p', 'none', 'sqrt')),
    case_table        VARCHAR(50),                       -- tên bảng lưu cases (để routing)
    is_active         BOOLEAN          DEFAULT TRUE,
    description       TEXT,
    created_at        TIMESTAMPTZ      DEFAULT NOW()
);

-- Seed data:
-- INSERT INTO diseases (code, display_name, target_variable, target_transform)
-- VALUES ('flu', 'Influenza', 'inf_cases', 'log1p'),
--        ('dengue', 'Dengue fever', 'dengue_total', 'log1p');


-- 1b. Data sources — thêm nguồn dữ liệu mới = INSERT 1 row
CREATE TABLE data_sources (
    id                SERIAL           PRIMARY KEY,
    code              VARCHAR(30)      NOT NULL UNIQUE,  -- 'FluNet', 'WHO_PAHO', 'ERA5', 'ECDC'
    source_type       VARCHAR(20)      NOT NULL          -- 'disease', 'weather', 'socioeconomic'
                      CHECK (source_type IN ('disease', 'weather', 'socioeconomic')),
    url               TEXT,
    update_frequency  VARCHAR(20),                       -- 'weekly', 'monthly', 'realtime'
    spatial_coverage  VARCHAR(50),                       -- 'global', 'europe', 'americas'
    temporal_start    DATE,
    is_active         BOOLEAN          DEFAULT TRUE,
    description       TEXT
);

-- Seed data:
-- INSERT INTO data_sources (code, source_type, update_frequency)
-- VALUES ('FluNet', 'disease', 'weekly'),
--        ('WHO_PAHO', 'disease', 'weekly'),
--        ('ERA5', 'weather', 'monthly'),
--        ('OpenWeatherMap', 'weather', 'realtime'),
--        ('NOAA_ENSO', 'weather', 'monthly');


-- 1c. Weather variables — thêm biến mới = INSERT 1 row
CREATE TABLE weather_variables (
    id                SERIAL           PRIMARY KEY,
    code              VARCHAR(50)      NOT NULL UNIQUE,  -- 'temp_c', 'humidity_pct', 'oni_index'
    display_name      VARCHAR(100),
    unit              VARCHAR(20),                       -- '°C', '%', 'mm', 'W/m²'
    source_id         INTEGER          REFERENCES data_sources(id),
    era5_variable     VARCHAR(100),                      -- tên biến ERA5 gốc (nếu có)
    description       TEXT,
    is_active         BOOLEAN          DEFAULT TRUE
);

-- Seed ERA5 17 vars:
-- INSERT INTO weather_variables (code, unit, source_id) VALUES
-- ('temp_c', '°C', 3), ('humidity_pct', '%', 3), ('solar_wm2', 'W/m²', 3), ...
-- Thêm ENSO sau này:
-- ('oni_index', 'anomaly', 5), ('mei_index', 'anomaly', 5)
```

---

### LAYER 2 — OBSERVATIONS (generic, partitioned)

```sql
-- 2a. Disease cases — dùng cho mọi bệnh
-- Partitioned by year để query nhanh trên time-series dài
CREATE TABLE disease_cases (
    id                BIGSERIAL,
    disease_id        INTEGER          NOT NULL REFERENCES diseases(id),
    iso3              CHAR(3)          NOT NULL REFERENCES countries(iso3),
    source_id         INTEGER          REFERENCES data_sources(id),
    iso_year          SMALLINT         NOT NULL,
    iso_week          SMALLINT         NOT NULL,
    raw_count         INTEGER,                           -- số ca gốc từ source
    transformed_value DOUBLE PRECISION,                  -- log1p(raw) hoặc transform khác
    data_quality      SMALLINT         DEFAULT 1         -- 0=missing, 1=reported, 2=estimated
                      CHECK (data_quality IN (0, 1, 2)),
    ingested_at       TIMESTAMPTZ      DEFAULT NOW(),
    PRIMARY KEY (id, iso_year)                           -- composite PK cho partitioning
) PARTITION BY RANGE (iso_year);

-- Tạo partition theo năm (thêm bệnh mới không cần thêm partition, dùng chung)
CREATE TABLE disease_cases_2010 PARTITION OF disease_cases FOR VALUES FROM (2010) TO (2011);
CREATE TABLE disease_cases_2011 PARTITION OF disease_cases FOR VALUES FROM (2011) TO (2012);
-- ... (2012-2022)
CREATE TABLE disease_cases_2022 PARTITION OF disease_cases FOR VALUES FROM (2022) TO (2023);
CREATE TABLE disease_cases_default PARTITION OF disease_cases DEFAULT;

CREATE UNIQUE INDEX idx_disease_cases_unique
    ON disease_cases (disease_id, iso3, iso_year, iso_week, source_id);
CREATE INDEX idx_disease_cases_lookup
    ON disease_cases (iso3, disease_id, iso_year, iso_week);


-- 2b. Weather observations — JSONB cho flexible variables
-- Key insight: thêm biến ERA5 mới = chỉ cần thêm key vào JSONB, không ALTER TABLE
CREATE TABLE weather_observations (
    id                BIGSERIAL,
    iso3              CHAR(3)          NOT NULL REFERENCES countries(iso3),
    source_id         INTEGER          NOT NULL REFERENCES data_sources(id),
    iso_year          SMALLINT         NOT NULL,
    iso_week          SMALLINT         NOT NULL,
    -- JSONB chứa tất cả biến: {"temp_c": 25.3, "humidity_pct": 80.1, "oni_index": 0.5, ...}
    -- Thêm biến mới = không cần ALTER TABLE, chỉ cần INSERT với key mới
    data              JSONB            NOT NULL,
    ingested_at       TIMESTAMPTZ      DEFAULT NOW(),
    PRIMARY KEY (id, iso_year)
) PARTITION BY RANGE (iso_year);

CREATE TABLE weather_obs_2010 PARTITION OF weather_observations FOR VALUES FROM (2010) TO (2011);
-- ... (tương tự)
CREATE TABLE weather_obs_default PARTITION OF weather_observations DEFAULT;

CREATE UNIQUE INDEX idx_weather_unique
    ON weather_observations (iso3, source_id, iso_year, iso_week);

-- Query ví dụ — lấy temp và humidity:
-- SELECT iso3, iso_year, iso_week,
--        (data->>'temp_c')::float AS temp_c,
--        (data->>'humidity_pct')::float AS humidity_pct
-- FROM weather_observations
-- WHERE source_id = 3 AND iso_year = 2022;

-- GIN index cho JSONB queries nhanh
CREATE INDEX idx_weather_data_gin ON weather_observations USING GIN (data);
```

---

### LAYER 3 — ML PIPELINE

```sql
-- 3a. Feature configs — lag và transform config theo disease, queryable
-- Thêm bệnh mới = INSERT feature configs cho bệnh đó, không sửa code
CREATE TABLE feature_configs (
    id                SERIAL           PRIMARY KEY,
    disease_id        INTEGER          NOT NULL REFERENCES diseases(id),
    feature_name      VARCHAR(100)     NOT NULL,         -- tên cột output trong feature matrix
    source_type       VARCHAR(20)      NOT NULL          -- 'weather', 'ar_lag', 'geographic', 'socioeconomic'
                      CHECK (source_type IN ('weather', 'ar_lag', 'geographic', 'socioeconomic', 'calendar')),
    -- Với weather features:
    weather_variable  VARCHAR(50),                       -- FK về weather_variables.code
    lag_weeks         SMALLINT         DEFAULT 0,
    transform         VARCHAR(20)      DEFAULT 'none',   -- 'none', 'log1p', 'pca_component'
    -- Với AR lag features:
    ar_target         VARCHAR(50),                       -- 'transformed_value'
    ar_lag_weeks      SMALLINT,
    is_active         BOOLEAN          DEFAULT TRUE,
    version_tag       VARCHAR(30),                       -- 'v1.0', 'v1.1-pca' — gắn với model version
    UNIQUE (disease_id, feature_name, version_tag)
);

-- Seed flu features:
-- INSERT INTO feature_configs (disease_id, feature_name, source_type, weather_variable, lag_weeks)
-- VALUES
-- (1, 'temp_c_lag4',   'weather', 'temp_c',       4),
-- (1, 'humidity_lag8', 'weather', 'humidity_pct',  8),
-- (1, 'solar_lag8',    'weather', 'solar_wm2',     8),
-- (1, 'dew_lag2',      'weather', 'dewpoint_c',    2),
-- (1, 'ar_lag1',       'ar_lag',   NULL,           NULL),  -- ar_lag_weeks=1
-- (1, 'who_region_enc','geographic', NULL,         NULL);


-- 3b. Model versions — generic cho mọi disease
CREATE TABLE model_versions (
    id                SERIAL           PRIMARY KEY,
    disease_id        INTEGER          NOT NULL REFERENCES diseases(id),
    version           VARCHAR(30)      NOT NULL,
    algorithm         VARCHAR(30)      DEFAULT 'XGBoost',  -- 'XGBoost', 'LightGBM', 'LSTM'
    description       TEXT,
    train_year_start  SMALLINT         NOT NULL,
    train_year_end    SMALLINT         NOT NULL,
    val_year          SMALLINT,
    feature_config_tag VARCHAR(30),                        -- link về feature_configs.version_tag
    hyperparams       JSONB,
    artifact_path     VARCHAR(255),
    is_active         BOOLEAN          DEFAULT FALSE,
    is_champion       BOOLEAN          DEFAULT FALSE,      -- model tốt nhất trong A/B test
    created_at        TIMESTAMPTZ      DEFAULT NOW(),
    UNIQUE (disease_id, version)
);


-- 3c. Model evaluations — tách riêng khỏi model_versions để lưu nhiều eval sets
CREATE TABLE model_evaluations (
    id                SERIAL           PRIMARY KEY,
    model_version_id  INTEGER          NOT NULL REFERENCES model_versions(id),
    eval_set          VARCHAR(30)      NOT NULL,     -- 'val_2022', 'test_2023', 'cv_fold_3'
    eval_type         VARCHAR(20)      NOT NULL      -- 'holdout', 'cv', 'production_drift'
                      CHECK (eval_type IN ('holdout', 'cv', 'production_drift')),
    -- Regression metrics
    r2_score          DOUBLE PRECISION,
    mae               DOUBLE PRECISION,
    rmse              DOUBLE PRECISION,
    smape_nonzero     DOUBLE PRECISION,
    -- Classification metrics (risk level)
    risk_macro_f1     DOUBLE PRECISION,
    risk_accuracy     DOUBLE PRECISION,
    risk_low_f1       DOUBLE PRECISION,
    risk_medium_f1    DOUBLE PRECISION,
    risk_high_f1      DOUBLE PRECISION,
    -- Extra
    n_samples         INTEGER,
    notes             TEXT,
    evaluated_at      TIMESTAMPTZ      DEFAULT NOW()
);


-- 3d. Risk thresholds — generic cho mọi disease
CREATE TABLE risk_thresholds (
    id                SERIAL           PRIMARY KEY,
    disease_id        INTEGER          NOT NULL REFERENCES diseases(id),
    iso3              VARCHAR(10)      NOT NULL,     -- iso3 hoặc '_global' fallback
    q33               DOUBLE PRECISION NOT NULL,
    q67               DOUBLE PRECISION NOT NULL,
    n_nonzero_weeks   INTEGER,
    is_global_fallback BOOLEAN         DEFAULT FALSE,
    model_version_id  INTEGER          REFERENCES model_versions(id),
    updated_at        TIMESTAMPTZ      DEFAULT NOW(),
    UNIQUE (disease_id, iso3)
);


-- 3e. Predictions — generic, partitioned
CREATE TABLE predictions (
    id                BIGSERIAL,
    disease_id        INTEGER          NOT NULL REFERENCES diseases(id),
    iso3              CHAR(3)          NOT NULL REFERENCES countries(iso3),
    iso_year          SMALLINT         NOT NULL,
    iso_week          SMALLINT         NOT NULL,
    horizon_weeks     SMALLINT         DEFAULT 1,    -- h=1 hiện tại, h=2,3,4 multi-horizon
    predicted_value   DOUBLE PRECISION,              -- log1p scale (model output)
    predicted_cases   DOUBLE PRECISION,              -- expm1(predicted_value)
    risk_level        VARCHAR(10)      CHECK (risk_level IN ('Low', 'Medium', 'High')),
    risk_q33          DOUBLE PRECISION,
    risk_q67          DOUBLE PRECISION,
    model_version_id  INTEGER          REFERENCES model_versions(id),
    -- MLOps: audit trail — features tại thời điểm predict
    features_snapshot JSONB,
    confidence_lo     DOUBLE PRECISION,              -- lower bound prediction interval
    confidence_hi     DOUBLE PRECISION,              -- upper bound prediction interval
    created_at        TIMESTAMPTZ      DEFAULT NOW(),
    PRIMARY KEY (id, iso_year)
) PARTITION BY RANGE (iso_year);

CREATE TABLE predictions_2022 PARTITION OF predictions FOR VALUES FROM (2022) TO (2023);
CREATE TABLE predictions_default PARTITION OF predictions DEFAULT;

CREATE UNIQUE INDEX idx_predictions_unique
    ON predictions (disease_id, iso3, iso_year, iso_week, horizon_weeks, model_version_id);
CREATE INDEX idx_predictions_dashboard
    ON predictions (disease_id, iso_year, iso_week, risk_level);
```

---

### LAYER 4 — MLOPS & PRODUCTION OPS

```sql
-- 4a. Pipeline runs — tracking mọi job
CREATE TABLE pipeline_runs (
    run_id            UUID             PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_name     VARCHAR(50)      NOT NULL,    -- 'era5_ingest', 'score_flu', 'retrain_dengue'
    pipeline_version  VARCHAR(20),
    trigger_type      VARCHAR(20)      DEFAULT 'manual'
                      CHECK (trigger_type IN ('manual', 'scheduled', 'api', 'event')),
    status            VARCHAR(20)      NOT NULL
                      CHECK (status IN ('queued', 'running', 'success', 'failed', 'partial')),
    iso_year          SMALLINT,
    iso_week          SMALLINT,
    started_at        TIMESTAMPTZ      NOT NULL DEFAULT NOW(),
    completed_at      TIMESTAMPTZ,
    duration_sec      DOUBLE PRECISION GENERATED ALWAYS AS
                      (EXTRACT(EPOCH FROM (completed_at - started_at))) STORED,
    rows_processed    INTEGER,
    rows_inserted     INTEGER,
    rows_updated      INTEGER,
    rows_skipped      INTEGER,
    errors            JSONB,
    metadata          JSONB            -- file paths, API params, config used
);

CREATE INDEX idx_pipeline_runs_status ON pipeline_runs (pipeline_name, status, started_at DESC);


-- 4b. Data quality checks — tự động gate trước khi đưa vào pipeline
CREATE TABLE data_quality_checks (
    id                SERIAL           PRIMARY KEY,
    run_id            UUID             REFERENCES pipeline_runs(run_id),
    check_name        VARCHAR(100)     NOT NULL,    -- 'null_rate_inf_cases', 'coverage_pct', 'year_range'
    table_name        VARCHAR(50),
    iso_year          SMALLINT,
    iso_week          SMALLINT,
    threshold         DOUBLE PRECISION,             -- ngưỡng pass/fail
    actual_value      DOUBLE PRECISION,
    passed            BOOLEAN          NOT NULL,
    detail            TEXT,
    checked_at        TIMESTAMPTZ      DEFAULT NOW()
);


-- 4c. API request logs — production monitoring
CREATE TABLE api_request_logs (
    id                BIGSERIAL        PRIMARY KEY,
    endpoint          VARCHAR(100),    -- '/predict', '/risk_map', '/history'
    method            VARCHAR(10),
    disease           VARCHAR(20),
    iso3              CHAR(3),
    iso_year          SMALLINT,
    iso_week          SMALLINT,
    model_version_id  INTEGER,
    response_ms       INTEGER,         -- latency
    status_code       SMALLINT,
    user_agent        VARCHAR(200),
    client_ip         INET,
    requested_at      TIMESTAMPTZ      DEFAULT NOW()
) PARTITION BY RANGE (requested_at);

CREATE TABLE api_logs_2026 PARTITION OF api_request_logs
    FOR VALUES FROM ('2026-01-01') TO ('2027-01-01');
CREATE TABLE api_logs_default PARTITION OF api_request_logs DEFAULT;

CREATE INDEX idx_api_logs_endpoint ON api_request_logs (endpoint, requested_at DESC);
CREATE INDEX idx_api_logs_model ON api_request_logs (model_version_id);
```

---

### LAYER 5 — MATERIALIZED VIEWS (dashboard performance)

```sql
-- Latest predictions per country per disease — dashboard không cần query predictions thô
CREATE MATERIALIZED VIEW mv_latest_predictions AS
SELECT DISTINCT ON (disease_id, iso3, horizon_weeks)
    p.disease_id,
    d.code       AS disease_code,
    p.iso3,
    c.country_name,
    c.who_region,
    p.iso_year,
    p.iso_week,
    p.horizon_weeks,
    p.predicted_cases,
    p.risk_level,
    p.created_at
FROM predictions p
JOIN diseases d ON d.id = p.disease_id
JOIN countries c ON c.iso3 = p.iso3
ORDER BY disease_id, iso3, horizon_weeks, created_at DESC;

CREATE UNIQUE INDEX idx_mv_latest ON mv_latest_predictions (disease_id, iso3, horizon_weeks);

-- Refresh sau mỗi scoring run:
-- REFRESH MATERIALIZED VIEW CONCURRENTLY mv_latest_predictions;
```

---

## So sánh v1 vs v2

| Vấn đề | Schema v1 | Schema v2 |
|---|---|---|
| Thêm bệnh mới (COVID, mpox) | ALTER TABLE + thêm column | INSERT vào `diseases` catalog |
| Thêm biến thời tiết (ENSO ONI) | ALTER TABLE era5_weather | INSERT vào `weather_variables`, thêm key vào JSONB |
| Thêm nguồn data (ECDC, NOAA) | Hardcode trong code | INSERT vào `data_sources` |
| Thay đổi feature lag config | Sửa code Python | UPDATE `feature_configs` + tạo version_tag mới |
| So sánh 2 model versions | Không có | `model_evaluations` + `is_champion` flag |
| Multi-horizon forecasting | horizon_weeks=1 cứng | `predictions.horizon_weeks` = 1,2,3,4 |
| Data quality gate | Không có | `data_quality_checks` per pipeline run |
| Production monitoring | Không có | `api_request_logs` (latency, usage) |
| Dashboard performance | Full scan predictions | Materialized view, refresh sau mỗi run |
| Data volume lớn | Full table scan | Partitioning theo năm |

---

## Lộ trình implement (theo giai đoạn)

### Phase 1 — Thesis (hiện tại)
Chỉ cần implement các bảng sau để demo hoạt động:
```
countries, diseases (2 rows), data_sources
disease_cases, weather_observations
model_versions, risk_thresholds, predictions
pipeline_runs (basic)
```

### Phase 2 — Production MVP
```
+ model_evaluations (A/B testing)
+ data_quality_checks (tự động gate)
+ api_request_logs (monitoring)
+ mv_latest_predictions (dashboard performance)
+ feature_configs (config-driven)
```

### Phase 3 — MLOps Scale
```
+ Read replica cho dashboard queries
+ Redis cache layer trước PostgreSQL (predictions hot data)
+ Airflow/Prefect để schedule pipeline_runs
+ Prometheus metrics từ api_request_logs
+ Auto-retrain trigger khi production_drift detected
```

---

## FastAPI routing tương ứng

```
GET  /api/v1/diseases               → SELECT * FROM diseases WHERE is_active=TRUE
GET  /api/v1/predict/{disease}/{iso3}  → mv_latest_predictions
GET  /api/v1/risk_map/{disease}     → mv_latest_predictions GROUP BY iso3
GET  /api/v1/history/{disease}/{iso3}  → disease_cases + predictions JOIN
POST /api/v1/ingest/trigger         → INSERT pipeline_runs, trigger ETL
GET  /api/v1/models                 → model_versions + model_evaluations
```
