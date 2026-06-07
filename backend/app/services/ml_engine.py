"""
ML Engine — load và inference các production models.

Đây là single entry point cho mọi ML operation trong app.

Models:
  lgbm_flu_regressor_v2.pkl      — LightGBM, predict log1p(flu cases), velocity+accel features
  rf_dengue_regressor_v2.pkl     — RandomForest, predict log1p(dengue cases), velocity+accel features
  xgb_flu_classifier_v3.pkl      — XGBClassifier, predict P(Low/Med/High) flu, sample_weight balanced
  xgb_dengue_classifier_v3.pkl   — XGBClassifier, predict P(Low/Med/High) dengue, sample_weight balanced
"""

import json
import pickle
from pathlib import Path

import joblib
import numpy as np
from loguru import logger

# ── Internal state ─────────────────────────────────────────────────────────────

_regressors: dict = {}
_classifiers: dict = {}
_regressors_mh: dict = {}  # multi-horizon: {(disease, h): artifact}

_REGRESSOR_FILES = {
    "flu":    "lgbm_flu_regressor_v2",
    "dengue": "rf_dengue_regressor_v2",
}
_CLASSIFIER_FILES = {
    "flu":    "xgb_flu_classifier_v3",
    "dengue": "xgb_dengue_classifier_v3",
}

# Multi-horizon files (SESSION 8 — 21/05/2026)
_REGRESSOR_MH_FILES: dict[tuple[str, int], str] = {
    ("flu",    1): "lgbm_flu_regressor_h1_v1",
    ("flu",    2): "lgbm_flu_regressor_h2_v1",
    ("flu",    3): "lgbm_flu_regressor_h3_v1",
    ("flu",    4): "lgbm_flu_regressor_h4_v1",
    ("dengue", 1): "rf_dengue_regressor_h1_v1",
    ("dengue", 2): "rf_dengue_regressor_h2_v1",
    ("dengue", 3): "rf_dengue_regressor_h3_v1",
    ("dengue", 4): "rf_dengue_regressor_h4_v1",
}

HORIZONS = [1, 2, 3, 4]
_RISK_LABELS = {0: "Low", 1: "Medium", 2: "High"}


# ── Load ───────────────────────────────────────────────────────────────────────

def _load_artifact(models_dir: Path, stem: str) -> dict | None:
    pkl_path = models_dir / f"{stem}.pkl"
    if not pkl_path.exists():
        logger.warning(f"SKIP — không tìm thấy: {pkl_path}")
        return None

    try:
        model = joblib.load(pkl_path)
    except Exception:
        with open(pkl_path, "rb") as f:
            model = pickle.load(f)

    features_path = models_dir / f"{stem}_features.json"
    with open(features_path) as f:
        features_meta = json.load(f)
    features: list[str] = features_meta["features"]

    metrics: dict = {}
    metrics_path = models_dir / f"{stem}_metrics.json"
    if metrics_path.exists():
        with open(metrics_path) as f:
            metrics = json.load(f)

    return {"model": model, "features": features, "metrics": metrics}


def load_models(models_dir: Path) -> None:
    """Gọi 1 lần khi FastAPI khởi động (lifespan)."""
    models_dir = Path(models_dir)

    for disease, stem in _REGRESSOR_FILES.items():
        art = _load_artifact(models_dir, stem)
        if art:
            _regressors[disease] = art
            logger.info(f"regressor '{disease}' loaded — {len(art['features'])} features")

    for disease, stem in _CLASSIFIER_FILES.items():
        art = _load_artifact(models_dir, stem)
        if art:
            _classifiers[disease] = art
            logger.info(f"classifier '{disease}' loaded — {len(art['features'])} features")

    for (disease, h), stem in _REGRESSOR_MH_FILES.items():
        art = _load_artifact(models_dir, stem)
        if art:
            _regressors_mh[(disease, h)] = art
            logger.info(f"regressor_mh '{disease}' h={h} loaded — R²={art['metrics'].get('r2', 'n/a')}")


# ── Inference ──────────────────────────────────────────────────────────────────

def _build_input(feature_values: dict[str, float], feature_list: list[str]) -> np.ndarray:
    return np.array([[feature_values.get(f, 0.0) for f in feature_list]], dtype=np.float32)


def predict_regression(disease: str, feature_values: dict[str, float]) -> dict:
    if disease not in _regressors:
        raise ValueError(f"Regressor '{disease}' chưa được load")
    art = _regressors[disease]
    X = _build_input(feature_values, art["features"])
    predicted_log = float(art["model"].predict(X)[0])
    predicted_cases = float(np.expm1(max(predicted_log, 0.0)))
    return {
        "predicted_log": round(predicted_log, 4),
        "predicted_cases": round(predicted_cases, 1),
    }


def predict_horizon(disease: str, horizon: int, feature_values: dict[str, float]) -> dict:
    """Predict 1 horizon cụ thể (h=1..4) — dùng cho /forecast endpoint."""
    key = (disease, horizon)
    if key not in _regressors_mh:
        raise ValueError(f"Multi-horizon regressor '{disease}' h={horizon} chưa được load")
    art = _regressors_mh[key]
    X = _build_input(feature_values, art["features"])
    predicted_log = float(art["model"].predict(X)[0])
    predicted_cases = float(np.expm1(max(predicted_log, 0.0)))
    metrics = art["metrics"]
    return {
        "predicted_log": round(predicted_log, 4),
        "predicted_cases": round(predicted_cases, 1),
        "r2_cv": metrics.get("r2"),
        "rmse_cv": metrics.get("rmse"),
        "mae_cv": metrics.get("mae"),
        "model_version": f"{disease}_h{horizon}_v1",
    }


def predict_classification(disease: str, feature_values: dict[str, float]) -> dict:
    if disease not in _classifiers:
        raise ValueError(f"Classifier '{disease}' chưa được load")
    art = _classifiers[disease]
    X = _build_input(feature_values, art["features"])
    proba = art["model"].predict_proba(X)[0]
    pred_idx = int(np.argmax(proba))
    return {
        "risk_level": _RISK_LABELS[pred_idx],
        # Score = P(High) — đo "mức độ rủi ro" liên tục 0..1, không phải confidence.
        # Cao = nguy hiểm. Nước Low chắc chắn vẫn có score thấp (đúng intuition).
        "risk_probability": round(float(proba[2]), 4),
        "p_low":  round(float(proba[0]), 4),
        "p_med":  round(float(proba[1]), 4),
        "p_high": round(float(proba[2]), 4),
    }


# ── Query helpers ──────────────────────────────────────────────────────────────

def get_regressor_features(disease: str) -> list[str]:
    return _regressors[disease]["features"] if disease in _regressors else []


def get_classifier_features(disease: str) -> list[str]:
    return _classifiers[disease]["features"] if disease in _classifiers else []


def loaded_diseases() -> dict:
    return {
        "regressors": list(_regressors.keys()),
        "classifiers": list(_classifiers.keys()),
    }


def get_model_metrics(disease: str) -> dict:
    return {
        "regressor": _regressors[disease]["metrics"] if disease in _regressors else None,
        "classifier": _classifiers[disease]["metrics"] if disease in _classifiers else None,
    }


def get_metrics() -> dict:
    result = {}
    for disease, art in _regressors.items():
        m = art["metrics"]
        result[disease] = {
            "model_type": "Regressor",
            "r2_cv":   m.get("r2", 0.0),
            "rmse_cv": m.get("rmse", 0.0),
            "mae_cv":  m.get("mae", 0.0),
            "cv_folds": m.get("cv_folds", 0),
            "holdout_2022": m.get("test_2022"),
        }
    return result
