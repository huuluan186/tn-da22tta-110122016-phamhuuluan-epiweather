from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .ml.loader import load_models
from .routers import countries, diseases, health, infer, predictions, risk


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_models(settings.MODELS_DIR)
    yield


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

app.include_router(health.router)
app.include_router(countries.router, prefix="/api/v1")
app.include_router(diseases.router, prefix="/api/v1")
app.include_router(predictions.router, prefix="/api/v1")
app.include_router(risk.router, prefix="/api/v1")
app.include_router(infer.router)
