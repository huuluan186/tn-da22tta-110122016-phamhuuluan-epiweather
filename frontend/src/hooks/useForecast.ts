import { useQuery } from "@tanstack/react-query";
import { fetchAvailable, fetchForecast, fetchNowcast } from "../api/forecast";
import type { DiseaseId } from "../types/domain";

export function useForecast(
  disease: DiseaseId,
  iso3: string | undefined,
  asOfYear: number,
  asOfWeek: number,
  options?: { enabled?: boolean },
) {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["forecast", disease, iso3, asOfYear, asOfWeek],
    queryFn: () => fetchForecast(disease, iso3!, asOfYear, asOfWeek),
    enabled: Boolean(iso3) && (options?.enabled ?? true),
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });

  return { forecast: data, isLoading, isError, error };
}

export function useNowcast(
  disease: DiseaseId,
  iso3: string | undefined,
) {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["nowcast", disease, iso3],
    queryFn: () => fetchNowcast(disease, iso3!),
    enabled: Boolean(iso3),
    staleTime: 10 * 60 * 1000,
    retry: 1,
  });

  return { forecast: data, isLoading, isError, error };
}

export function useAvailableCountries(disease: DiseaseId) {
  const { data, isLoading } = useQuery({
    queryKey: ["available", disease],
    queryFn: () => fetchAvailable(disease),
    staleTime: 30 * 60 * 1000,  // 30 phút — danh sách này hiếm khi thay đổi
    retry: 1,
  });

  const availableSet = new Set(data?.countries.map((c) => c.iso3) ?? []);
  return { available: data, availableSet, isLoading };
}
