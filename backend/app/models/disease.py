from datetime import date
from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .geography import Base


class DataSource(Base):
    __tablename__ = "data_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(30), unique=True)
    source_type: Mapped[str] = mapped_column(String(20))
    url: Mapped[str | None] = mapped_column(Text)
    update_frequency: Mapped[str | None] = mapped_column(String(20))
    spatial_coverage: Mapped[str | None] = mapped_column(String(50))
    temporal_start: Mapped[date | None]
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    description: Mapped[str | None] = mapped_column(Text)


class WeatherVariable(Base):
    __tablename__ = "weather_variables"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True)
    display_name: Mapped[str | None] = mapped_column(String(100))
    unit: Mapped[str | None] = mapped_column(String(20))
    source_id: Mapped[int | None] = mapped_column(Integer)
    era5_variable: Mapped[str | None] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Disease(Base):
    __tablename__ = "diseases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True)
    display_name: Mapped[str] = mapped_column(String(100))
    target_variable: Mapped[str] = mapped_column(String(50))
    target_transform: Mapped[str] = mapped_column(String(20), default="log1p")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    description: Mapped[str | None] = mapped_column(Text)

    predictions: Mapped[list["Prediction"]] = relationship(  # noqa: F821
        "Prediction", back_populates="disease"
    )
    disease_cases: Mapped[list["DiseaseCase"]] = relationship(  # noqa: F821
        "DiseaseCase", back_populates="disease"
    )
    risk_thresholds: Mapped[list["RiskThreshold"]] = relationship(  # noqa: F821
        "RiskThreshold", back_populates="disease"
    )
    model_versions: Mapped[list["ModelVersion"]] = relationship(  # noqa: F821
        "ModelVersion", back_populates="disease"
    )
    feature_configs: Mapped[list["FeatureConfig"]] = relationship(  # noqa: F821
        "FeatureConfig", back_populates="disease"
    )
