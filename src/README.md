# Source Code — EpiWeather

Source code của dự án được tổ chức ở thư mục gốc của repository thay vì nằm trong `src/`
do cấu hình Docker Compose yêu cầu các file `Dockerfile` và `docker-compose.yml` ở root.

## Cấu trúc thư mục gốc

```
KLTN/
├── backend/                    ← FastAPI backend (Python 3.11)
│   ├── app/
│   │   ├── api/v1/endpoints/   ← REST API endpoints
│   │   ├── core/               ← Config, logging, exceptions
│   │   ├── crud/               ← Database operations
│   │   ├── db/                 ← SQLAlchemy session + Alembic migrations
│   │   ├── models/             ← ORM models (16 tables)
│   │   ├── schemas/            ← Pydantic schemas
│   │   └── services/           ← ML engine, data services
│   ├── alembic/                ← Database migrations
│   ├── tests/                  ← pytest test suite
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/                   ← React + Tailwind + Leaflet
│   ├── src/
│   │   ├── components/         ← UI components (Map, Charts, Sidebar)
│   │   ├── pages/              ← HomePage, DiseaseDetailPage, AnalyticsPage
│   │   ├── hooks/              ← Custom hooks (useMapData, usePrediction...)
│   │   └── types/              ← TypeScript type definitions
│   └── Dockerfile
│
├── notebooks/                  ← ML pipeline notebooks
│   └── KLTN_EpiWeather_ML_vFinal.ipynb   ← Pipeline hoàn chỉnh
│
├── scripts/                    ← Tiện ích, seed dữ liệu, schema DB
│   └── seed_countries.py
│
├── ml_models/                  ← Trained model artifacts (.pkl)
│   ├── lgbm_flu_regressor_h1_v1.pkl
│   ├── lgbm_flu_regressor_h2_v1.pkl
│   ├── lgbm_flu_regressor_h3_v1.pkl
│   ├── lgbm_flu_regressor_h4_v1.pkl
│   ├── xgb_flu_classifier_v4.pkl
│   ├── rf_dengue_regressor_h1_v1.pkl
│   └── xgb_dengue_classifier_v4.pkl
│
├── kltn_schema.sql             ← Cơ sở dữ liệu (schema đầy đủ 16 bảng)
├── docker-compose.yml          ← Triển khai toàn bộ stack (backend + db + frontend)
├── Dockerfile.scheduler        ← Docker cho scheduler service
└── .env.example                ← Template biến môi trường
```

## Cơ sở dữ liệu

File `kltn_schema.sql` ở thư mục gốc chứa schema đầy đủ của PostgreSQL database:
- 16 bảng nghiệp vụ: `countries`, `diseases`, `observations`, `predictions`, `risk_thresholds`, v.v.
- 1 materialized view: `country_summary`

Để khôi phục database:

```bash
psql -U postgres -c "CREATE DATABASE kltn_epiweather;"
psql -U postgres -d kltn_epiweather -f kltn_schema.sql
```

## Hình ảnh và tài liệu hỗ trợ

Xem thư mục `docs/figures/` cho các hình vẽ kiến trúc hệ thống và biểu đồ kết quả ML.

## Video demo

Xem `docs/demo_video.mp4` (hoặc link trong README.md chính).

## Cách chạy

Xem [README.md](../README.md) ở thư mục gốc — mục **Hướng dẫn setup**.
