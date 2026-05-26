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

export interface FeatureImportance {
  disease: string;
  horizon: number;
  features: string[];
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
