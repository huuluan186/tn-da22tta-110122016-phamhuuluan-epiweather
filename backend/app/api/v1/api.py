"""APIRouter tổng hợp tất cả endpoints v1 — main.py chỉ cần include file này."""

from fastapi import APIRouter

from .endpoints import analytics, countries, diseases, infer, predictions, risk, weather

api_router = APIRouter()

api_router.include_router(countries.router)
api_router.include_router(diseases.router)
api_router.include_router(predictions.router)
api_router.include_router(risk.router)
api_router.include_router(infer.router)
api_router.include_router(weather.router)
api_router.include_router(analytics.router)
