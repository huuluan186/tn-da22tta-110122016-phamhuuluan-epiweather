"""Test /api/v1/countries — danh sách quốc gia."""

from app.models.geography import Country


def test_list_countries_returns_200(client):
    r = client.get("/api/v1/countries")
    assert r.status_code == 200


def test_list_countries_returns_list(client):
    body = client.get("/api/v1/countries").json()
    assert isinstance(body, list)


def test_list_countries_includes_iso2(client, db_session):
    db_session.add(
        Country(
            iso3="VNM",
            iso2="VN",
            country_name="Viet Nam",
            who_region="WPRO",
            latitude=14.1,
            longitude=108.3,
        )
    )
    db_session.flush()

    body = client.get("/api/v1/countries").json()

    assert body[0]["iso3"] == "VNM"
    assert body[0]["iso2"] == "VN"


def test_get_country_not_found_404(client):
    """ISO3 không tồn tại → 404."""
    r = client.get("/api/v1/countries/ZZZ")
    assert r.status_code == 404


def test_get_country_invalid_iso3_format(client):
    """ISO3 quá ngắn → FastAPI trả 404 (không match route) hoặc 422."""
    r = client.get("/api/v1/countries/VN")
    assert r.status_code in (404, 422)
