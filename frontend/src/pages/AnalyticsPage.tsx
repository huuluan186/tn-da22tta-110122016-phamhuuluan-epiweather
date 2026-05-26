import * as echarts from "echarts";
import { useEffect, useMemo, useRef } from "react";
import { DISEASES } from "../constants";
import { useFeatureImportance, useModelPerformance } from "../hooks/useAnalytics";
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

const FEATURE_LABEL: Record<string, string> = {
  flu_log_lag1: "Cases lag 1w (AR)",
  flu_log_lag2: "Cases lag 2w (AR)",
  flu_log_lag3: "Cases lag 3w (AR)",
  flu_log_rollmean4: "Cases rolling mean 4w",
  flu_log_rollmean8: "Cases rolling mean 8w",
  dengue_log_lag1: "Cases lag 1w (AR)",
  dengue_log_lag2: "Cases lag 2w (AR)",
  dengue_log_lag4: "Cases lag 4w (AR)",
  dengue_log_rollmean4: "Cases rolling mean 4w",
  dengue_log_rollmean12: "Cases rolling mean 12w",
  temp_c_lag1: "Temperature lag 1w",
  temp_c_lag3: "Temperature lag 3w",
  temp_c_lag4: "Temperature lag 4w",
  temp_c_lag7: "Temperature lag 7w",
  humidity_pct_lag1: "Humidity lag 1w",
  humidity_pct_lag2: "Humidity lag 2w",
  humidity_pct_lag7: "Humidity lag 7w",
  humidity_pct_lag8: "Humidity lag 8w",
  solar_wm2_lag4: "Solar radiation lag 4w",
  solar_wm2_lag7: "Solar radiation lag 7w",
  solar_wm2_lag8: "Solar radiation lag 8w",
  solar_wm2_lag16: "Solar radiation lag 16w",
  dewpoint_c_lag1: "Dew point lag 1w",
  dewpoint_c_lag2: "Dew point lag 2w",
  precip_mm: "Precipitation",
  iso_week_sin: "Seasonality (sin)",
  iso_week_cos: "Seasonality (cos)",
  iso_year: "Year trend",
  HEMISPHERE_NH: "Northern hemisphere",
  HEMISPHERE_SH: "Southern hemisphere",
};

function featureLabel(name: string): string {
  return FEATURE_LABEL[name] ?? name;
}

export default function AnalyticsPage() {
  const disease = useUIStore((s) => s.disease);
  const setDisease = useUIStore((s) => s.setDisease);
  const d = DISEASES.find((x) => x.id === disease)!;
  const themeColor = disease === "flu" ? "#3b82f6" : "#f59e0b";

  const { entries, meta, isLoading: mapLoading, isError: mapError } = useLatestRiskMap(disease);
  const { performance, isLoading: perfLoading } = useModelPerformance(disease);
  const { importance, isLoading: featLoading } = useFeatureImportance(disease, 1);

  const totalCountries = entries.length;
  const totalCases = entries.reduce((sum, e) => sum + (e.predictedCases ?? 0), 0);
  const highRiskCount = entries.filter((e) => e.risk === "high").length;

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
                  Latest predictions: W{String(meta.week).padStart(2, "0")}/{meta.year} · {meta.count} countries
                </>
              ) : mapLoading ? (
                "Đang tải…"
              ) : (
                "Chưa có dữ liệu"
              )}
            </div>
          </div>
          <div className="flex gap-1.5 p-1 bg-[var(--color-surface-2)] rounded-lg">
            {DISEASES.map((dx) => (
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
              Total predicted cases
            </div>
            <div className="text-2xl font-semibold text-[var(--color-text-1)] tabular-nums">
              {mapLoading ? "…" : Math.round(totalCases).toLocaleString()}
            </div>
          </div>
          <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4">
            <div className="text-[10px] uppercase tracking-widest text-[var(--color-text-3)] mb-1">
              High-risk countries
            </div>
            <div className="text-2xl font-semibold text-[var(--color-risk-high)] tabular-nums">
              {mapLoading ? "…" : highRiskCount}
            </div>
          </div>
          <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4">
            <div className="text-[10px] uppercase tracking-widest text-[var(--color-text-3)] mb-1">
              Countries with data
            </div>
            <div className="text-2xl font-semibold text-[var(--color-text-1)] tabular-nums">
              {mapLoading ? "…" : totalCountries}
            </div>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <Card title="Top 10 Countries" sub={`predicted cases · ${d.label}`}>
            {mapLoading && <LoadingBlock height={300} />}
            {!mapLoading && mapError && <ErrorBlock height={300} message="API lỗi khi tải risk map." />}
            {!mapLoading && !mapError && entries.length > 0 && (
              <TopCountriesChart entries={entries} color={themeColor} />
            )}
            {!mapLoading && !mapError && entries.length === 0 && <ErrorBlock height={300} />}
          </Card>

          <Card title="Model Performance" sub="walk-forward CV · h=1..4">
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

          <Card title="Features Used by Model" sub={`h=1 · ${d.label}`} full>
            {featLoading && <LoadingBlock height={200} />}
            {!featLoading && importance && importance.features.length > 0 && (
              <div className="grid grid-cols-2 gap-2">
                {importance.features.map((f, idx) => {
                  const isClimate = !f.includes("log") && !f.includes("iso") && !f.includes("HEMI");
                  return (
                    <div
                      key={f}
                      className="flex items-center gap-3 text-[12px] px-3 py-2 bg-[var(--color-surface-2)] border border-[var(--color-border-soft)] rounded-md"
                    >
                      <span className="text-[var(--color-text-3)] tabular-nums w-5">
                        {String(idx + 1).padStart(2, "0")}
                      </span>
                      <div
                        className="w-1.5 h-4 rounded-full"
                        style={{ backgroundColor: isClimate ? "#10b981" : themeColor }}
                      />
                      <span className="text-[var(--color-text-2)] flex-1">{featureLabel(f)}</span>
                      <span className="text-[10px] text-[var(--color-text-3)] tabular-nums">{f}</span>
                    </div>
                  );
                })}
              </div>
            )}
            {!featLoading && (!importance || importance.features.length === 0) && (
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
