"""Analytics endpoints — đọc trực tiếp metrics + feature importance từ ml_models/."""

import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import distinct, func
from sqlalchemy.orm import Session

from ....core.config import settings
from ....crud import diseases as disease_crud
from ....crud import feature_configs as feature_config_crud
from ....db.session import get_db
from ....models.observation import DiseaseCase
from ....services import feature_lookup, ml_engine

router = APIRouter(prefix="/analytics", tags=["analytics"])

# Training window cố định (xem CLAUDE.md): 2010-2019, bỏ 2020-2021 (COVID/NPI),
# 2022 dành cho validation.
TRAIN_YEAR_START = 2010
TRAIN_YEAR_END = 2019

# MODELS_DIR từ config (env-aware): host = <repo>/ml_models, container = /app/ml_models.
# KHÔNG tự suy từ parents[N] — số cấp khác nhau giữa host (backend/ là subdir) và
# Docker (context ./backend → /app), sẽ trỏ sai đường dẫn trong container.
ML_MODELS_DIR = Path(settings.MODELS_DIR)

DISEASE_MODEL_PREFIX = {
    "flu": "lgbm_flu_regressor",
    "dengue": "rf_dengue_regressor",
}


def _load_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


@router.get("/summary")
def get_summary():
    """Số liệu meta tổng quan — placeholder, tránh break các caller hiện có."""
    return {"message": "Analytics endpoint OK", "ml_models_dir": str(ML_MODELS_DIR)}


@router.get("/model-performance/{disease}")
def model_performance(disease: str):
    """
    Trả CV metrics (R², RMSE, MAE) cho 4 horizon h=1..4 của disease.

    Đọc từ ml_models/{prefix}_h{1..4}_v1_metrics.json.
    """
    if disease not in DISEASE_MODEL_PREFIX:
        raise HTTPException(status_code=400, detail="disease phải là 'flu' hoặc 'dengue'")
    prefix = DISEASE_MODEL_PREFIX[disease]

    horizons = []
    for h in (1, 2, 3, 4):
        path = ML_MODELS_DIR / f"{prefix}_h{h}_v1_metrics.json"
        data = _load_json(path)
        if data is None:
            continue
        horizons.append({
            "horizon": h,
            "r2": data.get("r2"),
            "rmse": data.get("rmse"),
            "mae": data.get("mae"),
            "cv_folds": data.get("cv_folds"),
            "training_period": data.get("training_period"),
        })

    if not horizons:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy metrics cho '{disease}'")

    return {
        "disease": disease,
        "model_type": "LightGBM" if disease == "flu" else "Random Forest",
        "horizons": horizons,
    }


@router.get("/training-coverage/{disease}")
def training_coverage(disease: str, db: Session = Depends(get_db)):
    """
    Độ phủ dữ liệu huấn luyện 2010-2019 từ bảng disease_cases: số năm, số quốc gia,
    số quan sát theo từng năm, trung bình số tuần báo cáo/quốc gia/năm.

    Phục vụ chứng minh độ tin cậy model (dữ liệu nền tảng rộng đến đâu).
    """
    disease_row = disease_crud.get_by_code(db, disease)
    if disease_row is None:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy bệnh '{disease}'")

    year_filter = (
        DiseaseCase.disease_id == disease_row.id,
        DiseaseCase.iso_year.between(TRAIN_YEAR_START, TRAIN_YEAR_END),
    )

    per_year_rows = (
        db.query(
            DiseaseCase.iso_year,
            func.count().label("observations"),
            func.count(distinct(DiseaseCase.iso3)).label("n_countries"),
        )
        .filter(*year_filter)
        .group_by(DiseaseCase.iso_year)
        .order_by(DiseaseCase.iso_year)
        .all()
    )

    per_year = [
        {"year": int(y), "observations": int(obs), "n_countries": int(nc)}
        for y, obs, nc in per_year_rows
    ]
    if not per_year:
        raise HTTPException(status_code=404, detail=f"Chưa có dữ liệu huấn luyện cho '{disease}'")

    total_obs = sum(p["observations"] for p in per_year)
    # Mỗi (quốc gia, năm) là một cặp; tổng n_countries qua các năm = số cặp.
    n_pairs = sum(p["n_countries"] for p in per_year)
    n_countries = (
        db.query(func.count(distinct(DiseaseCase.iso3))).filter(*year_filter).scalar() or 0
    )
    years = [p["year"] for p in per_year]

    return {
        "disease": disease,
        "year_start": min(years),
        "year_end": max(years),
        "n_years": len(years),
        "n_countries": int(n_countries),
        "total_observations": total_obs,
        "avg_weeks_per_country_year": round(total_obs / n_pairs, 1) if n_pairs else 0.0,
        "per_year": per_year,
    }


@router.get("/feature-importance/{disease}")
def feature_importance(disease: str, horizon: int = 1, db: Session = Depends(get_db)):
    """
    Trả feature importance toàn cục của model multi-horizon production.
    """
    if disease not in DISEASE_MODEL_PREFIX:
        raise HTTPException(status_code=400, detail="disease phải là 'flu' hoặc 'dengue'")
    if horizon not in (1, 2, 3, 4):
        raise HTTPException(status_code=400, detail="horizon phải là 1..4")

    prefix = DISEASE_MODEL_PREFIX[disease]
    path = ML_MODELS_DIR / f"{prefix}_h{horizon}_v1_features.json"
    data = _load_json(path)
    if data is None:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy features cho '{disease}' h={horizon}")

    try:
        importance = ml_engine.get_horizon_feature_importance(disease, horizon)
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    feature_names = data.get("features", [])
    disease_row = disease_crud.get_by_code(db, disease)
    metadata_rows = (
        feature_config_crud.metadata_by_names(db, disease_row.id, feature_names)
        if disease_row
        else {}
    )

    # Hệ số tương quan Pearson (feature ↔ log1p số ca) precompute offline — gắn kèm
    # importance để "chứng minh" mức ảnh hưởng bằng tương quan thực tế trên training set.
    corr_data = _load_json(ML_MODELS_DIR / f"{prefix}_h1_v1_correlation.json")
    corr_map = {
        c["feature"]: c.get("pearson_r")
        for c in (corr_data.get("correlations", []) if corr_data else [])
    }

    def feature_metadata(feature_name: str) -> dict:
        row = metadata_rows.get(feature_name)
        return {
            "feature": feature_name,
            "display_name_vi": row.display_name_vi if row else None,
            "description_vi": row.description_vi if row else None,
            "source_type": row.source_type if row else None,
            "pearson_r": corr_map.get(feature_name),
        }

    return {
        "disease": disease,
        "horizon": horizon,
        "features": feature_names,
        "feature_metadata": [feature_metadata(name) for name in feature_names],
        "importance": [
            {**item, **feature_metadata(item["feature"])}
            for item in importance
        ],
        "target": data.get("target"),
        "model_type": data.get("model_type"),
        "training_date": data.get("date"),
        "correlation_scope": corr_data.get("scope") if corr_data else None,
    }


@router.get("/feature-signals/{disease}/{iso3}")
def feature_signals(
    disease: str,
    iso3: str,
    year: int = Query(..., ge=2010),
    week: int = Query(..., ge=1, le=53),
    db: Session = Depends(get_db),
):
    """
    Tín hiệu tuần này: giá trị thực tế của các feature đầu vào mô hình
    tại (disease, iso3, year, week), kèm importance + tương quan Pearson
    + metadata tiếng Việt.

    Khác với /feature-importance (trả importance toàn cục, không đổi theo quốc gia
    hay tuần), endpoint này trả GIÁ TRỊ THỰC TẾ cho từng biến đầu vào → giải thích
    TẠI SAO mô hình đưa ra dự báo cụ thể cho tuần này tại quốc gia này.
    """
    if disease not in DISEASE_MODEL_PREFIX:
        raise HTTPException(status_code=400, detail="disease phải là 'flu' hoặc 'dengue'")

    disease_obj = disease_crud.get_by_code(db, disease)
    if not disease_obj:
        raise HTTPException(status_code=404, detail=f"Disease '{disease}' không tìm thấy")

    # 1. Lookup feature snapshot cho đúng (disease, iso3, year, week)
    snapshot = feature_lookup.get_features(db, disease_obj.id, iso3.upper(), year, week)
    if snapshot is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Không có feature snapshot cho {disease}/{iso3.upper()} "
                f"tại Tuần {week:02d}, Năm {year}"
            ),
        )

    # 2. Feature importance toàn cục (h=1) — dùng để sort theo mức ảnh hưởng
    try:
        importance_list = ml_engine.get_horizon_feature_importance(disease, 1)
    except ValueError:
        importance_list = []
    importance_map = {item["feature"]: item["importance"] for item in importance_list}

    # 3. Pearson correlation (precomputed offline trên training set)
    prefix = DISEASE_MODEL_PREFIX[disease]
    corr_data = _load_json(ML_MODELS_DIR / f"{prefix}_h1_v1_correlation.json")
    corr_map = {
        c["feature"]: c.get("pearson_r")
        for c in (corr_data.get("correlations", []) if corr_data else [])
    }

    # 3b. Mean/std mỗi feature trên training set — để tính direction theo tuần.
    # Direction phải phản ánh GIÁ TRỊ TUẦN NÀY cao/thấp so với bình thường, không
    # phải chỉ dấu tương quan toàn cục (vốn cố định qua mọi tuần).
    stats_data = _load_json(ML_MODELS_DIR / f"{prefix}_h1_v1_feature_stats.json")
    stats_map = stats_data.get("stats", {}) if stats_data else {}

    # 4. Metadata tiếng Việt
    feature_names = list(importance_map.keys()) if importance_map else list(snapshot.keys())
    metadata_rows = feature_config_crud.metadata_by_names(db, disease_obj.id, feature_names)

    # 5. Build signals — chỉ lấy features có trong snapshot AND model
    signals = []
    for feat_name in feature_names:
        value = snapshot.get(feat_name)
        if value is None:
            continue
        row = metadata_rows.get(feat_name)
        pearson_r = corr_map.get(feat_name)
        imp = importance_map.get(feat_name, 0.0)

        # Direction: giá trị feature TUẦN NÀY đẩy dự báo lên hay xuống?
        # So value với mean training (độ lệch), rồi nhân dấu tương quan:
        #   sign(pearson_r × (value − mean)) > 0 → đẩy lên; < 0 → đẩy xuống.
        # Chuẩn hóa độ lệch theo std để lọc dao động nhỏ (|z| < 0.1 coi là neutral).
        direction = "neutral"
        stat = stats_map.get(feat_name)
        if pearson_r is not None and abs(pearson_r) >= 0.05 and stat:
            std = stat.get("std") or 0.0
            deviation = float(value) - stat.get("mean", 0.0)
            z = (deviation / std) if std > 0 else 0.0
            if abs(z) >= 0.1:
                direction = "up" if (pearson_r * deviation) > 0 else "down"

        signals.append({
            "feature": feat_name,
            "value": round(float(value), 4),
            "importance": round(imp, 4),
            "pearson_r": pearson_r,
            "direction": direction,
            "display_name_vi": row.display_name_vi if row else None,
            "description_vi": row.description_vi if row else None,
            "source_type": row.source_type if row else None,
        })

    signals.sort(key=lambda x: x["importance"], reverse=True)

    return {
        "disease": disease,
        "iso3": iso3.upper(),
        "iso_year": year,
        "iso_week": week,
        "signals": signals,
    }
