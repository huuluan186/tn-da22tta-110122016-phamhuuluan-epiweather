# Database Schema v2 - Mô tả theo tầng

Tài liệu này trình bày CSDL theo từng tầng để dễ theo dõi: đang viết tới tầng nào, bảng nào, cột nào. Mỗi bảng có bảng cột gồm: tên cột, kiểu dữ liệu, PK/FK, ý nghĩa.

Tổng số bảng: **15** (14 bảng nghiệp vụ + 1 bảng hệ thống `alembic_version`; không tính materialized view).

---

## (1) Tầng 0 - Địa lý chuẩn

### Bảng 01 - `countries`
**Mục đích:** danh mục quốc gia dùng xuyên suốt hệ thống.

| Tên cột | Kiểu dữ liệu | PK/FK | Ý nghĩa |
|---|---|---|---|
| `iso3` | CHAR(3) | PK | Mã ISO alpha-3 (khóa chính) |
| `iso2` | CHAR(2) | - | Mã ISO alpha-2 |
| `country_name` | VARCHAR(100) | - | Tên quốc gia |
| `who_region` | VARCHAR(10) | - | Vùng WHO (AFR, AMR, EMR, EUR, SEAR, WPR) |
| `who_region_enc` | SMALLINT | - | Mã hóa số vùng WHO (0-5) |
| `latitude` | DOUBLE PRECISION | - | Vĩ độ centroid |
| `longitude` | DOUBLE PRECISION | - | Kinh độ centroid |
| `population` | BIGINT | - | Dân số |
| `created_at` | TIMESTAMPTZ | - | Thời điểm tạo bản ghi |

**Quan hệ:** `countries` 1-N với `disease_cases`, `weather_observations`, `feature_snapshots`, `predictions`.

---

## (2) Tầng 1 - Catalog (config-driven)

### Bảng 02 - `diseases`
**Mục đích:** danh mục bệnh (flu, dengue) và metadata liên quan.

| Tên cột | Kiểu dữ liệu | PK/FK | Ý nghĩa |
|---|---|---|---|
| `id` | SERIAL/INTEGER | PK | Khóa chính |
| `code` | VARCHAR(20) | - | Mã bệnh (flu, dengue) |
| `display_name` | VARCHAR(100) | - | Tên hiển thị (tiếng Anh) |
| `display_name_vi` | VARCHAR(100) | - | Tên hiển thị tiếng Việt |
| `target_variable` | VARCHAR(50) | - | Tên biến mục tiêu gốc |
| `target_transform` | VARCHAR(20) | - | Transform (log1p/none/sqrt) |
| `is_active` | BOOLEAN | - | Trạng thái sử dụng |
| `description` | TEXT | - | Mô tả (tiếng Anh) |
| `description_vi` | TEXT | - | Mô tả tiếng Việt |
| `created_at` | TIMESTAMPTZ | - | Thời điểm tạo |

**Quan hệ:** `diseases` 1-N với `disease_cases`, `feature_configs`, `model_versions`, `predictions`.

---

### Bảng 03 - `data_sources`
**Mục đích:** danh mục nguồn dữ liệu (FluNet, OpenDengue, ERA5, Open-Meteo).

| Tên cột | Kiểu dữ liệu | PK/FK | Ý nghĩa |
|---|---|---|---|
| `id` | SERIAL/INTEGER | PK | Khóa chính |
| `code` | VARCHAR(30) | - | Mã nguồn dữ liệu |
| `source_type` | VARCHAR(20) | - | Loại nguồn (disease/weather) |
| `url` | TEXT | - | Link nguồn |
| `update_frequency` | VARCHAR(20) | - | Tần suất cập nhật |
| `spatial_coverage` | VARCHAR(50) | - | Phạm vi phủ |
| `temporal_start` | DATE | - | Mốc thời gian bắt đầu |
| `is_active` | BOOLEAN | - | Trạng thái sử dụng |
| `description` | TEXT | - | Mô tả |

**Quan hệ:** `data_sources` 1-N với `disease_cases`, `weather_observations`, `weather_variables`.

---

### Bảng 04 - `weather_variables`
**Mục đích:** danh mục biến thời tiết (17 biến ERA5 + biến dẫn xuất).

| Tên cột | Kiểu dữ liệu | PK/FK | Ý nghĩa |
|---|---|---|---|
| `id` | SERIAL/INTEGER | PK | Khóa chính |
| `code` | VARCHAR(50) | - | Mã biến (temp_c, humidity_pct, ...) |
| `display_name` | VARCHAR(100) | - | Tên hiển thị |
| `unit` | VARCHAR(20) | - | Đơn vị |
| `source_id` | INTEGER | FK → `data_sources.id` | Nguồn dữ liệu |
| `era5_variable` | VARCHAR(100) | - | Tên gốc trong ERA5 |
| `description` | TEXT | - | Mô tả |
| `is_active` | BOOLEAN | - | Trạng thái sử dụng |

---

## (3) Tầng 2 - Observations (time-series)

### Bảng 05 - `disease_cases`
**Mục đích:** lưu số ca bệnh theo tuần ISO (dùng cho train và lag features).

| Tên cột | Kiểu dữ liệu | PK/FK | Ý nghĩa |
|---|---|---|---|
| `id` | BIGSERIAL | PK | Khóa chính |
| `disease_id` | INTEGER | FK → `diseases.id` | Bệnh |
| `iso3` | CHAR(3) | FK → `countries.iso3` | Quốc gia |
| `source_id` | INTEGER | FK → `data_sources.id` | Nguồn |
| `iso_year` | SMALLINT | - | Năm ISO |
| `iso_week` | SMALLINT | - | Tuần ISO |
| `raw_count` | INTEGER | - | Số ca gốc |
| `transformed_value` | DOUBLE PRECISION | - | Giá trị đã transform (log1p) |
| `data_quality` | SMALLINT | - | Chất lượng dữ liệu (reported/estimated) |
| `ingested_at` | TIMESTAMPTZ | - | Thời điểm nạp |

**Ghi chú:** bảng **partition theo `iso_year`**.

---

### Bảng 06 - `weather_observations`
**Mục đích:** lưu thời tiết theo tuần ISO, dạng JSON để linh hoạt.

| Tên cột | Kiểu dữ liệu | PK/FK | Ý nghĩa |
|---|---|---|---|
| `id` | BIGSERIAL | PK | Khóa chính |
| `iso3` | CHAR(3) | FK → `countries.iso3` | Quốc gia |
| `source_id` | INTEGER | FK → `data_sources.id` | Nguồn |
| `iso_year` | SMALLINT | - | Năm ISO |
| `iso_week` | SMALLINT | - | Tuần ISO |
| `data` | JSONB | - | Map biến → giá trị (temp, humidity, precip, solar, ...) |
| `ingested_at` | TIMESTAMPTZ | - | Thời điểm nạp |

**Ghi chú:** bảng **partition theo `iso_year`**.

---

## (4) Tầng 3 - ML pipeline

### Bảng 07 - `feature_configs`
**Mục đích:** registry các feature theo bệnh và version.

| Tên cột | Kiểu dữ liệu | PK/FK | Ý nghĩa |
|---|---|---|---|
| `id` | SERIAL/INTEGER | PK | Khóa chính |
| `disease_id` | INTEGER | FK → `diseases.id` | Bệnh |
| `feature_name` | VARCHAR(100) | - | Tên feature |
| `display_name_vi` | VARCHAR(150) | - | Tên hiển thị tiếng Việt |
| `description_vi` | VARCHAR(500) | - | Mô tả tiếng Việt |
| `source_type` | VARCHAR(20) | - | weather/ar_lag/geographic/calendar |
| `weather_variable` | VARCHAR(50) | - | Tên biến thời tiết (nếu có) |
| `lag_weeks` | SMALLINT | - | Độ trễ tuần |
| `transform` | VARCHAR(20) | - | Transform (none/log1p/...) |
| `ar_target` | VARCHAR(50) | - | Target cho AR lag (nếu có) |
| `ar_lag_weeks` | SMALLINT | - | Độ trễ AR |
| `is_active` | BOOLEAN | - | Trạng thái sử dụng |
| `version_tag` | VARCHAR(30) | - | Tag feature set |

---

### Bảng 08 - `feature_snapshots`
**Mục đích:** cache feature vector theo tuần để inference nhanh.

| Tên cột | Kiểu dữ liệu | PK/FK | Ý nghĩa |
|---|---|---|---|
| `disease_id` | INTEGER | PK, FK → `diseases.id` | Bệnh (thành phần khóa ghép) |
| `iso3` | CHAR(3) | PK, FK → `countries.iso3` | Quốc gia (thành phần khóa ghép) |
| `iso_year` | SMALLINT | PK | Năm ISO |
| `iso_week` | SMALLINT | PK | Tuần ISO |
| `feature_version` | VARCHAR(10) | PK | Version feature set |
| `features` | JSONB | - | Map feature → giá trị |
| `created_at` | TIMESTAMPTZ | - | Thời điểm tạo |
| `updated_at` | TIMESTAMPTZ | - | Thời điểm cập nhật |

---

### Bảng 09 - `model_versions`
**Mục đích:** quản lý version model.

| Tên cột | Kiểu dữ liệu | PK/FK | Ý nghĩa |
|---|---|---|---|
| `id` | SERIAL/INTEGER | PK | Khóa chính |
| `disease_id` | INTEGER | FK → `diseases.id` | Bệnh |
| `version` | VARCHAR(30) | - | Version (v1, v2, ...) |
| `algorithm` | VARCHAR(30) | - | LightGBM/RF/XGBoost |
| `description` | TEXT | - | Mô tả mô hình |
| `train_year_start` | SMALLINT | - | Năm bắt đầu train |
| `train_year_end` | SMALLINT | - | Năm kết thúc train |
| `val_year` | SMALLINT | - | Năm validation |
| `feature_config_tag` | VARCHAR(30) | - | Tag feature set |
| `hyperparams` | JSONB | - | Siêu tham số |
| `artifact_path` | VARCHAR(255) | - | Đường dẫn .pkl |
| `is_active` | BOOLEAN | - | Đang sử dụng |
| `is_champion` | BOOLEAN | - | Model tốt nhất |
| `created_at` | TIMESTAMPTZ | - | Thời điểm tạo |

---

### Bảng 10 - `model_evaluations`
**Mục đích:** lưu kết quả đánh giá.

| Tên cột | Kiểu dữ liệu | PK/FK | Ý nghĩa |
|---|---|---|---|
| `id` | SERIAL/INTEGER | PK | Khóa chính |
| `model_version_id` | INTEGER | FK → `model_versions.id` | Version model |
| `eval_set` | VARCHAR(30) | - | Tập đánh giá (cv/val_2022/...) |
| `eval_type` | VARCHAR(20) | - | Loại đánh giá (cv/holdout/drift) |
| `r2_score` | DOUBLE PRECISION | - | R² |
| `mae` | DOUBLE PRECISION | - | MAE |
| `rmse` | DOUBLE PRECISION | - | RMSE |
| `smape_nonzero` | DOUBLE PRECISION | - | sMAPE non-zero |
| `risk_macro_f1` | DOUBLE PRECISION | - | Macro-F1 |
| `risk_accuracy` | DOUBLE PRECISION | - | Độ chính xác phân loại |
| `risk_low_f1` | DOUBLE PRECISION | - | F1 Low |
| `risk_medium_f1` | DOUBLE PRECISION | - | F1 Medium |
| `risk_high_f1` | DOUBLE PRECISION | - | F1 High |
| `n_samples` | INTEGER | - | Số mẫu |
| `notes` | TEXT | - | Ghi chú |
| `evaluated_at` | TIMESTAMPTZ | - | Thời điểm đánh giá |

---

### Bảng 11 - `predictions`
**Mục đích:** lưu dự báo theo tuần để phục vụ dashboard.

| Tên cột | Kiểu dữ liệu | PK/FK | Ý nghĩa |
|---|---|---|---|
| `id` | BIGSERIAL | PK | Khóa chính |
| `disease_id` | INTEGER | FK → `diseases.id` | Bệnh |
| `iso3` | CHAR(3) | FK → `countries.iso3` | Quốc gia |
| `iso_year` | SMALLINT | - | Năm ISO |
| `iso_week` | SMALLINT | - | Tuần ISO |
| `horizon_weeks` | SMALLINT | - | H=1..4 |
| `predicted_value` | DOUBLE PRECISION | - | Output log1p |
| `predicted_cases` | DOUBLE PRECISION | - | expm1 cho hiển thị |
| `risk_level` | VARCHAR(10) | - | Low/Medium/High |
| `risk_probability` | DOUBLE PRECISION | - | P(High) từ classifier |
| `model_version_id` | INTEGER | FK → `model_versions.id` | Version model |
| `features_snapshot` | JSONB | - | Feature vector tại thời điểm predict |
| `confidence_lo` | DOUBLE PRECISION | - | Cận dưới interval |
| `confidence_hi` | DOUBLE PRECISION | - | Cận trên interval |
| `created_at` | TIMESTAMPTZ | - | Thời điểm tạo |

**Ghi chú:** bảng **partition theo `iso_year`**.

---

## (5) Tầng 4 - MLOps/Ops

### Bảng 12 - `pipeline_runs`
**Mục đích:** log mỗi lần chạy pipeline.

| Tên cột | Kiểu dữ liệu | PK/FK | Ý nghĩa |
|---|---|---|---|
| `run_id` | UUID | PK | Khóa chính |
| `pipeline_name` | VARCHAR(50) | - | Tên job |
| `pipeline_version` | VARCHAR(20) | - | Version pipeline |
| `trigger_type` | VARCHAR(20) | - | manual/scheduled/api |
| `status` | VARCHAR(20) | - | running/success/failed/partial |
| `iso_year` | SMALLINT | - | Năm xử lý |
| `iso_week` | SMALLINT | - | Tuần xử lý |
| `started_at` | TIMESTAMPTZ | - | Bắt đầu |
| `completed_at` | TIMESTAMPTZ | - | Kết thúc |
| `duration_sec` | DOUBLE PRECISION | - | Thời lượng |
| `rows_processed` | INTEGER | - | Tổng xử lý |
| `rows_inserted` | INTEGER | - | Số insert |
| `rows_updated` | INTEGER | - | Số update |
| `rows_skipped` | INTEGER | - | Số skip |
| `errors` | JSONB | - | Lỗi chi tiết |
| `metadata` | JSONB | - | Metadata bổ sung |

---

### Bảng 13 - `data_quality_checks`
**Mục đích:** lưu kết quả kiểm tra chất lượng dữ liệu.

| Tên cột | Kiểu dữ liệu | PK/FK | Ý nghĩa |
|---|---|---|---|
| `id` | SERIAL/INTEGER | PK | Khóa chính |
| `run_id` | UUID | FK → `pipeline_runs.run_id` | Lần chạy pipeline |
| `check_name` | VARCHAR(100) | - | Tên check |
| `table_name` | VARCHAR(50) | - | Bảng được kiểm tra |
| `iso_year` | SMALLINT | - | Năm ISO |
| `iso_week` | SMALLINT | - | Tuần ISO |
| `threshold` | DOUBLE PRECISION | - | Ngưỡng |
| `actual_value` | DOUBLE PRECISION | - | Giá trị thực |
| `passed` | BOOLEAN | - | Pass/Fail |
| `detail` | TEXT | - | Diễn giải |
| `checked_at` | TIMESTAMPTZ | - | Thời điểm check |

---

### Bảng 14 - `api_request_logs`
**Mục đích:** theo dõi request API trong production.

| Tên cột | Kiểu dữ liệu | PK/FK | Ý nghĩa |
|---|---|---|---|
| `id` | BIGSERIAL | PK | Khóa chính |
| `endpoint` | VARCHAR(100) | - | Endpoint gọi |
| `method` | VARCHAR(10) | - | HTTP method |
| `disease` | VARCHAR(20) | - | Bệnh |
| `iso3` | CHAR(3) | - | Quốc gia |
| `iso_year` | SMALLINT | - | Năm ISO |
| `iso_week` | SMALLINT | - | Tuần ISO |
| `model_version_id` | INTEGER | - | Version model (tham chiếu logic, không ràng buộc FK) |
| `response_ms` | INTEGER | - | Latency |
| `status_code` | SMALLINT | - | Mã phản hồi |
| `requested_at` | TIMESTAMPTZ | PK | Thời điểm gọi (khóa phân mảnh) |

**Ghi chú:** bảng **partition theo thời gian**.

---

### Bảng 15 - `alembic_version`
**Mục đích:** bảng hệ thống do công cụ migration Alembic sinh ra, lưu mã phiên bản schema hiện tại. Không thuộc nghiệp vụ, nhưng tồn tại thật trong cơ sở dữ liệu.

| Tên cột | Kiểu dữ liệu | PK/FK | Ý nghĩa |
|---|---|---|---|
| `version_num` | VARCHAR(32) | PK | Mã phiên bản migration hiện tại |

**Ghi chú:** chỉ có 1 dòng.

---

## (6) Tầng 5 - Materialized view (dashboard performance)

### View `mv_latest_predictions`
**Mục đích:** lấy dự báo mới nhất cho mỗi (disease, iso3, horizon) để dashboard truy vấn nhanh.

| Tên cột | Kiểu dữ liệu | PK/FK | Ý nghĩa |
|---|---|---|---|
| `disease_id` | INTEGER | - | Bệnh |
| `disease_code` | VARCHAR(20) | - | Mã bệnh (flu/dengue) |
| `iso3` | CHAR(3) | - | Quốc gia |
| `country_name` | VARCHAR(100) | - | Tên quốc gia |
| `who_region` | VARCHAR(10) | - | Vùng WHO |
| `iso_year` | SMALLINT | - | Năm ISO |
| `iso_week` | SMALLINT | - | Tuần ISO |
| `horizon_weeks` | SMALLINT | - | H=1..4 |
| `predicted_cases` | DOUBLE PRECISION | - | Số ca dự báo (scale gốc) |
| `risk_level` | VARCHAR(10) | - | Low/Medium/High |
| `created_at` | TIMESTAMPTZ | - | Thời điểm tạo dự báo |

---

## Quan hệ chính (tóm tắt)

1. `countries` 1-N `disease_cases`, `weather_observations`, `feature_snapshots`, `predictions`.
2. `diseases` 1-N `disease_cases`, `feature_configs`, `model_versions`, `predictions`.
3. `model_versions` 1-N `model_evaluations`, `predictions`.
4. `pipeline_runs` 1-N `data_quality_checks`.

---

## Luồng dữ liệu tóm tắt

1. **Sync dữ liệu** → ghi `disease_cases`, `weather_observations`.
2. **Build features** → lưu `feature_snapshots` để inference nhanh.
3. **Predict** → ghi `predictions` (kèm `risk_level`, `risk_probability`).
4. **Dashboard** → đọc `mv_latest_predictions` theo tuần.
5. **MLOps** → log `pipeline_runs`, kiểm tra `data_quality_checks`.