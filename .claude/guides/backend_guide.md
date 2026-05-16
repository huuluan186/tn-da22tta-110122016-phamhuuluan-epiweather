# Backend Guide — EpiWeather FastAPI

## Cấu trúc thư mục

```
backend/
├── app/
│   ├── main.py              ← Entry point: FastAPI app, CORS, lifespan, include routers
│   ├── config.py            ← Settings đọc từ .env (pydantic-settings)
│   ├── database.py          ← SQLAlchemy engine + SessionLocal + get_db() dependency
│   │
│   ├── models/              ← ORM: khai báo bảng DB (chỉ schema, không logic)
│   │   ├── __init__.py         re-export tất cả models
│   │   ├── geography.py        Country
│   │   ├── disease.py          Disease, DataSource, WeatherVariable
│   │   ├── observation.py      DiseaseCase, WeatherObservation, FeatureConfig
│   │   ├── prediction.py       Prediction, RiskThreshold, ModelVersion, ModelEvaluation
│   │   └── mlops.py            PipelineRun, DataQualityCheck, ApiRequestLog
│   │
│   ├── crud/                ← DB query functions (nhận Session, trả ORM objects)
│   │   ├── countries.py        get_by_iso3(), list_all()
│   │   ├── diseases.py         get_by_code(), list_active()
│   │   └── predictions.py      get_one(), list_for_map(), list_history(), list_actuals()
│   │
│   ├── services/            ← Business logic (orchestrate crud, validate, format)
│   │   ├── prediction_service.py   resolve_disease(), get_prediction(), get_history()
│   │   └── risk_service.py         get_risk_map()
│   │
│   ├── routers/             ← Thin controllers: parse params → gọi service → trả response
│   │   ├── health.py           GET /health
│   │   ├── countries.py        GET /api/v1/countries, /{iso3}
│   │   ├── diseases.py         GET /api/v1/diseases, /model-metrics
│   │   ├── predictions.py      GET /api/v1/predictions/{disease}/{iso3}, /history
│   │   └── risk.py             GET /api/v1/risk-map/{disease}
│   │
│   ├── ml/
│   │   └── loader.py        ← Load .pkl + feature_list.json + model_metrics.json lúc startup
│   │
│   └── schemas/             ← Pydantic response models (validate + serialize)
│       ├── country.py          Country, CountryDetail
│       ├── disease.py          Disease, ModelMetrics
│       └── prediction.py       PredictionPoint, RiskMapItem, RiskMapResponse, HistoryResponse
│
├── Dockerfile
└── requirements.txt
```

---

## 8 API Endpoints

| Method | Path | Mô tả |
|--------|------|--------|
| GET | `/health` | Status DB + models loaded + metrics summary |
| GET | `/api/v1/countries` | Danh sách quốc gia (iso3, tên, lat/lng) |
| GET | `/api/v1/countries/{iso3}` | Chi tiết 1 quốc gia |
| GET | `/api/v1/diseases` | Danh sách bệnh active |
| GET | `/api/v1/diseases/model-metrics` | Metrics từ model_metrics.json |
| GET | `/api/v1/risk-map/{disease}?year=&week=` | Risk level toàn bộ quốc gia (Leaflet map) |
| GET | `/api/v1/predictions/{disease}/{iso3}?year=&week=` | Dự báo 1 tuần, 1 quốc gia |
| GET | `/api/v1/predictions/{disease}/{iso3}/history?start_year=&end_year=` | Time series predicted vs actual |

> `{disease}` nhận giá trị: `flu` hoặc `dengue`

---

## Flow xử lý request

```
HTTP Request
    ↓
Router        — validate path/query params, gọi service
    ↓
Service       — resolve business logic, validate domain rules, gọi crud
    ↓
CRUD          — SQLAlchemy ORM query, trả ORM object hoặc list
    ↓
Model (ORM)   — mapping với bảng PostgreSQL
    ↓
Database      — psycopg2 + SQLAlchemy engine (connection pool)
```

---

## Quy tắc viết code

### Router — chỉ làm 3 việc

```python
@router.get("/{disease}/{iso3}/history", response_model=HistoryResponse)
def get_history(
    disease: str,
    iso3: str,
    start_year: int = Query(2022, ge=2010),
    end_year: int = Query(2022, le=2030),
    db: Session = Depends(get_db),          # inject session
):
    return prediction_service.get_history(db, disease, iso3, start_year, end_year)
```

**Không được** viết query hay business logic trong router. Router chỉ: nhận params → gọi service → trả kết quả.

### CRUD — chỉ query, không raise HTTPException

```python
# ĐÚNG — trả None nếu không tìm thấy
def get_by_iso3(db: Session, iso3: str) -> Country | None:
    return db.get(Country, iso3.upper())

# SAI — CRUD không biết context HTTP, không raise HTTPException
def get_by_iso3(db: Session, iso3: str) -> Country:
    country = db.get(Country, iso3.upper())
    if not country:
        raise HTTPException(...)   # ← không làm thế này ở CRUD
```

### Service — xử lý logic, raise HTTPException

```python
def get_prediction(db, disease_code, iso3, year, week) -> PredictionPoint:
    disease = resolve_disease(db, disease_code)   # validate + 400/404
    row = prediction_crud.get_one(db, disease.id, iso3.upper(), year, week)
    if not row:
        raise HTTPException(status_code=404, detail="Không có dự báo")
    return PredictionPoint.model_validate(row, from_attributes=True)
```

### ORM Models — chỉ khai báo schema

```python
class Prediction(Base):
    __tablename__ = "predictions"
    # Partitioned tables: map vào parent table, PG tự route đến đúng partition
    __table_args__ = {"postgresql_partition_by": "RANGE (iso_year)"}
    ...
```

**Không** thêm method logic vào model class. Model chỉ là schema mapping.

### Bảng DB đã map (13 tables)

| File | Bảng |
|------|------|
| `geography.py` | `countries` |
| `disease.py` | `diseases`, `data_sources`, `weather_variables` |
| `observation.py` | `disease_cases`✱, `weather_observations`✱, `feature_configs` |
| `prediction.py` | `predictions`✱, `risk_thresholds`, `model_versions`, `model_evaluations` |
| `mlops.py` | `pipeline_runs`, `data_quality_checks`, `api_request_logs`✱ |

✱ = partitioned table (map vào parent, PG route tự động)

---

## Workflow thêm endpoint mới

1. **CRUD** — thêm function query vào `crud/<domain>.py`
2. **Service** — thêm function orchestrate vào `services/<domain>_service.py`
3. **Schema** — thêm Pydantic model vào `schemas/<domain>.py` nếu cần response mới
4. **Router** — thêm route handler (thin, gọi service)
5. **Test** — Swagger UI tại `http://localhost:8000/docs`

---

## Lộ trình tích hợp sau Demo lần 1

### CI/CD (GitHub Actions)
- Mỗi layer (crud, service) cần pytest unit test để CI chạy được
- Dockerfile build reproducible → pin version trong `requirements.txt`
- Build image → push Docker Hub → deploy

### MLOps
Schema DB đã sẵn sàng, implement theo thứ tự:
- `api_request_logs` → middleware log mọi request vào predictions endpoint
- `pipeline_runs` → khi retrain tự động, ghi kết quả
- `model_versions` + `is_champion` → champion/challenger switching không cần restart server

**Nguyên tắc giữ code MLOps-ready:**
- Không hardcode `model_version_id` — query `is_champion = TRUE` khi cần
- `MODELS_DIR` đọc từ env → CI/CD override path dễ dàng

---

## Chạy local (không Docker)

```bash
cd backend
# Đảm bảo DATABASE_URL trong .env trỏ đúng PostgreSQL local
uvicorn app.main:app --reload --port 8000
```

Swagger UI: http://localhost:8000/docs

---

## Biến môi trường (.env)

| Biến | Mô tả | Default |
|------|--------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://postgres:postgres@localhost:5432/kltn_epiweather` |
| `MODELS_DIR` | Đường dẫn tới thư mục chứa .pkl | `../models` |
| `DEBUG` | Bật debug mode | `false` |
| `CORS_ORIGINS` | JSON array origins cho frontend | `["http://localhost:3000"]` |
