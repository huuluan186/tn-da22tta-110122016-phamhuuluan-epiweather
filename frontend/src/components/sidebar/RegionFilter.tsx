import { useMemo } from "react";
import { WHO_REGIONS } from "../../constants";
import { ALL_ISO3, getCountryRegion, mockRiskScore } from "../../lib/mockRisk";
import type { DiseaseId } from "../../types/domain";

interface Props {
  value: string[];
  onToggle: (id: string) => void;
  disease: DiseaseId;
  week: number;
}

export default function RegionFilter({ value, onToggle, disease, week }: Props) {
  const counts = useMemo(() => {
    const out: Record<string, number> = {};
    WHO_REGIONS.forEach((r) => (out[r.id] = 0));
    ALL_ISO3.forEach((iso3) => {
      const r = mockRiskScore(iso3, disease, week);
      const region = getCountryRegion(iso3);
      if (r.risk === "high" || r.risk === "critical") {
        out[region] = (out[region] ?? 0) + 1;
      }
    });
    return out;
  }, [disease, week]);

  return (
    <div className="flex flex-col gap-0.5">
      {WHO_REGIONS.map((r) => {
        const on = value.includes(r.id);
        return (
          <div
            key={r.id}
            onClick={() => onToggle(r.id)}
            className={`flex items-center gap-2 px-1 py-1.5 cursor-pointer rounded text-xs select-none ${
              on
                ? "text-[var(--color-text-1)]"
                : "text-[var(--color-text-2)] hover:text-[var(--color-text-1)] hover:bg-[var(--color-surface-3)]"
            }`}
          >
            <div
              className={`w-3.5 h-3.5 border-[1.5px] rounded-[3px] grid place-items-center shrink-0 transition-colors ${
                on
                  ? "bg-[#3b82f6] border-[#3b82f6]"
                  : "bg-[var(--color-surface-2)] border-[var(--color-border)]"
              }`}
            >
              {on && (
                <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M20 6 9 17l-5-5" />
                </svg>
              )}
            </div>
            <span>{r.label}</span>
            <span className="ml-auto text-[11px] text-[var(--color-text-3)] tabular-nums">
              {counts[r.id] ?? 0}
            </span>
          </div>
        );
      })}
    </div>
  );
}
