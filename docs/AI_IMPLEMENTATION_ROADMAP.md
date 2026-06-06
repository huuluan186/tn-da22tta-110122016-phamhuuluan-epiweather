# Roadmap trien khai Skills va Agents

Roadmap nay uu tien tao he thong AI support co gia tri ngay cho repo EpiWeather, khong tao qua nhieu skill ngay tu dau.

## Trang thai repo hien tai

Da quan sat:
- Backend: FastAPI, SQLAlchemy, Alembic, pytest, service layer, model loading trong `backend/app/services/ml_engine.py`.
- Frontend: React/Vite, TypeScript, React Query, Zustand, Leaflet/ECharts/Recharts, API clients trong `frontend/src/api`.
- ML: notebooks training, processed CSVs, `ml_models/*.pkl`, `_features.json`, `_metrics.json`, multi-horizon h=1..4.
- Pipeline: scripts sync data, build features, batch predict, daily scheduler cho Windows Task Scheduler.
- Ops: Docker Compose gom PostgreSQL, backend, frontend; Makefile co dev/test/migrate/docker targets.
- Docs: da co nhieu tai lieu KLTN va presentation.

Luu y:
- `git status` hien tai bi chan boi Git safe.directory trong sandbox vi owner repo khac user sandbox. Chua can sua de lap plan.
- README va mot so file hien thi bi mojibake trong terminal, co the do encoding/output console; khi cap nhat docs moi nen dung ASCII hoac UTF-8 on dinh.

## Phase 1: Tao core skill skeletons

Muc tieu:
- Tao 5 skills P0 co `SKILL.md` va `agents/openai.yaml`.
- Dat trong `~/.codex/skills` neu muon Codex tu nhan dien, hoac trong workspace neu muon version control cung repo.

Skills:
- `epiwatch-architecture`
- `epiwatch-ml-pipeline`
- `epiwatch-backend-api`
- `epiwatch-frontend-app`
- `epiwatch-mlops-deployment`

Viec can lam:
- Dung script `init_skill.py` cua skill-creator.
- Viet frontmatter description that ro trigger.
- Tao references toi thieu, khong copy toan bo docs hien co.
- Chay `quick_validate.py` cho tung skill.

Acceptance criteria:
- Tat ca skill pass validate.
- Moi skill co trigger examples va workflow ngan.
- Khong co file README/CHANGELOG phu trong skill folders.

## Phase 2: Bo sung references theo repo

Muc tieu:
- Bien knowledge hien co trong repo thanh references nho, de agent doc dung luc.

References can tao:
- `system-map.md`: BE/FE/ML/DB/data flow.
- `ml-artifacts.md`: model naming, features/metrics contract.
- `feature-contract.md`: disease, ISO year/week, country iso3, valid week.
- `backend-patterns.md`: endpoint/schema/service/crud/model/test pattern.
- `frontend-patterns.md`: api/hook/page/component/store conventions.
- `runtime-contract.md`: env vars, ports, Docker volumes, model loading.

Acceptance criteria:
- Moi reference du ngan de doc nhanh.
- Moi reference chi chua thong tin thuc su can cho agent.
- SKILL.md link thang den reference lien quan.

## Phase 3: Them utility scripts neu can

Chi tao scripts khi chung giup giam loi lap lai.

Candidates:
- `check_model_artifacts.py`: kiem tra moi model stem co `.pkl`, `_features.json`, optional `_metrics.json`, JSON hop le, features non-empty.
- `check_api_contract.py`: smoke test cac endpoint public neu backend dang chay.
- `summarize_repo_contract.py`: sinh tom tat endpoint/model/env tu repo de review nhanh.

Acceptance criteria:
- Script chay duoc doc lap.
- Co exit code ro rang.
- Khong phu thuoc secret production.

## Phase 4: Forward-test skills tren task thuc

Muc tieu:
- Kiem tra skill co giup agent lam dung viec khong.

Task test de xuat:
- ML: kiem tra artifact completeness va noi ro missing/risk.
- Backend: them/sua mot endpoint nho va test.
- Frontend: sua mot component hoac hook nho, build frontend.
- MLOps: review Docker Compose/env contract.
- Architecture: lap plan cho feature end-to-end.

Acceptance criteria:
- Agent khong doc qua nhieu file thua.
- Agent de xuat validation dung module.
- Agent khong tao pattern trai voi repo.

## Phase 5: Tach P1 skills

Chi tach khi core skills bat dau dai hoac hay bi trigger sai.

Skills P1:
- `epiwatch-db-migrations`
- `epiwatch-qa-review`
- `epiwatch-docs-thesis`

Acceptance criteria:
- Co ly do tach ro rang.
- Skill moi giam duplication thay vi tao them overhead.

## De xuat buoc tiep theo

1. Chon noi dat skills:
   - `C:\Users\HP\.codex\skills` de Codex tu dong nhan dien.
   - `F:\BAO_CAO\DO_AN_TOT_NGHIEP\KLTN\.codex\skills` de version control cung project.
2. Tao 5 skills P0.
3. Validate bang `quick_validate.py`.
4. Dung thu skill dau tien tren mot task that nho, vi du review ML artifact contract.

