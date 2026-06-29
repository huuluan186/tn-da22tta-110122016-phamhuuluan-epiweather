# EpiWeather - Hệ thống Cảnh báo Nguy cơ Dịch bệnh Theo Mùa

> Đồ án tốt nghiệp (KLTN) — Đại học Trà Vinh, Khoa Công nghệ Thông tin
>
> **Sinh viên:** Phạm Hữu Luân · **MSSV:** 110122016 · **Lớp:** DA22TTA · **GVHD:** Bùi Thị Thanh Mai

Hệ thống tích hợp dữ liệu y tế toàn cầu (WHO FluNet, WHO Dengue) và dữ liệu khí hậu (ERA5/ECMWF) để dự báo nguy cơ dịch cúm và sốt xuất huyết theo tuần, cấp quốc gia. Pipeline gồm hai nhánh song song: **Regression** (dự báo số ca) và **Classification** (cảnh báo mức độ Low/Medium/High).

---

## Table of contents

- [Introduction](#introduction)
- [Features](#features)
- [Architecture](#architecture)
- [How it works](#how-it-works)
- [Tech stack](#tech-stack)
- [Repository structure](#repository-structure)
- [Requirements](#requirements)
- [Setup guide](#setup-guide)
- [Environment variables](#environment-variables)
- [API endpoints](#api-endpoints)
- [ML pipeline](#ml-pipeline)
- [Author](#author)

---

## Introduction

Influenza and dengue both move with the weather. Respiratory viruses spread more
in cold, dry, low-sunlight weeks; dengue follows the mosquito breeding cycle, which
depends on temperature, humidity and rainfall. EpiWeather uses that link to forecast
where outbreaks are heading. It merges weekly WHO surveillance data (FluNet for flu,
WHO reports for dengue) with 17 ERA5 climate variables, then models how case counts
respond to weather a few weeks earlier.

There are two outputs. The regression branch predicts weekly case counts up to four
weeks ahead. The classification branch assigns each country a Low, Medium or High
label using the endemic channel method (Bortman 1999, WHO EWARS), which compares the
forecast against that country's own historical baseline for the same week of the year.
A country with 500 cases might be Low if 500 is normal for that week, or High if its
baseline is 50. Both outputs are served over a REST API and drawn on a world map with
per-country detail pages.

Training covers 2010–2019. The years 2020–2021 are left out because pandemic control
measures cut flu reporting by roughly 99%, which would teach the model the wrong
seasonality; 2022 is used for validation. Coverage is 189 countries for influenza and
41 for dengue.

---

## Features

- Weekly case-count forecasts for influenza (189 countries) and dengue (41 countries),
  four horizons ahead (h1–h4)
- Low / Medium / High risk labels per country, from the endemic channel threshold
- A Leaflet world map coloured by risk level, switchable between the latest week and
  any past week (backtest)
- Per-disease detail pages with a forecast trend chart, seasonal heatmap, country
  mini-map, and the model's R²/RMSE/MAE
- An analytics page comparing model performance, feature importance and training-data
  coverage
- 17 ERA5 climate variables, each shifted by a disease-specific lag
- FastAPI REST API with OpenAPI docs at `/docs`
- A background scheduler that refreshes predictions for the most recent week

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                     Frontend (React)                     │
│          Leaflet choropleth · ECharts / Recharts         │
└─────────────────────┬────────────────────────────────────┘
                      │ HTTP / REST
┌─────────────────────▼────────────────────────────────────┐
│                  FastAPI Backend                         │
│   /api/v1/countries  /api/v1/diseases  /api/v1/infer    │
│   /api/v1/predictions  /api/v1/risk  /api/v1/analytics  │
└──────────┬──────────────────────────┬────────────────────┘
           │                          │
┌──────────▼──────────┐   ┌───────────▼───────────────────┐
│     PostgreSQL      │   │        ML Models (.pkl)        │
│  countries          │   │  lgbm_flu_regressor_h1..h4_v1  │
│  diseases           │   │  rf_dengue_regressor_h1..h4_v1 │
│  observations       │   │  xgb_flu_classifier_v4         │
│  predictions        │   │  xgb_dengue_classifier_v4      │
└─────────────────────┘   └───────────────────────────────┘
```

---

## How it works

There are two halves. The training pipeline runs once in the notebooks and produces
the model files. The serving stack is what starts when you run the app.

Data comes in first. WHO surveillance and ERA5 climate grids are pulled for 2010–2022.
ERA5 is the slow part, since it ships as hourly grids of 721×1440 cells. A KD-tree
matches each country centroid to its nearest grid cell, and the hourly values are
rolled up to one number per country per week. Disease and weather are then joined on
`iso3 × ISO-week`.

Next the features. Cross-correlation analysis showed that disease lags weather rather
than reacting to it the same week, so each climate variable is shifted accordingly. Flu
lines up with temperature about 4 weeks back and humidity about 8; dengue follows
humidity around 2 weeks and solar radiation around 4. Past case counts (auto-regressive
lags) and the week-of-year go in too. The target is `log1p(case_count)` because a few
countries dominate the raw totals.

Then training. Four regression models — XGBoost, LightGBM, Random Forest, and a Prophet
baseline — run through walk-forward cross-validation (6 folds, validation years
2014–2019) and get compared on RMSE, MAE and R². A separate XGBClassifier handles the
Low/Medium/High label. Each winning model is saved as a `.pkl` next to its feature list
and metrics. Production ended up using LightGBM for flu and Random Forest for dengue.

Serving ties it together. On first start the database is seeded with countries, history,
features and precomputed predictions. The FastAPI backend loads the model files and
serves the prediction, risk-map and analytics endpoints; the React frontend calls those
to draw the map and detail pages. The scheduler keeps the latest week up to date in the
background.

---

## Tech stack

| Layer                 | Technology                                                           |
| --------------------- | -------------------------------------------------------------------- |
| Backend               | Python 3.11, FastAPI 0.110, Uvicorn, SQLAlchemy 2.0                  |
| Database              | PostgreSQL 15                                                        |
| ML                    | XGBoost 2.0, LightGBM 4.3, scikit-learn 1.6, Prophet                 |
| Hyperparameter tuning | Optuna                                                               |
| Climate data          | ERA5 (ECMWF) — historical training · Open-Meteo for recent periods |
| Frontend              | React, Tailwind CSS, Leaflet.js, ECharts, Recharts                   |
| Containerization      | Docker, Docker Compose v2                                            |

---

## Repository structure

```
tn-da22tta-110122016-phamhuuluan-epiweather/
├── src/                           ← all source code
│   ├── backend/                   ← FastAPI backend (Python 3.11)
│   │   ├── app/
│   │   │   ├── api/v1/endpoints/  ← REST routes: countries, diseases, predictions, risk, analytics
│   │   │   ├── core/              ← config, logging, exceptions
│   │   │   ├── crud/              ← database CRUD
│   │   │   ├── models/            ← SQLAlchemy ORM (16 tables)
│   │   │   ├── schemas/           ← Pydantic schemas
│   │   │   └── services/          ← ML engine, prediction, risk services
│   │   ├── alembic/               ← DB migrations
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── frontend/                  ← React + Tailwind CSS + Leaflet + ECharts
│   │   ├── src/
│   │   └── Dockerfile
│   ├── notebooks/                 ← ML pipeline notebooks (Google Colab)
│   ├── ml_models/                 ← trained model artifacts (.pkl + _features/_metrics.json)
│   ├── data/processed/            ← feature CSVs used by the backend
│   ├── scripts/                   ← seed, sync, batch predict, bootstrap DB
│   ├── kltn_schema.sql            ← full PostgreSQL schema (16 tables + 1 view)
│   ├── docker-compose.yml
│   ├── Dockerfile.scheduler
│   └── .env.example
├── docs/                          ← official submission documents
│   └── huong_dan_su_dung.md       ← user guide
└── README.md
```

---

## Requirements

- Docker & Docker Compose v2+ **(recommended — no other dependencies needed)**
- Or: Python 3.11+, Node.js 18+, PostgreSQL 15+

---

## Setup guide

### Option 1 — Docker Compose (recommended)

```bash
# 1. Clone the repository
git clone https://github.com/huuluan186/tn-da22tta-110122016-phamhuuluan-epiweather.git
cd tn-da22tta-110122016-phamhuuluan-epiweather/src

# 2. Create .env from template
cp .env.example .env
# Edit .env: set DB_PASSWORD (and optionally CDS_KEY for ERA5 downloads)

# 3. Start all services
#    This automatically: starts PostgreSQL, seeds the database,
#    loads ML models, and starts the backend + frontend.
docker compose up -d

# 4. Wait ~2 minutes for the seed service to finish, then verify
curl http://localhost:8000/health
```

- Frontend: http://localhost:3000
- API docs: http://localhost:8000/docs

To watch seed progress: `docker compose logs -f seed`

---

### Option 2 — Local development

```bash
# 1. Clone the repository
git clone https://github.com/huuluan186/tn-da22tta-110122016-phamhuuluan-epiweather.git
cd tn-da22tta-110122016-phamhuuluan-epiweather/src

# 2. Backend — create virtual environment and install dependencies
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/macOS
pip install -r backend/requirements.txt

# 3. Create .env
cp .env.example .env
# Edit .env: set DB_HOST=localhost, DB_PASSWORD, etc.

# 4. Create the PostgreSQL database and apply schema
psql -U postgres -c "CREATE DATABASE kltn_epiweather;"
psql -U postgres -d kltn_epiweather -f kltn_schema.sql

# 5. Seed data (countries, observations, features, predictions)
python scripts/bootstrap_db.py

# 6. Start the backend
cd backend
uvicorn app.main:app --reload --port 8000

# 7. Frontend (separate terminal)
cd ../frontend
npm install
npm run dev     # runs on http://localhost:5173
```

---

### Running the ML notebook

The training notebook is at `src/notebooks/KLTN_EpiWeather_ML_final.ipynb`.
Run on **Google Colab** (recommended) or locally:

```bash
pip install jupyter xgboost lightgbm optuna prophet scikit-learn pandas numpy
jupyter notebook src/notebooks/
```

Place datasets in `src/data/processed/` before running (or mount Google Drive).

---

## Environment variables

Copy `.env.example` to `.env` and fill in the required values:

| Variable                 | Description                                   | Default                                               |
| ------------------------ | --------------------------------------------- | ----------------------------------------------------- |
| `DB_USER`              | PostgreSQL username                           | `epiweather`                                        |
| `DB_PASSWORD`          | PostgreSQL password                           | *(required)*                                        |
| `DB_NAME`              | Database name                                 | `kltn_epiweather`                                   |
| `DB_HOST`              | Database host                                 | `localhost`                                         |
| `DB_PORT`              | Database port                                 | `5432`                                              |
| `MODELS_DIR`           | Path to model artifacts directory             | `ml_models`                                         |
| `CDS_KEY`              | ERA5/CDS API key for downloading climate data | *(optional)*                                        |
| `DEBUG`                | Enable debug mode                             | `false`                                             |
| `APP_VERSION`          | Version shown in API responses                | `1.0.0`                                             |
| `CORS_ORIGINS`         | Allowed CORS origins                          | `["http://localhost:3000","http://localhost:5173"]` |
| `ENABLE_API_SCHEDULER` | Enable background prediction scheduler        | `true`                                              |

---

## API endpoints

| Method   | Endpoint                | Description                             |
| -------- | ----------------------- | --------------------------------------- |
| `GET`  | `/health`             | Health check                            |
| `GET`  | `/api/v1/countries`   | List countries                          |
| `GET`  | `/api/v1/diseases`    | List diseases                           |
| `POST` | `/api/v1/infer`       | Run inference from feature input        |
| `GET`  | `/api/v1/predictions` | Prediction history                      |
| `GET`  | `/api/v1/risk`        | Current risk map data                   |
| `GET`  | `/api/v1/analytics`   | Model performance and training coverage |

Full OpenAPI schema: http://localhost:8000/docs

---

## ML pipeline

Two parallel training branches, results compared in the final notebook:

**Branch A — Regression** (case count forecast)

| Model                   | Target                | Metrics        |
| ----------------------- | --------------------- | -------------- |
| XGBoost Regressor       | `log1p(case_count)` | RMSE, MAE, R² |
| LightGBM Regressor      | `log1p(case_count)` | RMSE, MAE, R² |
| Random Forest Regressor | `log1p(case_count)` | RMSE, MAE, R² |
| Prophet (baseline)      | `case_count`        | RMSE, MAE, R² |

**Branch B — Classification** (Low / Medium / High alert)

| Model                 | Target                | Metrics           |
| --------------------- | --------------------- | ----------------- |
| XGBClassifier         | Endemic channel label | macro-F1, AUC OvR |
| Regressor + threshold | Endemic channel label | macro-F1, AUC OvR |

**Data split:**

- Train: 2010–2019 (2020–2021 excluded due to NPI reporting bias)
- Validation: 2022
- CV: walk-forward 6 folds (val years 2014–2019)

---

## Author

|                      |                        |
| -------------------- | ---------------------- |
| **Student**    | Phạm Hữu Luân       |
| **ID**         | 110122016              |
| **Class**      | DA22TTA                |
| **University** | Đại học Trà Vinh   |
| **Faculty**    | Công nghệ Thông tin |
| **Supervisor** | Phạm Thị Trúc Mai |
| **Year**       | 2025–2026             |

Copyright © 2026 Phạm Hữu Luân. Source code provided for academic purposes only.
