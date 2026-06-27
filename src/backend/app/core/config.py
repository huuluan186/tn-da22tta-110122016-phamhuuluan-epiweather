from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Project root = parent của backend/ — anchor cho relative paths trong .env
# config.py → core/ → app/ → backend/ → project root (4 levels up)
PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        extra="ignore",
    )

    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/kltn_epiweather"
    MODELS_DIR: Path = PROJECT_ROOT / "ml_models"
    DEBUG: bool = False
    APP_VERSION: str = "1.0.0"
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    ENABLE_API_SCHEDULER: bool = True

    # Weather provider keys
    OWM_API_KEY: str = ""  # OpenWeatherMap — fallback provider (Phase 8 MLOps)
    # Open-Meteo Archive API không cần key, dùng làm primary provider (Phase A-1)

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, v):
        if isinstance(v, str):
            normalized = v.strip().lower()
            if normalized in {"release", "prod", "production"}:
                return False
            if normalized in {"debug", "dev", "development"}:
                return True
        return v

    @field_validator("MODELS_DIR", mode="before")
    @classmethod
    def resolve_models_dir(cls, v):
        """Relative paths trong .env (./models, ../models) anchor vào PROJECT_ROOT."""
        p = Path(v)
        if not p.is_absolute():
            p = (PROJECT_ROOT / p).resolve()
        return p


settings = Settings()
