-- ============================================================
-- EpiWeather ML System — Database Init Script
-- DB: kltn_epiweather
-- Schema: v2 (generalized, MLOps-ready)
-- ============================================================

-- Chạy lệnh này trước (với superuser):
--   CREATE DATABASE kltn_epiweather;
--   \c kltn_epiweather

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "pgcrypto";   -- gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS "pg_trgm";    -- fuzzy search country name (optional)

-- ============================================================
-- LAYER 0 — Master geography
-- ============================================================

CREATE TABLE IF NOT EXISTS countries (
    iso3              CHAR(3)          PRIMARY KEY,
    iso2              CHAR(2),
    country_name      VARCHAR(100)     NOT NULL,
    who_region        VARCHAR(10),
    who_region_enc    SMALLINT,
    latitude          DOUBLE PRECISION,
    longitude         DOUBLE PRECISION,
    population        BIGINT,
    created_at        TIMESTAMPTZ      DEFAULT NOW()
);

-- ============================================================
-- LAYER 1 — Catalog (config-driven)
-- ============================================================

CREATE TABLE IF NOT EXISTS diseases (
    id                SERIAL           PRIMARY KEY,
    code              VARCHAR(20)      NOT NULL UNIQUE,
    display_name      VARCHAR(100)     NOT NULL,
    target_variable   VARCHAR(50)      NOT NULL,
    target_transform  VARCHAR(20)      DEFAULT 'log1p'
                      CHECK (target_transform IN ('log1p', 'none', 'sqrt')),
    is_active         BOOLEAN          DEFAULT TRUE,
    description       TEXT,
    created_at        TIMESTAMPTZ      DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS data_sources (
    id                SERIAL           PRIMARY KEY,
    code              VARCHAR(30)      NOT NULL UNIQUE,
    source_type       VARCHAR(20)      NOT NULL
                      CHECK (source_type IN ('disease', 'weather', 'socioeconomic')),
    url               TEXT,
    update_frequency  VARCHAR(20),
    spatial_coverage  VARCHAR(50),
    temporal_start    DATE,
    is_active         BOOLEAN          DEFAULT TRUE,
    description       TEXT
);

CREATE TABLE IF NOT EXISTS weather_variables (
    id                SERIAL           PRIMARY KEY,
    code              VARCHAR(50)      NOT NULL UNIQUE,
    display_name      VARCHAR(100),
    unit              VARCHAR(20),
    source_id         INTEGER          REFERENCES data_sources(id),
    era5_variable     VARCHAR(100),
    description       TEXT,
    is_active         BOOLEAN          DEFAULT TRUE
);

-- ============================================================
-- LAYER 2 — Observations (partitioned by year)
-- ============================================================

CREATE TABLE IF NOT EXISTS disease_cases (
    id                BIGSERIAL,
    disease_id        INTEGER          NOT NULL REFERENCES diseases(id),
    iso3              CHAR(3)          NOT NULL REFERENCES countries(iso3),
    source_id         INTEGER          REFERENCES data_sources(id),
    iso_year          SMALLINT         NOT NULL,
    iso_week          SMALLINT         NOT NULL,
    raw_count         INTEGER,
    transformed_value DOUBLE PRECISION,
    data_quality      SMALLINT         DEFAULT 1
                      CHECK (data_quality IN (0, 1, 2)),
    ingested_at       TIMESTAMPTZ      DEFAULT NOW(),
    PRIMARY KEY (id, iso_year)
) PARTITION BY RANGE (iso_year);

CREATE TABLE IF NOT EXISTS disease_cases_2010 PARTITION OF disease_cases FOR VALUES FROM (2010) TO (2011);
CREATE TABLE IF NOT EXISTS disease_cases_2011 PARTITION OF disease_cases FOR VALUES FROM (2011) TO (2012);
CREATE TABLE IF NOT EXISTS disease_cases_2012 PARTITION OF disease_cases FOR VALUES FROM (2012) TO (2013);
CREATE TABLE IF NOT EXISTS disease_cases_2013 PARTITION OF disease_cases FOR VALUES FROM (2013) TO (2014);
CREATE TABLE IF NOT EXISTS disease_cases_2014 PARTITION OF disease_cases FOR VALUES FROM (2014) TO (2015);
CREATE TABLE IF NOT EXISTS disease_cases_2015 PARTITION OF disease_cases FOR VALUES FROM (2015) TO (2016);
CREATE TABLE IF NOT EXISTS disease_cases_2016 PARTITION OF disease_cases FOR VALUES FROM (2016) TO (2017);
CREATE TABLE IF NOT EXISTS disease_cases_2017 PARTITION OF disease_cases FOR VALUES FROM (2017) TO (2018);
CREATE TABLE IF NOT EXISTS disease_cases_2018 PARTITION OF disease_cases FOR VALUES FROM (2018) TO (2019);
CREATE TABLE IF NOT EXISTS disease_cases_2019 PARTITION OF disease_cases FOR VALUES FROM (2019) TO (2020);
CREATE TABLE IF NOT EXISTS disease_cases_2020 PARTITION OF disease_cases FOR VALUES FROM (2020) TO (2021);
CREATE TABLE IF NOT EXISTS disease_cases_2021 PARTITION OF disease_cases FOR VALUES FROM (2021) TO (2022);
CREATE TABLE IF NOT EXISTS disease_cases_2022 PARTITION OF disease_cases FOR VALUES FROM (2022) TO (2023);
CREATE TABLE IF NOT EXISTS disease_cases_default PARTITION OF disease_cases DEFAULT;

CREATE UNIQUE INDEX IF NOT EXISTS idx_disease_cases_unique
    ON disease_cases (disease_id, iso3, iso_year, iso_week, source_id);
CREATE INDEX IF NOT EXISTS idx_disease_cases_lookup
    ON disease_cases (iso3, disease_id, iso_year, iso_week);


CREATE TABLE IF NOT EXISTS weather_observations (
    id                BIGSERIAL,
    iso3              CHAR(3)          NOT NULL REFERENCES countries(iso3),
    source_id         INTEGER          NOT NULL REFERENCES data_sources(id),
    iso_year          SMALLINT         NOT NULL,
    iso_week          SMALLINT         NOT NULL,
    data              JSONB            NOT NULL,
    ingested_at       TIMESTAMPTZ      DEFAULT NOW(),
    PRIMARY KEY (id, iso_year)
) PARTITION BY RANGE (iso_year);

CREATE TABLE IF NOT EXISTS weather_obs_2010 PARTITION OF weather_observations FOR VALUES FROM (2010) TO (2011);
CREATE TABLE IF NOT EXISTS weather_obs_2011 PARTITION OF weather_observations FOR VALUES FROM (2011) TO (2012);
CREATE TABLE IF NOT EXISTS weather_obs_2012 PARTITION OF weather_observations FOR VALUES FROM (2012) TO (2013);
CREATE TABLE IF NOT EXISTS weather_obs_2013 PARTITION OF weather_observations FOR VALUES FROM (2013) TO (2014);
CREATE TABLE IF NOT EXISTS weather_obs_2014 PARTITION OF weather_observations FOR VALUES FROM (2014) TO (2015);
CREATE TABLE IF NOT EXISTS weather_obs_2015 PARTITION OF weather_observations FOR VALUES FROM (2015) TO (2016);
CREATE TABLE IF NOT EXISTS weather_obs_2016 PARTITION OF weather_observations FOR VALUES FROM (2016) TO (2017);
CREATE TABLE IF NOT EXISTS weather_obs_2017 PARTITION OF weather_observations FOR VALUES FROM (2017) TO (2018);
CREATE TABLE IF NOT EXISTS weather_obs_2018 PARTITION OF weather_observations FOR VALUES FROM (2018) TO (2019);
CREATE TABLE IF NOT EXISTS weather_obs_2019 PARTITION OF weather_observations FOR VALUES FROM (2019) TO (2020);
CREATE TABLE IF NOT EXISTS weather_obs_2022 PARTITION OF weather_observations FOR VALUES FROM (2022) TO (2023);
CREATE TABLE IF NOT EXISTS weather_obs_default PARTITION OF weather_observations DEFAULT;

CREATE UNIQUE INDEX IF NOT EXISTS idx_weather_unique
    ON weather_observations (iso3, source_id, iso_year, iso_week);
CREATE INDEX IF NOT EXISTS idx_weather_data_gin
    ON weather_observations USING GIN (data);

-- ============================================================
-- LAYER 3 — ML Pipeline
-- ============================================================

CREATE TABLE IF NOT EXISTS feature_configs (
    id                SERIAL           PRIMARY KEY,
    disease_id        INTEGER          NOT NULL REFERENCES diseases(id),
    feature_name      VARCHAR(100)     NOT NULL,
    source_type       VARCHAR(20)      NOT NULL
                      CHECK (source_type IN ('weather', 'ar_lag', 'geographic', 'socioeconomic', 'calendar')),
    weather_variable  VARCHAR(50),
    lag_weeks         SMALLINT         DEFAULT 0,
    transform         VARCHAR(20)      DEFAULT 'none',
    ar_target         VARCHAR(50),
    ar_lag_weeks      SMALLINT,
    is_active         BOOLEAN          DEFAULT TRUE,
    version_tag       VARCHAR(30),
    UNIQUE (disease_id, feature_name, version_tag)
);

CREATE TABLE IF NOT EXISTS model_versions (
    id                SERIAL           PRIMARY KEY,
    disease_id        INTEGER          NOT NULL REFERENCES diseases(id),
    version           VARCHAR(30)      NOT NULL,
    algorithm         VARCHAR(30)      DEFAULT 'XGBoost',
    description       TEXT,
    train_year_start  SMALLINT         NOT NULL,
    train_year_end    SMALLINT         NOT NULL,
    val_year          SMALLINT,
    feature_config_tag VARCHAR(30),
    hyperparams       JSONB,
    artifact_path     VARCHAR(255),
    is_active         BOOLEAN          DEFAULT FALSE,
    is_champion       BOOLEAN          DEFAULT FALSE,
    created_at        TIMESTAMPTZ      DEFAULT NOW(),
    UNIQUE (disease_id, version)
);

CREATE TABLE IF NOT EXISTS model_evaluations (
    id                SERIAL           PRIMARY KEY,
    model_version_id  INTEGER          NOT NULL REFERENCES model_versions(id),
    eval_set          VARCHAR(30)      NOT NULL,
    eval_type         VARCHAR(20)      NOT NULL
                      CHECK (eval_type IN ('holdout', 'cv', 'production_drift')),
    r2_score          DOUBLE PRECISION,
    mae               DOUBLE PRECISION,
    rmse              DOUBLE PRECISION,
    smape_nonzero     DOUBLE PRECISION,
    risk_macro_f1     DOUBLE PRECISION,
    risk_accuracy     DOUBLE PRECISION,
    risk_low_f1       DOUBLE PRECISION,
    risk_medium_f1    DOUBLE PRECISION,
    risk_high_f1      DOUBLE PRECISION,
    n_samples         INTEGER,
    notes             TEXT,
    evaluated_at      TIMESTAMPTZ      DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS risk_thresholds (
    id                SERIAL           PRIMARY KEY,
    disease_id        INTEGER          NOT NULL REFERENCES diseases(id),
    iso3              VARCHAR(10)      NOT NULL,
    q33               DOUBLE PRECISION NOT NULL,
    q67               DOUBLE PRECISION NOT NULL,
    n_nonzero_weeks   INTEGER,
    is_global_fallback BOOLEAN         DEFAULT FALSE,
    model_version_id  INTEGER          REFERENCES model_versions(id),
    updated_at        TIMESTAMPTZ      DEFAULT NOW(),
    UNIQUE (disease_id, iso3)
);

CREATE TABLE IF NOT EXISTS predictions (
    id                BIGSERIAL,
    disease_id        INTEGER          NOT NULL REFERENCES diseases(id),
    iso3              CHAR(3)          NOT NULL REFERENCES countries(iso3),
    iso_year          SMALLINT         NOT NULL,
    iso_week          SMALLINT         NOT NULL,
    horizon_weeks     SMALLINT         DEFAULT 1,
    predicted_value   DOUBLE PRECISION,
    predicted_cases   DOUBLE PRECISION,
    risk_level        VARCHAR(10)      CHECK (risk_level IN ('Low', 'Medium', 'High')),
    risk_q33          DOUBLE PRECISION,
    risk_q67          DOUBLE PRECISION,
    model_version_id  INTEGER          REFERENCES model_versions(id),
    features_snapshot JSONB,
    confidence_lo     DOUBLE PRECISION,
    confidence_hi     DOUBLE PRECISION,
    created_at        TIMESTAMPTZ      DEFAULT NOW(),
    PRIMARY KEY (id, iso_year)
) PARTITION BY RANGE (iso_year);

CREATE TABLE IF NOT EXISTS predictions_2022 PARTITION OF predictions FOR VALUES FROM (2022) TO (2023);
CREATE TABLE IF NOT EXISTS predictions_2023 PARTITION OF predictions FOR VALUES FROM (2023) TO (2024);
CREATE TABLE IF NOT EXISTS predictions_default PARTITION OF predictions DEFAULT;

CREATE UNIQUE INDEX IF NOT EXISTS idx_predictions_unique
    ON predictions (disease_id, iso3, iso_year, iso_week, horizon_weeks, model_version_id);
CREATE INDEX IF NOT EXISTS idx_predictions_dashboard
    ON predictions (disease_id, iso_year, iso_week, risk_level);

-- ============================================================
-- LAYER 4 — MLOps & Ops
-- ============================================================

CREATE TABLE IF NOT EXISTS pipeline_runs (
    run_id            UUID             PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_name     VARCHAR(50)      NOT NULL,
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
    metadata          JSONB
);

CREATE INDEX IF NOT EXISTS idx_pipeline_runs_status
    ON pipeline_runs (pipeline_name, status, started_at DESC);

CREATE TABLE IF NOT EXISTS data_quality_checks (
    id                SERIAL           PRIMARY KEY,
    run_id            UUID             REFERENCES pipeline_runs(run_id),
    check_name        VARCHAR(100)     NOT NULL,
    table_name        VARCHAR(50),
    iso_year          SMALLINT,
    iso_week          SMALLINT,
    threshold         DOUBLE PRECISION,
    actual_value      DOUBLE PRECISION,
    passed            BOOLEAN          NOT NULL,
    detail            TEXT,
    checked_at        TIMESTAMPTZ      DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS api_request_logs (
    id                BIGSERIAL        PRIMARY KEY,
    endpoint          VARCHAR(100),
    method            VARCHAR(10),
    disease           VARCHAR(20),
    iso3              CHAR(3),
    iso_year          SMALLINT,
    iso_week          SMALLINT,
    model_version_id  INTEGER,
    response_ms       INTEGER,
    status_code       SMALLINT,
    requested_at      TIMESTAMPTZ      DEFAULT NOW()
) PARTITION BY RANGE (requested_at);

CREATE TABLE IF NOT EXISTS api_logs_2026 PARTITION OF api_request_logs
    FOR VALUES FROM ('2026-01-01') TO ('2027-01-01');
CREATE TABLE IF NOT EXISTS api_logs_default PARTITION OF api_request_logs DEFAULT;

-- ============================================================
-- LAYER 5 — Materialized view (dashboard)
-- ============================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_latest_predictions AS
SELECT DISTINCT ON (p.disease_id, p.iso3, p.horizon_weeks)
    p.disease_id,
    d.code           AS disease_code,
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
JOIN diseases  d ON d.id  = p.disease_id
JOIN countries c ON c.iso3 = p.iso3
ORDER BY p.disease_id, p.iso3, p.horizon_weeks, p.created_at DESC;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_latest
    ON mv_latest_predictions (disease_id, iso3, horizon_weeks);

-- ============================================================
-- SEED DATA — Catalog
-- ============================================================

INSERT INTO diseases (code, display_name, target_variable, target_transform, description)
VALUES
    ('flu',    'Influenza',     'inf_cases',     'log1p', 'Seasonal influenza A+B — FluNet source'),
    ('dengue', 'Dengue fever',  'dengue_total',  'log1p', 'Dengue hemorrhagic fever — WHO PAHO source')
ON CONFLICT (code) DO NOTHING;

INSERT INTO data_sources (code, source_type, update_frequency, spatial_coverage, description)
VALUES
    ('FluNet',         'disease', 'weekly',  'global',   'WHO FluNet — influenza surveillance'),
    ('WHO_PAHO',       'disease', 'weekly',  'americas', 'PAHO dengue surveillance'),
    ('ERA5',           'weather', 'monthly', 'global',   'ECMWF ERA5 reanalysis — 17 variables'),
    ('OpenWeatherMap', 'weather', 'realtime','global',   'Real-time weather API for serving'),
    ('NOAA_ENSO',      'weather', 'monthly', 'global',   'NOAA ONI/MEI ENSO indices')
ON CONFLICT (code) DO NOTHING;

INSERT INTO weather_variables (code, display_name, unit, source_id, era5_variable)
VALUES
    ('temp_c',          '2m Temperature',           '°C',     3, '2m_temperature'),
    ('temp_min_c',      '2m Temp Min',              '°C',     3, 'minimum_2m_air_temperature'),
    ('temp_max_c',      '2m Temp Max',              '°C',     3, 'maximum_2m_air_temperature'),
    ('dewpoint_c',      '2m Dewpoint',              '°C',     3, '2m_dewpoint_temperature'),
    ('humidity_pct',    'Relative Humidity',         '%',      3, NULL),
    ('precip_mm',       'Total Precipitation',       'mm',     3, 'total_precipitation'),
    ('solar_wm2',       'Surface Solar Radiation',   'W/m²',   3, 'surface_solar_radiation_downwards'),
    ('wind_u_ms',       'U-wind Component',          'm/s',    3, '10m_u_component_of_wind'),
    ('wind_v_ms',       'V-wind Component',          'm/s',    3, '10m_v_component_of_wind'),
    ('wind_speed_ms',   'Wind Speed',                'm/s',    3, NULL),
    ('pressure_hpa',    'Surface Pressure',          'hPa',    3, 'surface_pressure'),
    ('blh_m',           'Boundary Layer Height',     'm',      3, 'boundary_layer_height'),
    ('soil_temp_c',     'Soil Temperature',          '°C',     3, 'soil_temperature_level_1'),
    ('total_water_col', 'Total Column Water Vapour', 'kg/m²',  3, 'total_column_water_vapour'),
    ('cape_jkg',        'CAPE',                      'J/kg',   3, 'convective_available_potential_energy'),
    ('snowfall_m',      'Snowfall',                  'm',      3, 'snowfall'),
    -- ENSO (thêm sau, không cần ALTER TABLE)
    ('oni_index',       'Oceanic Niño Index',        'anomaly',5, NULL),
    ('mei_index',       'Multivariate ENSO Index',   'anomaly',5, NULL)
ON CONFLICT (code) DO NOTHING;
