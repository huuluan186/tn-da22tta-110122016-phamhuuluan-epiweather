import { useMemo } from "react";
import { useDiseases } from "../../hooks/useDiseases";
import type { RiskEntry } from "../../types/api";
import type { DiseaseId } from "../../types/domain";
import Icon from "../common/Icon";
import InfoTooltip from "../common/InfoTooltip";

interface Props {
  disease: DiseaseId;
  year: number;
  week: number;
  entries: RiskEntry[];
  totalReportingCountries: number;
}

function formatNumber(value: number): string {
  return Math.round(value).toLocaleString();
}

function StatLabel({
  children,
  tooltip,
  align = "start",
}: {
  children: string;
  tooltip: string;
  align?: "start" | "end";
}) {
  return (
    <div className="relative mb-1 flex items-center gap-1.5 text-[10px] font-semibold uppercase text-slate-100">
      <span className="min-w-0 truncate">{children}</span>
      <InfoTooltip text={tooltip} align={align} />
    </div>
  );
}

export default function SummaryStats({
  disease,
  year,
  week,
  entries,
  totalReportingCountries,
}: Props) {
  const { getDisease } = useDiseases();
  const d = getDisease(disease);

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
      avgScore: reporting ? (totalScore / reporting).toFixed(1) : "-",
    };
  }, [entries]);

  return (
    <div className="grid grid-cols-2 gap-2">
      <div className="p-2.5 bg-[var(--color-panel-inset)] border border-[var(--color-panel-border)] rounded-md">
        <StatLabel tooltip="Số quốc gia đang hiện trên bản đồ so với số quốc gia có dữ liệu dự báo trong tuần được chọn.">
          Quốc gia
        </StatLabel>
        <div className="text-lg font-semibold tabular-nums">
          {stats.reporting} / {Math.max(stats.reporting, totalReportingCountries)}
        </div>
        <div className="text-[11px] mt-0.5 text-slate-100">Hiển thị / dữ liệu</div>
      </div>

      <div className="p-2.5 bg-[var(--color-panel-inset)] border border-[var(--color-panel-border)] rounded-md">
        <StatLabel
          tooltip="Số quốc gia được mô hình xếp vào nhóm rủi ro cao trong tuần và năm đang xem."
          align="end"
        >
          Rủi ro cao
        </StatLabel>
        <div className="text-lg font-semibold text-[var(--color-risk-high)]">{stats.high}</div>
        <div className="inline-flex items-center gap-1 mt-0.5 text-[11px] font-medium tabular-nums text-slate-100">
          <Icon name="arrow-up" size={10} />
          Tuần {String(week).padStart(2, "0")} · {year}
        </div>
      </div>

      <div className="col-span-2 p-2.5 bg-[var(--color-panel-inset)] border border-[var(--color-panel-border)] rounded-md">
        <StatLabel tooltip="Tổng số ca dự báo từ API risk-map cho các quốc gia đang hiển thị. Đây là tổng dự báo của mô hình, không phải số ca thực tế đã ghi nhận.">
          Số ca dự báo
        </StatLabel>
        <div className="text-lg font-semibold tabular-nums">{formatNumber(stats.totalCases)}</div>
        <div className="text-[11px] mt-0.5 text-slate-100">Tổng dự báo</div>
      </div>

      <div className="col-span-2 p-2.5 bg-[var(--color-panel-inset)] border border-[var(--color-panel-border)] rounded-md">
        <StatLabel tooltip="Trung bình P(High) của các quốc gia đang hiển thị. Chỉ số này cho biết khả năng thuộc nhóm cảnh báo cao, không phải xác suất một người mắc bệnh.">
          P(High) TB
        </StatLabel>
        <div className="flex items-baseline gap-2">
          <div className="text-lg font-semibold" style={{ color: d.color }}>
            {stats.avgScore}
          </div>
          <div className="text-[11px] text-slate-100">%</div>
        </div>
      </div>
    </div>
  );
}
