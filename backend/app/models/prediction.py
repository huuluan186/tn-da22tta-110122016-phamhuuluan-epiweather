from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, JSON, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .geography import Base


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    disease_id: Mapped[int] = mapped_column(ForeignKey("diseases.id"))
    version: Mapped[str] = mapped_column(String(30))
    algorithm: Mapped[str] = mapped_column(String(30), default="XGBoost")
    description: Mapped[str | None] = mapped_column(Text)
    train_year_start: Mapped[int] = mapped_column(SmallInteger)
    train_year_end: Mapped[int] = mapped_column(SmallInteger)
    val_year: Mapped[int | None] = mapped_column(SmallInteger)
    feature_config_tag: Mapped[str | None] = mapped_column(String(30))
    hyperparams: Mapped[dict | None] = mapped_column(JSON)
    artifact_path: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    is_champion: Mapped[bool] = mapped_column(Boolean, default=False)

    disease: Mapped["Disease"] = relationship(  # noqa: F821
        "Disease", back_populates="model_versions"
    )
    evaluations: Mapped[list["ModelEvaluation"]] = relationship(
        "ModelEvaluation", back_populates="model_version"
    )


class ModelEvaluation(Base):
    __tablename__ = "model_evaluations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    model_version_id: Mapped[int] = mapped_column(ForeignKey("model_versions.id"))
    eval_set: Mapped[str] = mapped_column(String(30))
    eval_type: Mapped[str] = mapped_column(String(20))
    r2_score: Mapped[float | None]
    mae: Mapped[float | None]
    rmse: Mapped[float | None]
    smape_nonzero: Mapped[float | None]
    risk_macro_f1: Mapped[float | None]
    risk_accuracy: Mapped[float | None]
    risk_low_f1: Mapped[float | None]
    risk_medium_f1: Mapped[float | None]
    risk_high_f1: Mapped[float | None]
    n_samples: Mapped[int | None] = mapped_column(Integer)
    notes: Mapped[str | None] = mapped_column(Text)

    model_version: Mapped["ModelVersion"] = relationship(
        "ModelVersion", back_populates="evaluations"
    )


class Prediction(Base):
    # Partitioned parent table — PostgreSQL routes to correct partition.
    __tablename__ = "predictions"
    __table_args__ = {"postgresql_partition_by": "RANGE (iso_year)"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    disease_id: Mapped[int] = mapped_column(ForeignKey("diseases.id"))
    iso3: Mapped[str] = mapped_column(String(3), ForeignKey("countries.iso3"))
    iso_year: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    iso_week: Mapped[int] = mapped_column(SmallInteger)
    horizon_weeks: Mapped[int] = mapped_column(SmallInteger, default=1)
    predicted_value: Mapped[float | None]
    predicted_cases: Mapped[float | None]
    risk_level: Mapped[str | None] = mapped_column(String(10))
    risk_probability: Mapped[float | None]  # P(High) từ classifier — FE × 100 = severity score
    model_version_id: Mapped[int | None] = mapped_column(
        ForeignKey("model_versions.id")
    )
    features_snapshot: Mapped[dict | None] = mapped_column(JSON)
    confidence_lo: Mapped[float | None]
    confidence_hi: Mapped[float | None]

    country: Mapped["Country"] = relationship(  # noqa: F821
        "Country", back_populates="predictions"
    )
    disease: Mapped["Disease"] = relationship(  # noqa: F821
        "Disease", back_populates="predictions"
    )
