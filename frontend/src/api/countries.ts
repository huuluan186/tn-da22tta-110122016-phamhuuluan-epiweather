import api from "./axios";

export interface Country {
  id: number;
  iso3: string;
  iso2: string | null;
  country_name: string;
  who_region: string | null;
  latitude: number | null;
  longitude: number | null;
}

export async function fetchCountries(): Promise<Country[]> {
  const { data } = await api.get<Country[]>("/countries");
  return data;
}

export async function fetchCountry(iso3: string): Promise<Country> {
  const { data } = await api.get<Country>(`/countries/${iso3}`);
  return data;
}
