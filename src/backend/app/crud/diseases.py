from sqlalchemy.orm import Session

from ..models import Disease


def get_by_code(db: Session, code: str) -> Disease | None:
    return db.query(Disease).filter(Disease.code == code).first()


def list_active(db: Session) -> list[Disease]:
    return db.query(Disease).filter(Disease.is_active == True).all()
