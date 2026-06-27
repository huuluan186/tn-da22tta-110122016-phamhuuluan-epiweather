import { useMemo } from "react";
import { WHO_REGIONS } from "../../constants";
import type { RiskEntry } from "../../types/api";

const RISK_PILLS = [
  { id: "high",   label: "Cao",    activeClass: "bg-[#7f1d1d] border-[#f87171] text-white" },
  { id: "medium", label: "TB",     activeClass: "bg-[#854d0e] border-[#fbbf24] text-white" },
  { id: "low",    label: "Thấp",   activeClass: "bg-[#166534] border-[#4ade80] text-white" },
] as const;

interface Props {
  value: string[];
  onToggle: (id: string) => void;
  entries: RiskEntry[];
  riskLevels: string[];
  onToggleRiskLevel: (level: string) => void;
}

export default function RegionFilter({
  value,
  onToggle,
  entries,
  riskLevels,
  onToggleRiskLevel,
}: Props) {
  // Không chọn gì hoặc chọn hết = tổng số quốc gia có báo cáo; chọn 1-2 level = tổng của các level đó
  const counts = useMemo(() => {
    const out: Record<string, number> = {};
    WHO_REGIONS.forEach((r) => (out[r.id] = 0));
    entries.forEach((e) => {
      if (!e.whoRegion || out[e.whoRegion] === undefined) return;
      if (riskLevels.length === 0 || riskLevels.includes(e.risk ?? "")) {
        out[e.whoRegion]++;
      }
    });
    return out;
  }, [entries, riskLevels]);

  return (
    <div className="flex flex-col gap-0.5">
      {/* Risk level multi-select pills */}
      <div className="flex items-center gap-1 mb-2 flex-wrap">
        {RISK_PILLS.map((pill) => {
          const active = riskLevels.includes(pill.id);
          return (
            <button
              key={pill.id}
              onClick={() => onToggleRiskLevel(pill.id)}
              className={`text-[10px] px-2 py-0.5 rounded border font-semibold transition-colors ${
                active
                  ? pill.activeClass
                  : "bg-[var(--color-panel-inset)] border-[var(--color-panel-border)] text-slate-100 hover:text-white hover:border-white"
              }`}
              title={active ? `Bỏ lọc mức ${pill.label}` : `Lọc mức ${pill.label}`}
            >
              {active ? "● " : "○ "}{pill.label}
            </button>
          );
        })}
        {riskLevels.length > 0 && (
          <button
            onClick={() => riskLevels.forEach((l) => onToggleRiskLevel(l))}
            className="text-[10px] px-1.5 py-0.5 rounded border border-[var(--color-panel-border)] bg-[var(--color-panel-inset)] text-slate-100 hover:text-white hover:border-white transition-colors"
            title="Xóa tất cả bộ lọc mức độ"
          >
            ✕
          </button>
        )}
      </div>
      {WHO_REGIONS.map((r) => {
        const on = value.includes(r.id);
        return (
          <div
            key={r.id}
            onClick={() => onToggle(r.id)}
            className={`flex items-center gap-2 px-1 py-1.5 cursor-pointer rounded text-xs select-none ${
              on
                ? "bg-[#245b8f] text-white font-semibold"
                : "text-slate-100 hover:text-white hover:bg-[var(--color-panel-raised)]"
            }`}
          >
            <div
              className={`w-3.5 h-3.5 border-[1.5px] rounded-[3px] grid place-items-center shrink-0 transition-colors ${
                on
                  ? "bg-[#2563eb] border-[#93c5fd]"
                  : "bg-[var(--color-panel-inset)] border-[var(--color-panel-border)]"
              }`}
            >
              {on && (
                <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M20 6 9 17l-5-5" />
                </svg>
              )}
            </div>
            <span>{r.label}</span>
            <span
              className={`ml-auto text-[11px] tabular-nums ${on ? "text-white font-bold" : "text-slate-100"}`}
              title={`${counts[r.id] ?? 0} quốc gia trong vùng ${r.label}`}
            >
              {counts[r.id] ?? 0}
            </span>
          </div>
        );
      })}
    </div>
  );
}
