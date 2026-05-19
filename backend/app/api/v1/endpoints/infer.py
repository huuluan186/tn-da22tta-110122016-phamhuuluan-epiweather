from fastapi import APIRouter, HTTPException

from ....schemas.infer import InferRequest, InferResponse
from ....services import ml_engine

router = APIRouter(prefix="/infer", tags=["inference"])


@router.post("", response_model=InferResponse)
def live_infer(req: InferRequest):
    """
    Live inference: nhận feature values, trả về kết quả từ cả 2 model.

    - regression: predicted_cases (số ca ước tính)
    - classification: risk_level + P(Low/Med/High)

    Thiếu feature key trong dict → dùng 0.0.
    """
    try:
        reg_result = ml_engine.predict_regression(req.disease, req.features)
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))

    try:
        cls_result = ml_engine.predict_classification(req.disease, req.features)
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))

    return InferResponse(
        disease=req.disease,
        iso3=req.iso3.upper(),
        predicted_log=reg_result["predicted_log"],
        predicted_cases=reg_result["predicted_cases"],
        risk_level=cls_result["risk_level"],
        p_low=cls_result["p_low"],
        p_med=cls_result["p_med"],
        p_high=cls_result["p_high"],
        regressor_features=ml_engine.get_regressor_features(req.disease),
        classifier_features=ml_engine.get_classifier_features(req.disease),
    )


@router.get("/features/{disease}")
def get_required_features(disease: str):
    """Trả về feature list cho regressor và classifier của 1 disease."""
    if disease not in ("flu", "dengue"):
        raise HTTPException(status_code=400, detail="disease phải là 'flu' hoặc 'dengue'")

    reg_features = ml_engine.get_regressor_features(disease)
    cls_features = ml_engine.get_classifier_features(disease)

    if not reg_features and not cls_features:
        raise HTTPException(status_code=503, detail=f"Chưa load model nào cho '{disease}'")

    return {
        "disease": disease,
        "regressor_features": reg_features,
        "classifier_features": cls_features,
    }
