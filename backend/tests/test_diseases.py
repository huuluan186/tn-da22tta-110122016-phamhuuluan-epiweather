"""Test /api/v1/diseases — danh sách loại bệnh và model metrics."""


def test_list_diseases_returns_200(client):
    r = client.get("/api/v1/diseases")
    assert r.status_code == 200


def test_list_diseases_returns_list(client):
    """Response phải là list (dù rỗng khi DB SQLite chưa seed)."""
    body = client.get("/api/v1/diseases").json()
    assert isinstance(body, list)


def test_model_metrics_returns_200(client):
    r = client.get("/api/v1/diseases/model-metrics")
    assert r.status_code == 200


def test_model_metrics_has_flu_and_dengue(client):
    """Phải có metrics cho cả flu và dengue (từ models đã load)."""
    body = client.get("/api/v1/diseases/model-metrics").json()
    diseases = {item["disease"] for item in body}
    assert "flu" in diseases, "Thiếu metrics cho flu"
    assert "dengue" in diseases, "Thiếu metrics cho dengue"


def test_model_metrics_schema(client):
    """Mỗi item phải có đầy đủ fields theo ModelMetrics schema."""
    body = client.get("/api/v1/diseases/model-metrics").json()
    required_keys = {"disease", "model_type", "r2_cv", "rmse_cv", "mae_cv", "cv_folds"}
    for item in body:
        assert required_keys.issubset(item.keys()), f"Thiếu fields trong: {item}"


def test_model_metrics_r2_in_valid_range(client):
    """R² nằm trong khoảng hợp lý [-1, 1]."""
    body = client.get("/api/v1/diseases/model-metrics").json()
    for item in body:
        assert -1.0 <= item["r2_cv"] <= 1.0, f"R² bất thường: {item['r2_cv']}"
