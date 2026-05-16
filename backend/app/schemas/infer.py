from pydantic import BaseModel, ConfigDict, Field


class InferRequest(BaseModel):
    disease: str = Field(..., pattern="^(flu|dengue)$", description="flu hoặc dengue")
    iso3: str = Field(..., min_length=3, max_length=3, description="ISO 3166-1 alpha-3")
    features: dict[str, float] = Field(
        ...,
        description="Feature values theo tên feature trong pkl. Thiếu key → dùng 0.0",
    )


class InferResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    disease: str
    iso3: str
    region: str
    model_used: str
    risk_level: str
    p_low: float
    p_med: float
    p_high: float
    features_used: list[str]
