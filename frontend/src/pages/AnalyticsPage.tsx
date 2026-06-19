import * as echarts from "echarts";
import { useEffect, useMemo, useRef } from "react";
import FeatureTooltip from "../components/common/FeatureTooltip";
import { useFeatureImportance, useModelPerformance, type FeatureMetadata } from "../hooks/useAnalytics";
import { useDiseases } from "../hooks/useDiseases";
import { useLatestRiskMap } from "../hooks/useRiskMap";
import { useUIStore } from "../store/uiStore";
import type { RiskEntry } from "../types/api";

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
        borderColor: "#2a3040",
        textStyle: { color: "#f1f5f9", fontSize: 11 },
        formatter: (p: { name: string; value: number }[]) =>
          `${p[0].name}: <b>${p[0].value.toLocaleString()}</b> cases`,
      },
      xAxis: {
        type: "value",
        axisLine: { show: false },
        axisLabel: { color: "#64748b", fontSize: 10 },
        splitLine: { lineStyle: { color: "#1e2535", type: "dashed" } },
      },
      yAxis: {
        type: "category",
        data: data.names,
        axisLine: { lineStyle: { color: "#2a3040" } },
        axisLabel: { color: "#94a3b8", fontSize: 10 },
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
    const onResize = () => ch.resize();
    window.addEventListener("resize", onResize);
    return () => {
      window.removeEventListener("resize", onResize);
      ch.dispose();
    };
  }, [data, color]);

  return <div ref={ref} className="w-full h-[300px]" />;
}

function HorizonMetricsChart({
  horizons,
  color,
}: {
  horizons: { horizon: number; r2: number; rmse: number; mae: number }[];
  color: string;
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
        borderColor: "#2a3040",
        textStyle: { color: "#f1f5f9", fontSize: 11 },
      },
      legend: {
        data: ["R²", "RMSE", "MAE"],
        textStyle: { color: "#94a3b8", fontSize: 10 },
        right: 0,
        top: 0,
      },
      xAxis: {
        type: "category",
        data: horizons.map((h) => `h=${h.horizon}`),
        axisLine: { lineStyle: { color: "#2a3040" } },
        axisLabel: { color: "#64748b", fontSize: 10 },
      },
      yAxis: {
        type: "value",
        axisLine: { show: false },
        axisLabel: { color: "#64748b", fontSize: 10 },
        splitLine: { lineStyle: { color: "#1e2535", type: "dashed" } },
      },
      series: [
        {
          name: "R²",
          type: "bar",
          data: horizons.map((h) => +h.r2.toFixed(3)),
          itemStyle: { color, borderRadius: [4, 4, 0, 0] },
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
          lineStyle: { color: "#10b981", width: 2 },
          itemStyle: { color: "#10b981" },
        },
      ],
    });
    const onResize = () => ch.resize();
    window.addEventListener("resize", onResize);
    return () => {
      window.removeEventListener("resize", onResize);
      ch.dispose();
    };
  }, [horizons, color]);

  return <div ref={ref} className="w-full h-[260px]" />;
}

function sourceTypeLabel(sourceType: string | null): string {
  if (sourceType === "weather") return "Khí hậu";
  if (sourceType === "autoregressive") return "Dịch tễ quá khứ";
  if (sourceType === "temporal") return "Thời gian/mùa vụ";
  return "Biến mô hình";
}

export default function AnalyticsPage() {
  const disease = useUIStore((s) => s.disease);
  const setDisease = useUIStore((s) => s.setDisease);
  const { diseases, getDisease } = useDiseases();
  const d = getDisease(disease);
  const themeColor = disease === "flu" ? "#3b82f6" : "#f59e0b";

  const { entries, meta, isLoading: mapLoading, isError: mapError } = useLatestRiskMap(disease);
  const { performance, isLoading: perfLoading } = useModelPerformance(disease);
  const { importance, isLoading: featLoading } = useFeatureImportance(disease, 1);

  const totalCountries = entries.length;
  const totalCases = entries.reduce((sum, e) => sum + (e.predictedCases ?? 0), 0);
  const highRiskCount = entries.filter((e) => e.risk === "high").length;
  const featureRows = useMemo<FeatureMetadata[]>(() => {
    if (!importance) return [];
    const metadataByName = new Map(
      (importance.feature_metadata ?? []).map((item) => [item.feature, item]),
    );

    if (importance.importance?.length) {
      return importance.importance.map((item) => ({
        feature: item.feature,
        display_name_vi: item.display_name_vi ?? metadataByName.get(item.feature)?.display_name_vi ?? null,
        description_vi: item.description_vi ?? metadataByName.get(item.feature)?.description_vi ?? null,
        source_type: item.source_type ?? metadataByName.get(item.feature)?.source_type ?? null,
      }));
    }

    return importance.features.map((feature) => {
      const metadata = metadataByName.get(feature);
      return metadata ?? {
        feature,
        display_name_vi: null,
        description_vi: null,
        source_type: null,
      };
    });
  }, [importance]);

  return (
    <div className="flex-1 overflow-y-auto p-6 bg-[var(--color-bg)]">
      <div className="max-w-[1400px] mx-auto flex flex-col gap-4">

        {/* Header với disease toggle + meta */}
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div>
            <h1 className="text-xl font-semibold text-[var(--color-text-1)]">
              Analytics · {d.label}
            </h1>
            <div className="text-[11px] text-[var(--color-text-3)] mt-0.5">
              {meta ? (
                <>
                  Dự báo mới nhất: Tuần {String(meta.week).padStart(2, "0")} · Năm {meta.year} · {meta.count} quốc gia
                </>
              ) : mapLoading ? (
                "Đang tải…"
              ) : (
                "Chưa có dữ liệu"
              )}
            </div>
          </div>
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

        {/* KPI strip */}
        <div className="grid grid-cols-3 gap-3">
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
              Quốc gia rủi ro cao
            </div>
            <div className="text-2xl font-semibold text-[var(--color-risk-high)] tabular-nums">
              {mapLoading ? "…" : highRiskCount}
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
                <HorizonMetricsChart horizons={performance.horizons} color={themeColor} />
                <div className="mt-2 text-[10px] text-[var(--color-text-3)] text-center">
                  {performance.model_type} · trained {performance.horizons[0]?.training_period}
                </div>
              </>
            )}
            {!perfLoading && (!performance || performance.horizons.length === 0) && (
              <ErrorBlock height={260} message="Chưa có metrics file." />
            )}
          </Card>

          <Card title="Biến mô hình sử dụng" sub={`h=1 · ${d.label}`} full>
            {featLoading && <LoadingBlock height={200} />}
            {!featLoading && featureRows.length > 0 && (
              <div className="grid grid-cols-2 gap-2">
                {featureRows.map((metadata, idx) => {
                  const isClimate = metadata.source_type === "weather";
                  return (
                    <div
                      key={metadata.feature}
                      className="flex items-center gap-3 text-[12px] px-3 py-2 bg-[var(--color-surface-2)] border border-[var(--color-border-soft)] rounded-md"
                    >
                      <span className="text-[var(--color-text-3)] tabular-nums w-5">
                        {String(idx + 1).padStart(2, "0")}
                      </span>
                      <div
                        className="w-1.5 h-4 rounded-full"
                        style={{ backgroundColor: isClimate ? "#10b981" : themeColor }}
                      />
                      <FeatureTooltip metadata={metadata} className="flex-1" />
                      <span className="text-[10px] text-[var(--color-text-3)]">
                        {sourceTypeLabel(metadata.source_type)}
                      </span>
                    </div>
                  );
                })}
              </div>
            )}
            {!featLoading && featureRows.length === 0 && (
              <ErrorBlock height={200} />
            )}
            {importance && (
              <div className="mt-3 text-[10px] text-[var(--color-text-3)]">
                Target: <code className="text-[var(--color-text-2)]">{importance.target}</code>
                {" · "}Trained: {importance.training_date}
                {" · "}<span className="inline-block w-2 h-2 rounded-full bg-emerald-500 align-middle mr-1" />
                Climate
                {" · "}<span className="inline-block w-2 h-2 rounded-full align-middle mr-1" style={{ backgroundColor: themeColor }} />
                Autoregressive / temporal
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
}
