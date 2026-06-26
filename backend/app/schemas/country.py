from pydantic import BaseModel


class Country(BaseModel):
    iso3: str
    iso2: str | None
    country_name: str
    who_region: str | None
    latitude: float | None
    longitude: float | None
    population: int | None


class CountryDetail(Country):
    iso2: str | None
    who_region_enc: int | None
