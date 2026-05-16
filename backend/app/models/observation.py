from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, JSON, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .geography import Base


class DiseaseCase(Base):
    # Partitioned parent table — PostgreSQL routes to correct partition.
    __tablename__ = "disease_cases"
    __table_args__ = {"postgresql_partition_by": "RANGE (iso_year)"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    disease_id: Mapped[int] = mapped_column(ForeignKey("diseases.id"))
    iso3: Mapped[str] = mapped_column(String(3), ForeignKey("countries.iso3"))
    iso_year: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    iso_week: Mapped[int] = mapped_column(SmallInteger)
    raw_count: Mapped[int | None] = mapped_column(Integer)
    transformed_value: Mapped[float | None]
    data_quality: Mapped[int] = mapped_column(SmallInteger, default=1)

    country: Mapped["Country"] = relationship(  # noqa: F821
        "Country", back_populates="disease_cases"
    )
    disease: Mapped["Disease"] = relationship(  # noqa: F821
        "Disease", back_populates="disease_cases"
    )


class WeatherObservation(Base):
    # Partitioned parent table.
    __tablename__ = "weather_observations"
    __table_args__ = {"postgresql_partition_by": "RANGE (iso_year)"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    iso3: Mapped[str] = mapped_column(String(3), ForeignKey("countries.iso3"))
    source_id: Mapped[int] = mapped_column(Integer, ForeignKey("data_sources.id"))
    iso_year: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    iso_week: Mapped[int] = mapped_column(SmallInteger)
    data: Mapped[dict] = mapped_column(JSON)


class FeatureConfig(Base):
    __tablename__ = "feature_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    disease_id: Mapped[int] = mapped_column(ForeignKey("diseases.id"))
    feature_name: Mapped[str] = mapped_column(String(100))
    source_type: Mapped[str] = mapped_column(String(20))
    weather_variable: Mapped[str | None] = mapped_column(String(50))
    lag_weeks: Mapped[int] = mapped_column(SmallInteger, default=0)
    transform: Mapped[str] = mapped_column(String(20), default="none")
    ar_target: Mapped[str | None] = mapped_column(String(50))
    ar_lag_weeks: Mapped[int | None] = mapped_column(SmallInteger)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    version_tag: Mapped[str | None] = mapped_column(String(30))

    disease: Mapped["Disease"] = relationship(  # noqa: F821
        "Disease", back_populates="feature_configs"
    )
