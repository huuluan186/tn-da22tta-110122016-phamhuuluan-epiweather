import { useQuery } from "@tanstack/react-query";
import { useMemo } from "react";
import api from "../api/axios";
import type { RiskEntry, RiskMapPeriodsResponse, RiskMapResponse } from "../types/api";
import type { DiseaseId, RiskLevel } from "../types/domain";

// Fallback chỉ dùng khi prediction cũ trong DB chưa có risk_probability (NULL).
// Sau khi batch_predict re-run đầy đủ thì fallback này không bao giờ chạy.
const RISK_SCORE_FALLBACK: Record<string, number> = {
  high: 68,
  medium: 42,
  low: 18,
  none: 5,
};

function toRiskLevel(raw: string | null): RiskLevel {
  const normalized = raw?.toLowerCase() ?? "";
  if (normalized === "high" || normalized === "medium" || normalized === "low") return normalized;
  return "none";
}

function apiItemsToEntries(items: RiskMapResponse["items"]): RiskEntry[] {
  return items.map((item) => {
    const risk = toRiskLevel(item.risk_level);
    const score =
      item.risk_probability != null
        ? Math.round(item.risk_probability * 100)
        : RISK_SCORE_FALLBACK[risk] ?? 5;
    return {
      iso3: item.iso3,
      countryName: item.country_name,
      whoRegion: item.who_region,
      risk,
      score,
      predictedCases: item.predicted_cases,
    };
  });
}

async function fetchRiskMap(
  disease: DiseaseId,
  year: number,
  week: number,
): Promise<RiskMapResponse> {
  const { data } = await api.get<RiskMapResponse>(`/risk-map/${disease}`, {
    params: { year, week },
  });
  return data;
}

async function fetchLatestRiskMap(disease: DiseaseId): Promise<RiskMapResponse> {
  const { data } = await api.get<RiskMapResponse>(`/risk-map/${disease}/latest`);
  return data;
}


async function fetchRiskMapPeriods(disease: DiseaseId): Promise<RiskMapPeriodsResponse> {
  const { data } = await api.get<RiskMapPeriodsResponse>(`/risk-map/${disease}/periods`);
  return data;
}
export function useRiskMap(
  disease: DiseaseId,
  year: number,
  week: number,
  options?: { enabled?: boolean },
) {
  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ["risk-map", disease, year, week],
    queryFn: () => fetchRiskMap(disease, year, week),
    staleTime: 5 * 60 * 1000,
    retry: 1,
    enabled: options?.enabled ?? true,
  });

  const entries = useMemo<RiskEntry[]>(
    () => (data?.items ? apiItemsToEntries(data.items) : []),
    [data],
  );

  const meta = useMemo(
    () => (data ? { year: data.iso_year, week: data.iso_week, count: data.count } : null),
    [data],
  );

  return { entries, meta, isLoading, isError, error, refetch, isFetching };
}

export function useLatestRiskMap(disease: DiseaseId, options?: { enabled?: boolean }) {
  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ["risk-map-latest", disease],
    queryFn: () => fetchLatestRiskMap(disease),
    staleTime: 5 * 60 * 1000,
    retry: 1,
    enabled: options?.enabled ?? true,
  });

  // Memoize entries + meta để reference stable giữa các render
  // (tránh useEffect ở HomePage fire vô tận → infinite loop)
  const entries = useMemo<RiskEntry[]>(
    () => (data?.items ? apiItemsToEntries(data.items) : []),
    [data],
  );

  const meta = useMemo(
    () => (data ? { year: data.iso_year, week: data.iso_week, count: data.count } : null),
    [data],
  );

  return { entries, meta, isLoading, isError, error, refetch, isFetching };
}
export function useRiskMapPeriods(disease: DiseaseId) {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["risk-map-periods", disease],
    queryFn: () => fetchRiskMapPeriods(disease),
    staleTime: 30 * 60 * 1000,
    retry: 1,
  });

  return { periods: data, isLoading, isError, error };
}
