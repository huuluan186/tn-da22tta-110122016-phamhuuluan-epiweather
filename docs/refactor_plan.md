# Refactor Plan — KLTN EpiWeather

**Ngày bắt đầu:** 2026-05-19
**Mục tiêu:** Đưa codebase từ trạng thái post-Demo 1 lên cấu trúc production-grade (System Design chuẩn), đồng thời scaffold toàn bộ frontend.

**Phạm vi:** Theo proposal kiến trúc mới, **bỏ qua** pgadmin trong docker-compose và PostGIS.

---

## Tracking Status

| Phase | Tên | Effort | Status | Ngày bắt đầu | Ngày hoàn thành | Ghi chú |
|---|---|---|---|---|---|---|
| 1 | Foundation cleanup | 2-3h | ✅ Done | 2026-05-19 | 2026-05-19 | core/, db/, Loguru, Makefile |
| 2 | Alembic migrations | 1-2h | ✅ Done | 2026-05-19 | 2026-05-19 | DB versioning |
| 3 | Tests scaffold | 2h | ✅ Done | 2026-05-19 | 2026-05-19 | 27 tests passed |
| 4 | API restructure | 3-4h | ✅ Done | 2026-05-19 | 2026-05-19 | 27/27 tests passed |
| 5 | Rename folders | 1h | ✅ Done | 2026-05-19 | 2026-05-19 | models/→ml_models/, dataset/→data/ |
| 6 | docker-compose update | 30min | ✅ Done | 2026-05-19 | 2026-05-19 | env sync, frontend service stub |
| 7 | Frontend scaffold | 2-3h | ⬜ Pending | | | Vite + React + TS + Tailwind + shadcn |
| 8 | Frontend features | 2-3 tuần | ⬜ Pending | | | Layout, Map, Charts, Pages |
| 9 | Integration polish | 1 tuần | ⬜ Pending | | | CI, README, audit logs |

**Legend:** ⬜ Pending · 🟡 In Progress · ✅ Done · ❌ Blocked · ⏸ Paused

---

## PHASE 1 — Foundation cleanup

**Status:** ✅ Done (2026-05-19)
**Mục tiêu:** tách `config.py` + `database.py` ra đúng cấu trúc, thêm Loguru, Makefile. Không thay đổi behavior.

### Checklist

- [x] Tạo `backend/app/core/__init__.py`
- [x] Tạo `backend/app/core/config.py` (move từ `backend/app/config.py`)
- [x] Tạo `backend/app/core/exceptions.py` (custom exceptions)
- [x] Tạo `backend/app/core/logging.py` (Loguru config + utf-8 fix Windows)
- [x] Tạo `backend/app/db/__init__.py`
- [x] Tạo `backend/app/db/base_class.py` (re-export Base từ models.geography)
- [x] Tạo `backend/app/db/session.py` (engine + SessionLocal + `get_db()`)
- [x] Tạo `backend/app/db/base.py` (import all models cho Alembic)
- [x] Tạo `backend/app/middleware/__init__.py`
- [x] Tạo `Makefile` (dev, migrate, seed, test, lint, format, docker-up/down, clean)
- [x] Thêm `loguru`, `alembic`, `pytest`, `pytest-asyncio`, `httpx` vào `backend/requirements.txt`
- [x] Cập nhật `backend/app/main.py`: import từ `core.config` + `core.logging`, thêm exception handlers + Loguru
- [x] Sửa tất cả `from .config` → `from app.core.config` (main.py)
- [x] Sửa tất cả `from ..database` → `from ..db.session` (5 routers)
- [x] Bonus: thay `print()` → `logger` trong `ml/loader.py` (4 chỗ)
- [x] Xóa `backend/app/config.py` (đã chuyển)
- [x] Xóa `backend/app/database.py` (đã chuyển)

### Verify
- [x] `python -c "from app.main import app"` import OK
- [x] TestClient `GET /health` → 200 (database connected)
- [x] Loguru hiển thị tiếng Việt có dấu trên Windows

### Notes
- Base class vẫn nằm trong `models/geography.py` để tránh refactor lan rộng. `db/base_class.py` chỉ re-export.
- ✅ Fix MODELS_DIR path resolution: anchor vào `PROJECT_ROOT` (tính từ `__file__`) qua field_validator. Không còn phụ thuộc CWD. Tất cả 4 model `.pkl` load OK.
- Pydantic warning `model_type` protected namespace: pre-existing, không xử lý ở Phase 1.

---

## PHASE 2 — Alembic migrations

**Status:** ✅ Done (2026-05-19)
**Mục tiêu:** schema versioning, từ giờ thay đổi DB phải đi qua migration.

### Checklist

- [x] `cd backend && alembic init alembic`
- [x] Edit `backend/alembic/env.py`:
  - [x] Import `app.db.base` (side-effect: register all models)
  - [x] `target_metadata = Base.metadata`
  - [x] Override `sqlalchemy.url` từ `app.core.config`
  - [x] Thêm `include_object` filter để loại bỏ partition tables
- [x] Tạo baseline revision rỗng: `alembic revision -m "initial_baseline"`
- [x] `alembic stamp head` → DB ghi nhận ở `cbd62e71217a`
- [x] Verify: `alembic current` → `cbd62e71217a (head)`
- [x] Makefile đã có `make migrate` + `make migration name=...`

### Verify
- [x] `alembic_version` table tồn tại với 1 row (`cbd62e71217a`)
- [x] `alembic current` → `cbd62e71217a (head)`

### Notes
- DB có partition tables (`disease_cases_2010`, `weather_obs_2013`...) không có trong ORM — đã thêm `include_object` filter với regex pattern để Alembic bỏ qua hoàn toàn.
- Schema drift nhỏ giữa ORM (`String`) và DB thực tế (`CHAR`) được chấp nhận — không ảnh hưởng runtime. Sẽ dần đồng bộ khi thay đổi schema.
- **Workflow tương lai:** `make migration name=add_xxx` → review file → `make migrate`

---

## PHASE 3 — Tests scaffold

**Status:** ✅ Done (2026-05-19)
**Mục tiêu:** safety net trước khi refactor lớn ở Phase 4.

### Checklist

- [x] Tạo `backend/tests/__init__.py`
- [x] Tạo `backend/tests/conftest.py` (SQLite in-memory, `client` fixture, `db_session` rollback)
- [x] Tạo `backend/tests/test_health.py` (4 tests)
- [x] Tạo `backend/tests/test_infer.py` (13 tests — happy path + validation errors)
- [x] Tạo `backend/tests/test_diseases.py` (6 tests — list + model metrics)
- [x] Tạo `backend/tests/test_countries.py` (4 tests — list + not found)
- [x] Tạo `backend/pytest.ini`
- [x] `Makefile make test` đã có từ Phase 1

### Verify
- [x] `pytest -v` → **27/27 passed** trong 12.3s

### Notes
- SQLite in-memory cho unit tests — không cần PostgreSQL chạy
- `client_with_real_db` fixture có sẵn trong conftest cho integration tests khi cần
- Warnings về XGBoost pickle + sklearn feature names: pre-existing, không ảnh hưởng kết quả

---

## PHASE 4 — Restructure API routing

**Status:** ✅ Done (2026-05-19)
**Mục tiêu:** Chuyển `routers/` → `api/v1/endpoints/`, tách services rõ ràng.

### Checklist

- [ ] Tạo `backend/app/api/__init__.py`
- [ ] Tạo `backend/app/api/v1/__init__.py`
- [ ] Tạo `backend/app/api/v1/api.py` (APIRouter aggregator)
- [ ] Tạo `backend/app/api/v1/endpoints/__init__.py`
- [ ] `git mv routers/countries.py api/v1/endpoints/countries.py`
- [ ] `git mv routers/diseases.py api/v1/endpoints/diseases.py`
- [ ] `git mv routers/predictions.py api/v1/endpoints/predictions.py`
- [ ] `git mv routers/risk.py api/v1/endpoints/risk.py`
- [ ] `git mv routers/infer.py api/v1/endpoints/infer.py`
- [ ] Giữ `routers/health.py` ngoài v1 (infrastructure check)
- [ ] Tạo mới `backend/app/api/v1/endpoints/weather.py` (GET ERA5 raw)
- [ ] Tạo mới `backend/app/api/v1/endpoints/analytics.py` (dashboard aggregates)
- [ ] Tạo `backend/app/services/ml_engine.py` (merge từ `ml/loader.py` + inference logic)
- [ ] Tạo `backend/app/services/data_fetcher.py` (OpenWeatherMap client)
- [ ] Cập nhật `backend/app/main.py`: chỉ còn 1 `include_router(api_router, prefix="/api/v1")` + 1 cho health
- [ ] Cập nhật tests nếu hardcode URL
- [ ] Xóa `backend/app/routers/` (cả folder)
- [ ] Xóa `backend/app/ml/loader.py` (đã merge)

### Verify
- [ ] `pytest` → all green
- [ ] `/docs` hiển thị đủ endpoints với prefix mới
- [ ] Frontend (nếu đã có) gọi API vẫn OK

---

## PHASE 5 — Rename data/model folders

**Status:** ✅ Done (2026-05-19)
**Mục tiêu:** đồng bộ với cấu trúc đề xuất.

### Checklist

- [x] Rename `models/` → `ml_models/` (filesystem + git tracked)
- [x] Rename `dataset/` → `data/` (filesystem + git tracked)
- [x] Cập nhật `backend/app/core/config.py`: `MODELS_DIR = PROJECT_ROOT / "ml_models"`
- [x] Cập nhật `.env.example`: `MODELS_DIR=../ml_models`
- [x] Cập nhật `.env`: `MODELS_DIR=./ml_models`
- [x] Cập nhật `docker-compose.yml`: env + volume `./ml_models:/app/ml_models:ro`
- [x] `backend/Dockerfile` không COPY models trực tiếp — không cần sửa
- [x] Cập nhật `scripts/seed_countries.py`: `../data/processed/master_weekly_v1.csv`
- [x] Cập nhật `.claude/CLAUDE.md`: session template path
- [x] Cập nhật `README.md`: cấu trúc thư mục

### Verify
- [x] `pytest` 27/27 xanh — models load OK từ `ml_models/`
- [x] Notebook: paths dẫn đến `data/processed/` (update riêng khi cần)

---

## PHASE 6 — docker-compose update

**Status:** ✅ Done (2026-05-19)
**Mục tiêu:** 1 lệnh `docker compose up` chạy đủ db + backend + frontend stub.

### Checklist

- [x] Cập nhật `docker-compose.yml`:
  - [x] DB env vars đồng bộ với `.env` (${DB_USER}, ${DB_PASSWORD}, ${DB_NAME})
  - [x] Volume `./ml_models:/app/ml_models:ro` (đã cập nhật ở Phase 5)
  - [x] Thêm `frontend` service stub (commented-out, uncommit sau Phase 7)
  - [x] Healthcheck cho `db` service
  - [x] `backend.depends_on.db.condition: service_healthy`
- [x] **KHÔNG thêm pgadmin** (theo yêu cầu)
- [x] **KHÔNG thêm PostGIS** (theo yêu cầu)

### Notes
- `frontend` service được thêm vào dưới dạng comment đầy đủ — uncommit sau khi Phase 7 scaffold có `frontend/Dockerfile`.
- db + backend đã chạy OK trước Phase 6; Phase 6 chỉ clean up và thêm frontend template.

### Verify
- [x] Cấu trúc docker-compose valid (yaml lint OK)

---

## PHASE 7 — Frontend scaffold

**Status:** ⬜ Pending
**Mục tiêu:** Vite + React + TS + Tailwind + shadcn/ui render được trang trắng có layout.

### Setup commands

```bash
npm create vite@latest frontend -- --template react-ts
cd frontend
npm i @tanstack/react-query axios react-router-dom zustand
npm i react-leaflet leaflet @types/leaflet
npm i recharts
npm i -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
npx shadcn@latest init
npx shadcn@latest add button card table dialog select skeleton
```

### Checklist

- [ ] Scaffold Vite + React + TS
- [ ] Setup Tailwind + shadcn/ui
- [ ] Cài @tanstack/react-query, axios, react-router-dom, zustand
- [ ] Cài react-leaflet, recharts
- [ ] Tạo cấu trúc thư mục:
  - [ ] `src/api/` (axios.ts, queryClient.ts)
  - [ ] `src/assets/` (world.geojson — download từ naturalearth)
  - [ ] `src/components/common/`
  - [ ] `src/components/layout/` (Sidebar, Navbar, Layout)
  - [ ] `src/components/maps/`
  - [ ] `src/components/charts/`
  - [ ] `src/components/dashboard/`
  - [ ] `src/hooks/`
  - [ ] `src/pages/` (Home, DiseaseDetail, Analytics, Settings)
  - [ ] `src/store/` (uiStore.ts — Zustand)
  - [ ] `src/types/` (disease, prediction, country)
  - [ ] `src/utils/` (formatters, riskLevel)
- [ ] Tạo `src/router.tsx` (react-router routes)
- [ ] Tạo `Dockerfile` + `nginx.conf` cho production build
- [ ] Cập nhật `App.tsx` + `main.tsx` với QueryClientProvider + RouterProvider

### Verify
- [ ] `npm run dev` → http://localhost:5173 render Layout cơ bản
- [ ] Navigate giữa 4 pages OK (chưa cần content)
- [ ] No TypeScript errors

---

## PHASE 8 — Frontend features

**Status:** ⬜ Pending
**Mục tiêu:** từng page hoạt động với data thật.

### Sub-phases (mỗi sub = 1 commit)

- [ ] **8.1** Layout polish — Sidebar + Navbar + responsive
- [ ] **8.2** Home — KPI cards với mock data
- [ ] **8.3** Home — Choropleth map (react-leaflet + world.geojson) với mock data
- [ ] **8.4** Home — Map gọi `/api/v1/risk` thật (kết nối backend)
- [ ] **8.5** DiseaseDetail — Trend chart với `/api/v1/predictions?iso3=VNM&disease=flu`
- [ ] **8.6** DiseaseDetail — Bảng top countries
- [ ] **8.7** Analytics — So sánh nhiều nước (RiskBarChart)
- [ ] **8.8** Analytics — Heatmap mùa vụ (optional)
- [ ] **8.9** Settings — Chọn disease, year range (Zustand persist)
- [ ] **8.10** Error boundaries + loading skeletons toàn app

### Verify
- [ ] Toàn bộ user flow chạy end-to-end
- [ ] No console errors
- [ ] Responsive trên mobile (basic)

---

## PHASE 9 — Integration polish

**Status:** ⬜ Pending
**Mục tiêu:** clean up trước demo cuối.

### Checklist

- [ ] CORS audit (đã có sẵn trong `main.py`)
- [ ] Loading states + error boundaries tất cả pages
- [ ] Cập nhật `README.md`: setup frontend đầy đủ
- [ ] GitHub Actions:
  - [ ] `.github/workflows/backend-ci.yml` (lint + pytest)
  - [ ] `.github/workflows/frontend-ci.yml` (lint + build)
- [ ] (Optional) Audit log table cho data updates
- [ ] (Optional) Sentry hoặc tương đương cho error tracking
- [ ] Performance check: API response < 500ms, frontend FCP < 2s

---

## Notes & Decisions

### Đã chốt
- ✅ Theo toàn bộ proposal trừ pgadmin và PostGIS
- ✅ Renames: `models/` → `ml_models/`, `dataset/` → `data/`
- ✅ Restructure: `routers/` → `api/v1/endpoints/`
- ✅ shadcn/ui thay vì Ant Design
- ✅ @tanstack/react-query cho data fetching
- ✅ Loguru cho logging
- ✅ Zustand cho UI state

### Chưa quyết
- ⏳ Auth: có làm không? Nếu có thì JWT hay session?
- ⏳ Notebook giữ ở root hay move vào `notebooks/`?
- ⏳ ECDC validation data: làm endpoint riêng hay merge vào predictions?

### Risks
- 🔴 Phase 4 (API restructure): có thể break imports nếu thiếu test coverage → bắt buộc làm Phase 3 trước
- 🟡 Phase 5 (rename folders): notebook paths có thể bị miss → check Colab + local
- 🟡 Phase 7-8 (frontend): effort lớn nhất, có thể trượt deadline nếu không scope cẩn thận

---

## Lịch sử cập nhật

| Ngày | Phase | Sự kiện |
|---|---|---|
| 2026-05-19 | — | Tạo planning document |
| 2026-05-19 | 1 | Hoàn thành Phase 1 — Foundation cleanup. /health verify OK |
| 2026-05-19 | 1 | Fix MODELS_DIR resolve relative path qua PROJECT_ROOT anchor. 4 models load OK |
| 2026-05-19 | 2 | Hoàn thành Phase 2 — Alembic init + partition filter + stamp baseline cbd62e71217a |
| 2026-05-19 | 3 | Hoàn thành Phase 3 — 27/27 tests passed (health, infer, diseases, countries) |
| 2026-05-19 | 4 | Hoàn thành Phase 4 — API restructure, ml_engine.py, 27/27 tests passed |
