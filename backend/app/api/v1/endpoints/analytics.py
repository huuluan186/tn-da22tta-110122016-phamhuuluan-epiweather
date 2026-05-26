"""Analytics endpoints — đọc trực tiếp metrics + feature importance từ ml_models/."""

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/analytics", tags=["analytics"])

PROJECT_ROOT = Path(__file__).resolve().parents[5]
ML_MODELS_DIR = PROJECT_ROOT / "ml_models"

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
def feature_importance(disease: str, horizon: int = 1):
    """
    Trả danh sách features dùng cho model + best hyperparameters.

    Không có feature_importance thật (chưa lưu .feature_importances_),
    nên trả thứ tự features từ json — FE có thể hiển thị theo thứ tự ưu tiên domain.
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

    return {
        "disease": disease,
        "horizon": horizon,
        "features": data.get("features", []),
        "target": data.get("target"),
        "model_type": data.get("model_type"),
        "training_date": data.get("date"),
    }
