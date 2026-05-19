import type { DiseaseDef, RiskLevel } from "./types/domain";

export const DISEASES: DiseaseDef[] = [
  { id: "flu", label: "Influenza", short: "FLU", color: "#3b82f6" },
  { id: "dengue", label: "Dengue", short: "DEN", color: "#f59e0b" },
];

export const RISK_LEVELS: Record<RiskLevel, { label: string; color: string }> = {
  none: { label: "No data", color: "#2a3040" },
  low: { label: "LOW", color: "#22c55e" },
  medium: { label: "MEDIUM", color: "#f59e0b" },
  high: { label: "HIGH", color: "#ef4444" },
  critical: { label: "CRITICAL", color: "#dc2626" },
};

export const RISK_ORDER: Record<RiskLevel, number> = {
  critical: 4,
  high: 3,
  medium: 2,
  low: 1,
  none: 0,
};

export const WHO_REGIONS = [
  { id: "AFRO", label: "African Region (AFRO)" },
  { id: "AMRO", label: "Americas (PAHO/AMRO)" },
  { id: "EMRO", label: "Eastern Mediterranean (EMRO)" },
  { id: "EURO", label: "European Region (EURO)" },
  { id: "SEARO", label: "South-East Asia (SEARO)" },
  { id: "WPRO", label: "Western Pacific (WPRO)" },
] as const;
