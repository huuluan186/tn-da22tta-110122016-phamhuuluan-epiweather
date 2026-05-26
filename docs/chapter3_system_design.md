# CHƯƠNG 3: PHÂN TÍCH VÀ THIẾT KẾ HỆ THỐNG

## 3.1. Kiến trúc tổng thể hệ thống

Hệ thống EpiWeather được thiết kế theo kiến trúc ba tầng (three-tier architecture), phân tách rõ ràng giữa tầng dữ liệu, tầng xử lý và tầng giao diện. Mục tiêu thiết kế là đảm bảo khả năng mở rộng (extensibility) — có thể bổ sung bệnh mới hoặc nguồn dữ liệu mới mà không cần thay đổi cấu trúc lõi — đồng thời sẵn sàng triển khai trong môi trường production.

Toàn bộ luồng dữ liệu của hệ thống trải qua năm giai đoạn chính, được mô tả trong Hình 3.1:

```
[Thu thập dữ liệu]          [Huấn luyện mô hình]       [Nạp CSDL]
  WHO FluNet ─┐               Google Colab               load_db.py
  OpenDengue ─┼─► ETL ─────► Feature Eng. ─► XGBoost ─► PostgreSQL
  ERA5 ECMWF ─┘               Walk-forward CV              │
                                                            │
[Phục vụ dự báo]                                [Hiển thị]│
  FastAPI ◄─── PostgreSQL ◄───────────────────────────────┘
     │            (predictions,                   React + Leaflet.js
     │             risk_thresholds)               Dashboard cảnh báo
     └─── XGBoost .pkl (in-memory serve)
```
*Hình 3.1. Sơ đồ kiến trúc tổng thể hệ thống EpiWeather.*

**Tầng dữ liệu** bao gồm hệ quản trị cơ sở dữ liệu PostgreSQL lưu trữ toàn bộ dữ liệu quan sát, kết quả dự báo, siêu dữ liệu mô hình và nhật ký hệ thống. Dữ liệu ca bệnh từ WHO FluNet và OpenDengue cùng dữ liệu khí hậu từ ERA5 được nạp vào tầng này thông qua script ETL sau quá trình tiền xử lý.

**Tầng xử lý** đảm nhận hai vai trò: (1) huấn luyện mô hình học máy trên Google Colab với dữ liệu lịch sử 2010–2019; (2) phục vụ dự báo thời gian thực thông qua FastAPI, nạp mô hình từ file .pkl và truy vấn đặc trưng từ cơ sở dữ liệu.

**Tầng giao diện** là ứng dụng web React.js với bản đồ tương tác Leaflet.js hiển thị mức độ cảnh báo nguy cơ dịch bệnh theo tuần cho từng quốc gia, và dashboard thống kê xu hướng dịch bệnh theo thời gian.

## 3.2. Cài đặt môi trường và công cụ

Môi trường phát triển của đề tài được chia thành hai phần tách biệt theo chức năng: môi trường huấn luyện mô hình trên đám mây và môi trường phát triển hệ thống trên máy cục bộ.

**Môi trường huấn luyện (Google Colab):** Toàn bộ quá trình thu thập và xử lý dữ liệu ERA5, feature engineering và huấn luyện mô hình được thực hiện trên Google Colab với GPU T4. Lựa chọn này xuất phát từ khối lượng dữ liệu ERA5 lớn (6,2 GB định dạng NetCDF) và yêu cầu tính toán cao của quá trình Optuna hyperparameter tuning. Kết quả huấn luyện (file model .pkl, danh sách feature, ngưỡng nguy cơ) được lưu vào Google Drive và đồng bộ về máy cục bộ để tích hợp vào hệ thống phục vụ.

**Môi trường phát triển cục bộ (Windows 11):** Bao gồm Python 3.11, PostgreSQL 15, Node.js 20 và Docker Desktop. Đây là môi trường phát triển backend FastAPI và frontend React, cũng là môi trường tích hợp toàn bộ hệ thống trước khi đóng gói bằng Docker Compose.

Bảng 3.1 tóm tắt các công nghệ và thư viện chính được sử dụng trong đề tài.

*Bảng 3.1. Công nghệ và thư viện sử dụng.*

| Tầng | Công nghệ / Thư viện | Phiên bản | Mục đích |
|---|---|---|---|
| Xử lý dữ liệu | pandas, numpy, xarray | 2.x, 1.x, 2.x | ETL, feature engineering |
| Spatial mapping | scikit-learn (KDTree) | 1.4 | Ánh xạ lưới ERA5 → iso3 |
| Mô hình ML | XGBoost | 2.0 | Huấn luyện và inference |
| Mô hình baseline | Prophet | 1.1 | So sánh với XGBoost |
| Tối ưu hyperparameter | Optuna | 3.x | Tìm kiếm siêu tham số |
| Cơ sở dữ liệu | PostgreSQL | 15 | Lưu trữ toàn bộ dữ liệu |
| CSDL client | psycopg2 | 2.9 | Kết nối Python – PostgreSQL |
| Backend API | FastAPI, Uvicorn | 0.110 | REST API server |
| Validation | Pydantic | 2.x | Kiểm tra schema request/response |
| Frontend | React.js, Tailwind CSS | 18, 3.x | Giao diện web |
| Bản đồ | Leaflet.js | 1.9 | Bản đồ cảnh báo tương tác |
| Biểu đồ | Recharts | 2.x | Biểu đồ thống kê xu hướng |
| Triển khai | Docker, Docker Compose | 24 | Đóng gói và triển khai hệ thống |

## 3.3. Thiết kế pipeline thu thập và xử lý dữ liệu (ETL)

Pipeline ETL (Extract – Transform – Load) của hệ thống xử lý ba luồng dữ liệu riêng biệt — ca bệnh Influenza, ca bệnh Dengue và dữ liệu khí hậu ERA5 — sau đó tích hợp thành bộ đặc trưng thống nhất theo hai chiều khóa là mã quốc gia iso3 và tuần ISO (iso_year, iso_week).

### 3.3.1. Thu thập dữ liệu ca bệnh

**WHO FluNet — Influenza A+B:** Dữ liệu được tải về dưới định dạng CSV từ cổng thông tin FluNet của WHO [5]. Sau khi kiểm tra, biến mục tiêu được xác định là tổng INF_A + INF_B (số ca Influenza A và B hàng tuần). Biến INF_ALL không được sử dụng do có khoảng 44% giá trị bị thiếu. Các giá trị thiếu của INF_A và INF_B được điền bằng 0, với lý giải rằng dữ liệu bị thiếu trong bối cảnh giám sát dịch bệnh thường đồng nghĩa với không có ca bệnh được báo cáo trong tuần đó. Dataset sau làm sạch bao gồm 197 quốc gia với giai đoạn 2010–2019 (training) và năm 2022 (validation).

**OpenDengue v1.3 — Dengue:** Dữ liệu Dengue từ OpenDengue v1.3 [6] được thu thập cho 102 quốc gia. Sau khi lọc các quốc gia có ít nhất 10 tuần dữ liệu non-zero trong giai đoạn 2010–2019, dataset cuối gồm 41 quốc gia endemic tại khu vực châu Mỹ La-tinh, Đông Nam Á và Nam Á.

### 3.3.2. Thu thập và xử lý dữ liệu khí hậu ERA5

ERA5 cung cấp dữ liệu khí hậu toàn cầu tại độ phân giải không gian 0,25° × 0,25°, tương đương lưới 721 × 1440 điểm bao phủ toàn bộ bề mặt Trái Đất [7]. Trong nghiên cứu này, 17 biến khí hậu monthly means (trung bình tháng) được tải qua Copernicus CDS API cho giai đoạn 2010–2019 và năm 2022 bằng thư viện cdsapi và xarray.

**Spatial mapping — KD-tree nearest centroid:** Bước then chốt trong xử lý ERA5 là chuyển đổi dữ liệu từ dạng lưới tọa độ sang dạng bảng theo mã quốc gia iso3. Phương pháp KD-tree nearest centroid hoạt động như sau: với mỗi quốc gia, tọa độ trung tâm (centroid) được tính từ shapefile Natural Earth 50m; sau đó KDTree (scikit-learn) tìm điểm lưới ERA5 gần nhất trong không gian hai chiều (latitude, longitude) với độ phức tạp O(log n). Phương pháp này đạt độ bao phủ 158/172 quốc gia (≈92%); 14 quốc gia còn lại không được ánh xạ do kích thước địa lý quá nhỏ (đảo, city-state) không có điểm lưới đại diện.

**Tổng hợp tuần ISO:** Dữ liệu khí hậu monthly means được resample về độ phân giải tuần ISO (Monday–Sunday) bằng cách nội suy tuyến tính (linear interpolation) và align với lịch ISO week của dữ liệu ca bệnh. Quá trình này đảm bảo dữ liệu khí hậu và ca bệnh có cùng khung thời gian để tính lag features.

**17 biến khí hậu được sử dụng** (Bảng 3.2):

*Bảng 3.2. Danh sách biến khí hậu ERA5 trong hệ thống.*

| Nhóm | Mã biến | Tên hiển thị | Đơn vị |
|---|---|---|---|
| Nhiệt độ | temp_c, temp_min_c, temp_max_c | Nhiệt độ trung bình/min/max 2m | °C |
| Điểm sương | dewpoint_c | Nhiệt độ điểm sương 2m | °C |
| Độ ẩm | humidity_pct | Độ ẩm tương đối | % |
| Lượng mưa | precip_mm, snowfall_m | Tổng lượng mưa, tuyết | mm, m |
| Bức xạ | solar_wm2 | Bức xạ mặt trời bề mặt | W/m² |
| Gió | wind_u_ms, wind_v_ms, wind_speed_ms | Thành phần U/V gió, tốc độ gió | m/s |
| Khí áp | pressure_hpa | Áp suất bề mặt | hPa |
| Khí quyển | blh_m, total_water_col, cape_jkg | Chiều cao lớp biên, hơi nước, CAPE | m, kg/m², J/kg |
| Đất | soil_temp_c | Nhiệt độ đất tầng 1 | °C |

### 3.3.3. Feature engineering

Feature engineering trong nghiên cứu này bao gồm hai nhóm đặc trưng chính: đặc trưng lag thời tiết (climate lag features) và đặc trưng tự hồi quy (autoregressive features).

**Lag features thời tiết — xác định bằng CCF:** Khoảng trễ tối ưu giữa từng biến khí hậu và ca bệnh được xác định thông qua Cross-Correlation Function (CCF) trên chuỗi thời gian 2010–2019 toàn cầu (chi tiết trong mục 2.2). Kết quả CCF analysis được áp dụng trực tiếp vào feature engineering: biến khí hậu X tại tuần t được shift thành X tại tuần t − k*, trong đó k* là lag tối ưu. Bảng 3.3 tóm tắt các lag được chốt cho từng bệnh.

*Bảng 3.3. Lag time tối ưu áp dụng trong feature engineering.*

| Bệnh | Biến khí hậu | Lag tối ưu (tuần) | Ghi chú |
|---|---|---|---|
| Influenza | temp_c | 4 | Đỉnh CCF r = −0,73 |
| Influenza | humidity_pct | 8 | CCF r = +0,65 |
| Influenza | solar_wm2 | 8 | CCF r = −0,76 |
| Influenza | dewpoint_c | 2 | CCF r = −0,61 |
| Dengue | temp_c | 0 | Điều kiện nền, ổn định mọi lag |
| Dengue | humidity_pct | 2 | CCF r = +0,42 |
| Dengue | solar_wm2 | 4 | CCF r = −0,38 |
| Dengue | precip_mm | 0 | Signal rõ ở monthly resolution |

**Autoregressive (AR) lag features:** Cả hai mô hình sử dụng giá trị log1p của target tại các tuần t−1, t−2, t−4 làm đặc trưng. AR lags đóng vai trò quan trọng nhất trong mô hình vì tính mùa vụ mạnh của cả Influenza và Dengue — giá trị ca bệnh tuần trước là tín hiệu dự báo mạnh nhất cho tuần tiếp theo.

**Đặc trưng địa lý:** WHO region encoding (who_region_enc) ánh xạ 6 vùng WHO thành giá trị số nguyên (AFR=0, AMR=1, EMR=2, EUR=3, SEAR=4, WPR=5). Phân tích feature importance cho thấy đặc trưng này có mức độ ảnh hưởng rất khác biệt giữa hai bệnh: khoảng 2% với Influenza (vì AR lags đã nắm bắt được tính địa lý mùa vụ) nhưng lên đến 19% với Dengue (vùng endemic vs. non-endemic là tín hiệu quan trọng).

Bộ đặc trưng cuối cùng gồm **13 features cho Influenza** và **15 features cho Dengue**.

## 3.4. Thiết kế cơ sở dữ liệu

### 3.4.1. Yêu cầu thiết kế

Cơ sở dữ liệu phải đáp ứng bốn yêu cầu chính: (1) **catalog-driven** — thêm bệnh hoặc nguồn dữ liệu mới chỉ cần INSERT vào bảng cấu hình, không cần ALTER TABLE; (2) **linh hoạt về schema** — biến thời tiết có thể tăng thêm mà không thay đổi DDL; (3) **hiệu năng truy vấn** trên dữ liệu time-series trải dài nhiều năm; (4) **MLOps native** — theo dõi phiên bản mô hình, kết quả đánh giá và nhật ký vận hành.

### 3.4.2. Kiến trúc năm tầng

Schema được thiết kế theo năm tầng logic, mỗi tầng phục vụ một mục đích riêng biệt:

```
TẦNG 0 — Địa lý chuẩn
    countries (iso3 PK, country_name, who_region, who_region_enc, lat, lon)

TẦNG 1 — Catalog (config-driven)
    diseases ─── data_sources ─── weather_variables

TẦNG 2 — Observations (partitioned by iso_year)
    disease_cases ─── weather_observations (JSONB)

TẦNG 3 — ML Pipeline
    feature_configs ─── feature_snapshots
    model_versions ─── model_evaluations
    risk_thresholds ─── predictions

TẦNG 4 — MLOps & Ops
    pipeline_runs ─── pipeline_run_logs ─── data_quality_checks ─── api_request_logs

TẦNG 5 — Materialized View (dashboard)
    mv_latest_predictions
```

**Tầng 0 — Địa lý chuẩn:** Bảng `countries` lưu thông tin 149 quốc gia với iso3 là khóa chính. Trường `who_region_enc` được lưu sẵn để tránh JOIN khi phục vụ dự báo — đây là kỹ thuật denormalization có chủ đích nhằm tăng tốc độ inference.

**Tầng 1 — Catalog:** Ba bảng `diseases`, `data_sources` và `weather_variables` đóng vai trò cấu hình hệ thống. Việc bổ sung bệnh mới (ví dụ: Malaria) chỉ yêu cầu INSERT một hàng vào `diseases` và các hàng tương ứng vào `feature_configs` — không cần sửa code backend.

**Tầng 2 — Observations:** Bảng `disease_cases` được partition theo `iso_year`, mỗi partition chứa dữ liệu của một năm. Bảng `weather_observations` lưu toàn bộ 17 biến ERA5 trong một cột JSONB với GIN index — giải pháp này cho phép bổ sung biến thời tiết mới mà không cần ALTER TABLE.

**Tầng 3 — ML Pipeline:** Nhóm bảng này theo dõi toàn bộ vòng đời mô hình. `feature_configs` định nghĩa feature set; `feature_snapshots` lưu vector features theo tuần để inference nhanh; `model_versions` lưu siêu dữ liệu phiên bản; `model_evaluations` lưu kết quả đánh giá; `risk_thresholds` lưu ngưỡng phân loại nguy cơ per-country; `predictions` lưu kết quả dự báo và được partition theo năm tương tự `disease_cases`.

**Tầng 4 — MLOps:** `pipeline_runs` ghi lại mỗi lần chạy ETL hoặc inference pipeline; `pipeline_run_logs` lưu log từng bước chi tiết; `api_request_logs` theo dõi từng yêu cầu API trong production và được partition theo `requested_at` để quản lý vòng đời dữ liệu monitoring.

**Tầng 5 — Materialized View:** `mv_latest_predictions` chỉ giữ lại dự báo mới nhất cho mỗi cặp (disease, country, horizon_weeks), được refresh sau mỗi lần load data mới. Frontend truy vấn view này thay vì scan toàn bộ bảng `predictions`.

### 3.4.3. Sơ đồ quan hệ thực thể (ERD)

Hình 3.2 mô tả sơ đồ ERD rút gọn của hệ thống với các mối quan hệ chính:

```
countries (iso3) ──────< disease_cases (iso3 FK)
countries (iso3) ──────< weather_observations (iso3 FK)
countries (iso3) ──────< feature_snapshots (iso3 FK)
countries (iso3) ──────< predictions (iso3 FK)
countries (iso3) ──────< risk_thresholds (iso3)

diseases (id) ──────< disease_cases (disease_id FK)
diseases (id) ──────< model_versions (disease_id FK)
diseases (id) ──────< predictions (disease_id FK)
diseases (id) ──────< risk_thresholds (disease_id FK)
diseases (id) ──────< feature_configs (disease_id FK)

data_sources (id) ──────< disease_cases (source_id FK)
data_sources (id) ──────< weather_observations (source_id FK)
data_sources (id) ──────< weather_variables (source_id FK)

model_versions (id) ──────< model_evaluations (model_version_id FK)
model_versions (id) ──────< predictions (model_version_id FK)
model_versions (id) ──────< risk_thresholds (model_version_id FK)
model_versions (id) ──────< feature_configs (version_tag)

pipeline_runs (run_id) ──────< pipeline_run_logs (run_id FK)
```
*Hình 3.2. Sơ đồ quan hệ thực thể hệ thống EpiWeather.*

### 3.4.4. Một số quyết định thiết kế đáng chú ý

**JSONB cho `weather_observations.data`:** Thay vì tạo 17 cột riêng cho từng biến ERA5, toàn bộ quan sát thời tiết của một tuần/quốc gia được lưu trong một cột JSONB. Lựa chọn này có hai ưu điểm: (1) có thể thêm biến thời tiết mới (ENSO index, dữ liệu vệ tinh) chỉ bằng INSERT mà không cần ALTER TABLE; (2) GIN index trên cột JSONB đảm bảo hiệu năng truy vấn theo key cụ thể.

**Partitioning theo `iso_year`:** Các bảng `disease_cases`, `weather_observations` và `predictions` đều được partition theo `iso_year`. Với dataset 70.000+ hàng trải dài 13 năm, partition pruning của PostgreSQL cho phép query "năm 2022" chỉ scan partition tương ứng thay vì toàn bảng, cải thiện đáng kể hiệu năng khi hệ thống được mở rộng thêm dữ liệu.

**`api_request_logs` partition theo `requested_at`:** Nhật ký API được partition theo tháng/năm, cho phép xóa dữ liệu monitoring cũ (drop partition) mà không ảnh hưởng đến dữ liệu còn lại — thực hành chuẩn trong MLOps production.

## 3.5. Thiết kế mô hình học máy

### 3.5.1. Tổng quan quy trình

Quy trình xây dựng mô hình học máy gồm bốn giai đoạn tuần tự: chuẩn bị dữ liệu, huấn luyện mô hình, đánh giá và xuất artifact. Toàn bộ quy trình được thực hiện trên Google Colab và kết quả được lưu lại dưới dạng các file độc lập (pkl, JSON, CSV) để tích hợp vào hệ thống phục vụ.

### 3.5.2. Chiến lược phân chia dữ liệu

Dữ liệu được phân chia thành ba phần như Hình 3.3:

```
2010 ──────────────────────── 2019    2020  2021    2022
│←────────── Training ─────────────→│←─ Bỏ ──→│←─ Val ─→│
```
*Hình 3.3. Phân chia dữ liệu training/validation.*

Giai đoạn 2020–2021 bị loại bỏ do ảnh hưởng của đại dịch COVID-19 làm lệch pattern dịch bệnh tự nhiên: các biện pháp giãn cách xã hội, đóng cửa biên giới và thay đổi hành vi y tế cộng đồng khiến số ca cúm giảm đột ngột không phản ánh mối quan hệ thông thường giữa khí hậu và dịch bệnh. Năm 2022 được chọn làm tập validation vì đây là năm post-COVID gần nhất, phản ánh khả năng tổng quát hóa của mô hình trên pattern dịch bệnh hậu đại dịch.

### 3.5.3. Biến đổi target (log1p transformation)

Phân phối số ca bệnh Influenza có đuôi dài nặng (heavy-tail distribution): một số quốc gia lớn như Hoa Kỳ, Trung Quốc báo cáo hàng chục nghìn ca mỗi tuần trong khi phần lớn quốc gia nhỏ báo cáo dưới 100 ca. Biến đổi log1p (log(x+1)) nén phân phối về dạng đối xứng hơn, giúp mô hình học hiệu quả hơn trên toàn phổ giá trị. Tác động cụ thể: R² tăng từ 0,488 lên 0,791 sau khi áp dụng log1p cho Influenza. Với Dengue, biến đổi này còn cần thiết hơn vì Brazil chiếm khoảng 70% tổng ca toàn cầu trong giai đoạn 2010–2022 [2].

### 3.5.4. Walk-forward Cross-Validation

Đối với dữ liệu chuỗi thời gian, phương pháp k-fold cross-validation truyền thống vi phạm tính thứ tự thời gian khi cho phép model nhìn thấy dữ liệu tương lai trong quá trình training. Walk-forward cross-validation giải quyết vấn đề này bằng chiến lược expanding window: tại mỗi fold, tập train chỉ gồm dữ liệu trước thời điểm validation và mở rộng dần qua các fold. Trong nghiên cứu này, 6 fold được sử dụng với val_year ∈ {2014, 2015, 2016, 2017, 2018, 2019}, cung cấp đánh giá ổn định và phản ánh đúng điều kiện triển khai thực tế.

### 3.5.5. Lựa chọn và tối ưu mô hình

**XGBoost** [4] được lựa chọn làm mô hình chính với bốn lý do: xử lý tốt dữ liệu dạng bảng (tabular) với feature engineering thủ công; hỗ trợ regularization (L1/L2) giúp tránh overfitting; tốc độ inference nhanh (70.000+ hàng trong vài giây); và đầu ra feature importance hỗ trợ giải thích model. Hàm mục tiêu XGBoost được định nghĩa:

$$\mathcal{L}(\phi) = \sum_i l(\hat{y}_i, y_i) + \sum_k \Omega(f_k)$$

trong đó $l$ là hàm mất mát MSE cho bài toán hồi quy, $\Omega(f_k) = \gamma T + \frac{1}{2}\lambda\|w\|^2$ là số hạng regularization với $T$ là số lá và $w$ là trọng số lá.

Với mô hình Influenza, hyperparameter được tối ưu bằng Optuna (60 trials, TPE Sampler, MedianPruner) trên không gian tìm kiếm gồm n_estimators ∈ [300, 1500], max_depth ∈ [3, 8], learning_rate ∈ [0,01, 0,3] và các tham số regularization reg_alpha, reg_lambda. Mô hình Dengue sử dụng tham số mặc định của XGBoost vì dataset nhỏ hơn (1.537 hàng validation) và đã đạt hiệu năng tốt mà không cần Optuna.

**Prophet** [3] được sử dụng làm baseline so sánh, khai thác khả năng phân rã cộng tính (additive decomposition) của chuỗi thời gian toàn cầu:

$$y(t) = g(t) + s(t) + h(t) + \epsilon_t$$

trong đó $g(t)$ là xu hướng (trend), $s(t)$ là mùa vụ (seasonality) mô hình hóa bằng chuỗi Fourier, $h(t)$ là ảnh hưởng ngày lễ và $\epsilon_t$ là nhiễu.

### 3.5.6. Hệ thống phân loại nguy cơ

Mỗi giá trị dự báo ca bệnh được chuyển thành ba mức nguy cơ Low / Medium / High dựa trên ngưỡng phân vị. Thay vì sử dụng một ngưỡng toàn cầu, hệ thống áp dụng **per-country quantile thresholds** cho Influenza: với mỗi quốc gia, hai ngưỡng q33 và q67 được tính trên các tuần non-zero của tập training (2010–2019), phản ánh mức độ dịch bệnh đặc thù của từng quốc gia. Các quốc gia có ít hơn 10 tuần non-zero được gán ngưỡng global fallback. Với Dengue, do dataset nhỏ hơn, một ngưỡng toàn cầu duy nhất được sử dụng.

Tác động của phương pháp này so với ngưỡng toàn cầu: Flu Medium F1 tăng từ 0,06 lên 0,52; Flu Macro F1 tăng từ 0,40 lên 0,72.

## 3.6. Thiết kế Backend API

### 3.6.1. Kiến trúc và công nghệ

Backend được xây dựng bằng **FastAPI** — framework Python hỗ trợ async native, tự động sinh tài liệu OpenAPI (Swagger UI) và validation schema thông qua Pydantic. Mô hình XGBoost được nạp vào bộ nhớ một lần khi khởi động server (model warm-up), và được dùng chung cho tất cả các request, tránh chi phí I/O cho mỗi lần predict.

Kết nối cơ sở dữ liệu sử dụng psycopg2 với connection pool, giảm overhead tạo kết nối mới cho mỗi request. Các truy vấn nặng (lấy features cho 197 quốc gia) được phục vụ từ materialized view `mv_latest_predictions` thay vì bảng gốc.

### 3.6.2. Danh sách endpoints

*Bảng 3.4. Danh sách API endpoints.*

| Method | Endpoint | Mô tả |
|---|---|---|
| GET | `/health` | Kiểm tra trạng thái server, kết nối DB và model |
| GET | `/countries` | Danh sách quốc gia có dữ liệu dự báo |
| GET | `/diseases` | Danh sách bệnh được hỗ trợ |
| GET | `/predict/{disease}/{iso3}` | Dự báo tuần hiện tại (từ predictions trong DB) |
| POST | `/predict` | Dự báo với weather input tùy chọn (future weeks) |
| GET | `/risk-map/{disease}/{year}/{week}` | Toàn bộ nguy cơ một tuần cụ thể cho bản đồ |
| GET | `/history/{disease}/{iso3}` | Lịch sử ca bệnh và dự báo theo quốc gia |
| GET | `/model-info/{disease}` | Thông tin model version đang hoạt động |

### 3.6.3. Luồng xử lý dự báo

Khi nhận request dự báo, hệ thống thực hiện theo luồng ưu tiên cache trước:

```
Request (disease, iso3, year, week)
        │
        ▼
   Tìm trong predictions DB
   ────────────────────────
   Có?                Không?
    │                    │
    ▼                    ▼
Trả về            Lấy AR lags từ disease_cases
cached            Lấy weather từ OpenWeatherMap API
result                   │
                         ▼
                  model.predict(features)
                         │
                         ▼
                  Lookup risk_thresholds
                  (per-country → global fallback)
                         │
                         ▼
                  Trả về JSON response
```
*Hình 3.4. Luồng xử lý request dự báo.*

**Schema response dự báo:**

```json
{
  "disease": "flu",
  "iso3": "VNM",
  "country_name": "Viet Nam",
  "iso_year": 2026,
  "iso_week": 20,
  "predicted_cases": 1243,
  "risk_level": "Medium",
  "risk_probability": 0.42,
  "risk_q33": null,
  "risk_q67": null,
  "model_version": "v1.0",
  "confidence_lo": 890,
  "confidence_hi": 1650
}
```

## 3.7. Thiết kế giao diện Frontend

### 3.7.1. Kiến trúc giao diện

Giao diện được xây dựng bằng **React.js** (SPA — Single Page Application) với Tailwind CSS cho styling và Leaflet.js cho bản đồ tương tác. Thiết kế theo component-based architecture, mỗi thành phần giao diện là một React component độc lập và có thể tái sử dụng.

### 3.7.2. Các trang chính

Hệ thống gồm ba màn hình chính:

**Trang bản đồ cảnh báo toàn cầu (Global Risk Map):** Hiển thị bản đồ choropleth toàn cầu với màu sắc biểu diễn mức nguy cơ của từng quốc gia trong tuần được chọn. Người dùng có thể chọn loại bệnh (Influenza / Dengue), tuần cụ thể và nhấp vào quốc gia để xem chi tiết dự báo. Bản đồ được render bằng Leaflet.js với GeoJSON từ Natural Earth.

**Trang dashboard xu hướng (Trend Dashboard):** Hiển thị biểu đồ đường (line chart) thể hiện xu hướng ca bệnh và dự báo theo thời gian cho một quốc gia được chọn, kết hợp với các chỉ số thống kê tổng hợp. Biểu đồ được render bằng Recharts.

**Trang tra cứu quốc gia (Country Detail):** Bảng chi tiết lịch sử ca bệnh, dự báo tuần tiếp theo và phân bố mức nguy cơ theo thời gian của một quốc gia. Hỗ trợ lọc theo khoảng thời gian và xuất dữ liệu CSV.

### 3.7.3. Wireframe trang bản đồ chính

```
┌──────────────────────────────────────────────────────────┐
│  EpiWeather   [Influenza ▼]  [Tuần 20/2026 ▼]  [About]  │
├──────────────────────────────────────────────────────────┤
│                                                          │
│    ┌──────────────────────────────────┐  ┌────────────┐  │
│    │                                  │  │  Risk      │  │
│    │      BẢN ĐỒ CHOROPLETH          │  │  ■ High    │  │
│    │      (Leaflet.js)                │  │  ■ Medium  │  │
│    │                                  │  │  ■ Low     │  │
│    │  [Click quốc gia → popup]        │  │  □ No data │  │
│    │                                  │  └────────────┘  │
│    └──────────────────────────────────┘                  │
│                                                          │
│    [← Tuần trước]  Tuần 20, 2026  [Tuần sau →]          │
├──────────────────────────────────────────────────────────┤
│  HIGH RISK (12):  USA, CHN, BRA...  MEDIUM (45):  ...   │
└──────────────────────────────────────────────────────────┘
```
*Hình 3.5. Wireframe trang bản đồ cảnh báo toàn cầu.*

---

## Tài liệu tham khảo (Chương 3)

[1] O. J. Brady et al., "Forecast of dengue incidence using temperature and rainfall", *PLoS Neglected Trop. Dis.*, vol. 6, no. 11, p. e1908, Nov. 2012. doi: 10.1371/journal.pntd.0001908.

[2] S. Bhatt et al., "The global distribution and burden of dengue", *Nature*, vol. 496, no. 7446, pp. 504–507, Apr. 2013. doi: 10.1038/nature12060.

[3] S. J. Taylor and B. Letham, "Forecasting at scale", *Am. Stat.*, vol. 72, no. 1, pp. 37–45, Jan. 2018. doi: 10.1080/00031305.2017.1380080.

[4] T. Chen and C. Guestrin, "XGBoost: A scalable tree boosting system", in *Proc. 22nd ACM SIGKDD*, San Francisco, CA, 2016, pp. 785–794.

[5] World Health Organization, "FluNet - Global Influenza Surveillance and Response System", WHO. [Online]. Available: https://www.who.int/tools/flunet. [Accessed: Apr. 05, 2026].

[6] OpenDengue Project, "OpenDengue v1.3 - Global dengue surveillance data", GitHub. [Online]. Available: https://github.com/OpenDengue/master-repo. [Accessed: Apr. 05, 2026].

[7] H. Hersbach et al., "The ERA5 global reanalysis", *Q.J.R. Meteorol. Soc.*, vol. 146, no. 730, pp. 1999–2049, Jul. 2020. doi: 10.1002/qj.3803.
