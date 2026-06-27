from sqlalchemy.orm import Session

from ..models import Country


def get_by_iso3(db: Session, iso3: str) -> Country | None:
    return db.get(Country, iso3.upper())


def list_all(db: Session) -> list[Country]:
    return (
        db.query(Country)
        .filter(Country.latitude.isnot(None))
        .order_by(Country.country_name)
        .all()
    )
