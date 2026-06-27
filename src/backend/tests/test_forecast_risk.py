from app.services.prediction_service import _risk_from_bortman


def test_bortman_risk_levels():
    baseline = (10.0, 20.0)

    assert _risk_from_bortman(9.9, baseline) == "Low"
    assert _risk_from_bortman(10.0, baseline) == "Medium"
    assert _risk_from_bortman(19.9, baseline) == "Medium"
    assert _risk_from_bortman(20.0, baseline) == "High"


def test_bortman_zero_baseline():
    assert _risk_from_bortman(0.0, (0.0, 0.0)) == "Low"
    assert _risk_from_bortman(1.0, (0.0, 0.0)) == "High"


def test_bortman_missing_baseline():
    assert _risk_from_bortman(10.0, None) is None