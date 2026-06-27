from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..db.session import get_db
from ..services import ml_engine

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "error"

    models = ml_engine.loaded_diseases()

    return {
        "status": "ok" if db_status == "connected" else "degraded",
        "database": db_status,
        "models_loaded": models,
    }
