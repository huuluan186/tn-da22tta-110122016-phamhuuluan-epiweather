from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..crud import diseases as disease_crud
from ..database import get_db
from ..ml.loader import get_metrics
from ..schemas.disease import Disease, ModelMetrics

router = APIRouter(prefix="/diseases", tags=["diseases"])


@router.get("", response_model=list[Disease])
def list_diseases(db: Session = Depends(get_db)):
    return disease_crud.list_active(db)


@router.get("/model-metrics", response_model=list[ModelMetrics])
def model_metrics():
    raw = get_metrics()
    return [
        ModelMetrics(
            disease=disease,
            version=data["version"],
            algorithm=data["algorithm"],
            r2_score=data["holdout"]["r2_score"],
            mae=data["holdout"]["mae"],
            rmse=data["holdout"]["rmse"],
            smape_nonzero=data["holdout"]["smape_nonzero"],
            risk_macro_f1=data["holdout"]["risk_macro_f1"],
            risk_accuracy=data["holdout"]["risk_accuracy"],
            n_samples=data["holdout"]["n_samples"],
            notes=data["holdout"]["notes"],
        )
        for disease, data in raw.items()
    ]
