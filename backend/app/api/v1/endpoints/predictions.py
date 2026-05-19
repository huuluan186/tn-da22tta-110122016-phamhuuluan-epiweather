from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ....db.session import get_db
from ....schemas.prediction import HistoryResponse, PredictionPoint
from ....services import prediction_service

router = APIRouter(prefix="/predictions", tags=["predictions"])


@router.get("/{disease}/{iso3}", response_model=PredictionPoint)
def get_prediction(
    disease: str,
    iso3: str,
    year: int = Query(..., ge=2022, le=2030),
    week: int = Query(..., ge=1, le=53),
    db: Session = Depends(get_db),
):
    return prediction_service.get_prediction(db, disease, iso3, year, week)


@router.get("/{disease}/{iso3}/history", response_model=HistoryResponse)
def get_history(
    disease: str,
    iso3: str,
    start_year: int = Query(2022, ge=2010),
    end_year: int = Query(2022, le=2030),
    db: Session = Depends(get_db),
):
    return prediction_service.get_history(db, disease, iso3, start_year, end_year)
