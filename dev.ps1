# dev.ps1 — Windows alternative cho Makefile
# Dùng: .\dev.ps1 <command>
# Ví dụ: .\dev.ps1 test

param([string]$Command = "help")

$BackendDir = Join-Path $PSScriptRoot "backend"

switch ($Command) {
    "help" {
        Write-Host "Cac lenh co san:"
        Write-Host "  .\dev.ps1 dev        - Chay FastAPI dev server (port 8000)"
        Write-Host "  .\dev.ps1 install    - Cai dependencies backend"
        Write-Host "  .\dev.ps1 test       - Chay pytest"
        Write-Host "  .\dev.ps1 migrate    - alembic upgrade head"
        Write-Host "  .\dev.ps1 migration  - Tao migration moi (them -name <ten>)"
        Write-Host "  .\dev.ps1 seed       - Seed countries vao DB"
        Write-Host "  .\dev.ps1 lint       - Lint backend code"
    }
    "dev" {
        Set-Location $BackendDir
        uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    }
    "install" {
        Set-Location $BackendDir
        pip install -r requirements.txt
    }
    "test" {
        Set-Location $BackendDir
        pytest -v
    }
    "migrate" {
        Set-Location $BackendDir
        alembic upgrade head
    }
    "migration" {
        param([string]$name = "migration")
        Set-Location $BackendDir
        alembic revision --autogenerate -m $name
    }
    "seed" {
        python scripts/seed_countries.py
    }
    "lint" {
        Set-Location $BackendDir
        python -m ruff check app/ tests/
    }
    default {
        Write-Host "Lenh khong hop le: $Command. Chay '.\dev.ps1 help' de xem danh sach."
    }
}
