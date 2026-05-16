from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..crud import countries as country_crud
from ..database import get_db
from ..schemas.country import Country, CountryDetail

router = APIRouter(prefix="/countries", tags=["countries"])


@router.get("", response_model=list[Country])
def list_countries(db: Session = Depends(get_db)):
    return country_crud.list_all(db)


@router.get("/{iso3}", response_model=CountryDetail)
def get_country(iso3: str, db: Session = Depends(get_db)):
    country = country_crud.get_by_iso3(db, iso3)
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    return country
