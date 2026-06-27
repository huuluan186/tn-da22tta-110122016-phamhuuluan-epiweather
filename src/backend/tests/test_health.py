"""Test /health endpoint."""


def test_health_returns_200(client):
    r = client.get("/health")
    assert r.status_code == 200


def test_health_schema(client):
    """Response phải có đủ 3 keys: status, database, models_loaded."""
    body = client.get("/health").json()
    assert "status" in body
    assert "database" in body
    assert "models_loaded" in body


def test_health_models_loaded(client):
    """Cả 4 model phải load được (flu + dengue, regressor + classifier)."""
    body = client.get("/health").json()
    loaded = body["models_loaded"]
    assert "flu" in loaded["regressors"], "Regressor flu chưa load"
    assert "dengue" in loaded["regressors"], "Regressor dengue chưa load"
    assert "flu" in loaded["classifiers"], "Classifier flu chưa load"
    assert "dengue" in loaded["classifiers"], "Classifier dengue chưa load"


def test_health_status_ok_when_db_connected(client):
    """status = 'ok' khi DB connect được (SQLite in-memory luôn OK)."""
    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert body["database"] == "connected"
