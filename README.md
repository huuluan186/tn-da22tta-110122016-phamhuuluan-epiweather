# EpiWeather — Hệ thống Cảnh báo Nguy cơ Dịch bệnh Theo Mùa

> Đồ án tốt nghiệp (KLTN) — Đại học Duy Tân, Khoa Công nghệ Thông tin

Hệ thống tích hợp dữ liệu y tế toàn cầu (WHO FluNet, WHO Dengue) và dữ liệu khí hậu (ERA5/ECMWF) để dự báo nguy cơ dịch cúm và sốt xuất huyết theo tuần, cấp quốc gia. Pipeline gồm hai nhánh song song: **Regression** (dự báo số ca) và **Classification** (cảnh báo mức độ Low/Medium/High).

## Tài liệu bảo vệ KLTN

Bộ tài liệu trình bày mới nằm trong `docs/presentation/`:

- [Pipeline ML và dữ liệu](docs/presentation/ml_pipeline.md)
- [Kiến trúc hệ thống và dashboard](docs/presentation/system_architecture.md)
- [MLOps trong phạm vi KLTN](docs/presentation/mlops.md)
- [Q&A bảo vệ](docs/presentation/qa_defense.md)

Thuật ngữ dashboard dùng nhất quán: **MỚI NHẤT** là tuần mới nhất hệ thống có prediction trong database; **BACKTEST** là tuần/năm quá khứ được chọn để mô phỏng hoặc kiểm chứng dự báo. Không gọi chung là realtime nếu dữ liệu bệnh không thật sự realtime.

---

## Mục lục

- [Tính năng](#tính-năng)
- [Kiến trúc hệ thống](#kiến-trúc-hệ-thống)
- [Tech stack](#tech-stack)
- [Cấu trúc thư mục](#cấu-trúc-thư-mục)
- [Yêu cầu hệ thống](#yêu-cầu-hệ-thống)
- [Hướng dẫn setup](#hướng-dẫn-setup)
- [Biến môi trường](#biến-môi-trường)
- [API Endpoints](#api-endpoints)
- [ML Pipeline](#ml-pipeline)
- [Tác giả & Bản quyền](#tác-giả--bản-quyền)

---

## Tính năng

- **Dự báo dịch bệnh** — Influenza (189 quốc gia) và Dengue (41 quốc gia), grain tuần ISO
- **Cảnh báo mức độ** — Low / Medium / High theo endemic channel threshold (Bortman 1999)
- **4 models so sánh** — XGBoost, LightGBM, Random Forest, Prophet (baseline)
- **Tích hợp khí hậu** — 17 biến ERA5: nhiệt độ, độ ẩm, lượng mưa, solar radiation, v.v.
- **REST API** — FastAPI, OpenAPI docs tại `/docs`
- **PostgreSQL** — lưu trữ dự báo, lịch sử, thông tin địa lý

---

## Kiến trúc hệ thống

```
┌──────────────────────────────────────────────────────────┐
│                     Frontend (React)                     │
│          Leaflet choropleth · Recharts trend             │
└─────────────────────┬────────────────────────────────────┘
                      │ HTTP / REST
┌─────────────────────▼────────────────────────────────────┐
│                  FastAPI Backend                         │
│   /api/v1/countries  /api/v1/diseases  /api/v1/infer    │
│   /api/v1/predictions  /api/v1/risk  /health             │
└──────────┬──────────────────────────┬────────────────────┘
           │                          │
┌──────────▼──────────┐   ┌───────────▼───────────────────┐
│     PostgreSQL      │   │        ML Models (.pkl)        │
│  countries          │   │  lgbm_flu_regressor_v1         │
│  diseases           │   │  rf_dengue_regressor_v1        │
│  observations       │   │  xgb_flu_classifier_v1         │
│  predictions        │   │  xgb_dengue_classifier_v1      │
└─────────────────────┘   └───────────────────────────────┘
```

---

## Tech stack

| Tầng | Công nghệ |
|---|---|
| Backend | Python 3.11, FastAPI 0.110, Uvicorn, SQLAlchemy 2.0 |
| Database | PostgreSQL 15 |
| ML | XGBoost 2.0, LightGBM 4.3, scikit-learn 1.6, Prophet |
| Hyperparameter tuning | Optuna |
| Dữ liệu khí hậu | ERA5 (ECMWF) lịch sử · Open-Meteo/nguồn vận hành cho giai đoạn mới nhất |
| Frontend | React, Tailwind CSS, Leaflet.js, Recharts |
| Containerization | Docker, Docker Compose |

---

## Cấu trúc thư mục

```
KLTN/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── health.py          # GET /health
│   │   │   └── v1/endpoints/      # 7 endpoint modules
│   │   ├── core/                  # config, exceptions, logging
│   │   ├── crud/                  # CRUD operations
│   │   ├── db/                    # session, base, migrations
│   │   ├── models/                # SQLAlchemy ORM models
│   │   ├── schemas/               # Pydantic schemas
│   │   ├── services/              # ml_engine, data_fetcher
│   │   └── main.py                # FastAPI entry point
│   ├── alembic/                   # DB migrations
│   ├── tests/                     # pytest (27 tests)
│   ├── Dockerfile
│   └── requirements.txt
├── data/
│   └── processed/             # Feature CSVs (flu, dengue, master_weekly)
├── docs/
│   └── session_summaries/     # Ghi chú sau mỗi buổi làm việc
├── ml_models/                 # Trained model artifacts (.pkl + _features.json + _metrics.json)
│   ├── lgbm_flu_regressor_v1.pkl
│   ├── rf_dengue_regressor_v1.pkl
│   ├── xgb_flu_classifier_v1.pkl
│   └── xgb_dengue_classifier_v1.pkl
├── scripts/
│   ├── seed_countries.py      # Seed dữ liệu quốc gia vào DB
│   └── db_init.sql
├── KLTN_EpiWeather_ML_v5.ipynb   # Notebook ML pipeline chính
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Yêu cầu hệ thống

- **Python** 3.11+
- **PostgreSQL** 15+ (hoặc Docker)
- **Docker & Docker Compose** v2+ (khuyến nghị cho setup nhanh)
- RAM: tối thiểu 4 GB (8 GB khuyến nghị cho training)

---

## Hướng dẫn setup

### Option 1 — Docker Compose (khuyến nghị)

```bash
# 1. Clone repo
git clone https://github.com/huuluan186/KLTN.git
cd KLTN

# 2. Tạo file .env từ template
cp .env.example .env
# Chỉnh sửa .env: đặt DB_PASSWORD, APP_VERSION, v.v.

# 3. Khởi động toàn bộ stack
docker compose up -d

# 4. Seed dữ liệu quốc gia (chạy 1 lần)
docker compose exec backend python scripts/seed_countries.py

# 5. Kiểm tra
curl http://localhost:8000/health
```

API docs: http://localhost:8000/docs

---

### Option 2 — Local development

```bash
# 1. Tạo virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/macOS

# 2. Cài dependencies
pip install -r backend/requirements.txt

# 3. Tạo .env
cp .env.example .env

# 4. Đảm bảo PostgreSQL đang chạy, tạo database
psql -U postgres -c "CREATE DATABASE kltn_epiweather;"

# 5. Khởi động server
cd backend
uvicorn app.main:app --reload --port 8000
```

---

### Chạy ML Notebook

Notebook chính nên đối chiếu `KLTN_EpiWeather_ML_v6.ipynb` trước, sau đó dùng `KLTN_EpiWeather_ML_v5.ipynb` để xem pipeline h=1 và validation nền. Chạy trên **Google Colab** (khuyến nghị) hoặc Jupyter local:

```bash
pip install jupyter xgboost lightgbm optuna prophet scikit-learn pandas numpy
jupyter notebook KLTN_EpiWeather_ML_v6.ipynb
```

Mount Google Drive hoặc đặt dataset vào `data/processed/` trước khi chạy.

---

## Biến môi trường

Tạo file `.env` từ `.env.example`:

| Biến | Mô tả | Mặc định |
|---|---|---|
| `DB_USER` | PostgreSQL username | `epiweather` |
| `DB_PASSWORD` | PostgreSQL password | *(bắt buộc đặt)* |
| `DB_NAME` | Tên database | `kltn_epiweather` |
| `DB_HOST` | Database host | `localhost` |
| `DB_PORT` | Database port | `5432` |
| `MODELS_DIR` | Đường dẫn tới thư mục models | `../models` |
| `CDS_KEY` | API key cho ERA5/CDS | *(tùy chọn)* |
| `DEBUG` | Bật debug mode | `false` |
| `APP_VERSION` | Version hiển thị trong API | `1.0.0` |
| `CORS_ORIGINS` | Danh sách origin được phép | `["http://localhost:3000"]` |

---

## API Endpoints

| Method | Endpoint | Mô tả |
|---|---|---|
| `GET` | `/health` | Health check |
| `GET` | `/api/v1/countries` | Danh sách quốc gia |
| `GET` | `/api/v1/diseases` | Danh sách loại bệnh |
| `POST` | `/api/v1/infer` | Dự báo nguy cơ từ feature input |
| `GET` | `/api/v1/predictions` | Lịch sử dự báo |
| `GET` | `/api/v1/risk` | Mức độ cảnh báo hiện tại |

OpenAPI schema đầy đủ: `http://localhost:8000/docs`

---

## ML Pipeline

Pipeline gồm 2 nhánh huấn luyện song song, so sánh kết quả:

**Nhánh A — Regression** (dự báo số ca)

| Model | Target | Metrics |
|---|---|---|
| XGBoost Regressor | `log1p(case_count)` | RMSE, MAE, R² |
| LightGBM Regressor | `log1p(case_count)` | RMSE, MAE, R² |
| Random Forest Regressor | `log1p(case_count)` | RMSE, MAE, R² |
| Prophet (baseline) | `case_count` | RMSE, MAE, R² |

**Nhánh B — Classification** (cảnh báo Low/Medium/High)

| Model | Target | Metrics |
|---|---|---|
| XGBClassifier | Endemic channel label | macro-F1, AUC OvR |
| Regressor + threshold | Endemic channel label | macro-F1, AUC OvR |

**Data split:**
- Train: 2010–2019 (bỏ 2020–2021 do NPI bias)
- Validation: 2022
- CV: Walk-forward 6 folds (val year 2014–2019)

---

## Tác giả & Bản quyền

| | |
|---|---|
| **Sinh viên** | Phạm Hữu Luân |
| **MSSV** | 110122016 |
| **Lớp** | DA22TTA |
| **Trường** | Đại học Trà Vinh |
| **Khoa** | Công nghệ Thông tin |
| **GVHD** | *(Tên giảng viên hướng dẫn)* |
| **Năm** | 2025–2026 |
| **Liên hệ** | phamhuuluan18.com |

**Bản quyền © 2026 Phạm Hữu Luân.** Mã nguồn được cung cấp cho mục đích học thuật.
Không được sử dụng thương mại khi chưa có sự đồng ý bằng văn bản của tác giả.

---

*Đồ án tốt nghiệp — Hệ thống Cảnh báo Nguy cơ Dịch bệnh từ Dữ liệu Y tế và Thời tiết Toàn cầu*
