import { useMemo } from "react";
import { DISEASES } from "../../constants";
import { useAvailableCountries } from "../../hooks/useForecast";
import type { RiskEntry } from "../../types/api";
import type { DiseaseId } from "../../types/domain";
import Icon from "../common/Icon";

interface Props {
  disease: DiseaseId;
  week: number;
  entries: RiskEntry[];
}

export default function SummaryStats({ disease, week, entries }: Props) {
  const d = DISEASES.find((x) => x.id === disease)!;
  const { available } = useAvailableCountries(disease);
  const totalCoverage = available?.total_countries ?? null;

  const stats = useMemo(() => {
    let reporting = 0,
      high = 0,
      totalScore = 0;
    entries.forEach((e) => {
      if (e.risk !== "none") {
        reporting++;
        totalScore += e.score;
      }
      if (e.risk === "high") high++;
    });
    return {
      reporting,
      high,
      avgScore: reporting ? (totalScore / reporting).toFixed(1) : "—",
    };
  }, [entries]);

  return (
    <div className="grid grid-cols-2 gap-2">
      <div className="p-2.5 bg-[var(--color-surface-2)] border border-[var(--color-border-soft)] rounded-md">
        <div className="text-[10px] uppercase text-[var(--color-text-3)] mb-1">Đang báo cáo</div>
        <div className="text-lg font-semibold">{stats.reporting}</div>
        <div
          className="text-[11px] mt-0.5 text-[var(--color-text-3)] tabular-nums"
          title={`${d.label} hiện cover ${totalCoverage ?? "—"} quốc gia (toàn bộ dataset, không đổi theo filter)`}
        >
          / {totalCoverage ?? "—"} nước có dữ liệu {d.label.toLowerCase()}
        </div>
      </div>

      <div className="p-2.5 bg-[var(--color-surface-2)] border border-[var(--color-border-soft)] rounded-md">
        <div className="text-[10px] uppercase text-[var(--color-text-3)] mb-1">Rủi ro cao</div>
        <div className="text-lg font-semibold text-[var(--color-risk-high)]">{stats.high}</div>
        <div className="inline-flex items-center gap-1 mt-0.5 text-[11px] font-medium tabular-nums text-[var(--color-text-3)]">
          <Icon name="arrow-up" size={10} />
          Tuần {week}
        </div>
      </div>

      <div className="col-span-2 p-2.5 bg-[var(--color-surface-2)] border border-[var(--color-border-soft)] rounded-md">
        <div className="text-[10px] uppercase text-[var(--color-text-3)] mb-1">Phần trăm xảy ra trung bình</div>
        <div className="flex items-baseline gap-2">
          <div className="text-lg font-semibold" style={{ color: d.color }}>
            {stats.avgScore}
          </div>
          <div className="text-[11px] text-[var(--color-text-3)]">%</div>
        </div>
      </div>
    </div>
  );
}
