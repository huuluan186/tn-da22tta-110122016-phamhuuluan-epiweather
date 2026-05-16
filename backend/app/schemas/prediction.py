from pydantic import BaseModel


class PredictionPoint(BaseModel):
    iso3: str
    iso_year: int
    iso_week: int
    predicted_value: float | None
    predicted_cases: float | None
    risk_level: str | None
    risk_q33: float | None
    risk_q67: float | None
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
    risk_q33: float | None
    risk_q67: float | None


class RiskMapResponse(BaseModel):
    disease: str
    iso_year: int
    iso_week: int
    count: int
    items: list[RiskMapItem]


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
