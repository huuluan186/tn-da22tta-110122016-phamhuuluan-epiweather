import { create } from "zustand";
import type { DiseaseId } from "../types/domain";

// Mỗi disease có "latest available" week khác nhau:
// - flu:    latest 2026-W23 (fallback trước khi API /latest trả về)
// - dengue: nowcast  2023-W36 (OpenDengue v1.3 tới 9/2023)
// Khi API /latest trả về thì year/week được đồng bộ lại qua useEffect ở HomePage.
export const DISEASE_DEFAULTS: Record<DiseaseId, { year: number; week: number }> = {
  flu:    { year: 2026, week: 22 },
  dengue: { year: 2023, week: 36 },
};

interface UIState {
  disease: DiseaseId;
  year: number;
  week: number;
  // Tuần thực tế mới nhất có data — set bởi API /latest, KHÔNG đổi theo picker.
  // Dùng cho TopNav "MỚI NHẤT · Tuần XX" để luôn phản ánh "data mới nhất hiện có".
  latestYear: number | null;
  latestWeek: number | null;
  regions: string[];
  selectedIso3: string | null;
  riskLevels: string[];            // filter map + alerts: empty = show all
  setDisease: (d: DiseaseId) => void;
  setYear: (y: number) => void;
  setWeek: (w: number) => void;
  setLatest: (year: number, week: number) => void;
  toggleRegion: (id: string) => void;
  setSelectedIso3: (iso3: string | null) => void;
  toggleRiskLevel: (level: string) => void;
}

export const useUIStore = create<UIState>((set) => ({
  disease: "flu",
  year:    DISEASE_DEFAULTS.flu.year,
  week:    DISEASE_DEFAULTS.flu.week,
  latestYear: null,
  latestWeek: null,
  regions: [],
  selectedIso3: null,
  riskLevels: [],
  setDisease: (disease) =>
    set({
      disease,
      year:         DISEASE_DEFAULTS[disease].year,
      week:         DISEASE_DEFAULTS[disease].week,
      selectedIso3: null,
    }),
  setYear: (year) => set({ year }),
  setWeek: (week) => set({ week }),
  setLatest: (year, week) => set({ latestYear: year, latestWeek: week }),
  toggleRegion: (id) =>
    set((s) => ({
      regions: s.regions.includes(id) ? s.regions.filter((x) => x !== id) : [...s.regions, id],
    })),
  setSelectedIso3: (selectedIso3) => set({ selectedIso3 }),
  toggleRiskLevel: (level) =>
    set((s) => ({
      riskLevels: s.riskLevels.includes(level)
        ? s.riskLevels.filter((x) => x !== level)
        : [...s.riskLevels, level],
    })),
}));
