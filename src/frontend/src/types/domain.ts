export type DiseaseId = "flu" | "dengue";
export type RiskLevel = "none" | "low" | "medium" | "high";

export interface DiseaseDef {
  id: DiseaseId;
  label: string;
  color: string;
  description: string;
}

export interface RiskScore {
  iso3: string;
  score: number;
  risk: RiskLevel;
}
