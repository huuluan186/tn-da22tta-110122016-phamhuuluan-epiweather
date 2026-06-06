# Ke hoach Codex Skills cho EpiWeather

Tai lieu nay dinh nghia bo skills nen tao cho he thong EpiWeather: ML pipeline, backend, frontend va MLOps. Muc tieu la giup Codex lam viec co quy trinh, dung bien module hien co, va tao output nhat quan khi sua code trong repo.

## Nguyen tac thiet ke

- Moi skill phai co pham vi ro, khong gom qua nhieu viec khong lien quan.
- Uu tien doc context tu repo truoc khi sua code: `README.md`, `docs/`, `backend/app`, `frontend/src`, `scripts`, `ml_models`.
- Khong tao abstraction moi neu codebase da co pattern tuong duong.
- Moi thay doi user-facing API/UI/ML behavior phai co buoc validation tuong ung.
- Skill nen nho gon; chi dung `references/` khi thong tin dai hoac co nhieu bien the.

## Skill uu tien P0

### `epiwatch-architecture`

Dung khi can phan tich kien truc tong the, tach module, lap ke hoach feature lon, hoac danh gia tac dong BE/FE/ML/MLOps.

Pham vi:
- Doc luong du lieu tu data/raw, processed features, model artifacts, FastAPI, PostgreSQL, frontend dashboard.
- Xac dinh module bi anh huong truoc khi sua code.
- Tao implementation plan co thu tu va validation.

Resources nen co:
- `references/system-map.md`: so do module va ownership.
- `references/api-contracts.md`: endpoint chinh va data contract.

### `epiwatch-ml-pipeline`

Dung khi can xu ly data, feature engineering, training, evaluation, model artifact, hoac batch prediction.

Pham vi:
- Lam viec voi `scripts/sync_flunet.py`, `scripts/sync_weather.py`, `scripts/feature_builder.py`, `scripts/batch_predict.py`, `scripts/run_daily_pipeline.py`.
- Dam bao feature list trong `ml_models/*_features.json` khop voi inference.
- Cap nhat metrics/model version khi thay model.
- Phan biet regression, classification va multi-horizon forecast h=1..4.

Resources nen co:
- `references/ml-artifacts.md`: quy uoc ten file `.pkl`, `_features.json`, `_metrics.json`.
- `references/feature-contract.md`: feature snapshot, valid week, disease/country grain.
- Co the them script helper de check artifact completeness.

### `epiwatch-backend-api`

Dung khi can them/sua FastAPI endpoint, schema, CRUD, service, DB model, migration, hoac test backend.

Pham vi:
- Lam viec trong `backend/app/api/v1/endpoints`, `schemas`, `crud`, `services`, `models`.
- Giu convention router theo domain, service chua business logic, CRUD chua DB query.
- Them/sua Alembic migration khi doi schema.
- Cap nhat pytest trong `backend/tests`.

Resources nen co:
- `references/backend-patterns.md`: router/service/crud/schema/model pattern.
- `references/error-handling.md`: HTTPException va `EpiWeatherException` conventions.

### `epiwatch-frontend-app`

Dung khi can sua React dashboard, page, component, API client, hook, map/chart, UI state.

Pham vi:
- Lam viec voi `frontend/src/pages`, `components`, `hooks`, `api`, `store`.
- Giu API integration qua `frontend/src/api/*.ts` va React Query hooks.
- Dam bao dashboard co layout on dinh, khong overflow, khong overlap tren desktop/mobile.
- Dung domain terms nhat quan: `LATEST`, `BACKTEST`, disease, country, iso year/week.

Resources nen co:
- `references/frontend-patterns.md`: page/hook/api/component conventions.
- `references/ui-domain-language.md`: thuat ngu hien thi.

### `epiwatch-mlops-deployment`

Dung khi can Docker, Compose, env vars, scheduled pipeline, logging, healthcheck, CI/CD, deployment.

Pham vi:
- Lam viec voi `docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile`, `nginx.conf`, `.env.example`, `Makefile`, `scripts/setup_windows_task*.ps1`.
- Dam bao backend load models tu `MODELS_DIR`, frontend goi dung API base URL.
- Giu pipeline scheduled co audit trail trong DB va log file.

Resources nen co:
- `references/runtime-contract.md`: env vars, ports, volumes, model mount.
- `references/ops-runbook.md`: lenh dev/test/deploy va troubleshooting.

## Skill P1 nen tao sau

### `epiwatch-db-migrations`

Dung khi thay doi PostgreSQL schema, SQLAlchemy model, Alembic migration, seed data.

Ly do tach rieng: DB schema anh huong ca scripts, backend va dashboard; can validation chat hon.

### `epiwatch-qa-review`

Dung khi user yeu cau review, test strategy, regression check, release readiness.

Pham vi:
- Chay/dinh nghia test backend.
- De xuat frontend validation.
- Kiem tra risk: data leakage, feature mismatch, API contract break, stale model artifact.

### `epiwatch-docs-thesis`

Dung khi cap nhat tai lieu KLTN, slide, kich ban thuyet trinh, Q&A bao ve.

Pham vi:
- Lam viec trong `docs/`, nhat la `docs/presentation/`.
- Giu ngon ngu hoc thuat va thuat ngu thong nhat.

## Trigger examples

- "Them endpoint forecast theo country" -> `epiwatch-backend-api`, co the dung `epiwatch-architecture`.
- "Cap nhat model dengue h=1..4" -> `epiwatch-ml-pipeline`, co the dung `epiwatch-mlops-deployment`.
- "Sua dashboard map hien risk sai" -> `epiwatch-frontend-app`, co the dung `epiwatch-backend-api`.
- "Dong goi deploy bang docker compose" -> `epiwatch-mlops-deployment`.
- "Review truoc khi nop KLTN" -> `epiwatch-qa-review`, `epiwatch-docs-thesis`.

## Thu tu tao skills

1. Tao `epiwatch-architecture` de lam skill dieu huong.
2. Tao `epiwatch-ml-pipeline` vi day la loi nghiep vu cua do an.
3. Tao `epiwatch-backend-api`.
4. Tao `epiwatch-frontend-app`.
5. Tao `epiwatch-mlops-deployment`.
6. Sau khi dung thuc te, tach them P1 neu skill P0 qua dai hoac hay bi sai.

