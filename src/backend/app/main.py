from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from app.api.health import router as health_router
from app.api.v1.api import api_router
from app.core.config import settings
from app.core.exceptions import EpiWeatherException
from app.core.logging import setup_logging
from app.services.ml_engine import load_models
from app.services.scheduler import init_scheduler, shutdown_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info(f"Starting EpiWeather API v{settings.APP_VERSION} (DEBUG={settings.DEBUG})")
    logger.info(f"Loading models from {settings.MODELS_DIR}")
    load_models(settings.MODELS_DIR)
    if settings.ENABLE_API_SCHEDULER:
        init_scheduler()
    else:
        logger.info("API scheduler disabled; scheduled pipeline should run in scheduler service")
    logger.info("Startup complete")
    yield
    shutdown_scheduler()
    logger.info("Shutting down EpiWeather API")


app = FastAPI(
    title="EpiWeather API",
    version=settings.APP_VERSION,
    description="Hệ thống cảnh báo nguy cơ dịch bệnh theo mùa — Influenza & Dengue",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.exception_handler(EpiWeatherException)
async def epiweather_exception_handler(request: Request, exc: EpiWeatherException):
    logger.warning(f"{exc.__class__.__name__} at {request.url.path}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "error": exc.__class__.__name__},
    )


app.include_router(health_router)
app.include_router(api_router, prefix="/api/v1")
