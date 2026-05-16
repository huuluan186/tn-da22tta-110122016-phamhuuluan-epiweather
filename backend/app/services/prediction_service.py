from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..crud import diseases as disease_crud
from ..crud import predictions as prediction_crud
from ..schemas.prediction import HistoryPoint, HistoryResponse, PredictionPoint

VALID_DISEASES = {"flu", "dengue"}


def resolve_disease(db: Session, code: str):
    """Valida disease code và trả về ORM object. Raise 400/404 nếu không hợp lệ."""
    if code not in VALID_DISEASES:
        raise HTTPException(
            status_code=400,
            detail=f"Disease phải là một trong: {sorted(VALID_DISEASES)}",
        )
    disease = disease_crud.get_by_code(db, code)
    if not disease:
        raise HTTPException(status_code=404, detail="Disease không tìm thấy trong database")
    return disease


def get_prediction(
    db: Session,
    disease_code: str,
    iso3: str,
    year: int,
    week: int,
) -> PredictionPoint:
    disease = resolve_disease(db, disease_code)
    row = prediction_crud.get_one(db, disease.id, iso3.upper(), year, week)
    if not row:
        raise HTTPException(status_code=404, detail="Không có dự báo cho tuần này")
    return PredictionPoint.model_validate(row, from_attributes=True)


def get_history(
    db: Session,
    disease_code: str,
    iso3: str,
    start_year: int,
    end_year: int,
) -> HistoryResponse:
    disease = resolve_disease(db, disease_code)
    iso3 = iso3.upper()

    predictions = prediction_crud.list_history(db, disease.id, iso3, start_year, end_year)
    actuals = prediction_crud.list_actuals(db, disease.id, iso3, start_year, end_year)

    points = [
        HistoryPoint(
            iso_year=p.iso_year,
            iso_week=p.iso_week,
            predicted_cases=p.predicted_cases,
            actual_cases=actuals.get((p.iso_year, p.iso_week)),
            risk_level=p.risk_level,
        )
        for p in predictions
    ]
    return HistoryResponse(disease=disease_code, iso3=iso3, points=points)
