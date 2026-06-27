from fastapi import APIRouter

router = APIRouter(prefix="/weather", tags=["weather"])


@router.get("/variables")
def list_weather_variables():
    """Danh sách 17 biến ERA5 dùng trong pipeline."""
    return {
        "variables": [
            "temp_mean", "temp_min", "temp_max",
            "humidity_mean", "dewpoint_mean",
            "precipitation_sum", "solar_radiation_mean",
            "wind_speed_mean", "surface_pressure_mean",
            "temp_range", "heat_index_mean",
            "temp_lag4", "humidity_lag8", "solar_lag8",
            "dewpoint_lag2", "precipitation_lag0",
            "week_of_year",
        ]
    }
