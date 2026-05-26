import { useQuery } from "@tanstack/react-query";
import { fetchHistory, fetchPrediction } from "../api/predictions";
import type { DiseaseId } from "../types/domain";

export function usePrediction(
  disease: DiseaseId,
  iso3: string | undefined,
  year: number,
  week: number,
) {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["prediction", disease, iso3, year, week],
    queryFn: () => fetchPrediction(disease, iso3!, year, week),
    enabled: Boolean(iso3),
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });

  return { prediction: data, isLoading, isError, error };
}

export function useHistory(
  disease: DiseaseId,
  iso3: string | undefined,
  startYear: number,
  endYear: number,
) {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["history", disease, iso3, startYear, endYear],
    queryFn: () => fetchHistory(disease, iso3!, startYear, endYear),
    enabled: Boolean(iso3),
    staleTime: 10 * 60 * 1000,
    retry: 1,
  });

  return { history: data, isLoading, isError, error };
}
