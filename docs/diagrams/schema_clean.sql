-- EpiWeather - Schema for ERD (drawDB compatible)
-- 14 parent tables, explicit FOREIGN KEY constraints

CREATE TABLE countries (
    iso3           char(3)       PRIMARY KEY,
    iso2           char(2),
    country_name   varchar(100)  NOT NULL,
    who_region     varchar(10),
    who_region_enc smallint,
    latitude       double precision,
    longitude      double precision,
    population     bigint,
    created_at     timestamp
);

CREATE TABLE diseases (
    id               serial        PRIMARY KEY,
    code             varchar(20)   NOT NULL UNIQUE,
    display_name     varchar(100)  NOT NULL,
    display_name_vi  varchar(100),
    target_variable  varchar(50)   NOT NULL,
    target_transform varchar(20)   DEFAULT 'log1p',
    is_active        boolean       DEFAULT true,
    description      text,
    description_vi   text,
    created_at       timestamp
);

CREATE TABLE data_sources (
    id               serial        PRIMARY KEY,
    code             varchar(30)   NOT NULL UNIQUE,
    source_type      varchar(20)   NOT NULL,
    url              text,
    update_frequency varchar(20),
    spatial_coverage varchar(50),
    temporal_start   date,
    is_active        boolean       DEFAULT true,
    description      text
);

CREATE TABLE weather_variables (
    id            serial        PRIMARY KEY,
    code          varchar(50)   NOT NULL UNIQUE,
    display_name  varchar(100),
    unit          varchar(20),
    source_id     integer,
    era5_variable varchar(100),
    description   text,
    is_active     boolean       DEFAULT true,
    FOREIGN KEY (source_id) REFERENCES data_sources(id)
);

CREATE TABLE disease_cases (
    id                bigint    PRIMARY KEY,
    disease_id        integer   NOT NULL,
    iso3              char(3)   NOT NULL,
    source_id         integer,
    iso_year          smallint  NOT NULL,
    iso_week          smallint  NOT NULL,
    raw_count         integer,
    transformed_value double precision,
    data_quality      smallint  DEFAULT 1,
    ingested_at       timestamp,
    FOREIGN KEY (disease_id) REFERENCES diseases(id),
    FOREIGN KEY (iso3)       REFERENCES countries(iso3),
    FOREIGN KEY (source_id)  REFERENCES data_sources(id)
);

CREATE TABLE weather_observations (
    id          bigint    PRIMARY KEY,
    iso3        char(3)   NOT NULL,
    source_id   integer   NOT NULL,
    iso_year    smallint  NOT NULL,
    iso_week    smallint  NOT NULL,
    data        text      NOT NULL,
    ingested_at timestamp,
    FOREIGN KEY (iso3)      REFERENCES countries(iso3),
    FOREIGN KEY (source_id) REFERENCES data_sources(id)
);

CREATE TABLE feature_configs (
    id               serial       PRIMARY KEY,
    disease_id       integer      NOT NULL,
    feature_name     varchar(100) NOT NULL,
    display_name_vi  varchar(150),
    description_vi   varchar(500),
    source_type      varchar(20)  NOT NULL,
    weather_variable varchar(50),
    lag_weeks        smallint     DEFAULT 0,
    transform        varchar(20)  DEFAULT 'none',
    ar_target        varchar(50),
    ar_lag_weeks     smallint,
    is_active        boolean      DEFAULT true,
    version_tag      varchar(30),
    FOREIGN KEY (disease_id) REFERENCES diseases(id)
);

CREATE TABLE feature_snapshots (
    disease_id      integer     NOT NULL,
    iso3            char(3)     NOT NULL,
    iso_year        smallint    NOT NULL,
    iso_week        smallint    NOT NULL,
    feature_version varchar(10) NOT NULL DEFAULT 'v1',
    features        text        NOT NULL,
    created_at      timestamp,
    updated_at      timestamp,
    PRIMARY KEY (disease_id, iso3, iso_year, iso_week, feature_version),
    FOREIGN KEY (disease_id) REFERENCES diseases(id),
    FOREIGN KEY (iso3)       REFERENCES countries(iso3)
);

CREATE TABLE model_versions (
    id                 serial       PRIMARY KEY,
    disease_id         integer      NOT NULL,
    version            varchar(30)  NOT NULL,
    algorithm          varchar(30)  DEFAULT 'XGBoost',
    description        text,
    train_year_start   smallint     NOT NULL,
    train_year_end     smallint     NOT NULL,
    val_year           smallint,
    feature_config_tag varchar(30),
    hyperparams        text,
    artifact_path      varchar(255),
    is_active          boolean      DEFAULT false,
    is_champion        boolean      DEFAULT false,
    created_at         timestamp,
    UNIQUE (disease_id, version),
    FOREIGN KEY (disease_id) REFERENCES diseases(id)
);

CREATE TABLE model_evaluations (
    id               serial      PRIMARY KEY,
    model_version_id integer     NOT NULL,
    eval_set         varchar(30) NOT NULL,
    eval_type        varchar(20) NOT NULL,
    r2_score         double precision,
    mae              double precision,
    rmse             double precision,
    smape_nonzero    double precision,
    risk_macro_f1    double precision,
    risk_accuracy    double precision,
    risk_low_f1      double precision,
    risk_medium_f1   double precision,
    risk_high_f1     double precision,
    n_samples        integer,
    notes            text,
    evaluated_at     timestamp,
    FOREIGN KEY (model_version_id) REFERENCES model_versions(id)
);

CREATE TABLE predictions (
    id                bigint   PRIMARY KEY,
    disease_id        integer  NOT NULL,
    iso3              char(3)  NOT NULL,
    iso_year          smallint NOT NULL,
    iso_week          smallint NOT NULL,
    horizon_weeks     smallint DEFAULT 1,
    predicted_value   double precision,
    predicted_cases   double precision,
    risk_level        varchar(10),
    risk_probability  double precision,
    model_version_id  integer,
    features_snapshot text,
    confidence_lo     double precision,
    confidence_hi     double precision,
    created_at        timestamp,
    FOREIGN KEY (disease_id)       REFERENCES diseases(id),
    FOREIGN KEY (iso3)             REFERENCES countries(iso3),
    FOREIGN KEY (model_version_id) REFERENCES model_versions(id)
);

CREATE TABLE pipeline_runs (
    run_id           char(36)    PRIMARY KEY,
    pipeline_name    varchar(50) NOT NULL,
    pipeline_version varchar(20),
    trigger_type     varchar(20) DEFAULT 'manual',
    status           varchar(20) NOT NULL,
    iso_year         smallint,
    iso_week         smallint,
    started_at       timestamp   NOT NULL,
    completed_at     timestamp,
    duration_sec     double precision,
    rows_processed   integer,
    rows_inserted    integer,
    rows_updated     integer,
    rows_skipped     integer,
    errors           text,
    metadata         text
);

CREATE TABLE data_quality_checks (
    id           serial       PRIMARY KEY,
    run_id       char(36),
    check_name   varchar(100) NOT NULL,
    table_name   varchar(50),
    iso_year     smallint,
    iso_week     smallint,
    threshold    double precision,
    actual_value double precision,
    passed       boolean      NOT NULL,
    detail       text,
    checked_at   timestamp,
    FOREIGN KEY (run_id) REFERENCES pipeline_runs(run_id)
);

CREATE TABLE api_request_logs (
    id               bigint      PRIMARY KEY,
    endpoint         varchar(100),
    method           varchar(10),
    disease          varchar(20),
    iso3             char(3),
    iso_year         smallint,
    iso_week         smallint,
    model_version_id integer,
    response_ms      integer,
    status_code      smallint,
    requested_at     timestamp   NOT NULL
);
