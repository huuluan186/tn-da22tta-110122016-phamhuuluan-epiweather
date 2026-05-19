"""Import tất cả ORM models để Alembic autogenerate detect được.

Đây là entry point duy nhất Alembic env.py cần import. KHÔNG import file này
trong runtime code — chỉ dùng cho migration tooling.
"""

from app.db.base_class import Base  # noqa: F401

# Import tất cả models để chúng được register vào Base.metadata
from app.models import (  # noqa: F401
    ApiRequestLog,
    Country,
    DataQualityCheck,
    DataSource,
    Disease,
    DiseaseCase,
    FeatureConfig,
    ModelEvaluation,
    ModelVersion,
    PipelineRun,
    Prediction,
    RiskThreshold,
    WeatherObservation,
    WeatherVariable,
)
