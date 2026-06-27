from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ....db.session import get_db
from ....schemas.prediction import AvailableCountry, AvailableResponse, ForecastResponse
from ....services import feature_lookup, prediction_service

router = APIRouter(prefix="/forecast", tags=["forecast"])


@router.get("/{disease}/available", response_model=AvailableResponse)
def available_countries(
    disease: str,
    db: Session = Depends(get_db),
):
    """
    Danh sách countries có feature snapshot cho disease này.

    Dùng ở FE để:
    - Chỉ enable dự báo cho countries thực sự có data
    - Hiển thị badge "training data" vs "realtime" vs "no data"
    - Không phục vụ dự báo cho countries ngoài danh sách này
    """
    disease_obj = prediction_service.resolve_disease(db, disease)
    items = feature_lookup.get_available_countries(db, disease_obj.id)
    countries = [AvailableCountry(**item) for item in items]
    return AvailableResponse(
        disease=disease,
        total_countries=len(countries),
        countries=countries,
    )


@router.get("/{disease}/{iso3}", response_model=ForecastResponse)
def get_forecast(
    disease: str,
    iso3: str,
    as_of_year: int = Query(..., ge=2010, description="Tuần 'hiện tại' làm input cho model"),
    as_of_week: int = Query(..., ge=1, le=53),
    db: Session = Depends(get_db),
):
    """
    Multi-horizon forecast (h=1..4 tuần ahead) cho 1 country.

    Pipeline:
    1. Lookup feature snapshot tại (iso3, as_of_year, as_of_week) trong DB
    2. Predict bằng 4 model multi-horizon (h=1,2,3,4)
    3. Trả 4 ForecastPoint với target_iso_year/week đã tính ISO 8601 boundary
    """
    return prediction_service.get_forecast(db, disease, iso3, as_of_year, as_of_week)


@router.get("/{disease}/{iso3}/nowcast", response_model=ForecastResponse)
def nowcast(
    disease: str,
    iso3: str,
    db: Session = Depends(get_db),
):
    """
    Nowcast: tự động tìm tuần mới nhất có feature snapshot rồi forecast h=1..4.

    Dùng khi Phase A (auto-sync + feature_builder) đã chạy và có data mới nhất.
    Không cần truyền as_of_year/as_of_week — tự detect từ feature_snapshots.
    """
    disease_obj = prediction_service.resolve_disease(db, disease)
    latest = feature_lookup.get_latest_available_week(db, disease_obj.id, iso3.upper())
    if latest is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Chưa có feature snapshot nào cho {disease}/{iso3.upper()}. "
                "Chạy sync_flunet + sync_weather + feature_builder trước."
            ),
        )
    as_of_year, as_of_week = latest
    return prediction_service.get_forecast(db, disease, iso3, as_of_year, as_of_week)
