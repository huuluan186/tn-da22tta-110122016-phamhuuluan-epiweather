# Ke hoach AI Agents cho EpiWeather

Tai lieu nay dinh nghia cac vai tro agent nen dung khi phoi hop nhieu nhiem vu trong he thong EpiWeather. Agent la vai tro lam viec; skill la bo huong dan va tai nguyen agent se dung.

## Nguyen tac phoi hop

- Mot agent chiu trach nhiem chinh cho moi task.
- Agent phu chi duoc goi khi task cham sang module khac.
- Reviewer/QA khong tu dong sua code lon; nhiem vu chinh la tim bug, risk, missing validation.
- Architect chi lap bien va thu tu xu ly, khong nen gom het viec cua ML/BE/FE/MLOps.

## Agents de xuat

### `architect-agent`

Trach nhiem:
- Phan tich yeu cau lon va tach thanh work items.
- Xac dinh module bi anh huong: scripts, backend, frontend, docs, deployment.
- Chon skill chinh/phu.
- Tao plan co validation.

Skills chinh:
- `epiwatch-architecture`
- `epiwatch-qa-review`

Output chuan:
- Scope.
- Files/modules can doc.
- Implementation sequence.
- Validation gates.

### `ml-engineer-agent`

Trach nhiem:
- Data ingestion, feature engineering, training, evaluation, model artifacts.
- Kiem tra feature/model compatibility.
- Dam bao disease, horizon, ISO week, country grain dung.

Skills chinh:
- `epiwatch-ml-pipeline`
- `epiwatch-db-migrations` khi co feature snapshot/schema.

Output chuan:
- Code/scripts thay doi.
- Artifact contract update.
- Metrics/validation summary.
- Rui ro ML: leakage, stale features, missing values, data coverage.

### `backend-agent`

Trach nhiem:
- FastAPI endpoints, schemas, services, CRUD, models, migrations.
- API contract cho frontend.
- Backend tests.

Skills chinh:
- `epiwatch-backend-api`
- `epiwatch-db-migrations`

Output chuan:
- Endpoint behavior.
- Schema request/response.
- DB impact.
- Pytest result hoac ly do chua chay duoc.

### `frontend-agent`

Trach nhiem:
- Dashboard UI, pages, components, hooks, API clients.
- Map/chart state, loading/error states, responsive layout.
- Dong bo domain language voi backend.

Skills chinh:
- `epiwatch-frontend-app`

Output chuan:
- User flow thay doi.
- API calls bi anh huong.
- Build/check result.
- UI validation notes.

### `mlops-agent`

Trach nhiem:
- Docker Compose, Dockerfiles, env vars, scheduled jobs, logs, healthchecks.
- Runtime contract giua DB/backend/frontend/models.
- Deployment/runbook.

Skills chinh:
- `epiwatch-mlops-deployment`

Output chuan:
- Runtime changes.
- Commands de run/test/deploy.
- Env var changes.
- Rollback/troubleshooting notes neu can.

### `qa-agent`

Trach nhiem:
- Lap test strategy va regression checklist.
- Kiem tra API contract, model feature mismatch, frontend state issues.
- Chay test/build khi phu hop.

Skills chinh:
- `epiwatch-qa-review`

Output chuan:
- Findings theo muc do nghiem trong.
- Missing tests.
- Commands da chay.
- Residual risk.

### `docs-agent`

Trach nhiem:
- Cap nhat tai lieu KLTN, presentation, system design, runbook.
- Dong bo docs voi code sau thay doi.

Skills chinh:
- `epiwatch-docs-thesis`
- `epiwatch-architecture`

Output chuan:
- Docs files thay doi.
- Noi dung technical da cap nhat.
- Diem can doi chieu voi GVHD/bao cao.

## Routing matrix

| Yeu cau | Agent chinh | Agent phu |
|---|---|---|
| Them API moi | backend-agent | frontend-agent, qa-agent |
| Sua model/inference | ml-engineer-agent | backend-agent, qa-agent |
| Sua dashboard | frontend-agent | backend-agent |
| Deployment/Docker | mlops-agent | backend-agent, frontend-agent |
| Review release | qa-agent | architect-agent |
| Cap nhat bao cao | docs-agent | architect-agent |
| Feature lon end-to-end | architect-agent | ml/backend/frontend/mlops theo module |

## Workflow mau

### Feature end-to-end

1. `architect-agent` xac dinh scope va module.
2. Agent chinh doc code hien co va lap plan ngan.
3. Agent chinh sua code theo skill tuong ung.
4. Agent phu xu ly integration neu can.
5. `qa-agent` chay validation va review risk.
6. `docs-agent` cap nhat docs neu behavior thay doi.

### Bug fix

1. Agent chinh reproduce hoac xac dinh path gay loi.
2. Sua nho, dung pattern hien co.
3. Them/chay test lien quan.
4. Neu loi anh huong contract, bao frontend/backend tuong ung.

### Release check

1. `qa-agent` kiem tra backend tests, frontend build, docker compose config.
2. `mlops-agent` kiem tra env/model mount/healthcheck.
3. `docs-agent` cap nhat runbook va presentation neu can.
