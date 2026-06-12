# Tổng quan cấu trúc dự án EpiWeather

## 1. Giới thiệu chung

**EpiWeather** là hệ thống dự báo nguy cơ dịch bệnh theo mùa dạng full-stack. Dự án kết hợp dữ liệu dịch tễ và dữ liệu thời tiết để:

- Dự báo số ca bệnh theo tuần đối với **cúm mùa** và **sốt xuất huyết**.
- Phân loại mức độ rủi ro thành **Thấp**, **Trung bình** hoặc **Cao**.
- Hiển thị kết quả dự báo trên dashboard trực quan.

Luồng tổng quát của hệ thống:

```text
Dữ liệu bệnh + dữ liệu thời tiết thô
                ↓
Tiền xử lý dữ liệu, tạo đặc trưng và huấn luyện mô hình ML
                ↓
Lưu trữ vào PostgreSQL
                ↓
FastAPI backend xử lý API và nghiệp vụ
                ↓
React dashboard hiển thị bản đồ, biểu đồ và cảnh báo
```

---

## 2. Cấu trúc thư mục chính

```text
KLTN/
├── backend/              Backend FastAPI và database models
├── frontend/             Dashboard React/Vite
├── scripts/              Script lấy dữ liệu, tạo feature và chạy dự báo
├── data/                 Dữ liệu thô và dữ liệu đã xử lý
├── ml_models/            Model đã huấn luyện, metric và artifact
├── notebooks/            Notebook nghiên cứu, huấn luyện và đánh giá mô hình
├── docs/                 Tài liệu luận văn, kiến trúc, database và slide
├── logs/                 Log của pipeline chạy định kỳ
├── docker-compose.yml    Cấu hình chạy toàn bộ hệ thống
└── Makefile              Các lệnh phát triển thường dùng
```

Nhìn tổng thể, project được chia khá rõ thành 5 phần lớn:

| Nhóm | Vai trò chính |
|---|---|
| `backend/` | Cung cấp API, xử lý nghiệp vụ, kết nối database và chạy inference |
| `frontend/` | Giao diện dashboard cho người dùng |
| `scripts/` | Pipeline dữ liệu và dự báo tự động |
| `data/` | Nơi lưu dữ liệu thô, dữ liệu thời tiết và dữ liệu đã xử lý |
| `ml_models/` | Nơi lưu các model đã huấn luyện và thông tin đánh giá |

---

## 3. Backend - FastAPI Application

Thư mục `backend/` chứa phần backend của hệ thống. Backend có nhiệm vụ cung cấp API cho frontend, truy vấn database, xử lý logic dự báo và trả về dữ liệu cho dashboard.

```text
backend/
├── app/
│   ├── api/              Các router và endpoint API
│   ├── core/             Cấu hình hệ thống, logging và exception
│   ├── crud/             Hàm hỗ trợ truy vấn database
│   ├── db/               Cấu hình SQLAlchemy session và base
│   ├── models/           ORM models ánh xạ với database
│   ├── schemas/          Schema request/response của API
│   ├── services/         Logic nghiệp vụ và xử lý dự báo
│   └── main.py           Entry point của FastAPI
├── alembic/              Database migrations
├── tests/                Unit test/backend test
├── Dockerfile
└── requirements.txt
```

### 3.1. Các file backend quan trọng

| File | Vai trò |
|---|---|
| `backend/app/main.py` | Khởi tạo FastAPI app, load ML models, cấu hình CORS và đăng ký route |
| `backend/app/api/v1/api.py` | Gom các router API thuộc nhóm `/api/v1` |
| `backend/app/core/config.py` | Đọc cấu hình database, đường dẫn model, CORS và scheduler |
| `backend/app/services/ml_engine.py` | Load model artifact và chạy inference |
| `backend/app/services/prediction_service.py` | Xử lý dự báo, lịch sử dự báo và forecast nhiều tuần |
| `backend/app/services/risk_service.py` | Tạo dữ liệu bản đồ nguy cơ toàn cầu |

### 3.2. Các nhóm API chính

Backend cung cấp nhiều nhóm API để phục vụ dashboard và pipeline:

| API group | Chức năng chính |
|---|---|
| `/countries` | Lấy danh sách quốc gia và thông tin địa lý |
| `/diseases` | Lấy thông tin bệnh |
| `/predictions` | Lấy kết quả dự báo đã lưu |
| `/forecast` | Lấy dự báo theo nhiều tuần |
| `/risk-map` | Lấy dữ liệu bản đồ rủi ro |
| `/infer` | Chạy dự báo trực tiếp |
| `/weather` | Truy vấn dữ liệu thời tiết |
| `/analytics` | Xem đánh giá mô hình và thống kê |
| `/admin` | Các chức năng quản trị/hỗ trợ hệ thống |

### 3.3. Database models

Các ORM models trong backend mô tả những nhóm dữ liệu chính như:

- Quốc gia.
- Bệnh.
- Quan sát dịch tễ.
- Snapshot đặc trưng.
- Phiên bản mô hình.
- Kết quả dự báo.
- Kết quả đánh giá mô hình.
- Log chạy pipeline.

---

## 4. Frontend - React Dashboard

Thư mục `frontend/` chứa giao diện người dùng. Frontend được xây dựng bằng **React 19**, **TypeScript**, **Vite**, **Tailwind CSS**, **ECharts** và **React Query**.

```text
frontend/src/
├── api/                  Các hàm gọi API backend
├── components/           Component bản đồ, biểu đồ, sidebar, alert và layout
├── hooks/                React Query hooks để lấy dữ liệu
├── pages/                Các trang chính của ứng dụng
├── store/                Global state bằng Zustand
├── types/                TypeScript types cho API và domain
├── App.tsx               Định nghĩa route và layout chính
└── main.tsx              File bootstrap React app
```

### 4.1. Các file frontend quan trọng

| File | Vai trò |
|---|---|
| `frontend/src/App.tsx` | Định nghĩa route và layout dùng chung |
| `frontend/src/pages/HomePage.tsx` | Trang chính hiển thị bản đồ nguy cơ toàn cầu |
| `frontend/src/pages/AnalyticsPage.tsx` | Trang phân tích hiệu năng mô hình |
| `frontend/src/pages/DiseaseDetailPage.tsx` | Trang chi tiết theo quốc gia/bệnh và forecast |
| `frontend/src/api/axios.ts` | Cấu hình HTTP client dùng chung, gọi `/api/v1` |
| `frontend/src/store/uiStore.ts` | Lưu trạng thái lọc như bệnh, tuần, quốc gia, vùng và mức rủi ro |

Ngoài ra, file:

```text
frontend/public/world.json
```

được dùng để cung cấp dữ liệu hình học bản đồ thế giới cho dashboard.

Thư mục:

```text
frontend/dist/
```

là thư mục output sau khi build production.

---

## 5. Scripts - Pipeline dữ liệu và dự báo

Thư mục `scripts/` chứa các script vận hành pipeline dữ liệu và dự báo. Đây là phần giúp hệ thống cập nhật dữ liệu, tạo feature và ghi kết quả dự báo vào database.

### 5.1. Luồng xử lý chính

```text
sync_flunet.py
        ↓
sync_weather.py
        ↓
feature_builder.py
        ↓
batch_predict.py
        ↓
scheduler_worker.py / run_daily_pipeline.py
```

### 5.2. Vai trò các script chính

| Script | Vai trò |
|---|---|
| `scripts/sync_flunet.py` | Tải dữ liệu cúm mới từ WHO FluNet |
| `scripts/sync_weather.py` | Tải dữ liệu thời tiết từ Open-Meteo |
| `scripts/feature_builder.py` | Tính lag features, rolling features, weather features và seasonal features |
| `scripts/batch_predict.py` | Chạy model đã huấn luyện và lưu kết quả dự báo |
| `scripts/scheduler_worker.py` | Chạy pipeline định kỳ trong Docker |
| `scripts/run_daily_pipeline.py` | Chạy pipeline qua Windows Task Scheduler |

### 5.3. Các file setup database

| File | Vai trò |
|---|---|
| `scripts/db_init.sql` | Tạo schema PostgreSQL ban đầu |
| `scripts/bootstrap_db.py` | Chạy migration và nạp dữ liệu khởi tạo |
| `scripts/load_db_v2.py` | Load feature đã xử lý, metadata model và prediction vào database |

---

## 6. Data - Dữ liệu của hệ thống

Thư mục `data/` lưu dữ liệu thô và dữ liệu đã xử lý. Đây là thư mục lớn nhất của project, khoảng **6.3 GB**.

```text
data/
├── epidemic/raw/         Dữ liệu WHO FluNet và dengue thô
├── weather/era5_raw/     Dữ liệu thời tiết ERA5 thô theo năm
├── weather/processed/    Dữ liệu thời tiết đã gom theo tuần
└── processed/            Dữ liệu feature cuối cùng dùng cho ML
```

### 6.1. Một số dataset đã xử lý

| File | Ý nghĩa |
|---|---|
| `master_weekly_v1.csv` | Dataset tổng hợp theo tuần |
| `features_flu_v1.csv` | Feature dataset cho mô hình cúm |
| `features_dengue_v1.csv` | Feature dataset cho mô hình sốt xuất huyết |

---

## 7. ML Models - Model đã huấn luyện

Thư mục `ml_models/` lưu các artifact của mô hình sau khi huấn luyện.

Thông thường, mỗi model sẽ có 3 file chính:

| File | Vai trò |
|---|---|
| `model.pkl` | Model đã huấn luyện, được serialize để backend load lại |
| `model_features.json` | Danh sách feature đầu vào mà model yêu cầu |
| `model_metrics.json` | Kết quả đánh giá mô hình |

### 7.1. Các nhóm model hiện có

Project hiện có nhiều nhóm model phục vụ các bài toán khác nhau:

- LightGBM regressor cho cúm.
- Random Forest regressor cho sốt xuất huyết.
- XGBoost classifier cho cúm.
- XGBoost classifier cho sốt xuất huyết.
- Các model dự báo theo horizon riêng, từ `h1` đến `h4`.

Backend sẽ load các artifact này khi ứng dụng khởi động để phục vụ API dự báo.

---

## 8. Notebooks - Nghiên cứu và huấn luyện mô hình

Thư mục `notebooks/` chứa các notebook phục vụ quá trình nghiên cứu, thử nghiệm và huấn luyện mô hình.

Một số notebook chính:

```text
KLTN_EpiWeather_ML.ipynb
KLTN_EpiWeather_ML_v3.ipynb
...
KLTN_EpiWeather_ML_v7.ipynb
```

Các notebook này ghi lại quá trình:

- Khám phá dữ liệu.
- Xây dựng feature.
- Chia tập train/validation/test.
- So sánh mô hình.
- Đánh giá kết quả.
- Xuất artifact phục vụ backend.

Có thể hiểu rằng:

- `notebooks/` là phần nghiên cứu và thử nghiệm.
- `scripts/` là phần đã được chuyển thành pipeline vận hành.

---

## 9. Docs - Tài liệu kỹ thuật và luận văn

Thư mục `docs/` chứa tài liệu phục vụ báo cáo, thiết kế hệ thống, database và thuyết trình.

Một số tài liệu quan trọng:

| Tài liệu | Nội dung |
|---|---|
| `docs/chapter3_system_design.md` | Chương thiết kế hệ thống |
| `docs/database_schema_v2.md` | Thiết kế database hiện tại |
| `docs/code_flow_BE_to_FE.md` | Luồng dữ liệu từ backend đến frontend |
| `docs/model_improvement_history.md` | Lịch sử cải thiện mô hình |
| `docs/presentation/` | Tài liệu và slide bảo vệ |
| `docs/session_summaries/` | Ghi chú các buổi làm việc |
| `docs/diagrams/` | Sơ đồ kiến trúc và luồng xử lý |

---

## 10. Runtime files

Một số file ở root project phục vụ việc chạy và triển khai hệ thống:

| File | Vai trò |
|---|---|
| `docker-compose.yml` | Chạy PostgreSQL, seed database, scheduler, backend và frontend |
| `Dockerfile.scheduler` | Build image cho các job chạy định kỳ |
| `Makefile` | Gom các lệnh thường dùng như `make dev`, `make test`, `make docker-up` |
| `README.md` | Tài liệu tổng quan, cách setup và kiến trúc hệ thống |

---

## 11. Luồng dữ liệu end-to-end

Luồng dữ liệu từ nguồn ban đầu đến dashboard có thể tóm tắt như sau:

```text
WHO FluNet / Dengue datasets / ERA5 / Open-Meteo
                        ↓
            sync_flunet.py + sync_weather.py
                        ↓
       disease_cases + weather_observations tables
                        ↓
                 feature_builder.py
                        ↓
                feature_snapshots table
                        ↓
                 batch_predict.py
                        ↓
                  predictions table
                        ↓
 FastAPI services → REST endpoints → React Query hooks
                        ↓
       Risk map, alerts, analytics, and forecasts
```

Diễn giải ngắn gọn:

1. Dữ liệu bệnh và thời tiết được tải từ các nguồn bên ngoài.
2. Các script pipeline chuẩn hóa và lưu dữ liệu vào database.
3. `feature_builder.py` tạo các đặc trưng đầu vào cho mô hình.
4. `batch_predict.py` chạy model và lưu kết quả dự báo.
5. FastAPI cung cấp dữ liệu thông qua REST API.
6. React frontend gọi API bằng React Query và hiển thị kết quả trên dashboard.

---

## 12. Ghi chú về điểm chưa nhất quán

Có một điểm cần chú ý trong repository:

> `scripts/config.py` vẫn tham chiếu đến layout cũ là `dataset/`, trong khi pipeline và artifact hiện tại đang dùng `data/` và `ml_models/`.

Điều này nên được kiểm tra lại để tránh lỗi đường dẫn khi chạy pipeline hoặc triển khai hệ thống.

Gợi ý xử lý:

- Kiểm tra lại toàn bộ đường dẫn trong `scripts/config.py`.
- Đồng bộ về cấu trúc hiện tại: `data/` và `ml_models/`.
- Chạy thử lại pipeline sau khi sửa bằng `codegraph sync` và test các script liên quan.

---

## 13. Kết luận

Cấu trúc project EpiWeather tương đối rõ ràng, tách biệt giữa các phần:

- Backend xử lý API, database và inference.
- Frontend hiển thị dashboard và tương tác người dùng.
- Scripts đảm nhiệm pipeline dữ liệu và dự báo.
- Data lưu dữ liệu thô và dữ liệu đã xử lý.
- ML models lưu artifact phục vụ dự báo.
- Docs và notebooks hỗ trợ nghiên cứu, báo cáo và bảo vệ luận văn.

Về tổng thể, project đã có đầy đủ các thành phần của một hệ thống dự báo dịch bệnh hoàn chỉnh: từ dữ liệu đầu vào, xử lý đặc trưng, mô hình học máy, database, backend API cho đến giao diện dashboard.
