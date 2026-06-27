import api from "./axios";

export interface DiseaseMetrics {
  model_type: string;
  r2_cv: number;
  rmse_cv: number;
  mae_cv: number;
  cv_folds: number;
}

export interface DiseaseListItem {
  id: number;
  code: string;
  display_name: string;
  display_name_vi?: string | null;
  target_variable: string;
  target_transform: string;
  description?: string | null;
  description_vi?: string | null;
}

export async function fetchDiseases(): Promise<DiseaseListItem[]> {
  const { data } = await api.get<DiseaseListItem[]>("/diseases");
  return data;
}

export async function fetchDiseaseMetrics(disease: string): Promise<DiseaseMetrics> {
  const { data } = await api.get<DiseaseMetrics>(`/diseases/${disease}/metrics`);
  return data;
}
