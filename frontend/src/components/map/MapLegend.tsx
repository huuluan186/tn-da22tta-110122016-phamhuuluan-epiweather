import { RISK_LEVELS } from "../../constants";
import { resolveMapThemePalette, type MapTheme } from "./mapTheme";

interface Props {
  theme: MapTheme;
}

export default function MapLegend({ theme }: Props) {
  const palette = resolveMapThemePalette(theme);
  const items = (["high", "medium", "low", "none"] as const).map(
    (k) => ({ key: k, ...RISK_LEVELS[k] }),
  );
  return (
    <div
      className="absolute bottom-4 left-5 flex gap-3.5 items-center px-3 py-2 rounded-lg text-[11px] z-[3] shadow-sm"
      style={{ background: palette.surface, border: `1px solid ${palette.surfaceBorder}` }}
    >
      <span className="text-[10px] font-bold uppercase" style={{ color: palette.mutedText }}>
        Mức độ
      </span>
      {items.map((r) => (
        <div key={r.label} className="flex items-center gap-1.5" style={{ color: palette.tooltipText }}>
          <div className="w-3.5 h-3.5 rounded-[3px]" style={{ background: palette.riskColors[r.key] }} />
          {r.label}
        </div>
      ))}
    </div>
  );
}
