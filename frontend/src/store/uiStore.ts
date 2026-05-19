import { create } from "zustand";
import type { DiseaseId } from "../types/domain";

interface UIState {
  disease: DiseaseId;
  year: number;
  week: number;
  regions: string[];
  setDisease: (d: DiseaseId) => void;
  setYear: (y: number) => void;
  setWeek: (w: number) => void;
  toggleRegion: (id: string) => void;
}

export const useUIStore = create<UIState>((set) => ({
  disease: "flu",
  year: 2026,
  week: 19,
  regions: [],
  setDisease: (disease) => set({ disease }),
  setYear: (year) => set({ year }),
  setWeek: (week) => set({ week }),
  toggleRegion: (id) =>
    set((s) => ({
      regions: s.regions.includes(id) ? s.regions.filter((x) => x !== id) : [...s.regions, id],
    })),
}));
