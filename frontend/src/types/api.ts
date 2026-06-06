import type { RiskLevel } from "./domain";

export interface RiskMapItem {
  iso3: string;
  country_name: string;
  latitude: number | null;
  longitude: number | null;
  who_region: string | null;
  predicted_cases: number | null;
  risk_level: string | null;
  risk_probability: number | null;   // P(High) 0..1, UI hiển thị dưới dạng %
}

export interface RiskMapResponse {
  disease: string;
  iso_year: number;
  iso_week: number;
  count: number;
  items: RiskMapItem[];
}

// Dạng dữ liệu đã chuẩn hóa cho các component UI
export interface RiskEntry {
  iso3: string;
  countryName: string;
  whoRegion: string | null;
  risk: RiskLevel;
  score: number;
  predictedCases: number | null;
}

export interface PredictionPoint {
  iso3: string;
  iso_year: number;
  iso_week: number;
  predicted_value: number | null;
  predicted_cases: number | null;
  risk_level: string | null;
  risk_q33: number | null;
  risk_q67: number | null;
  confidence_lo: number | null;
  confidence_hi: number | null;
}

export interface HistoryPoint {
  iso_year: number;
  iso_week: number;
  predicted_cases: number | null;
  actual_cases: number | null;
  risk_level: string | null;
}

export interface HistoryResponse {
  disease: string;
  iso3: string;
  points: HistoryPoint[];
}

// Multi-horizon forecast (SESSION 8 multi-horizon models)
export interface ForecastPoint {
  horizon: number;                // 1, 2, 3, 4
  target_iso_year: number;
  target_iso_week: number;
  predicted_log: number;
  predicted_cases: number;
  r2_cv: number | null;
  rmse_cv: number | null;
  model_version: string;
}

export interface DataCoverage {
  in_training_period: boolean;    // true = năm này trong 2010-2019
  snapshot_years: number[];       // các năm có feature snapshot
  training_years: number[];       // năm có disease_cases thực (2010-2019)
  warning: string | null;         // null = OK, string = cảnh báo extrapolation
}

export interface ForecastResponse {
  disease: string;
  iso3: string;
  as_of_iso_year: number;
  as_of_iso_week: number;
  points: ForecastPoint[];        // 4 points h=1..4
  data_coverage: DataCoverage | null;
}

export interface AvailableCountry {
  iso3: string;
  country_name: string | null;
  snapshot_years: number[];
  latest_year: number;
  latest_week: number;
  in_training_period: boolean;
}

export interface AvailableResponse {
  disease: string;
  total_countries: number;
  countries: AvailableCountry[];
}
