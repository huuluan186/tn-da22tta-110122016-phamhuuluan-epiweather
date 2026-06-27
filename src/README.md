# Source Code — EpiWeather

Toàn bộ mã nguồn, cơ sở dữ liệu và file triển khai của hệ thống nằm trong thư mục này.
Tài liệu đồ án (luận văn, slide, poster, hướng dẫn sử dụng) nằm ở `../docs/`.

## Cấu trúc

```
src/
├── backend/                    ← FastAPI backend (Python 3.11)
│   ├── app/
│   │   ├── api/v1/endpoints/   ← REST API: countries, diseases, predictions, risk, analytics
│   │   ├── core/               ← Config, logging, exceptions
│   │   ├── crud/               ← Database CRUD operations
│   │   ├── db/                 ← SQLAlchemy session
│   │   ├── models/             ← ORM models (16 bảng)
│   │   ├── schemas/            ← Pydantic schemas
│   │   └── services/           ← ML engine, prediction service, risk service
│   ├── alembic/                ← Database migrations
│   ├── tests/                  ← pytest test suite
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                   ← React + Tailwind CSS + Leaflet + Recharts
│   ├── src/
│   │   ├── components/         ← Map, Charts, Sidebar, Alerts
│   │   ├── pages/              ← HomePage, DiseaseDetailPage, AnalyticsPage
│   │   ├── hooks/              ← useMapData, usePrediction, useRisk
│   │   └── types/              ← TypeScript type definitions
│   └── Dockerfile
├── notebooks/                  ← Notebook pipeline ML (Google Colab)
├── scripts/                    ← Seed dữ liệu, sync data, batch predict, bootstrap DB
├── ml_models/                  ← Model đã huấn luyện (.pkl + _features.json + _metrics.json)
├── data/                       ← Dữ liệu thô và đã xử lý (CSV)
│   ├── epidemic/raw/           ← WHO FluNet, OpenDengue
│   ├── weather/processed/      ← ERA5 weekly 2010-2019
│   └── processed/              ← Feature CSV cho FastAPI
├── outputs/                    ← Hình sinh ra từ pipeline
├── kltn_schema.sql             ← Schema PostgreSQL đầy đủ (16 bảng + 1 view)
├── docker-compose.yml          ← Triển khai toàn bộ stack (db + backend + frontend + scheduler)
├── Dockerfile.scheduler        ← Image cho seed + scheduler service
├── Makefile / dev.ps1          ← Lệnh tiện ích (Linux/macOS và Windows)
└── .env.example                ← Template biến môi trường
```

## Chạy bằng Docker Compose

```bash
cd src
cp .env.example .env          # chỉnh DB_PASSWORD trước khi chạy
docker compose up -d
docker compose exec backend python scripts/seed_countries.py
curl http://localhost:8000/health
```

Frontend: http://localhost:3000 — API docs: http://localhost:8000/docs

## Khôi phục database từ schema

```bash
psql -U postgres -c "CREATE DATABASE kltn_epiweather;"
psql -U postgres -d kltn_epiweather -f kltn_schema.sql
```

Hướng dẫn chi tiết và biến môi trường: xem [../README.md](../README.md).
