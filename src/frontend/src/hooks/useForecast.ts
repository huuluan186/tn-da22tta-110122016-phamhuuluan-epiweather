import { useQuery } from "@tanstack/react-query";
import type { AxiosError } from "axios";
import { fetchAvailable, fetchForecast, fetchNowcast } from "../api/forecast";
import type { DiseaseId } from "../types/domain";

function shouldRetryTransientError(failureCount: number, error: unknown) {
  const status = (error as AxiosError | undefined)?.response?.status;
  if (status && status < 500) return false;
  return failureCount < 2;
}

function retryDelay(attemptIndex: number) {
  return Math.min(500 * 2 ** attemptIndex, 1_500);
}

export function useForecast(
  disease: DiseaseId,
  iso3: string | undefined,
  asOfYear: number,
  asOfWeek: number,
  options?: { enabled?: boolean },
) {
  const { data, isLoading, isError, error, isFetching, refetch } = useQuery({
    queryKey: ["forecast", disease, iso3, asOfYear, asOfWeek],
    queryFn: () => fetchForecast(disease, iso3!, asOfYear, asOfWeek),
    enabled: Boolean(iso3) && (options?.enabled ?? true),
    staleTime: 5 * 60 * 1000,
    retry: shouldRetryTransientError,
    retryDelay,
  });

  return { forecast: data, isLoading, isError, error, isFetching, refetch };
}

export function useNowcast(
  disease: DiseaseId,
  iso3: string | undefined,
  options?: { enabled?: boolean },
) {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["nowcast", disease, iso3],
    queryFn: () => fetchNowcast(disease, iso3!),
    enabled: Boolean(iso3) && (options?.enabled ?? true),
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
