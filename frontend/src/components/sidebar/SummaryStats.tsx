import { useMemo } from "react";
import { useDiseases } from "../../hooks/useDiseases";
import { useAvailableCountries } from "../../hooks/useForecast";
import type { RiskEntry } from "../../types/api";
import type { DiseaseId } from "../../types/domain";
import Icon from "../common/Icon";

interface Props {
  disease: DiseaseId;
  year: number;
  week: number;
  entries: RiskEntry[];
}

function formatNumber(value: number): string {
  return Math.round(value).toLocaleString();
}

export default function SummaryStats({ disease, year, week, entries }: Props) {
  const { getDisease } = useDiseases();
  const d = getDisease(disease);
  const { available } = useAvailableCountries(disease);
  const totalCoverage = available?.total_countries ?? null;

  const stats = useMemo(() => {
    let reporting = 0,
      high = 0,
      totalScore = 0,
      totalCases = 0;
    entries.forEach((e) => {
      if (e.risk !== "none") {
        reporting++;
        totalScore += e.score;
        totalCases += e.predictedCases ?? 0;
      }
      if (e.risk === "high") high++;
    });
    return {
      reporting,
      high,
      totalCases,
      avgScore: reporting ? (totalScore / reporting).toFixed(1) : "—",
      coveragePercent:
        totalCoverage && totalCoverage > 0 ? Math.round((reporting / totalCoverage) * 100) : null,
    };
  }, [entries, totalCoverage]);

  return (
    <div className="grid grid-cols-2 gap-2">
      <div className="p-2.5 bg-[var(--color-surface-2)] border border-[var(--color-border-soft)] rounded-md">
        <div className="text-[10px] uppercase text-[var(--color-text-3)] mb-1">Quốc gia có API</div>
        <div className="text-lg font-semibold">{stats.reporting}</div>
        <div
          className="text-[11px] mt-0.5 text-[var(--color-text-3)] tabular-nums"
          title={`${d.label} hiện cover ${totalCoverage ?? "—"} quốc gia (toàn bộ dataset, không đổi theo filter)`}
        >
          / {totalCoverage ?? "—"} nước · {stats.coveragePercent ?? "—"}%
        </div>
      </div>

      <div className="p-2.5 bg-[var(--color-surface-2)] border border-[var(--color-border-soft)] rounded-md">
        <div className="text-[10px] uppercase text-[var(--color-text-3)] mb-1">Rủi ro cao</div>
        <div className="text-lg font-semibold text-[var(--color-risk-high)]">{stats.high}</div>
        <div className="inline-flex items-center gap-1 mt-0.5 text-[11px] font-medium tabular-nums text-[var(--color-text-3)]">
          <Icon name="arrow-up" size={10} />
          Tuần {String(week).padStart(2, "0")} · Năm {year}
        </div>
      </div>

      <div className="col-span-2 p-2.5 bg-[var(--color-surface-2)] border border-[var(--color-border-soft)] rounded-md">
        <div className="text-[10px] uppercase text-[var(--color-text-3)] mb-1">Số ca dự báo</div>
        <div className="text-lg font-semibold tabular-nums">{formatNumber(stats.totalCases)}</div>
        <div className="text-[11px] mt-0.5 text-[var(--color-text-3)]">
          Tổng từ API risk-map
        </div>
      </div>

      <div className="col-span-2 p-2.5 bg-[var(--color-surface-2)] border border-[var(--color-border-soft)] rounded-md">
        <div className="text-[10px] uppercase text-[var(--color-text-3)] mb-1">Xác suất rủi ro cao TB</div>
        <div className="flex items-baseline gap-2">
          <div className="text-lg font-semibold" style={{ color: d.color }}>
            {stats.avgScore}
          </div>
          <div className="text-[11px] text-[var(--color-text-3)]">%</div>
        </div>
        <div className="mt-1 text-[10px] leading-relaxed text-[var(--color-text-3)]">
          Trung bình P(High) của các quốc gia đang hiển thị, không phải xác suất một người mắc bệnh.
        </div>
      </div>
    </div>
  );
}
