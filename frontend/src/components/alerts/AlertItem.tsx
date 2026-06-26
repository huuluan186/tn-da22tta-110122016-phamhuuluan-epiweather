import { RISK_LEVELS } from "../../constants";
import { useDiseases } from "../../hooks/useDiseases";
import type { DiseaseId } from "../../types/domain";

export interface AlertCountry {
  iso3: string;
  iso2: string | null;
  name: string;
  region: string;
  disease: DiseaseId;
  timeAgo: string;
  risk: keyof typeof RISK_LEVELS;
  score: number;
  predictedCases: number | null;
}

interface Props {
  item: AlertCountry;
  isSelected?: boolean;
  onSelect?: (iso3: string) => void;
}

export default function AlertItem({ item, isSelected, onSelect }: Props) {
  const { getDisease } = useDiseases();
  const d = getDisease(item.disease);
  const countryCode = item.iso2 ?? item.iso3;
  const countryCodeTitle = item.iso2 ? `Mã ISO2: ${item.iso2}` : `Mã ISO3: ${item.iso3}`;

  return (
    <div
      className={`px-4 py-3 border-b border-[var(--color-panel-border)] border-l-2 cursor-pointer transition-colors hover:bg-[var(--color-panel-raised)] ${
        isSelected ? "bg-[var(--color-focus-raised)] border-l-[var(--color-focus-accent)]" : "border-l-transparent"
      }`}
      onClick={() => onSelect?.(item.iso3)}
    >
      <div className="flex items-center gap-2">
        <div
          className="h-6 min-w-8 px-1.5 rounded-md border border-[var(--color-focus-border)] bg-[var(--color-focus-raised)] grid place-items-center text-[10px] font-bold tracking-[0.1em] text-white shrink-0"
          title={countryCodeTitle}
        >
          {countryCode}
        </div>
        <div className="min-w-0">
          <div className="font-bold text-white text-[13px]">{item.name}</div>
          <div className="text-[11px] text-slate-100">{item.region}</div>
        </div>
        {item.timeAgo && (
          <div className="ml-auto text-[10px] text-[var(--color-text-3)]">{item.timeAgo}</div>
        )}
      </div>

      <div className="mt-2 flex items-center gap-2">
        <span
          className="inline-flex items-center gap-1.5 text-[10px] font-semibold px-1.5 py-0.5 rounded-[3px]"
          style={{ background: d.color + "22", color: d.color }}
        >
          <span className="w-1.5 h-1.5 rounded-full" style={{ background: d.color }} />
          {d.label}
        </span>
        <span
          className="inline-flex items-center gap-1.5 text-[10px] font-bold px-1.5 py-0.5 rounded-[3px] text-white"
          style={{ background: RISK_LEVELS[item.risk].color }}
          title="Phần trăm xảy ra (0-100), tính từ xác suất P(High) của model phân loại"
        >
          {RISK_LEVELS[item.risk].label}
          <span className="px-1.5 py-0.5 rounded-[3px] bg-black/20">{item.score}%</span>
        </span>
      </div>

      <div className="mt-1.5 flex justify-between text-[11px] font-medium text-slate-100 tabular-nums">
        <span title="Số ca dự báo cho tuần này (từ model hồi quy)">
          {item.predictedCases !== null
            ? `Dự báo ${Math.round(item.predictedCases).toLocaleString()} ca`
            : "Dự báo —"}
        </span>
      </div>
    </div>
  );
}
