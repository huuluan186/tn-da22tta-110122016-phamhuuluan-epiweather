# KLTN EpiWeather — Makefile
# Sử dụng: make <target>
# Trên Windows: cài make qua `choco install make` hoặc dùng `pwsh` thay thế.

.PHONY: help dev install migrate migration seed test lint format docker-up docker-down clean

help:
	@echo "EpiWeather — available targets:"
	@echo "  install        Cai dependencies backend"
	@echo "  dev            Chay FastAPI dev server (port 8000)"
	@echo "  migrate        Alembic upgrade head"
	@echo "  migration      Tao migration moi (make migration name=add_xxx)"
	@echo "  seed           Seed countries vao DB"
	@echo "  test           Chay pytest"
	@echo "  lint           Lint backend code"
	@echo "  format         Format backend code"
	@echo "  docker-up      docker compose up -d"
	@echo "  docker-down    docker compose down"
	@echo "  clean          Xoa __pycache__, .pytest_cache"

install:
	cd backend && pip install -r requirements.txt

dev:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

migrate:
	cd backend && alembic upgrade head

migration:
	cd backend && alembic revision --autogenerate -m "$(name)"

seed:
	cd backend && python ../scripts/seed_countries.py

test:
	cd backend && pytest -v

lint:
	cd backend && python -m ruff check app/ tests/

format:
	cd backend && python -m ruff format app/ tests/

docker-up:
	docker compose up -d

docker-down:
	docker compose down

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
