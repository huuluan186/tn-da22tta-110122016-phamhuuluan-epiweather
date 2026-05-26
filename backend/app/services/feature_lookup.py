"""
feature_lookup.py — Query feature_snapshots từ DB.

Phase C-2: đọc features pre-computed từ bảng feature_snapshots (load từ CSV qua load_features.py).
Phase A-2 (sau): sẽ thay bằng feature_builder dynamic — query disease_cases + weather_observations
                  → compute features runtime cho realtime data.
"""

from sqlalchemy import distinct, func
from sqlalchemy.orm import Session

from ..models import Country, DiseaseCase, FeatureSnapshot

TRAINING_YEARS = set(range(2010, 2020))  # 2010-2019 — training window cả hai bệnh

# Dengue có thêm "nowcast" range: OpenDengue v1.3 batch-released tới 2023-W36.
# Đây KHÔNG phải extrapolation vô căn cứ — có ground truth từ OpenDengue,
# chỉ không thể validate real-time vì nguồn batch.
DENGUE_NOWCAST_YEARS = {2021, 2022, 2023}
DENGUE_DISEASE_ID = 2


def get_features(
    db: Session,
    disease_id: int,
    iso3: str,
    iso_year: int,
    iso_week: int,
    feature_version: str = "v1",
) -> dict[str, float] | None:
    """Trả về feature dict cho (disease, iso3, year, week) hoặc None nếu không có."""
    row = (
        db.query(FeatureSnapshot)
        .filter(
            FeatureSnapshot.disease_id == disease_id,
            FeatureSnapshot.iso3 == iso3.upper(),
            FeatureSnapshot.iso_year == iso_year,
            FeatureSnapshot.iso_week == iso_week,
            FeatureSnapshot.feature_version == feature_version,
        )
        .first()
    )
    return dict(row.features) if row else None


def get_latest_available_week(
    db: Session,
    disease_id: int,
    iso3: str,
    feature_version: str = "v1",
) -> tuple[int, int] | None:
    """Tuần mới nhất có feature snapshot cho (disease, iso3). Trả (iso_year, iso_week) hoặc None."""
    row = (
        db.query(FeatureSnapshot.iso_year, FeatureSnapshot.iso_week)
        .filter(
            FeatureSnapshot.disease_id == disease_id,
            FeatureSnapshot.iso3 == iso3.upper(),
            FeatureSnapshot.feature_version == feature_version,
        )
        .order_by(FeatureSnapshot.iso_year.desc(), FeatureSnapshot.iso_week.desc())
        .first()
    )
    return (row[0], row[1]) if row else None


def get_snapshot_years(
    db: Session,
    disease_id: int,
    iso3: str,
    feature_version: str = "v1",
) -> list[int]:
    """Danh sách năm có feature snapshot cho (disease, iso3), sorted."""
    rows = (
        db.query(distinct(FeatureSnapshot.iso_year))
        .filter(
            FeatureSnapshot.disease_id == disease_id,
            FeatureSnapshot.iso3 == iso3.upper(),
            FeatureSnapshot.feature_version == feature_version,
        )
        .order_by(FeatureSnapshot.iso_year)
        .all()
    )
    return [r[0] for r in rows]


def get_training_years_for_country(
    db: Session,
    disease_id: int,
    iso3: str,
) -> list[int]:
    """Năm có disease_cases thực tế (raw_count > 0) cho (disease, iso3)."""
    rows = (
        db.query(distinct(DiseaseCase.iso_year))
        .filter(
            DiseaseCase.disease_id == disease_id,
            DiseaseCase.iso3 == iso3.upper(),
            DiseaseCase.raw_count > 0,
            DiseaseCase.iso_year.between(2010, 2019),
        )
        .order_by(DiseaseCase.iso_year)
        .all()
    )
    return [r[0] for r in rows]


def get_available_countries(
    db: Session,
    disease_id: int,
    feature_version: str = "v1",
) -> list[dict]:
    """
    Danh sách tất cả countries có ít nhất 1 feature snapshot, kèm metadata coverage.
    Trả list[dict] với keys: iso3, country_name, snapshot_years, latest_year, latest_week.
    """
    rows = (
        db.query(
            FeatureSnapshot.iso3,
            func.array_agg(distinct(FeatureSnapshot.iso_year)).label("snap_years"),
            func.max(FeatureSnapshot.iso_year).label("latest_year"),
            func.max(FeatureSnapshot.iso_week).label("latest_week"),
        )
        .filter(
            FeatureSnapshot.disease_id == disease_id,
            FeatureSnapshot.feature_version == feature_version,
        )
        .group_by(FeatureSnapshot.iso3)
        .all()
    )

    # join country_name
    iso3_list = [r[0] for r in rows]
    country_map: dict[str, str] = {}
    if iso3_list:
        c_rows = (
            db.query(Country.iso3, Country.country_name)
            .filter(Country.iso3.in_(iso3_list))
            .all()
        )
        country_map = {r[0]: r[1] for r in c_rows}

    result = []
    for iso3, snap_years, latest_year, latest_week in rows:
        sorted_years = sorted(snap_years) if snap_years else []
        result.append({
            "iso3": iso3,
            "country_name": country_map.get(iso3),
            "snapshot_years": sorted_years,
            "latest_year": latest_year,
            "latest_week": latest_week,
            "in_training_period": bool(set(sorted_years) & TRAINING_YEARS),
        })
    result.sort(key=lambda x: x["iso3"])
    return result


def build_data_coverage(
    db: Session,
    disease_id: int,
    iso3: str,
    as_of_year: int,
    feature_version: str = "v1",
) -> dict:
    """
    Trả DataCoverage dict cho (disease, iso3, as_of_year).
    Dùng để populate ForecastResponse.data_coverage.
    """
    snap_years = get_snapshot_years(db, disease_id, iso3, feature_version)
    training_years = get_training_years_for_country(db, disease_id, iso3)
    in_training = as_of_year in TRAINING_YEARS
    is_dengue_nowcast = (
        disease_id == DENGUE_DISEASE_ID and as_of_year in DENGUE_NOWCAST_YEARS
    )

    warning: str | None = None
    if not snap_years:
        warning = f"Quốc gia này chưa có đủ dữ liệu để dự báo."
    elif as_of_year not in snap_years:
        warning = f"Năm {as_of_year} chưa có dữ liệu cho quốc gia này."
    elif not in_training:
        if is_dengue_nowcast:
            warning = (
                f"Dự báo nowcast {as_of_year}. Model đã validate trên hold-out 2022 (R²=0.87) "
                "và đối chiếu được với số ca thực OpenDengue đến W36/2023."
            )
        else:
            warning = (
                f"Dự báo realtime {as_of_year}. Model đã validate trên hold-out 2022 (R²=0.80) — "
                "số ca thực của năm này sẽ được dùng để đánh giá độ chính xác về sau."
            )

    return {
        "in_training_period": in_training,
        "is_nowcast": is_dengue_nowcast,
        "snapshot_years": snap_years,
        "training_years": training_years,
        "warning": warning,
    }
