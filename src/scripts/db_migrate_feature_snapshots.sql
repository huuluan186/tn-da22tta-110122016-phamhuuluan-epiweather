-- ============================================================
-- Migration — feature_snapshots
-- Phase C-2: lưu feature vector pre-computed per (disease, iso3, week)
-- ============================================================
-- Sau này Phase A-2 feature_builder sẽ INSERT/UPDATE vào cùng bảng này
-- khi có realtime data từ FluNet + OpenWeatherMap.
-- ============================================================

CREATE TABLE IF NOT EXISTS feature_snapshots (
    disease_id       INTEGER       NOT NULL REFERENCES diseases(id),
    iso3             CHAR(3)       NOT NULL REFERENCES countries(iso3),
    iso_year         SMALLINT      NOT NULL,
    iso_week         SMALLINT      NOT NULL,
    features         JSONB         NOT NULL,
    feature_version  VARCHAR(10)   DEFAULT 'v1',
    created_at       TIMESTAMPTZ   DEFAULT NOW(),
    updated_at       TIMESTAMPTZ   DEFAULT NOW(),
    PRIMARY KEY (disease_id, iso3, iso_year, iso_week, feature_version)
);

-- Lookup nhanh khi cần truy vấn theo (disease, year, week) không quan tâm iso3
CREATE INDEX IF NOT EXISTS idx_feature_snapshots_lookup
    ON feature_snapshots (disease_id, iso_year, iso_week);

-- Lookup nhanh khi cần lấy time-series 1 nước
CREATE INDEX IF NOT EXISTS idx_feature_snapshots_country
    ON feature_snapshots (disease_id, iso3, iso_year, iso_week);

COMMENT ON TABLE feature_snapshots IS
    'Pre-computed feature vectors cho ML inference. JSONB cho phép mở rộng feature set không cần ALTER TABLE.';
COMMENT ON COLUMN feature_snapshots.features IS
    'JSON dict: feature_name -> float. Ví dụ {"flu_log_lag1": 4.5, "temp_c_lag3": 25.6, ...}';
