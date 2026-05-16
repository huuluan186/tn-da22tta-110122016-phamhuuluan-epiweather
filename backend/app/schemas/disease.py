from pydantic import BaseModel


class Disease(BaseModel):
    id: int
    code: str
    display_name: str
    target_variable: str
    target_transform: str


class ModelMetrics(BaseModel):
    disease: str
    version: str
    algorithm: str
    r2_score: float
    mae: float
    rmse: float
    smape_nonzero: float
    risk_macro_f1: float
    risk_accuracy: float
    n_samples: int
    notes: str
