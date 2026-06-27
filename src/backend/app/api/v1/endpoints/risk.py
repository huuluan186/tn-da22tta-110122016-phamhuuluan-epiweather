from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ....db.session import get_db
from ....schemas.prediction import RiskMapPeriodsResponse, RiskMapResponse
from ....services import risk_service

router = APIRouter(prefix="/risk-map", tags=["risk"])


@router.get("/{disease}/latest", response_model=RiskMapResponse)
def get_latest_risk_map(disease: str, db: Session = Depends(get_db)):
    """Auto-detect tuần mới nhất trong predictions table và trả về risk map."""
    return risk_service.get_latest_risk_map(db, disease)



@router.get("/{disease}/periods", response_model=RiskMapPeriodsResponse)
def get_risk_map_periods(disease: str, db: Session = Depends(get_db)):
    """Các năm/tuần thật sự có prediction trong DB cho bộ lọc bản đồ."""
    return risk_service.get_risk_map_periods(db, disease)

@router.get("/{disease}", response_model=RiskMapResponse)
def get_risk_map(
    disease: str,
    year: int = Query(..., ge=2010),
    week: int = Query(..., ge=1, le=53),
    db: Session = Depends(get_db),
):
    return risk_service.get_risk_map(db, disease, year, week)
