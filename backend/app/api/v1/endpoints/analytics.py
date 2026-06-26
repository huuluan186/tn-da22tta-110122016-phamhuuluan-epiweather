"""Analytics endpoints — đọc trực tiếp metrics + feature importance từ ml_models/."""

import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ....core.config import settings
from ....crud import diseases as disease_crud
from ....crud import feature_configs as feature_config_crud
from ....db.session import get_db
from ....services import ml_engine

router = APIRouter(prefix="/analytics", tags=["analytics"])

# MODELS_DIR từ config (env-aware): host = <repo>/ml_models, container = /app/ml_models.
# KHÔNG tự suy từ parents[N] — số cấp khác nhau giữa host (backend/ là subdir) và
# Docker (context ./backend → /app), sẽ trỏ sai đường dẫn trong container.
ML_MODELS_DIR = Path(settings.MODELS_DIR)

DISEASE_MODEL_PREFIX = {
    "flu": "lgbm_flu_regressor",
    "dengue": "rf_dengue_regressor",
}


def _load_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


@router.get("/summary")
def get_summary():
    """Số liệu meta tổng quan — placeholder, tránh break các caller hiện có."""
    return {"message": "Analytics endpoint OK", "ml_models_dir": str(ML_MODELS_DIR)}


@router.get("/model-performance/{disease}")
def model_performance(disease: str):
    """
    Trả CV metrics (R², RMSE, MAE) cho 4 horizon h=1..4 của disease.

    Đọc từ ml_models/{prefix}_h{1..4}_v1_metrics.json.
    """
    if disease not in DISEASE_MODEL_PREFIX:
        raise HTTPException(status_code=400, detail="disease phải là 'flu' hoặc 'dengue'")
    prefix = DISEASE_MODEL_PREFIX[disease]

    horizons = []
    for h in (1, 2, 3, 4):
        path = ML_MODELS_DIR / f"{prefix}_h{h}_v1_metrics.json"
        data = _load_json(path)
        if data is None:
            continue
        horizons.append({
            "horizon": h,
            "r2": data.get("r2"),
            "rmse": data.get("rmse"),
            "mae": data.get("mae"),
            "cv_folds": data.get("cv_folds"),
            "training_period": data.get("training_period"),
        })

    if not horizons:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy metrics cho '{disease}'")

    return {
        "disease": disease,
        "model_type": "LightGBM" if disease == "flu" else "Random Forest",
        "horizons": horizons,
    }


@router.get("/feature-importance/{disease}")
def feature_importance(disease: str, horizon: int = 1, db: Session = Depends(get_db)):
    """
    Trả feature importance toàn cục của model multi-horizon production.
    """
    if disease not in DISEASE_MODEL_PREFIX:
        raise HTTPException(status_code=400, detail="disease phải là 'flu' hoặc 'dengue'")
    if horizon not in (1, 2, 3, 4):
        raise HTTPException(status_code=400, detail="horizon phải là 1..4")

    prefix = DISEASE_MODEL_PREFIX[disease]
    path = ML_MODELS_DIR / f"{prefix}_h{horizon}_v1_features.json"
    data = _load_json(path)
    if data is None:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy features cho '{disease}' h={horizon}")

    try:
        importance = ml_engine.get_horizon_feature_importance(disease, horizon)
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    feature_names = data.get("features", [])
    disease_row = disease_crud.get_by_code(db, disease)
    metadata_rows = (
        feature_config_crud.metadata_by_names(db, disease_row.id, feature_names)
        if disease_row
        else {}
    )

    def feature_metadata(feature_name: str) -> dict:
        row = metadata_rows.get(feature_name)
        return {
            "feature": feature_name,
            "display_name_vi": row.display_name_vi if row else None,
            "description_vi": row.description_vi if row else None,
            "source_type": row.source_type if row else None,
        }

    return {
        "disease": disease,
        "horizon": horizon,
        "features": feature_names,
        "feature_metadata": [feature_metadata(name) for name in feature_names],
        "importance": [
            {**item, **feature_metadata(item["feature"])}
            for item in importance
        ],
        "target": data.get("target"),
        "model_type": data.get("model_type"),
        "training_date": data.get("date"),
    }
