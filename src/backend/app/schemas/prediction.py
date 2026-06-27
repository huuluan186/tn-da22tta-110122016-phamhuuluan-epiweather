from pydantic import BaseModel, ConfigDict


class PredictionPoint(BaseModel):
    iso3: str
    iso_year: int
    iso_week: int
    predicted_value: float | None
    predicted_cases: float | None
    risk_level: str | None
    risk_probability: float | None
    confidence_lo: float | None
    confidence_hi: float | None


class RiskMapItem(BaseModel):
    iso3: str
    country_name: str
    latitude: float | None
    longitude: float | None
    who_region: str | None
    predicted_cases: float | None
    risk_level: str | None
    risk_probability: float | None  # P(High) 0..1 từ classifier — FE × 100 = severity score


class RiskMapResponse(BaseModel):
    disease: str
    iso_year: int
    iso_week: int
    count: int
    items: list[RiskMapItem]



class RiskMapPeriod(BaseModel):
    iso_year: int
    min_week: int
    max_week: int


class RiskMapPeriodsResponse(BaseModel):
    disease: str
    latest_year: int
    latest_week: int
    periods: list[RiskMapPeriod]
class HistoryPoint(BaseModel):
    iso_year: int
    iso_week: int
    predicted_cases: float | None
    actual_cases: int | None
    risk_level: str | None


class HistoryResponse(BaseModel):
    disease: str
    iso3: str
    points: list[HistoryPoint]


class ForecastPoint(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    horizon: int                  # 1, 2, 3, 4
    target_iso_year: int
    target_iso_week: int
    predicted_log: float
    predicted_cases: float
    risk_level: str | None
    r2_cv: float | None           # CV R² của model horizon này (confidence indicator)
    rmse_cv: float | None
    model_version: str            # ví dụ "flu_h2_v1"


class DataCoverage(BaseModel):
    """Metadata trung thực về phạm vi dữ liệu — không bịa, không phục vụ ngoài phạm vi."""
    in_training_period: bool       # True = 2010-2019, model đã thấy năm này lúc train
    is_nowcast: bool = False        # True = dengue 2021-2023, có ground truth OpenDengue
    snapshot_years: list[int]      # Các năm có feature snapshot cho country này
    training_years: list[int]      # Năm có disease_cases training (tham khảo)
    warning: str | None            # None nếu OK, chuỗi cảnh báo nếu extrapolation


class ForecastResponse(BaseModel):
    disease: str
    iso3: str
    as_of_iso_year: int           # tuần "hiện tại" làm input cho model
    as_of_iso_week: int
    points: list[ForecastPoint]   # 4 điểm h=1..4
    risk_method: str
    data_coverage: DataCoverage | None = None


class AvailableCountry(BaseModel):
    iso3: str
    country_name: str | None
    snapshot_years: list[int]
    latest_year: int
    latest_week: int
    in_training_period: bool       # có data trong 2010-2019


class AvailableResponse(BaseModel):
    disease: str
    total_countries: int
    countries: list[AvailableCountry]
