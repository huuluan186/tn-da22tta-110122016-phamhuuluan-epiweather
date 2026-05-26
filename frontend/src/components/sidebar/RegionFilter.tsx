import { useMemo } from "react";
import { WHO_REGIONS } from "../../constants";
import type { RiskEntry } from "../../types/api";

const RISK_PILLS = [
  { id: "high",   label: "Cao",    activeClass: "bg-[var(--color-risk-high)]/15 border-[var(--color-risk-high)]/50 text-[var(--color-risk-high)]" },
  { id: "medium", label: "TB",     activeClass: "bg-amber-500/15 border-amber-500/50 text-amber-300" },
  { id: "low",    label: "Thấp",   activeClass: "bg-emerald-500/15 border-emerald-500/50 text-emerald-300" },
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
                  : "bg-[var(--color-surface-2)] border-[var(--color-border)] text-[var(--color-text-3)] hover:text-[var(--color-text-1)]"
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
            className="text-[10px] px-1.5 py-0.5 rounded border border-[var(--color-border)] bg-[var(--color-surface-2)] text-[var(--color-text-3)] hover:text-[var(--color-text-1)] transition-colors"
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
            <span
              className="ml-auto text-[11px] tabular-nums text-[var(--color-text-2)]"
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
