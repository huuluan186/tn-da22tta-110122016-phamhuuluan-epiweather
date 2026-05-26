import api from "./axios";
import type { AvailableResponse, ForecastResponse } from "../types/api";

export async function fetchForecast(
  disease: string,
  iso3: string,
  asOfYear: number,
  asOfWeek: number,
): Promise<ForecastResponse> {
  const { data } = await api.get<ForecastResponse>(
    `/forecast/${disease}/${iso3}`,
    { params: { as_of_year: asOfYear, as_of_week: asOfWeek } },
  );
  return data;
}

export async function fetchNowcast(
  disease: string,
  iso3: string,
): Promise<ForecastResponse> {
  const { data } = await api.get<ForecastResponse>(
    `/forecast/${disease}/${iso3}/nowcast`,
  );
  return data;
}

export async function fetchAvailable(disease: string): Promise<AvailableResponse> {
  const { data } = await api.get<AvailableResponse>(`/forecast/${disease}/available`);
  return data;
}
