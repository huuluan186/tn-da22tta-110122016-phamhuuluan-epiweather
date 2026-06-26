from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..crud import diseases as disease_crud
from ..crud import predictions as prediction_crud
from ..schemas.prediction import RiskMapItem, RiskMapPeriod, RiskMapPeriodsResponse, RiskMapResponse
from . import feature_lookup

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



def get_risk_map_periods(db: Session, disease_code: str) -> RiskMapPeriodsResponse:
    disease = _resolve(db, disease_code)
    latest_observed = feature_lookup.get_last_observed_week(db, disease.id)
    max_year, max_week = latest_observed if latest_observed else (None, None)
    latest = prediction_crud.get_latest_week(
        db,
        disease.id,
        max_year=max_year,
        max_week=max_week,
    )
    if latest is None:
        raise HTTPException(
            status_code=404,
            detail=f"Chưa có prediction nào trong DB cho disease '{disease_code}'.",
        )
    periods = prediction_crud.list_available_periods(
        db,
        disease.id,
        max_year=latest[0],
        max_week=latest[1],
    )
    return RiskMapPeriodsResponse(
        disease=disease_code,
        latest_year=latest[0],
        latest_week=latest[1],
        periods=[RiskMapPeriod(**period) for period in periods],
    )

def get_risk_map(
    db: Session,
    disease_code: str,
    year: int,
    week: int,
) -> RiskMapResponse:
    disease = _resolve(db, disease_code)
    if feature_lookup.is_after_latest_valid_week(disease.id, year, week):
        latest_year, latest_week = feature_lookup.get_latest_valid_week(disease.id) or (None, None)
        raise HTTPException(
            status_code=404,
            detail=(
                f"{disease_code} chỉ có dữ liệu hợp lệ đến "
                f"Năm {latest_year}, Tuần {latest_week:02d} trong dataset hiện có."
            ),
        )
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
    latest_observed = feature_lookup.get_last_observed_week(db, disease.id)
    max_year, max_week = latest_observed if latest_observed else (None, None)
    latest = prediction_crud.get_latest_week(
        db,
        disease.id,
        max_year=max_year,
        max_week=max_week,
    )
    if latest is None:
        raise HTTPException(
            status_code=404,
            detail=f"Chưa có prediction nào trong DB cho disease '{disease_code}'.",
        )
    year, week = latest
    return get_risk_map(db, disease_code, year, week)
