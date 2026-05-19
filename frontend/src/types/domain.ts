export type DiseaseId = "flu" | "dengue";
export type RiskLevel = "none" | "low" | "medium" | "high" | "critical";

export interface DiseaseDef {
  id: DiseaseId;
  label: string;
  short: string;
  color: string;
}

export interface RiskScore {
  iso3: string;
  score: number;
  risk: RiskLevel;
}
