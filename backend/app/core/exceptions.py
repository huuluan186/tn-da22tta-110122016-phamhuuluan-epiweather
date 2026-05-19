"""Custom exceptions cho EpiWeather API."""


class EpiWeatherException(Exception):
    """Base exception cho domain errors."""

    status_code: int = 500
    detail: str = "Internal server error"

    def __init__(self, detail: str | None = None):
        if detail is not None:
            self.detail = detail
        super().__init__(self.detail)


class ModelNotLoadedError(EpiWeatherException):
    """Model chưa được load (file thiếu hoặc startup lỗi)."""

    status_code = 503

    def __init__(self, disease: str, model_type: str = "regressor"):
        super().__init__(f"{model_type.capitalize()} cho '{disease}' chưa được load")


class InvalidDiseaseError(EpiWeatherException):
    """Disease parameter không hợp lệ."""

    status_code = 400

    def __init__(self, disease: str, allowed: tuple[str, ...] = ("flu", "dengue")):
        super().__init__(
            f"disease='{disease}' không hợp lệ. Cho phép: {', '.join(allowed)}"
        )


class InvalidISO3Error(EpiWeatherException):
    """Mã ISO3 quốc gia không đúng định dạng hoặc không có trong DB."""

    status_code = 400

    def __init__(self, iso3: str):
        super().__init__(f"ISO3 code '{iso3}' không hợp lệ")


class CountryNotFoundError(EpiWeatherException):
    """Không tìm thấy country trong DB."""

    status_code = 404

    def __init__(self, iso3: str):
        super().__init__(f"Không tìm thấy quốc gia với iso3='{iso3}'")
