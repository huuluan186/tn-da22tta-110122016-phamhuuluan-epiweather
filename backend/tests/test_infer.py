"""Test /api/v1/infer — inference endpoint."""

import pytest

# Feature set tối thiểu — giá trị 0.0 hợp lệ (loader dùng 0.0 cho key thiếu)
_MINIMAL_FEATURES: dict[str, float] = {}

# Feature set đầy đủ hơn (dùng giá trị trung bình Việt Nam cuối năm)
_FLU_FEATURES: dict[str, float] = {
    "temp_mean": 25.0,
    "humidity_mean": 80.0,
    "solar_radiation_mean": 180.0,
    "dewpoint_mean": 22.0,
    "week_of_year": 48,
    "month": 12,
    "season_enc": 3,
}

_DENGUE_FEATURES: dict[str, float] = {
    "temp_mean": 28.0,
    "humidity_mean": 85.0,
    "precipitation_sum": 120.0,
    "solar_radiation_mean": 200.0,
    "week_of_year": 30,
    "month": 7,
    "season_enc": 2,
}


# ── Happy path ────────────────────────────────────────────────────────────────

def test_infer_flu_returns_200(client):
    r = client.post("/api/v1/infer", json={
        "disease": "flu",
        "iso3": "VNM",
        "features": _FLU_FEATURES,
    })
    assert r.status_code == 200, r.text


def test_infer_dengue_returns_200(client):
    r = client.post("/api/v1/infer", json={
        "disease": "dengue",
        "iso3": "BRA",
        "features": _DENGUE_FEATURES,
    })
    assert r.status_code == 200, r.text


def test_infer_response_schema(client):
    """Response phải có đầy đủ tất cả fields theo InferResponse schema."""
    r = client.post("/api/v1/infer", json={
        "disease": "flu",
        "iso3": "VNM",
        "features": _FLU_FEATURES,
    })
    body = r.json()
    required_keys = {
        "disease", "iso3",
        "predicted_log", "predicted_cases",
        "risk_level", "p_low", "p_med", "p_high",
        "regressor_features", "classifier_features",
    }
    assert required_keys.issubset(body.keys())


def test_infer_risk_level_valid(client):
    """risk_level phải là Low, Medium, hoặc High."""
    r = client.post("/api/v1/infer", json={
        "disease": "flu",
        "iso3": "VNM",
        "features": _MINIMAL_FEATURES,
    })
    assert r.json()["risk_level"] in ("Low", "Medium", "High")


def test_infer_probabilities_sum_to_one(client):
    """p_low + p_med + p_high phải xấp xỉ 1.0 (softmax output)."""
    r = client.post("/api/v1/infer", json={
        "disease": "dengue",
        "iso3": "BRA",
        "features": _DENGUE_FEATURES,
    })
    body = r.json()
    total = body["p_low"] + body["p_med"] + body["p_high"]
    assert abs(total - 1.0) < 0.01, f"Probabilities sum = {total}, expected ~1.0"


def test_infer_predicted_cases_non_negative(client):
    """predicted_cases = expm1(predicted_log) luôn >= 0."""
    r = client.post("/api/v1/infer", json={
        "disease": "flu",
        "iso3": "USA",
        "features": _FLU_FEATURES,
    })
    assert r.json()["predicted_cases"] >= 0


def test_infer_iso3_uppercased(client):
    """ISO3 trong response phải uppercase dù input lowercase."""
    r = client.post("/api/v1/infer", json={
        "disease": "flu",
        "iso3": "vnm",
        "features": _MINIMAL_FEATURES,
    })
    assert r.json()["iso3"] == "VNM"


def test_infer_minimal_features_still_works(client):
    """Thiếu hoàn toàn features → dùng 0.0 cho tất cả, vẫn trả kết quả."""
    r = client.post("/api/v1/infer", json={
        "disease": "flu",
        "iso3": "VNM",
        "features": {},
    })
    assert r.status_code == 200


# ── Validation errors (422) ───────────────────────────────────────────────────

def test_infer_invalid_disease_422(client):
    """disease không phải flu/dengue → Pydantic trả 422."""
    r = client.post("/api/v1/infer", json={
        "disease": "malaria",
        "iso3": "VNM",
        "features": {},
    })
    assert r.status_code == 422


def test_infer_iso3_too_short_422(client):
    """iso3 ngắn hơn 3 ký tự → Pydantic trả 422."""
    r = client.post("/api/v1/infer", json={
        "disease": "flu",
        "iso3": "VN",
        "features": {},
    })
    assert r.status_code == 422


def test_infer_iso3_too_long_422(client):
    """iso3 dài hơn 3 ký tự → Pydantic trả 422."""
    r = client.post("/api/v1/infer", json={
        "disease": "flu",
        "iso3": "VNMX",
        "features": {},
    })
    assert r.status_code == 422


def test_infer_missing_required_fields_422(client):
    """Thiếu field bắt buộc (disease) → 422."""
    r = client.post("/api/v1/infer", json={
        "iso3": "VNM",
        "features": {},
    })
    assert r.status_code == 422


def test_infer_features_wrong_type_422(client):
    """features value không phải float → 422."""
    r = client.post("/api/v1/infer", json={
        "disease": "flu",
        "iso3": "VNM",
        "features": {"temp_mean": "hot"},
    })
    assert r.status_code == 422
