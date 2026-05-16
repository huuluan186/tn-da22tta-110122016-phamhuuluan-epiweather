from fastapi import APIRouter, HTTPException

from ..ml import loader
from ..schemas.infer import InferRequest, InferResponse

router = APIRouter(prefix="/api/v1/infer", tags=["inference"])


@router.post("", response_model=InferResponse)
def live_infer(req: InferRequest):
    """
    Live inference: nhận feature values, trả về P(Low/Med/High) và risk_level.

    Dùng per-region model nếu có, fallback global nếu không.
    Thiếu feature key → dùng 0.0.
    """
    diseases = loader.loaded_diseases()
    if req.disease not in diseases:
        raise HTTPException(
            status_code=503,
            detail=f"Model cho '{req.disease}' chưa được load. Loaded: {diseases}",
        )

    try:
        result = loader.predict(req.disease, req.iso3, req.features)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    region = loader.ISO3_TO_REGION.get(req.iso3.upper(), "UNK")
    features_used = loader.get_features(req.disease)

    return InferResponse(
        disease=req.disease,
        iso3=req.iso3.upper(),
        region=region,
        model_used=result["model_used"],
        risk_level=result["risk_level"],
        p_low=result["p_low"],
        p_med=result["p_med"],
        p_high=result["p_high"],
        features_used=features_used,
    )


@router.get("/features/{disease}", tags=["inference"])
def get_required_features(disease: str):
    """Trả về danh sách feature names cần thiết cho inference."""
    if disease not in ("flu", "dengue"):
        raise HTTPException(status_code=400, detail="disease phải là 'flu' hoặc 'dengue'")
    features = loader.get_features(disease)
    if not features:
        raise HTTPException(status_code=503, detail=f"Model '{disease}' chưa load")
    return {"disease": disease, "features": features, "count": len(features)}
