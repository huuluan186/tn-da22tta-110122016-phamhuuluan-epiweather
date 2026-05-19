from pydantic import BaseModel


class Disease(BaseModel):
    id: int
    code: str
    display_name: str
    target_variable: str
    target_transform: str


class HoldoutMetrics(BaseModel):
    r2: float
    rmse: float
    mae: float
    n: int


class ModelMetrics(BaseModel):
    disease: str
    model_type: str        # LightGBM / RandomForest / XGBClassifier
    r2_cv: float
    rmse_cv: float
    mae_cv: float
    cv_folds: int
    holdout_2022: HoldoutMetrics | None
