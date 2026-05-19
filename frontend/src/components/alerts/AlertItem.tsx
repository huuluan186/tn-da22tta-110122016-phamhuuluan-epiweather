import { DISEASES, RISK_LEVELS } from "../../constants";
import { mockRiskScore } from "../../lib/mockRisk";
import type { DiseaseId } from "../../types/domain";
import Sparkline from "./Sparkline";

export interface AlertCountry {
  iso3: string;
  iso2: string;
  name: string;
  region: string;
  disease: DiseaseId;
  timeAgo: string;
}

interface Props {
  item: AlertCountry;
  week: number;
}

export default function AlertItem({ item, week }: Props) {
  const p = mockRiskScore(item.iso3, item.disease, week);
  const pp = mockRiskScore(item.iso3, item.disease, week - 1);
  const delta = p.score - pp.score;
  const d = DISEASES.find((x) => x.id === item.disease)!;
  const trend = Array.from({ length: 8 }, (_, i) =>
    mockRiskScore(item.iso3, item.disease, week - 7 + i).score,
  );

  return (
    <div className="px-4 py-3 border-b border-[var(--color-border-soft)] cursor-pointer hover:bg-[var(--color-surface-2)]">
      <div className="flex items-center gap-2">
        <div className="w-5 h-3.5 rounded-[2px] bg-[var(--color-surface-3)] grid place-items-center text-[9px] font-semibold tracking-wider text-[var(--color-text-3)] shrink-0">
          {item.iso2}
        </div>
        <div>
          <div className="font-semibold text-[13px]">{item.name}</div>
          <div className="text-[11px] text-[var(--color-text-3)]">{item.region}</div>
        </div>
        <div className="ml-auto text-[10px] text-[var(--color-text-3)]">{item.timeAgo}</div>
      </div>

      <div className="mt-2 flex items-center gap-2">
        <span
          className="inline-flex items-center gap-1.5 text-[10px] font-semibold px-1.5 py-0.5 rounded-[3px]"
          style={{ background: d.color + "22", color: d.color }}
        >
          <span className="w-1.5 h-1.5 rounded-full" style={{ background: d.color }} />
          {d.short}
        </span>
        <span
          className="text-[10px] font-bold px-1.5 py-0.5 rounded-[3px] text-white"
          style={{ background: RISK_LEVELS[p.risk].color }}
        >
          {RISK_LEVELS[p.risk].label}
        </span>
        <Sparkline data={trend} color={d.color} />
      </div>

      <div className="mt-1.5 flex justify-between text-[11px] text-[var(--color-text-2)] tabular-nums">
        <span>
          Score <strong className="text-[var(--color-text-1)]">{p.score}</strong>/100
        </span>
        <span
          className={`font-semibold ${
            delta > 0 ? "text-[var(--color-risk-high)]" : "text-[var(--color-risk-low)]"
          }`}
        >
          {delta >= 0 ? "+" : ""}
          {delta} vs last week
        </span>
      </div>
    </div>
  );
}
