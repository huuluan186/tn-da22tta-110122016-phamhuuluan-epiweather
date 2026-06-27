"""
Data Fetcher — lấy dữ liệu thời tiết realtime từ OpenWeatherMap.
Stub hiện tại, sẽ implement đầy đủ khi tích hợp frontend (Phase 8).
"""

from loguru import logger


async def fetch_current_weather(iso3: str, lat: float, lon: float) -> dict:
    """Lấy thời tiết hiện tại cho 1 tọa độ từ OpenWeatherMap API.

    Trả về dict feature values tương thích với InferRequest.features.
    """
    logger.info(f"fetch_current_weather: iso3={iso3}, lat={lat}, lon={lon} (stub)")
    # TODO: gọi OpenWeatherMap API, map response về feature dict
    return {}
