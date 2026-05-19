from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ....crud import diseases as disease_crud
from ....db.session import get_db
from ....schemas.disease import Disease, HoldoutMetrics, ModelMetrics
from ....services.ml_engine import get_metrics

router = APIRouter(prefix="/diseases", tags=["diseases"])


@router.get("", response_model=list[Disease])
def list_diseases(db: Session = Depends(get_db)):
    return disease_crud.list_active(db)


@router.get("/model-metrics", response_model=list[ModelMetrics])
def model_metrics():
    raw = get_metrics()
    result = []
    for disease, data in raw.items():
        h = data.get("holdout_2022")
        result.append(ModelMetrics(
            disease=disease,
            model_type=data["model_type"],
            r2_cv=data["r2_cv"],
            rmse_cv=data["rmse_cv"],
            mae_cv=data["mae_cv"],
            cv_folds=data["cv_folds"],
            holdout_2022=HoldoutMetrics(**h) if h else None,
        ))
    return result
