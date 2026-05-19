import { RISK_LEVELS } from "../../constants";

export default function MapLegend() {
  const items = (["critical", "high", "medium", "low", "none"] as const).map(
    (k) => RISK_LEVELS[k],
  );
  return (
    <div className="absolute bottom-4 left-5 flex gap-3.5 items-center px-3 py-2 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg text-[11px] z-[3]">
      <span className="text-[10px] font-semibold uppercase text-[var(--color-text-3)]">Risk</span>
      {items.map((r) => (
        <div key={r.label} className="flex items-center gap-1.5 text-[var(--color-text-2)]">
          <div className="w-3.5 h-3.5 rounded-[3px]" style={{ background: r.color }} />
          {r.label}
        </div>
      ))}
    </div>
  );
}
