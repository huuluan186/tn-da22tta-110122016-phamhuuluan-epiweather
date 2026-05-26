from sqlalchemy.orm import Session, joinedload

from ..models import DiseaseCase, Prediction


def get_one(
    db: Session,
    disease_id: int,
    iso3: str,
    year: int,
    week: int,
) -> Prediction | None:
    return (
        db.query(Prediction)
        .filter(
            Prediction.disease_id == disease_id,
            Prediction.iso3 == iso3,
            Prediction.iso_year == year,
            Prediction.iso_week == week,
        )
        .first()
    )


def get_latest_week(db: Session, disease_id: int) -> tuple[int, int] | None:
    """Tuần (iso_year, iso_week) mới nhất có ít nhất 1 prediction cho disease này."""
    row = (
        db.query(Prediction.iso_year, Prediction.iso_week)
        .filter(Prediction.disease_id == disease_id)
        .order_by(Prediction.iso_year.desc(), Prediction.iso_week.desc())
        .first()
    )
    return (row[0], row[1]) if row else None


def list_for_map(
    db: Session,
    disease_id: int,
    year: int,
    week: int,
) -> list[Prediction]:
    return (
        db.query(Prediction)
        .options(joinedload(Prediction.country))
        .filter(
            Prediction.disease_id == disease_id,
            Prediction.iso_year == year,
            Prediction.iso_week == week,
        )
        .all()
    )


def list_history(
    db: Session,
    disease_id: int,
    iso3: str,
    start_year: int,
    end_year: int,
) -> list[Prediction]:
    return (
        db.query(Prediction)
        .filter(
            Prediction.disease_id == disease_id,
            Prediction.iso3 == iso3,
            Prediction.iso_year.between(start_year, end_year),
        )
        .order_by(Prediction.iso_year, Prediction.iso_week)
        .all()
    )


def list_actuals(
    db: Session,
    disease_id: int,
    iso3: str,
    start_year: int,
    end_year: int,
) -> dict[tuple[int, int], int | None]:
    rows = (
        db.query(DiseaseCase)
        .filter(
            DiseaseCase.disease_id == disease_id,
            DiseaseCase.iso3 == iso3,
            DiseaseCase.iso_year.between(start_year, end_year),
        )
        .all()
    )
    return {(r.iso_year, r.iso_week): r.raw_count for r in rows}
