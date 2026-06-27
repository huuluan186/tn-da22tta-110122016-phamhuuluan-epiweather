from sqlalchemy import BigInteger, SmallInteger, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Country(Base):
    __tablename__ = "countries"

    iso3: Mapped[str] = mapped_column(String(3), primary_key=True)
    iso2: Mapped[str | None] = mapped_column(String(2))
    country_name: Mapped[str] = mapped_column(String(100))
    who_region: Mapped[str | None] = mapped_column(String(10))
    who_region_enc: Mapped[int | None] = mapped_column(SmallInteger)
    latitude: Mapped[float | None]
    longitude: Mapped[float | None]
    population: Mapped[int | None] = mapped_column(BigInteger)

    predictions: Mapped[list["Prediction"]] = relationship(  # noqa: F821
        "Prediction", back_populates="country"
    )
    disease_cases: Mapped[list["DiseaseCase"]] = relationship(  # noqa: F821
        "DiseaseCase", back_populates="country"
    )
