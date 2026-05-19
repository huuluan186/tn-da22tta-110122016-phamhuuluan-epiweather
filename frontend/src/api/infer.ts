import api from "./axios";

export interface InferRequest {
  disease: "flu" | "dengue";
  iso3: string;
  features: Record<string, number>;
}

export interface InferResponse {
  disease: string;
  iso3: string;
  risk_level: "Low" | "Medium" | "High";
  p_low: number;
  p_med: number;
  p_high: number;
  predicted_cases: number;
  predicted_log: number;
}

export async function runInference(payload: InferRequest): Promise<InferResponse> {
  const { data } = await api.post<InferResponse>("/infer", payload);
  return data;
}
