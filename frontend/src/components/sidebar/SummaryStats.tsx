import { useMemo } from "react";
import { DISEASES } from "../../constants";
import { ALL_ISO3, mockRiskScore } from "../../lib/mockRisk";
import type { DiseaseId } from "../../types/domain";
import Icon from "../common/Icon";

interface Props {
  disease: DiseaseId;
  week: number;
}

export default function SummaryStats({ disease, week }: Props) {
  const d = DISEASES.find((x) => x.id === disease)!;

  const stats = useMemo(() => {
    let reporting = 0,
      high = 0,
      totalScore = 0,
      prevHigh = 0;
    ALL_ISO3.forEach((iso3) => {
      const p = mockRiskScore(iso3, disease, week);
      const pp = mockRiskScore(iso3, disease, week - 1);
      if (p.risk !== "none") {
        reporting++;
        totalScore += p.score;
      }
      if (p.risk === "high" || p.risk === "critical") high++;
      if (pp.risk === "high" || pp.risk === "critical") prevHigh++;
    });
    return {
      reporting,
      high,
      highDelta: high - prevHigh,
      avgScore: reporting ? (totalScore / reporting).toFixed(1) : "—",
    };
  }, [disease, week]);

  const deltaClass =
    stats.highDelta > 0
      ? "text-[var(--color-risk-high)]"
      : stats.highDelta < 0
      ? "text-[var(--color-risk-low)]"
      : "text-[var(--color-text-3)]";

  return (
    <div className="grid grid-cols-2 gap-2">
      <div className="p-2.5 bg-[var(--color-surface-2)] border border-[var(--color-border-soft)] rounded-md">
        <div className="text-[10px] uppercase text-[var(--color-text-3)] mb-1">Reporting</div>
        <div className="text-lg font-semibold">{stats.reporting}</div>
        <div className="text-[11px] mt-0.5 text-[var(--color-text-3)] tabular-nums">
          of {ALL_ISO3.length} countries
        </div>
      </div>

      <div className="p-2.5 bg-[var(--color-surface-2)] border border-[var(--color-border-soft)] rounded-md">
        <div className="text-[10px] uppercase text-[var(--color-text-3)] mb-1">High / Critical</div>
        <div className="text-lg font-semibold text-[var(--color-risk-high)]">{stats.high}</div>
        <div className={`inline-flex items-center gap-1 mt-0.5 text-[11px] font-medium tabular-nums ${deltaClass}`}>
          <Icon name={stats.highDelta >= 0 ? "arrow-up" : "arrow-down"} size={10} />
          {stats.highDelta >= 0 ? "+" : ""}
          {stats.highDelta} vs W{week - 1}
        </div>
      </div>

      <div className="col-span-2 p-2.5 bg-[var(--color-surface-2)] border border-[var(--color-border-soft)] rounded-md">
        <div className="text-[10px] uppercase text-[var(--color-text-3)] mb-1">Avg Risk Index</div>
        <div className="flex items-baseline gap-2">
          <div className="text-lg font-semibold" style={{ color: d.color }}>
            {stats.avgScore}
          </div>
          <div className="text-[11px] text-[var(--color-text-3)]">/ 100</div>
        </div>
      </div>
    </div>
  );
}
