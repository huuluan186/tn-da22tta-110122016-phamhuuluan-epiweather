import api from "./axios";
import type { HistoryResponse, PredictionPoint } from "../types/api";

export async function fetchPrediction(
  disease: string,
  iso3: string,
  year: number,
  week: number,
): Promise<PredictionPoint> {
  const { data } = await api.get<PredictionPoint>(`/predictions/${disease}/${iso3}`, {
    params: { year, week },
  });
  return data;
}

export async function fetchHistory(
  disease: string,
  iso3: string,
  startYear: number,
  endYear: number,
): Promise<HistoryResponse> {
  const { data } = await api.get<HistoryResponse>(`/predictions/${disease}/${iso3}/history`, {
    params: { start_year: startYear, end_year: endYear },
  });
  return data;
}
