import { useQuery } from "@tanstack/react-query";
import api from "../api/axios";
import type { DiseaseId } from "../types/domain";

export interface HorizonMetric {
  horizon: number;
  r2: number;
  rmse: number;
  mae: number;
  cv_folds: number;
  training_period: string;
}

export interface ModelPerformance {
  disease: string;
  model_type: string;
  horizons: HorizonMetric[];
}

export interface FeatureMetadata {
  feature: string;
  display_name_vi: string | null;
  description_vi: string | null;
  source_type: string | null;
  pearson_r?: number | null;
}

export interface TrainingCoverageYear {
  year: number;
  observations: number;
  n_countries: number;
}

export interface TrainingCoverage {
  disease: string;
  year_start: number;
  year_end: number;
  n_years: number;
  n_countries: number;
  total_observations: number;
  avg_weeks_per_country_year: number;
  per_year: TrainingCoverageYear[];
}

export interface FeatureImportanceItem extends FeatureMetadata {
  importance: number;
}

export interface FeatureImportance {
  disease: string;
  horizon: number;
  features: string[];
  feature_metadata?: FeatureMetadata[];
  importance: FeatureImportanceItem[];
  target: string;
  model_type: string;
  training_date: string;
}

export function useModelPerformance(disease: DiseaseId) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["model-performance", disease],
    queryFn: async () =>
      (await api.get<ModelPerformance>(`/analytics/model-performance/${disease}`)).data,
    staleTime: 30 * 60 * 1000,
    retry: 1,
  });
  return { performance: data, isLoading, isError };
}

export function useTrainingCoverage(disease: DiseaseId) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["training-coverage", disease],
    queryFn: async () =>
      (await api.get<TrainingCoverage>(`/analytics/training-coverage/${disease}`)).data,
    staleTime: 30 * 60 * 1000,
    retry: 1,
  });
  return { coverage: data, isLoading, isError };
}

export function useFeatureImportance(disease: DiseaseId, horizon = 1) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["feature-importance", disease, horizon],
    queryFn: async () =>
      (await api.get<FeatureImportance>(`/analytics/feature-importance/${disease}`, {
        params: { horizon },
      })).data,
    staleTime: 30 * 60 * 1000,
    retry: 1,
  });
  return { importance: data, isLoading, isError };
}

// ── Feature Signals (dynamic per country × week) ────────────────────────────

export interface FeatureSignalItem {
  feature: string;
  value: number | null;
  importance: number;
  pearson_r: number | null;
  direction: "up" | "down" | "neutral";
  display_name_vi: string | null;
  description_vi: string | null;
  source_type: string | null;
}

export interface FeatureSignalsResponse {
  disease: string;
  iso3: string;
  iso_year: number;
  iso_week: number;
  signals: FeatureSignalItem[];
}

export function useFeatureSignals(
  disease: DiseaseId,
  iso3: string | undefined,
  year: number,
  week: number,
) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["feature-signals", disease, iso3, year, week],
    queryFn: async () =>
      (
        await api.get<FeatureSignalsResponse>(
          `/analytics/feature-signals/${disease}/${iso3}`,
          { params: { year, week } },
        )
      ).data,
    enabled: !!iso3,
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });
  return { signals: data, isLoading, isError };
}
