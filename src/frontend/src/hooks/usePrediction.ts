import { useQuery } from "@tanstack/react-query";
import type { AxiosError } from "axios";
import { fetchHistory, fetchPrediction } from "../api/predictions";
import type { DiseaseId } from "../types/domain";

// Retry lỗi tạm thời (mất kết nối / 5xx khi backend còn warm), KHÔNG retry 4xx
// (404 "không có dự báo tuần này" là kết quả hợp lệ, retry vô nghĩa).
function shouldRetryTransientError(failureCount: number, error: unknown) {
  const status = (error as AxiosError | undefined)?.response?.status;
  if (status && status < 500) return false;
  return failureCount < 2;
}

function retryDelay(attemptIndex: number) {
  return Math.min(500 * 2 ** attemptIndex, 1_500);
}

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
    retry: shouldRetryTransientError,
    retryDelay,
  });

  return { prediction: data, isLoading, isError, error };
}

export function useHistory(
  disease: DiseaseId,
  iso3: string | undefined,
  startYear: number,
  endYear: number,
  limit?: number,
  options?: { enabled?: boolean },
) {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["history", disease, iso3, startYear, endYear, limit],
    queryFn: () => fetchHistory(disease, iso3!, startYear, endYear, limit),
    enabled: Boolean(iso3) && (options?.enabled ?? true),
    staleTime: 10 * 60 * 1000,
    retry: 1,
  });

  return { history: data, isLoading, isError, error };
}
