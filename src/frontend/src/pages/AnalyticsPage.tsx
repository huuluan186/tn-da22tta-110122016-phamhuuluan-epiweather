import * as echarts from "echarts";
import { useEffect, useMemo, useRef, useState } from "react";
import FeatureTooltip from "../components/common/FeatureTooltip";
import Icon from "../components/common/Icon";
import { RISK_LEVELS } from "../constants";
import { useFeatureImportance, useModelPerformance, useTrainingCoverage, type FeatureImportanceItem, type FeatureMetadata, type TrainingCoverage } from "../hooks/useAnalytics";
import { useDiseases } from "../hooks/useDiseases";
import { useRiskMap, useRiskMapPeriods } from "../hooks/useRiskMap";
import { attachChartResize } from "../lib/echartsResize";
import { useUIStore } from "../store/uiStore";
import type { RiskEntry, RiskMapPeriod } from "../types/api";
import type { DiseaseId, RiskLevel } from "../types/domain";

function Card({
  title,
  sub,
  children,
  full,
}: {
  title: string;
  sub?: string;
  children: React.ReactNode;
  full?: boolean;
}) {
  return (
    <div
      className={`bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-5 flex flex-col ${
        full ? "col-span-2" : ""
      }`}
    >
      <div className="flex items-baseline gap-2 mb-4">
        <div className="text-[15px] font-semibold text-[var(--color-text-1)]">{title}</div>
        {sub && <div className="text-[11px] text-[var(--color-text-3)]">{sub}</div>}
      </div>
      {children}
    </div>
  );
}

function LoadingBlock({ height = 260 }: { height?: number }) {
  return (
    <div
      className="grid place-items-center text-[var(--color-text-3)] text-xs animate-pulse"
      style={{ height }}
    >
      Đang tải dữ liệu…
    </div>
  );
}

function ErrorBlock({ height = 260, message }: { height?: number; message?: string }) {
  return (
    <div
      className="grid place-items-center text-[var(--color-text-3)] text-xs text-center px-4"
      style={{ height }}
    >
      {message ?? "Không có dữ liệu từ API."}
    </div>
  );
}

function sortRiskPeriods(periods: RiskMapPeriod[] | undefined): RiskMapPeriod[] {
  return [...(periods ?? [])].sort((a, b) => a.iso_year - b.iso_year);
}

function buildFallbackPeriods(year: number, week: number): RiskMapPeriod[] {
  return [{ iso_year: year, min_week: 1, max_week: Math.max(1, week) }];
}

function getLatestPeriod(periods: RiskMapPeriod[], year: number, week: number) {
  const source = periods.length ? periods : buildFallbackPeriods(year, week);
  const last = source[source.length - 1];
  return { year: last.iso_year, week: last.max_week };
}

function getWeekRange(periods: RiskMapPeriod[], year: number, latest: { year: number; week: number }) {
  const period = periods.find((item) => item.iso_year === year);
  const min = period?.min_week ?? 1;
  const configuredMax = period?.max_week ?? (year === latest.year ? latest.week : 52);
  const max = year === latest.year ? Math.min(configuredMax, latest.week) : configuredMax;
  return { min, max: Math.max(min, max) };
}

function clampWeek(week: number, range: { min: number; max: number }) {
  return Math.min(Math.max(week, range.min), range.max);
}

function AnalyticsPeriodFilter({
  year,
  week,
  periods,
  onYearChange,
  onWeekChange,
}: {
  year: number;
  week: number;
  periods?: RiskMapPeriod[];
  onYearChange: (year: number) => void;
  onWeekChange: (week: number) => void;
}) {
  const validPeriods = sortRiskPeriods(periods);
  const latest = getLatestPeriod(validPeriods, year, week);
  const sourcePeriods = validPeriods.length ? validPeriods : buildFallbackPeriods(year, week);
  const validYears = sourcePeriods.map((item) => item.iso_year);
  const safeYear = validYears.includes(year) ? year : latest.year;
  const range = getWeekRange(sourcePeriods, safeYear, latest);
  const safeWeek = clampWeek(week, range);

  const changeYear = (nextYear: number) => {
    const nextRange = getWeekRange(sourcePeriods, nextYear, latest);
    const nextWeek = nextYear === latest.year ? nextRange.max : clampWeek(safeWeek, nextRange);
    onYearChange(nextYear);
    onWeekChange(nextWeek);
  };

  return (
    <div className="flex items-end gap-2 p-2 bg-[var(--color-surface-2)] border border-[var(--color-border)] rounded-lg">
      <label className="flex flex-col gap-1 text-[10px] uppercase tracking-widest text-[var(--color-text-3)]">
        Năm
        <select
          value={safeYear}
          onChange={(event) => changeYear(Number(event.target.value))}
          className="h-8 min-w-[92px] bg-[var(--color-surface)] border border-[var(--color-border)] rounded-md px-2 text-xs font-semibold text-[var(--color-text-1)] outline-none focus:border-[var(--color-primary)]"
        >
          {[...sourcePeriods].reverse().map((period) => (
            <option key={period.iso_year} value={period.iso_year}>
              {period.iso_year}
            </option>
          ))}
        </select>
      </label>
      <div className="flex flex-col gap-1">
        <span className="text-[10px] uppercase tracking-widest text-[var(--color-text-3)]">Tuần</span>
        <div className="flex items-center gap-1">
          <button
            type="button"
            onClick={() => onWeekChange(Math.max(range.min, safeWeek - 1))}
            disabled={safeWeek <= range.min}
            className="h-8 w-8 grid place-items-center bg-[var(--color-surface)] border border-[var(--color-border)] rounded-md text-[var(--color-text-2)] hover:text-[var(--color-text-1)] hover:border-[var(--color-primary)] disabled:opacity-35 disabled:cursor-not-allowed"
            aria-label="Tuần trước"
          >
            <Icon name="chevron-left" size={14} />
          </button>
          <div className="h-8 min-w-[86px] px-3 grid place-items-center bg-[var(--color-surface)] border border-[var(--color-border)] rounded-md text-xs font-semibold text-[var(--color-text-1)] tabular-nums">
            Tuần {String(safeWeek).padStart(2, "0")}
          </div>
          <button
            type="button"
            onClick={() => onWeekChange(Math.min(range.max, safeWeek + 1))}
            disabled={safeWeek >= range.max}
            className="h-8 w-8 grid place-items-center bg-[var(--color-surface)] border border-[var(--color-border)] rounded-md text-[var(--color-text-2)] hover:text-[var(--color-text-1)] hover:border-[var(--color-primary)] disabled:opacity-35 disabled:cursor-not-allowed"
            aria-label="Tuần sau"
          >
            <Icon name="chevron-right" size={14} />
          </button>
        </div>
      </div>
      <button
        type="button"
        onClick={() => {
          onYearChange(latest.year);
          onWeekChange(latest.week);
        }}
        className="h-8 px-3 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-md text-xs font-semibold text-[var(--color-text-2)] hover:text-[var(--color-text-1)] hover:border-[var(--color-primary)]"
      >
        Mới nhất
      </button>
    </div>
  );
}
const RISK_BREAKDOWN_ORDER: RiskLevel[] = ["high", "medium", "low", "none"];

const RISK_BREAKDOWN_LABELS: Record<RiskLevel, string> = {
  high: "Cao",
  medium: "Trung bình",
  low: "Thấp",
  none: "Chưa phân mức",
};

function RiskBreakdown({
  counts,
  total,
  isLoading,
  isError,
}: {
  counts: Record<RiskLevel, number>;
  total: number;
  isLoading: boolean;
  isError: boolean;
}) {
  if (isLoading) return <LoadingBlock height={150} />;
  if (isError) return <ErrorBlock height={150} message="API lỗi khi tải phân bố nhãn nguy cơ." />;
  if (total === 0) return <ErrorBlock height={150} message="Chưa có quốc gia nào để phân tích." />;

  return (
    <div className="flex flex-col gap-3">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {RISK_BREAKDOWN_ORDER.map((level) => {
          const count = counts[level];
          const percent = total > 0 ? Math.round((count / total) * 100) : 0;
          return (
            <div
              key={level}
              className="bg-[var(--color-surface-2)] border border-[var(--color-border-soft)] rounded-md p-3 min-h-[96px] flex flex-col justify-between"
            >
              <div className="flex items-center justify-between gap-2">
                <span className="text-[11px] font-semibold text-[var(--color-text-2)]">
                  {RISK_BREAKDOWN_LABELS[level]}
                </span>
                <span
                  className="h-2.5 w-2.5 rounded-full shrink-0"
                  style={{ backgroundColor: RISK_LEVELS[level].color }}
                />
              </div>
              <div>
                <div className="text-2xl font-semibold tabular-nums text-[var(--color-text-1)]">
                  {count.toLocaleString()}
                </div>
                <div className="text-[10px] text-[var(--color-text-3)] tabular-nums">
                  {percent}% tổng số quốc gia
                </div>
              </div>
            </div>
          );
        })}
      </div>
      <div className="text-[11px] leading-relaxed text-[var(--color-text-3)]">
        Phân tích này đếm mỗi quốc gia theo nhãn nguy cơ dự báo cho tuần đang xem.
        Nhãn nguy cơ là kết quả phân loại của hệ thống, không phải tỷ lệ dân số mắc bệnh.
      </div>
    </div>
  );
}

function TopCountriesChart({ entries, color }: { entries: RiskEntry[]; color: string }) {
  const ref = useRef<HTMLDivElement>(null);

  const data = useMemo(() => {
    const withCases = entries
      .filter((e) => e.predictedCases !== null && e.predictedCases !== undefined)
      .sort((a, b) => (b.predictedCases ?? 0) - (a.predictedCases ?? 0))
      .slice(0, 10);
    return {
      names: withCases.map((e) => e.countryName).reverse(),
      values: withCases.map((e) => Math.round(e.predictedCases ?? 0)).reverse(),
    };
  }, [entries]);

  useEffect(() => {
    if (!ref.current) return;
    const ch = echarts.init(ref.current);
    ch.setOption({
      backgroundColor: "transparent",
      grid: { top: 10, right: 30, bottom: 20, left: 110 },
      tooltip: {
        trigger: "axis",
        backgroundColor: "#1a1f2e",
        borderColor: "#3b4458",
        textStyle: { color: "#f1f5f9", fontSize: 11 },
        formatter: (p: { name: string; value: number }[]) =>
          `${p[0].name}: <b>${p[0].value.toLocaleString()}</b> cases`,
      },
      xAxis: {
        type: "value",
        axisLine: { show: false },
        axisLabel: { color: "#94a3b8", fontSize: 10 },
        splitLine: { lineStyle: { color: "#3a4358", type: "dashed" } },
      },
      yAxis: {
        type: "category",
        data: data.names,
        axisLine: { lineStyle: { color: "#3b4458" } },
        axisLabel: { color: "#cbd5e1", fontSize: 10 },
      },
      series: [
        {
          type: "bar",
          data: data.values,
          itemStyle: { color, borderRadius: [0, 4, 4, 0] },
          barWidth: 16,
        },
      ],
    });
    return attachChartResize(ref.current, ch);
  }, [data, color]);

  return <div ref={ref} className="w-full h-[300px]" />;
}

function HorizonMetricsChart({
  horizons,
}: {
  horizons: { horizon: number; r2: number; rmse: number; mae: number }[];
}) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!ref.current) return;
    const ch = echarts.init(ref.current);
    ch.setOption({
      backgroundColor: "transparent",
      grid: { top: 32, right: 16, bottom: 32, left: 40 },
      tooltip: {
        trigger: "axis",
        backgroundColor: "#1a1f2e",
        borderColor: "#3b4458",
        textStyle: { color: "#f1f5f9", fontSize: 11 },
      },
      legend: {
        data: ["R²", "RMSE", "MAE"],
        textStyle: { color: "#cbd5e1", fontSize: 10 },
        right: 0,
        top: 0,
      },
      xAxis: {
        type: "category",
        data: horizons.map((h) => `h=${h.horizon}`),
        axisLine: { lineStyle: { color: "#3b4458" } },
        axisLabel: { color: "#94a3b8", fontSize: 10 },
      },
      yAxis: {
        type: "value",
        axisLine: { show: false },
        axisLabel: { color: "#94a3b8", fontSize: 10 },
        splitLine: { lineStyle: { color: "#3a4358", type: "dashed" } },
      },
      series: [
        {
          name: "R²",
          type: "bar",
          data: horizons.map((h) => +h.r2.toFixed(3)),
          itemStyle: { color: "#60a5fa", borderRadius: [4, 4, 0, 0] },
          barWidth: 14,
        },
        {
          name: "RMSE",
          type: "line",
          data: horizons.map((h) => +h.rmse.toFixed(3)),
          smooth: true,
          symbol: "circle",
          symbolSize: 6,
          lineStyle: { color: "#f59e0b", width: 2 },
          itemStyle: { color: "#f59e0b" },
        },
        {
          name: "MAE",
          type: "line",
          data: horizons.map((h) => +h.mae.toFixed(3)),
          smooth: true,
          symbol: "circle",
          symbolSize: 6,
          lineStyle: { color: "#34d399", width: 2 },
          itemStyle: { color: "#34d399" },
        },
      ],
    });
    return attachChartResize(ref.current, ch);
  }, [horizons]);

  return <div ref={ref} className="w-full h-[260px]" />;
}


type FeatureImportanceRow = FeatureImportanceItem;

// source_type khớp đúng giá trị trong DB (xem db_migrate_feature_metadata.sql):
// weather = khí hậu, ar_lag = dịch tễ quá khứ, calendar = thời gian/mùa vụ,
// geographic = vị trí địa lý (bán cầu).
const FEATURE_SOURCE_COLORS: Record<string, string> = {
  weather: "#34d399",
  ar_lag: "#60a5fa",
  calendar: "#a855f7",
  geographic: "#f59e0b",
  other: "#cbd5e1",
};

function sourceTypeColor(sourceType: string | null): string {
  return FEATURE_SOURCE_COLORS[sourceType ?? "other"] ?? FEATURE_SOURCE_COLORS.other;
}

function featureLabel(metadata: FeatureMetadata): string {
  return metadata.display_name_vi || metadata.feature;
}

// Mỗi biến trong donut/bảng một màu riêng để dễ phân biệt; dùng chung theo thứ
// hạng nên màu trong donut và bảng luôn khớp nhau. Màu theo nhóm vẫn dùng riêng
// cho các chip lọc (sourceTypeColor).
const SLICE_PALETTE = [
  "#60a5fa", "#34d399", "#f59e0b", "#a855f7", "#ef4444",
  "#06b6d4", "#ec4899", "#84cc16", "#f97316", "#6366f1",
];

function sliceColor(index: number): string {
  return SLICE_PALETTE[index % SLICE_PALETTE.length];
}

function FeatureImportanceDonut({ rows }: { rows: FeatureImportanceRow[] }) {
  const ref = useRef<HTMLDivElement>(null);
  const topRows = useMemo(
    () => rows.filter((row) => row.importance > 0).slice(0, 10),
    [rows],
  );

  useEffect(() => {
    if (!ref.current) return;
    const ch = echarts.init(ref.current);
    ch.setOption({
      backgroundColor: "transparent",
      tooltip: {
        trigger: "item",
        backgroundColor: "#1a1f2e",
        borderColor: "#3b4458",
        textStyle: { color: "#f1f5f9", fontSize: 11 },
        formatter: (item: { name: string; value: number; marker: string }) =>
          `${item.marker}${item.name}: <b>${item.value.toFixed(1)}%</b>`,
      },
      series: [
        {
          name: "Mức ảnh hưởng",
          type: "pie",
          radius: ["42%", "64%"],
          center: ["50%", "50%"],
          avoidLabelOverlap: true,
          label: {
            show: true,
            formatter: "{c}%",
            color: "#e2e8f0",
            fontSize: 11,
            fontWeight: 600,
          },
          labelLine: { show: true, length: 8, length2: 8, lineStyle: { color: "#475569" } },
          itemStyle: {
            borderColor: "#1f2937",
            borderWidth: 2,
          },
          data: topRows.map((row, idx) => ({
            name: featureLabel(row),
            value: +(row.importance * 100).toFixed(2),
            itemStyle: { color: sliceColor(idx) },
          })),
        },
      ],
      graphic: [
        {
          type: "text",
          left: "center",
          top: "44%",
          style: {
            text: String(topRows.length),
            fill: "#f8fafc",
            fontSize: 18,
            fontWeight: 700,
            textAlign: "center",
          },
        },
        {
          type: "text",
          left: "center",
          top: "54%",
          style: {
            text: "biến",
            fill: "#cbd5e1",
            fontSize: 11,
            textAlign: "center",
          },
        },
      ],
    });
    return attachChartResize(ref.current, ch);
  }, [topRows]);

  return <div ref={ref} className="h-[300px] min-w-0" />;
}
function sourceTypeLabel(sourceType: string | null): string {
  if (sourceType === "weather") return "Khí hậu";
  if (sourceType === "ar_lag") return "Dịch tễ quá khứ";
  if (sourceType === "calendar") return "Thời gian/mùa vụ";
  if (sourceType === "geographic") return "Vị trí địa lý";
  return "Biến mô hình";
}

const CATEGORY_ORDER = ["weather", "ar_lag", "calendar", "geographic", "other"] as const;

type CategoryKey = (typeof CATEGORY_ORDER)[number] | "all";

function CategoryFilter({
  rows,
  selected,
  onSelect,
}: {
  rows: FeatureImportanceRow[];
  selected: CategoryKey;
  onSelect: (key: CategoryKey) => void;
}) {
  const totals = useMemo(() => {
    const sum = rows.reduce((acc, row) => acc + row.importance, 0) || 1;
    return CATEGORY_ORDER.map((type) => {
      const total = rows
        .filter((row) => (row.source_type ?? "other") === type)
        .reduce((acc, row) => acc + row.importance, 0);
      return { type, percent: (total / sum) * 100, color: sourceTypeColor(type) };
    }).filter((cat) => cat.percent > 0);
  }, [rows]);

  const chip = (active: boolean) =>
    `flex items-center gap-2 px-3 py-1.5 rounded-md border text-[11px] transition-colors ${
      active
        ? "bg-[var(--color-surface-3)] border-[var(--color-primary)] text-[var(--color-text-1)]"
        : "bg-[var(--color-surface-2)] border-[var(--color-border-soft)] text-[var(--color-text-2)] hover:border-[var(--color-text-3)]"
    }`;

  return (
    <div className="flex flex-wrap gap-2">
      <button type="button" onClick={() => onSelect("all")} className={chip(selected === "all")}>
        Tất cả
      </button>
      {totals.map((cat) => (
        <button
          key={cat.type}
          type="button"
          onClick={() => onSelect(cat.type)}
          className={chip(selected === cat.type)}
        >
          <span className="h-2.5 w-2.5 rounded-full shrink-0" style={{ backgroundColor: cat.color }} />
          {sourceTypeLabel(cat.type)}
          <span className="text-[12px] font-semibold tabular-nums text-[var(--color-text-1)]">
            {cat.percent.toFixed(0)}%
          </span>
        </button>
      ))}
    </div>
  );
}

function CorrelationBar({ r }: { r: number | null | undefined }) {
  if (r == null) {
    return <span className="text-[11px] text-[var(--color-text-3)]">—</span>;
  }
  const pct = Math.min(Math.abs(r), 1) * 50;
  const color = r >= 0 ? "#22c55e" : "#ef4444";
  return (
    <div className="flex items-center gap-1.5 w-[112px] shrink-0">
      <div className="relative h-2 flex-1 rounded-sm bg-[var(--color-surface-3)]">
        <span className="absolute inset-y-0 left-1/2 w-px bg-[var(--color-border)]" />
        <span
          className="absolute inset-y-0 rounded-sm"
          style={
            r >= 0
              ? { left: "50%", width: `${pct}%`, backgroundColor: color }
              : { right: "50%", width: `${pct}%`, backgroundColor: color }
          }
        />
      </div>
      <span
        className="w-[40px] text-right tabular-nums text-[11px] font-semibold"
        style={{ color }}
      >
        {r >= 0 ? "+" : ""}
        {r.toFixed(2)}
      </span>
    </div>
  );
}

function FeatureRankTable({ rows }: { rows: FeatureImportanceRow[] }) {
  const top = useMemo(() => rows.filter((row) => row.importance > 0).slice(0, 10), [rows]);

  return (
    <div className="flex flex-col gap-2.5">
      <div className="flex items-center gap-2.5 text-[10px] uppercase tracking-wide text-[var(--color-text-3)]">
        <span className="w-5 shrink-0 text-right">#</span>
        <span className="w-3 shrink-0" />
        <span className="flex-1">Biến</span>
        <span className="shrink-0 w-[44px] text-right">Ảnh hưởng</span>
        <span className="shrink-0 w-[112px] text-right">Tương quan</span>
      </div>
      {top.map((row, idx) => {
        const color = sliceColor(idx);
        return (
          <div key={row.feature} className="flex items-center gap-2.5 text-[12px]">
            <span className="w-5 shrink-0 text-right text-[11px] tabular-nums text-[var(--color-text-3)]">
              {idx + 1}
            </span>
            <span className="h-3 w-3 shrink-0 rounded-sm" style={{ backgroundColor: color }} />
            <FeatureTooltip metadata={row} className="flex-1" />
            <span className="shrink-0 w-[44px] text-right tabular-nums font-semibold text-[var(--color-text-1)]">
              {(row.importance * 100).toFixed(1)}%
            </span>
            <CorrelationBar r={row.pearson_r} />
          </div>
        );
      })}
    </div>
  );
}

function FeatureImportancePanel({ rows }: { rows: FeatureImportanceRow[] }) {
  const [selected, setSelected] = useState<CategoryKey>("all");
  const filtered = useMemo(
    () =>
      selected === "all"
        ? rows
        : rows.filter((row) => (row.source_type ?? "other") === selected),
    [rows, selected],
  );

  // Khi lọc 1 nhóm: normalize về 100% trong nhóm để donut tròn đầy và % có ý
  // nghĩa "đóng góp trong nhóm này". Chip vẫn giữ % toàn model.
  const displayRows = useMemo(() => {
    if (selected === "all" || filtered.length === 0) return filtered;
    const groupSum = filtered.reduce((acc, row) => acc + row.importance, 0);
    if (groupSum === 0) return filtered;
    return filtered.map((row) => ({ ...row, importance: row.importance / groupSum }));
  }, [filtered, selected]);

  return (
    <div className="flex flex-col gap-4">
      <CategoryFilter rows={rows} selected={selected} onSelect={setSelected} />
      {displayRows.length > 0 ? (
        <div className="grid grid-cols-1 items-center gap-5 md:grid-cols-2">
          <FeatureImportanceDonut rows={displayRows} />
          <FeatureRankTable rows={displayRows} />
        </div>
      ) : (
        <ErrorBlock height={200} message="Nhóm này chưa có biến nào." />
      )}
      <div className="text-[11px] leading-relaxed text-[var(--color-text-3)]">
        Cột "Ảnh hưởng" là mức quan trọng do model học (gain). Cột "Tương quan" là hệ số
        Pearson giữa biến và log1p số ca, tính trên toàn bộ training set 2010-2019 (gộp mọi
        quốc gia): +1 đồng biến mạnh, -1 nghịch biến mạnh, gần 0 không tuyến tính. Hai cột bổ
        sung nhau: biến vừa được model dùng nhiều vừa có tương quan rõ thì độ tin cậy cao hơn.
      </div>
    </div>
  );
}

function CoverageYearChart({ coverage, color }: { coverage: TrainingCoverage; color: string }) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!ref.current) return;
    const ch = echarts.init(ref.current);
    const years = coverage.per_year.map((p) => String(p.year));
    ch.setOption({
      backgroundColor: "transparent",
      grid: { top: 34, right: 48, bottom: 28, left: 56 },
      legend: {
        data: ["Số quan sát", "Số quốc gia"],
        textStyle: { color: "#e2e8f0", fontSize: 10 },
        top: 0,
        left: "center",
        itemGap: 18,
      },
      tooltip: {
        trigger: "axis",
        backgroundColor: "#1a1f2e",
        borderColor: "#475569",
        textStyle: { color: "#f1f5f9", fontSize: 11 },
      },
      xAxis: {
        type: "category",
        data: years,
        axisLine: { lineStyle: { color: "#94a3b8" } },
        axisLabel: { color: "#e2e8f0", fontSize: 10 },
      },
      yAxis: [
        {
          type: "value",
          name: "Quan sát",
          nameTextStyle: { color: "#e2e8f0", fontSize: 10 },
          axisLine: { show: false },
          axisLabel: { color: "#e2e8f0", fontSize: 10 },
          splitLine: { lineStyle: { color: "#475569", type: "dashed" } },
        },
        {
          type: "value",
          name: "Quốc gia",
          nameTextStyle: { color: "#e2e8f0", fontSize: 10 },
          axisLine: { show: false },
          axisLabel: { color: "#e2e8f0", fontSize: 10 },
          splitLine: { show: false },
        },
      ],
      series: [
        {
          name: "Số quan sát",
          type: "bar",
          data: coverage.per_year.map((p) => p.observations),
          itemStyle: { color, borderRadius: [4, 4, 0, 0] },
          barWidth: 18,
        },
        {
          name: "Số quốc gia",
          type: "line",
          yAxisIndex: 1,
          data: coverage.per_year.map((p) => p.n_countries),
          smooth: true,
          symbol: "circle",
          symbolSize: 7,
          lineStyle: { color: "#e2e8f0", width: 2.5 },
          itemStyle: { color: "#e2e8f0" },
        },
      ],
    });
    return attachChartResize(ref.current, ch);
  }, [coverage, color]);

  return <div ref={ref} className="w-full h-[240px]" />;
}

function TrainingCoveragePanel({
  coverage,
  isLoading,
  isError,
  color,
  disease,
}: {
  coverage: TrainingCoverage | undefined;
  isLoading: boolean;
  isError: boolean;
  color: string;
  disease: DiseaseId;
}) {
  if (isLoading) return <LoadingBlock height={300} />;
  if (isError || !coverage) return <ErrorBlock height={300} message="Chưa tải được độ phủ dữ liệu huấn luyện." />;

  const kpis = [
    { label: "Khoảng năm", value: `${coverage.year_start}–${coverage.year_end}`, sub: `${coverage.n_years} năm liên tục` },
    { label: "Số quốc gia", value: coverage.n_countries.toLocaleString("vi-VN"), sub: "có báo cáo ca bệnh" },
    { label: "Tổng quan sát", value: coverage.total_observations.toLocaleString("vi-VN"), sub: "bản ghi tuần × quốc gia" },
    { label: "TB tuần/nước/năm", value: `${coverage.avg_weeks_per_country_year}/52`, sub: "mật độ báo cáo" },
  ];

  return (
    <div className="flex flex-col gap-4">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {kpis.map((k) => (
          <div
            key={k.label}
            className="bg-[var(--color-surface-2)] border border-[var(--color-border-soft)] rounded-md p-3"
          >
            <div className="text-[10px] uppercase tracking-widest text-[var(--color-text-3)] mb-1">
              {k.label}
            </div>
            <div className="text-2xl font-semibold tabular-nums text-[var(--color-text-1)]">
              {k.value}
            </div>
            <div className="text-[10px] text-[var(--color-text-3)] mt-0.5">{k.sub}</div>
          </div>
        ))}
      </div>
      <CoverageYearChart coverage={coverage} color={color} />
      <div className="text-[11px] leading-relaxed text-[var(--color-text-3)]">
        Cột là số quan sát mỗi năm, đường trắng là số quốc gia báo cáo trong năm đó. Đây là tập
        sau bước feature engineering — đúng dữ liệu model học.{" "}
        {disease === "flu" ? (
          <>
            Cúm dùng 2010-2019; loại 2020-2021 vì giãn cách và NPI làm số ca giảm khoảng 99%
            không phản ánh quy luật tự nhiên, 2022 để riêng cho kiểm định ngoài mẫu.
          </>
        ) : (
          <>
            Dengue thu hẹp 2015-2019 vì 2010-2014 dữ liệu quá thưa (chỉ 5-9 nước, chưa đại diện
            toàn cầu); chỉ giữ quốc gia có từ 30 tuần báo cáo/năm trở lên.
          </>
        )}
      </div>
    </div>
  );
}

export default function AnalyticsPage() {
  const disease = useUIStore((s) => s.disease);
  const setDisease = useUIStore((s) => s.setDisease);
  const year = useUIStore((s) => s.year);
  const week = useUIStore((s) => s.week);
  const setYear = useUIStore((s) => s.setYear);
  const setWeek = useUIStore((s) => s.setWeek);
  const setLatest = useUIStore((s) => s.setLatest);
  const { diseases, getDisease } = useDiseases();
  const d = getDisease(disease);
  const themeColor = disease === "flu" ? "#60a5fa" : "#f59e0b";

  const riskPeriods = useRiskMapPeriods(disease);
  const sortedPeriods = useMemo(
    () => sortRiskPeriods(riskPeriods.periods?.periods),
    [riskPeriods.periods],
  );
  const latestPeriod = getLatestPeriod(sortedPeriods, year, week);
  const sourcePeriods = sortedPeriods.length ? sortedPeriods : buildFallbackPeriods(year, week);
  const validYears = sourcePeriods.map((period) => period.iso_year);
  const selectedYear = validYears.includes(year) ? year : latestPeriod.year;
  const selectedRange = getWeekRange(sourcePeriods, selectedYear, latestPeriod);
  const selectedWeek = clampWeek(week, selectedRange);

  useEffect(() => {
    setLatest(latestPeriod.year, latestPeriod.week);
  }, [latestPeriod.year, latestPeriod.week, setLatest]);

  useEffect(() => {
    if (year !== selectedYear) setYear(selectedYear);
    if (week !== selectedWeek) setWeek(selectedWeek);
  }, [selectedYear, selectedWeek, setYear, setWeek, week, year]);

  const { entries, meta, isLoading: mapLoading, isError: mapError } = useRiskMap(
    disease,
    selectedYear,
    selectedWeek,
  );
  const { performance, isLoading: perfLoading } = useModelPerformance(disease);
  const { coverage, isLoading: coverageLoading, isError: coverageError } = useTrainingCoverage(disease);
  const { importance, isLoading: featLoading } = useFeatureImportance(disease, 1);

  const totalCountries = entries.length;
  const displayMeta = meta ?? { year: selectedYear, week: selectedWeek, count: totalCountries };
  const totalCases = entries.reduce((sum, e) => sum + (e.predictedCases ?? 0), 0);
  const riskBreakdown = useMemo<Record<RiskLevel, number>>(() => {
    const counts: Record<RiskLevel, number> = { high: 0, medium: 0, low: 0, none: 0 };
    entries.forEach((entry) => {
      counts[entry.risk] += 1;
    });
    return counts;
  }, [entries]);
  const featureRows = useMemo<FeatureImportanceRow[]>(() => {
    if (!importance) return [];
    const metadataByName = new Map(
      (importance.feature_metadata ?? []).map((item) => [item.feature, item]),
    );

    if (importance.importance?.length) {
      return importance.importance.map((item) => ({
        feature: item.feature,
        importance: item.importance,
        display_name_vi: item.display_name_vi ?? metadataByName.get(item.feature)?.display_name_vi ?? null,
        description_vi: item.description_vi ?? metadataByName.get(item.feature)?.description_vi ?? null,
        source_type: item.source_type ?? metadataByName.get(item.feature)?.source_type ?? null,
        pearson_r: item.pearson_r ?? metadataByName.get(item.feature)?.pearson_r ?? null,
      }));
    }

    return importance.features.map((feature) => {
      const metadata = metadataByName.get(feature);
      return {
        feature,
        importance: importance.features.length ? 1 / importance.features.length : 0,
        display_name_vi: metadata?.display_name_vi ?? null,
        description_vi: metadata?.description_vi ?? null,
        source_type: metadata?.source_type ?? null,
        pearson_r: metadata?.pearson_r ?? null,
      };
    });
  }, [importance]);

  return (
    <div className="flex-1 px-6 md:px-10 lg:px-14 py-6 bg-[var(--color-bg)]">
      <div className="max-w-[1400px] mx-auto flex flex-col gap-4">

        {/* Header với disease toggle + meta */}
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div>
            <h1 className="text-xl font-semibold text-[var(--color-text-1)]">
              Phân tích nguy cơ · {d.label}
            </h1>
            <div className="text-[11px] text-[var(--color-text-3)] mt-0.5">
              {mapLoading ? (
                "Đang tải…"
              ) : mapError ? (
                "Không tải được dữ liệu phân tích"
              ) : (
                <>
                  Dữ liệu đang xem: Tuần {String(displayMeta.week).padStart(2, "0")} · Năm {displayMeta.year} · {displayMeta.count} quốc gia
                </>
              )}
            </div>
          </div>
          <div className="flex items-center justify-end flex-wrap gap-2">
            <AnalyticsPeriodFilter
              year={selectedYear}
              week={selectedWeek}
              periods={riskPeriods.periods?.periods}
              onYearChange={setYear}
              onWeekChange={setWeek}
            />
            <div className="flex gap-1.5 p-1 bg-[var(--color-surface-2)] rounded-lg">
              {diseases.map((dx) => (
                <button
                  key={dx.id}
                  onClick={() => setDisease(dx.id)}
                  className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-colors ${
                    disease === dx.id
                      ? "bg-[var(--color-surface)] text-[var(--color-text-1)]"
                      : "text-[var(--color-text-3)] hover:text-[var(--color-text-1)]"
                  }`}
                >
                  {dx.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* KPI strip */}
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4">
            <div className="text-[10px] uppercase tracking-widest text-[var(--color-text-3)] mb-1">
              Tổng số ca dự báo
            </div>
            <div className="text-2xl font-semibold text-[var(--color-text-1)] tabular-nums">
              {mapLoading ? "…" : Math.round(totalCases).toLocaleString()}
            </div>
          </div>
          <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4">
            <div className="text-[10px] uppercase tracking-widest text-[var(--color-text-3)] mb-1">
              Quốc gia có dữ liệu
            </div>
            <div className="text-2xl font-semibold text-[var(--color-text-1)] tabular-nums">
              {mapLoading ? "…" : totalCountries}
            </div>
          </div>
        </div>

        <Card
          title="Dữ liệu huấn luyện model"
          sub="từ disease_cases · nền tảng độ tin cậy"
        >
          <TrainingCoveragePanel
            coverage={coverage}
            isLoading={coverageLoading}
            isError={coverageError}
            color={themeColor}
            disease={disease}
          />
        </Card>

        <Card
          title="Phân bố nhãn nguy cơ"
          sub={`Số quốc gia theo nhãn · Tuần ${String(displayMeta.week).padStart(2, "0")} · Năm ${displayMeta.year}`}
        >
          <RiskBreakdown
            counts={riskBreakdown}
            total={totalCountries}
            isLoading={mapLoading}
            isError={mapError}
          />
        </Card>

        <div className="grid grid-cols-2 gap-4">
          <Card title="Top 10 quốc gia" sub={`số ca dự báo · ${d.label}`}>
            {mapLoading && <LoadingBlock height={300} />}
            {!mapLoading && mapError && <ErrorBlock height={300} message="API lỗi khi tải risk map." />}
            {!mapLoading && !mapError && entries.length > 0 && (
              <TopCountriesChart entries={entries} color={themeColor} />
            )}
            {!mapLoading && !mapError && entries.length === 0 && <ErrorBlock height={300} />}
          </Card>

          <Card title="Hiệu năng mô hình" sub="walk-forward CV · h=1..4">
            {perfLoading && <LoadingBlock height={260} />}
            {!perfLoading && performance && performance.horizons.length > 0 && (
              <>
                <HorizonMetricsChart horizons={performance.horizons} />
                <dl className="mt-3 space-y-2 rounded-md border border-[var(--color-border)] bg-[var(--color-surface-2)] p-3 text-[11px] leading-relaxed">
                  <div className="flex gap-2">
                    <span className="mt-1 h-2 w-2 shrink-0 rounded-full bg-[#60a5fa]" />
                    <div>
                      <dt className="inline font-semibold text-[var(--color-text-1)]">R² (hệ số xác định): </dt>
                      <dd className="inline text-[var(--color-text-3)]">
                        mô hình giải thích được bao nhiêu phần dao động số ca thực tế. Thang 0–1, càng gần 1 càng tốt; 0,80 nghĩa là giải thích được khoảng 80%.
                      </dd>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <span className="mt-1 h-2 w-2 shrink-0 rounded-full bg-[#f59e0b]" />
                    <div>
                      <dt className="inline font-semibold text-[var(--color-text-1)]">RMSE (sai số toàn phương trung bình): </dt>
                      <dd className="inline text-[var(--color-text-3)]">
                        trung bình độ lệch giữa dự báo và thực tế, phạt nặng các lần sai lớn. Càng nhỏ càng tốt. Tính trên thang log1p của số ca.
                      </dd>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <span className="mt-1 h-2 w-2 shrink-0 rounded-full bg-[#34d399]" />
                    <div>
                      <dt className="inline font-semibold text-[var(--color-text-1)]">MAE (sai số tuyệt đối trung bình): </dt>
                      <dd className="inline text-[var(--color-text-3)]">
                        trung bình khoảng cách tuyệt đối giữa dự báo và thực tế, ít nhạy với ngoại lệ hơn RMSE. Càng nhỏ càng tốt. Cũng tính trên thang log1p.
                      </dd>
                    </div>
                  </div>
                </dl>
                <div className="mt-2 text-[10px] text-[var(--color-text-3)] text-center">
                  {performance.model_type} · trained {performance.horizons[0]?.training_period}
                </div>
              </>
            )}
            {!perfLoading && (!performance || performance.horizons.length === 0) && (
              <ErrorBlock height={260} message="Chưa có metrics file." />
            )}
          </Card>

          <Card title="Biến quan trọng nhất của mô hình" sub={`top 10 theo mức ảnh hưởng · h=1 · ${d.label}`} full>
            {featLoading && <LoadingBlock height={300} />}
            {!featLoading && featureRows.length > 0 && (
              <FeatureImportancePanel rows={featureRows} />
            )}
            {!featLoading && featureRows.length === 0 && (
              <ErrorBlock height={300} />
            )}
            {importance && featureRows.length > 0 && (
              <div className="mt-4 text-[10px] text-[var(--color-text-3)]">
                Target: <code className="text-[var(--color-text-2)]">{importance.target}</code>
                {" · "}Mô hình: {importance.model_type}
                {" · "}Trained: {importance.training_date}
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
}
