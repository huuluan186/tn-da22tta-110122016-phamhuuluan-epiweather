from datetime import datetime
from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, JSON, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from .geography import Base


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    run_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    pipeline_name: Mapped[str] = mapped_column(String(50))
    pipeline_version: Mapped[str | None] = mapped_column(String(20))
    trigger_type: Mapped[str] = mapped_column(String(20), default="manual")
    status: Mapped[str] = mapped_column(String(20))
    iso_year: Mapped[int | None] = mapped_column(SmallInteger)
    iso_week: Mapped[int | None] = mapped_column(SmallInteger)
    rows_processed: Mapped[int | None] = mapped_column(Integer)
    rows_inserted: Mapped[int | None] = mapped_column(Integer)
    rows_updated: Mapped[int | None] = mapped_column(Integer)
    rows_skipped: Mapped[int | None] = mapped_column(Integer)
    errors: Mapped[dict | None] = mapped_column(JSON)
    metadata_: Mapped[dict | None] = mapped_column(JSON, name="metadata")


class DataQualityCheck(Base):
    __tablename__ = "data_quality_checks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[str | None] = mapped_column(ForeignKey("pipeline_runs.run_id"))
    check_name: Mapped[str] = mapped_column(String(100))
    table_name: Mapped[str | None] = mapped_column(String(50))
    iso_year: Mapped[int | None] = mapped_column(SmallInteger)
    iso_week: Mapped[int | None] = mapped_column(SmallInteger)
    threshold: Mapped[float | None]
    actual_value: Mapped[float | None]
    passed: Mapped[bool]
    detail: Mapped[str | None]


class ApiRequestLog(Base):
    # Partitioned by requested_at — dùng để tracking + drift detection sau này.
    __tablename__ = "api_request_logs"
    __table_args__ = {"postgresql_partition_by": "RANGE (requested_at)"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    endpoint: Mapped[str | None] = mapped_column(String(100))
    method: Mapped[str | None] = mapped_column(String(10))
    disease: Mapped[str | None] = mapped_column(String(20))
    iso3: Mapped[str | None] = mapped_column(String(3))
    iso_year: Mapped[int | None] = mapped_column(SmallInteger)
    iso_week: Mapped[int | None] = mapped_column(SmallInteger)
    model_version_id: Mapped[int | None] = mapped_column(Integer)
    response_ms: Mapped[int | None] = mapped_column(Integer)
    status_code: Mapped[int | None] = mapped_column(SmallInteger)
    requested_at: Mapped[datetime] = mapped_column(DateTime, primary_key=True)
