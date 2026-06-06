import type { DiseaseDef, RiskLevel } from "./types/domain";

export const DISEASES: DiseaseDef[] = [
  {
    id: "flu",
    label: "Influenza",
    short: "FLU",
    color: "#3b82f6",
    description: "Bệnh hô hấp theo mùa, lây qua giọt bắn và tiếp xúc gần.",
  },
  {
    id: "dengue",
    label: "Dengue",
    short: "DEN",
    color: "#f59e0b",
    description: "Bệnh do muỗi truyền, bùng phát mạnh theo mùa mưa và khí hậu nóng ẩm.",
  },
];

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
