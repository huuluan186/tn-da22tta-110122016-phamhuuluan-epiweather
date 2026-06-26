"""
ML Engine — load và inference các production models.

Đây là single entry point cho mọi ML operation trong app.

Models:
  lgbm_flu_regressor_v2.pkl      — LightGBM, predict log1p(flu cases), velocity+accel features
  rf_dengue_regressor_v2.pkl     — RandomForest, predict log1p(dengue cases), velocity+accel features
  xgb_flu_classifier_v4.pkl      — XGBClassifier, predict P(Low/Med/High) flu, encoding fix + imbalanced strategy
  xgb_dengue_classifier_v4.pkl   — XGBClassifier, predict P(Low/Med/High) dengue, encoding fix + imbalanced strategy

Lưu ý: classifier v4 dùng mapping tường minh Low=0/Medium=1/High=2 (sửa bug
LabelEncoder v3 sort alphabet thành High=0). predict_classification đọc class_order
từ metadata nên không phụ thuộc thứ tự encoding.
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
    "flu":    "xgb_flu_classifier_v4",
    "dengue": "xgb_dengue_classifier_v4",
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
    """
    Nạp metadata (features.json + metrics.json — vài KB) ngay; KHÔNG nạp pickle.

    Model nặng (RF dengue ~40MB/file) được lazy-load qua _get_model() ở lần predict
    đầu tiên, để startup không block server. art['model'] = None cho tới khi cần.
    """
    pkl_path = models_dir / f"{stem}.pkl"
    if not pkl_path.exists():
        logger.warning(f"SKIP — không tìm thấy: {pkl_path}")
        return None

    features_path = models_dir / f"{stem}_features.json"
    with open(features_path) as f:
        features_meta = json.load(f)
    features: list[str] = features_meta["features"]

    metrics: dict = {}
    metrics_path = models_dir / f"{stem}_metrics.json"
    if metrics_path.exists():
        with open(metrics_path) as f:
            metrics = json.load(f)

    # class_order: {"0":"Low","1":"Medium","2":"High"} — index của predict_proba → label.
    # Đọc từ metadata để KHÔNG hardcode (tránh bug LabelEncoder sort alphabet).
    class_order_raw = features_meta.get("class_order")
    label_of_index: dict[int, str] | None = None
    if class_order_raw:
        label_of_index = {int(k): v for k, v in class_order_raw.items()}
    high_threshold = features_meta.get("high_threshold")

    return {
        "model": None,            # lazy — nạp ở _get_model() khi predict lần đầu
        "pkl_path": pkl_path,
        "features": features,
        "metrics": metrics,
        "label_of_index": label_of_index,
        "high_threshold": high_threshold,
    }


def _get_model(art: dict):
    """Lazy-load pickle lần đầu, cache vào art['model']. Idempotent."""
    if art["model"] is None:
        pkl_path = art["pkl_path"]
        try:
            art["model"] = joblib.load(pkl_path)
        except Exception:
            with open(pkl_path, "rb") as f:
                art["model"] = pickle.load(f)
        logger.info(f"lazy-loaded model {pkl_path.name}")
    return art["model"]


def load_models(models_dir: Path) -> None:
    """
    Gọi 1 lần khi FastAPI khởi động (lifespan). Chỉ nạp metadata để startup hoàn tất
    ngay; pickle nặng được nạp on-demand ở request đầu tiên cần model đó.
    """
    models_dir = Path(models_dir)

    for disease, stem in _REGRESSOR_FILES.items():
        art = _load_artifact(models_dir, stem)
        if art:
            _regressors[disease] = art
            logger.info(f"regressor '{disease}' registered — {len(art['features'])} features (lazy)")

    for disease, stem in _CLASSIFIER_FILES.items():
        art = _load_artifact(models_dir, stem)
        if art:
            _classifiers[disease] = art
            logger.info(f"classifier '{disease}' registered — {len(art['features'])} features (lazy)")

    for (disease, h), stem in _REGRESSOR_MH_FILES.items():
        art = _load_artifact(models_dir, stem)
        if art:
            _regressors_mh[(disease, h)] = art
            logger.info(f"regressor_mh '{disease}' h={h} registered — R²={art['metrics'].get('r2', 'n/a')} (lazy)")


# ── Inference ──────────────────────────────────────────────────────────────────

def _build_input(feature_values: dict[str, float], feature_list: list[str]) -> np.ndarray:
    return np.array([[feature_values.get(f, 0.0) for f in feature_list]], dtype=np.float32)


def predict_regression(disease: str, feature_values: dict[str, float]) -> dict:
    if disease not in _regressors:
        raise ValueError(f"Regressor '{disease}' chưa được load")
    art = _regressors[disease]
    X = _build_input(feature_values, art["features"])
    predicted_log = float(_get_model(art).predict(X)[0])
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
    predicted_log = float(_get_model(art).predict(X)[0])
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
    proba = _get_model(art).predict_proba(X)[0]

    # Map index → label theo metadata (mặc định Low=0/Med=1/High=2 nếu thiếu).
    label_of_index = art.get("label_of_index") or _RISK_LABELS
    idx_of = {label: i for i, label in label_of_index.items()}
    p_low  = float(proba[idx_of["Low"]])
    p_med  = float(proba[idx_of["Medium"]])
    p_high = float(proba[idx_of["High"]])

    # Risk level: nếu có high_threshold (tuned từ notebook 6.8c), ưu tiên bắt High.
    high_threshold = art.get("high_threshold")
    if high_threshold is not None and p_high >= high_threshold:
        risk_level = "High"
    else:
        risk_level = max({"Low": p_low, "Medium": p_med, "High": p_high}.items(),
                         key=lambda kv: kv[1])[0]

    return {
        "risk_level": risk_level,
        # Score = P(High) — đo "mức độ rủi ro" liên tục 0..1, không phải confidence.
        # Cao = nguy hiểm. Nước Low chắc chắn vẫn có score thấp (đúng intuition).
        "risk_probability": round(p_high, 4),
        "p_low":  round(p_low, 4),
        "p_med":  round(p_med, 4),
        "p_high": round(p_high, 4),
    }


# ── Query helpers ──────────────────────────────────────────────────────────────

def get_regressor_features(disease: str) -> list[str]:
    return _regressors[disease]["features"] if disease in _regressors else []


def get_classifier_features(disease: str) -> list[str]:
    return _classifiers[disease]["features"] if disease in _classifiers else []


def get_horizon_feature_importance(disease: str, horizon: int) -> list[dict]:
    key = (disease, horizon)
    if key not in _regressors_mh:
        raise ValueError(f"Multi-horizon regressor '{disease}' h={horizon} chưa được load")

    art = _regressors_mh[key]
    features = art["features"]
    raw_importance = getattr(_get_model(art), "feature_importances_", None)

    if raw_importance is None:
        raise ValueError(f"Model '{disease}' h={horizon} không hỗ trợ feature importance")

    total = float(np.sum(raw_importance))
    return sorted(
        [
            {
                "feature": feature,
                "importance": float(value / total) if total > 0 else 0.0,
            }
            for feature, value in zip(features, raw_importance, strict=True)
        ],
        key=lambda item: item["importance"],
        reverse=True,
    )


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
