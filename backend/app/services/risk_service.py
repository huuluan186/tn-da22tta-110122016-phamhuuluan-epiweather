from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..crud import diseases as disease_crud
from ..crud import predictions as prediction_crud
from ..schemas.prediction import RiskMapItem, RiskMapResponse

VALID_DISEASES = {"flu", "dengue"}


def _resolve(db: Session, disease_code: str):
    if disease_code not in VALID_DISEASES:
        raise HTTPException(
            status_code=400,
            detail=f"Disease phải là một trong: {sorted(VALID_DISEASES)}",
        )
    disease = disease_crud.get_by_code(db, disease_code)
    if not disease:
        raise HTTPException(status_code=404, detail="Disease không tìm thấy trong database")
    return disease


def get_risk_map(
    db: Session,
    disease_code: str,
    year: int,
    week: int,
) -> RiskMapResponse:
    disease = _resolve(db, disease_code)
    rows = prediction_crud.list_for_map(db, disease.id, year, week)

    items = [
        RiskMapItem(
            iso3=p.iso3,
            country_name=p.country.country_name if p.country else p.iso3,
            latitude=p.country.latitude if p.country else None,
            longitude=p.country.longitude if p.country else None,
            who_region=p.country.who_region if p.country else None,
            predicted_cases=p.predicted_cases,
            risk_level=p.risk_level,
            risk_probability=p.risk_probability,
            risk_q33=p.risk_q33,
            risk_q67=p.risk_q67,
        )
        for p in rows
    ]

    return RiskMapResponse(
        disease=disease_code,
        iso_year=year,
        iso_week=week,
        count=len(items),
        items=items,
    )


def get_latest_risk_map(db: Session, disease_code: str) -> RiskMapResponse:
    """Risk map cho tuần mới nhất có data — dùng cho map mặc định khi load."""
    disease = _resolve(db, disease_code)
    latest = prediction_crud.get_latest_week(db, disease.id)
    if latest is None:
        raise HTTPException(
            status_code=404,
            detail=f"Chưa có prediction nào trong DB cho disease '{disease_code}'.",
        )
    year, week = latest
    return get_risk_map(db, disease_code, year, week)
