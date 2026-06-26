"""Test /api/v1/predictions - dự báo chi tiết theo quốc gia/tuần."""

from app.models import Country, Disease, Prediction


def test_prediction_detail_includes_risk_probability(client, db_session):
    db_session.add(
        Disease(
            id=1,
            code="flu",
            display_name="Influenza",
            target_variable="flu_cases",
        )
    )
    db_session.add(
        Country(
            iso3="VNM",
            iso2="VN",
            country_name="Viet Nam",
        )
    )
    db_session.add(
        Prediction(
            id=1,
            disease_id=1,
            iso3="VNM",
            iso_year=2019,
            iso_week=10,
            horizon_weeks=1,
            predicted_cases=125.0,
            risk_level="High",
            risk_probability=0.873,
        )
    )
    db_session.flush()

    response = client.get(
        "/api/v1/predictions/flu/VNM",
        params={"year": 2019, "week": 10},
    )

    assert response.status_code == 200, response.text
    assert response.json()["risk_probability"] == 0.873