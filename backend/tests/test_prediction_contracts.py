from app.schemas.prediction import ForecastPoint, ForecastResponse, HistoryResponse
from app.services import prediction_service


def test_history_limit_is_forwarded(client, monkeypatch):
    captured: dict[str, int | None] = {}

    def fake_get_history(db, disease, iso3, start_year, end_year, limit):
        captured["limit"] = limit
        return HistoryResponse(disease=disease, iso3=iso3, points=[])

    monkeypatch.setattr(prediction_service, "get_history", fake_get_history)

    response = client.get(
        "/api/v1/predictions/flu/USA/history",
        params={"start_year": 2010, "end_year": 2019, "limit": 52},
    )

    assert response.status_code == 200
    assert captured["limit"] == 52


def test_history_limit_must_be_positive(client):
    response = client.get(
        "/api/v1/predictions/flu/USA/history",
        params={"limit": 0},
    )

    assert response.status_code == 422



def test_forecast_response_exposes_risk_method():
    point = ForecastPoint(
        horizon=1,
        target_iso_year=2026,
        target_iso_week=22,
        predicted_log=1.2,
        predicted_cases=2.3,
        risk_level="Medium",
        r2_cv=0.8,
        rmse_cv=0.4,
        model_version="test",
    )
    response = ForecastResponse(
        disease="flu",
        iso3="VNM",
        as_of_iso_year=2026,
        as_of_iso_week=21,
        points=[point],
        risk_method="bortman_1999_endemic_channel",
    )

    assert response.points[0].risk_level == "Medium"
    assert response.risk_method == "bortman_1999_endemic_channel"
