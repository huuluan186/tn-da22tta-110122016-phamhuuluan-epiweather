# Session Log — EpiWeather KLTN

---

## 12/05/2026 — Xây dựng Backend FastAPI (Bước 1/3 Demo lần 1)

### Mục tiêu buổi
Xây dựng toàn bộ backend FastAPI cho hệ thống EpiWeather: 8 endpoints, kết nối PostgreSQL, load pkl model, cấu trúc thư mục sạch và mở rộng được.

### Kết quả

#### Cấu trúc backend đã tạo (`backend/`)
```
backend/
├── app/
│   ├── main.py              ← FastAPI app, CORS, lifespan
│   ├── config.py            ← pydantic-settings, đọc ../.env
│   ├── database.py          ← SQLAlchemy engine + get_db() dependency
│   ├── models/              ← 5 files, 13 bảng (đủ toàn bộ schema DB)
│   │   ├── geography.py        Country
│   │   ├── disease.py          Disease, DataSource, WeatherVariable
│   │   ├── observation.py      DiseaseCase, WeatherObservation, FeatureConfig
│   │   ├── prediction.py       Prediction, RiskThreshold, ModelVersion, ModelEvaluation
│   │   └── mlops.py            PipelineRun, DataQualityCheck, ApiRequestLog
│   ├── crud/                ← DB query functions thuần (không raise HTTPException)
│   │   ├── countries.py
│   │   ├── diseases.py
│   │   └── predictions.py
│   ├── services/            ← Business logic, validate domain, raise HTTPException
│   │   ├── prediction_service.py
│   │   └── risk_service.py
│   ├── routers/             ← Thin controllers, chỉ parse params + gọi service
│   │   ├── health.py           GET /health
│   │   ├── countries.py        GET /api/v1/countries, /{iso3}
│   │   ├── diseases.py         GET /api/v1/diseases, /model-metrics
│   │   ├── predictions.py      GET /api/v1/predictions/{disease}/{iso3}, /history
│   │   └── risk.py             GET /api/v1/risk-map/{disease}
│   ├── ml/
│   │   └── loader.py           Load .pkl + feature_list.json + model_metrics.json
│   └── schemas/             ← Pydantic response models
├── Dockerfile
└── requirements.txt
```

#### 8 API Endpoints
| Endpoint | Status |
|----------|--------|
| GET /health | ✅ hoạt động |
| GET /api/v1/countries | ✅ code xong |
| GET /api/v1/countries/{iso3} | ✅ code xong |
| GET /api/v1/diseases | ✅ code xong |
| GET /api/v1/diseases/model-metrics | ✅ code xong |
| GET /api/v1/risk-map/{disease}?year=&week= | ✅ code xong |
| GET /api/v1/predictions/{disease}/{iso3}?year=&week= | ✅ code xong |
| GET /api/v1/predictions/{disease}/{iso3}/history | ✅ code xong |

#### Infrastructure
- `docker-compose.yml` — postgres:15-alpine + backend service + volume mount models/
- `.env` — cập nhật đầy đủ DB credentials + backend config
- `.env.example` — template cho team/CI

#### Tài liệu
- `.claude/guides/backend_guide.md` — cấu trúc, flow, quy tắc code, MLOps roadmap

### Quyết định kỹ thuật buổi này
| Quyết định | Lý do |
|-----------|-------|
| SQLAlchemy ORM (không raw SQL) | Type-safe, pythonic, dễ test |
| 4-layer: Router → Service → CRUD → Model | Separation of concerns, dễ CI/CD + unit test sau |
| Partitioned tables map vào parent | PostgreSQL tự route partition, code không cần biết |
| `env_file="../.env"` trong config.py | .env đặt ở root project, backend chạy từ `backend/` |
| Sync `def` routes (không async) | SQLAlchemy sync session, FastAPI tự thread pool |

### Bugs đã fix
1. `Mapped[Date]` → `Mapped[date]` — SQLAlchemy 2.0 yêu cầu Python type trong Mapped[]
2. `Mapped[DateTime]` → `Mapped[datetime]` — idem
3. `env_file=".env"` → `env_file="../.env"` — sai working directory
4. `uvicorn app.main:app` phải chạy từ `backend/` không phải root

### Trạng thái cuối buổi
- ✅ Server khởi động được: `uvicorn app.main:app --reload --port 8000` từ `backend/`
- ✅ Models loaded: flu + dengue pkl load thành công
- ✅ Swagger UI: http://localhost:8000/docs
- ⏳ DB connection: đang fix — DATABASE_URL đã cập nhật đúng password (`111111111`), cần restart server để verify
- ⏳ Frontend React: chưa bắt đầu

### Việc còn lại (Demo lần 1)
- [ ] Verify DB connection hoạt động, test các endpoints với data 2022
- [ ] React frontend — bản đồ Leaflet.js hiển thị risk-map
- [ ] Kết nối frontend ↔ backend (CORS đã config sẵn)
- [ ] Docker Compose chạy được full stack (db + backend + frontend)
