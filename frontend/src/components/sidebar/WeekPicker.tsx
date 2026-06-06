import Icon from "../common/Icon";
import type { DiseaseId } from "../../types/domain";

interface Props {
  disease: DiseaseId;
  year: number;
  week: number;
  onYearChange: (y: number) => void;
  onWeekChange: (w: number) => void;
}

// Cấu hình per-disease: năm hợp lệ + week range
const DISEASE_CONFIG: Record<
  DiseaseId,
  {
    backtest: number[];
    latest: { year: number; label: string }[];
    weekRange: Record<number, { min: number; max: number }>;
    defaultYear: number;
  }
> = {
  flu: {
    backtest: Array.from({ length: 10 }, (_, i) => 2010 + i),
    latest: [{ year: 2026, label: "2026 (W02-W21)" }],
    weekRange: { 2026: { min: 2, max: 21 } },
    defaultYear: 2026,
  },
  dengue: {
    backtest: Array.from({ length: 10 }, (_, i) => 2010 + i),
    latest: [
      { year: 2023, label: "2023 (W01-W36)" },
      { year: 2022, label: "2022" },
      { year: 2021, label: "2021" },
    ],
    weekRange: { 2023: { min: 1, max: 36 } },
    defaultYear: 2023,
  },
};

function getRange(disease: DiseaseId, y: number) {
  return DISEASE_CONFIG[disease].weekRange[y] ?? { min: 1, max: 52 };
}

function isLatestPeriod(disease: DiseaseId, y: number) {
  return DISEASE_CONFIG[disease].latest.some((r) => r.year === y);
}

function getHintText(disease: DiseaseId, y: number): string {
  if (!isLatestPeriod(disease, y)) {
    return "Backtest: mô phỏng dự báo trên dữ liệu quá khứ để so sánh/đánh giá";
  }
  if (disease === "flu") return "Mới nhất: 2026-W02 đến W21 · dự báo từ mô hình ML";
  if (y === 2023) return "Mới nhất: 2023-W01 đến W36 · dữ liệu hiện có từ nguồn dịch tễ + thời tiết";
  return `Mới nhất: ${y} · tuần có dữ liệu dự báo trong hệ thống`;
}

export default function WeekPicker({ disease, year, week, onYearChange, onWeekChange }: Props) {
  const cfg = DISEASE_CONFIG[disease];
  const allValid = [...cfg.backtest, ...cfg.latest.map((r) => r.year)];

  const safeYear = allValid.includes(year) ? year : cfg.defaultYear;
  const { min: minWeek, max: maxWeek } = getRange(disease, safeYear);
  const safeWeek = Math.min(Math.max(week, minWeek), maxWeek);
  const pct = maxWeek > minWeek ? ((safeWeek - minWeek) / (maxWeek - minWeek)) * 100 : 0;

  return (
    <div>
      <div className="flex items-center gap-1.5 mb-2">
        <select
          value={safeYear}
          onChange={(e) => {
            const newYear = Number(e.target.value);
            onYearChange(newYear);
            const { min, max } = getRange(disease, newYear);
            const clampedWeek = Math.min(Math.max(week, min), max);
            if (clampedWeek !== week) onWeekChange(clampedWeek);
          }}
          className="flex-1 h-[30px] bg-[var(--color-surface-2)] border border-[var(--color-border)] rounded-md text-[var(--color-text-1)] text-xs font-semibold px-2 text-center cursor-pointer focus:outline-none focus:border-[var(--color-text-3)]"
        >
          <optgroup label="Mới nhất / dữ liệu vận hành">
            {cfg.latest.map((r) => (
              <option key={r.year} value={r.year}>{r.label}</option>
            ))}
          </optgroup>
          <optgroup label="Backtest / kiểm thử quá khứ">
            {cfg.backtest.map((y) => (
              <option key={y} value={y}>{y}</option>
            ))}
          </optgroup>
        </select>
      </div>
      <div className="mb-2 text-[10px] text-[var(--color-text-3)] leading-tight">
        {getHintText(disease, safeYear)}
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={() => onWeekChange(Math.max(minWeek, safeWeek - 1))}
          disabled={safeWeek <= minWeek}
          className="w-8 h-8 grid place-items-center bg-[var(--color-surface-2)] border border-[var(--color-border)] rounded-md text-[var(--color-text-2)] hover:text-[var(--color-text-1)] hover:border-[var(--color-text-3)] disabled:opacity-40 disabled:cursor-not-allowed"
        >
          <Icon name="chevron-left" size={14} />
        </button>
        <div className="flex-1 h-8 bg-[var(--color-surface-2)] border border-[var(--color-border)] rounded-md flex items-center justify-center text-xs font-semibold">
          W{String(safeWeek).padStart(2, "0")}
        </div>
        <button
          onClick={() => onWeekChange(Math.min(maxWeek, safeWeek + 1))}
          disabled={safeWeek >= maxWeek}
          className="w-8 h-8 grid place-items-center bg-[var(--color-surface-2)] border border-[var(--color-border)] rounded-md text-[var(--color-text-2)] hover:text-[var(--color-text-1)] hover:border-[var(--color-text-3)] disabled:opacity-40 disabled:cursor-not-allowed"
        >
          <Icon name="chevron-right" size={14} />
        </button>
      </div>

      <div className="mt-2 h-1 bg-[var(--color-surface-2)] rounded-sm overflow-hidden relative">
        <div
          className="absolute inset-y-0 left-0 rounded-sm bg-gradient-to-r from-[#3b82f6] to-[#8b5cf6] transition-[width] duration-200"
          style={{ width: `${pct}%` }}
        />
      </div>
      <div className="mt-1 flex justify-between text-[10px] text-[var(--color-text-3)] tabular-nums">
        <span>W{String(minWeek).padStart(2, "0")}</span>
        <span>W{String(safeWeek).padStart(2, "0")} / W{String(maxWeek).padStart(2, "0")}</span>
        <span>W{String(maxWeek).padStart(2, "0")}</span>
      </div>
    </div>
  );
}
