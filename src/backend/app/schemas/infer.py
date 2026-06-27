from pydantic import BaseModel, ConfigDict, Field


class InferRequest(BaseModel):
    disease: str = Field(..., pattern="^(flu|dengue)$", description="flu hoặc dengue")
    iso3: str = Field(..., min_length=3, max_length=3, description="ISO 3166-1 alpha-3")
    features: dict[str, float] = Field(
        ...,
        description="Feature values theo tên trong *_features.json. Thiếu key → dùng 0.0.",
    )


class InferResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    disease: str
    iso3: str

    # Regression output
    predicted_log: float
    predicted_cases: float

    # Classification output
    risk_level: str
    p_low: float
    p_med: float
    p_high: float

    # Feature lists (để frontend biết cần truyền gì)
    regressor_features: list[str]
    classifier_features: list[str]
