import type { DiseaseDef, DiseaseId, RiskLevel } from "./types/domain";

export const SUPPORTED_DISEASE_IDS: DiseaseId[] = ["flu", "dengue"];

export const DISEASE_PRESENTATION: Record<DiseaseId, Omit<DiseaseDef, "id">> = {
  flu: {
    label: "Cúm mùa",
    short: "CÚM",
    color: "#3b82f6",
    description: "Bệnh hô hấp theo mùa, lây qua giọt bắn và tiếp xúc gần.",
  },
  dengue: {
    label: "Sốt xuất huyết Dengue",
    short: "SXH",
    color: "#f59e0b",
    description: "Bệnh do muỗi truyền, bùng phát mạnh theo mùa mưa và khí hậu nóng ẩm.",
  },
};

export const DISEASES: DiseaseDef[] = SUPPORTED_DISEASE_IDS.map((id) => ({
  id,
  ...DISEASE_PRESENTATION[id],
}));

export const RISK_LEVELS: Record<RiskLevel, { label: string; color: string }> = {
  none: { label: "Không có dữ liệu", color: "#2a3040" },
  low: { label: "THẤP", color: "#22c55e" },
  medium: { label: "TRUNG BÌNH", color: "#f59e0b" },
  high: { label: "CAO", color: "#ef4444" },
};

export const RISK_ORDER: Record<RiskLevel, number> = {
  high: 3,
  medium: 2,
  low: 1,
  none: 0,
};

// WHO region codes — khớp với cột countries.who_region trong DB (AFR/AMR/EMR/EUR/SEAR/WPR)
export const WHO_REGIONS = [
  { id: "AFR",  label: "Châu Phi (AFR)" },
  { id: "AMR",  label: "Châu Mỹ (PAHO/AMR)" },
  { id: "EMR",  label: "Đông Địa Trung Hải (EMR)" },
  { id: "EUR",  label: "Châu Âu (EUR)" },
  { id: "SEAR", label: "Đông Nam Á (SEAR)" },
  { id: "WPR",  label: "Tây Thái Bình Dương (WPR)" },
] as const;
