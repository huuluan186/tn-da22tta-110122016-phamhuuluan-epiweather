from sqlalchemy.orm import Session

from ..models import FeatureConfig


def metadata_by_names(
    db: Session,
    disease_id: int,
    feature_names: list[str],
) -> dict[str, FeatureConfig]:
    if not feature_names:
        return {}

    rows = (
        db.query(FeatureConfig)
        .filter(
            FeatureConfig.disease_id == disease_id,
            FeatureConfig.feature_name.in_(feature_names),
            FeatureConfig.is_active == True,
        )
        .order_by(FeatureConfig.id.desc())
        .all()
    )

    result: dict[str, FeatureConfig] = {}
    for row in rows:
        result.setdefault(row.feature_name, row)
    return result
