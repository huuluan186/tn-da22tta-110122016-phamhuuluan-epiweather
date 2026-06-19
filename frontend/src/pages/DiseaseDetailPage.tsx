import * as echarts from "echarts";
import { useEffect, useMemo, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useNavigate, useParams } from "react-router-dom";
import FeatureTooltip from "../components/common/FeatureTooltip";
import ForecastChart from "../components/detail/ForecastChart";
import { DISEASES, RISK_LEVELS } from "../constants";
import { useFeatureImportance, type FeatureMetadata } from "../hooks/useAnalytics";
import { useForecast, useNowcast } from "../hooks/useForecast";
import { useHistory, usePrediction } from "../hooks/usePrediction";
import { ECHARTS_COUNTRY_NAMES } from "../lib/mockRisk";
import { useUIStore } from "../store/uiStore";
import type { HistoryPoint } from "../types/api";
import type { DiseaseId, RiskLevel } from "../types/domain";

// Năm hợp lệ cho từng disease (phải khớp với data trong predictions table)
const VALID_YEARS: Record<DiseaseId, { min: number; max: number; hint: string }> = {
  flu:    { min: 2010, max: 2026, hint: "Backtest 2010-2019 hoặc mới nhất 2026 (W02-W21)" },
  dengue: { min: 2010, max: 2023, hint: "Backtest 2010-2019 hoặc mới nhất 2021-2023 (W01-W36)" },
};

function toRiskLevel(raw: string | null | undefined): RiskLevel {
  const normalized = raw?.toLowerCase() ?? "";
  if (normalized === "high" || normalized === "medium" || normalized === "low") return normalized;
  return "none";
}

function clampPercent(value: number): number {
  return Math.max(0, Math.min(100, value));
}

function formatPercent(value: number | null): string {
  return value === null ? "—" : `${value.toFixed(1)}%`;
}

function riskMeaning(risk: RiskLevel): string {
  if (risk === "high") {
    return "Rủi ro cao nghĩa là quốc gia này có khả năng rơi vào nhóm nguy cơ bùng phát/số ca cao trong tuần dự báo. Đây không phải xác suất một cá nhân mắc bệnh.";
  }
  if (risk === "medium") {
    return "Rủi ro trung bình nghĩa là mô hình thấy dấu hiệu cần theo dõi, nhưng chưa đến nhóm cảnh báo cao.";
  }
  if (risk === "low") {
    return "Rủi ro thấp nghĩa là mô hình chưa thấy tín hiệu nổi bật cho nhóm nguy cơ cao ở tuần này.";
  }
  return "Chưa đủ dữ liệu để phân nhóm rủi ro cho tuần này.";
}

function sourceTypeLabel(sourceType: string | null): string {
  if (sourceType === "weather") return "Khí hậu";
  if (sourceType === "autoregressive") return "Dịch tễ quá khứ";
  if (sourceType === "temporal") return "Thời gian/mùa vụ";
  return "Biến mô hình";
}

function TrendChart({ points, disease }: { points: HistoryPoint[]; disease: "flu" | "dengue" }) {
  const elRef = useRef<HTMLDivElement>(null);
  const color = disease === "flu" ? "#3b82f6" : "#f59e0b";
  const series = useMemo(() => {
    const slice = points.slice(-52);
    return {
      labels: slice.map((p) => `W${String(p.iso_week).padStart(2, "0")}/${p.iso_year}`),
      values: slice.map((p) => p.predicted_cases ?? p.actual_cases ?? null),
    };
  }, [points]);

  useEffect(() => {
    if (!elRef.current) return;
    const ch = echarts.init(elRef.current);
    const data = series.values;
    const weeks = series.labels;

    ch.setOption({
      backgroundColor: "transparent",
      grid: { top: 16, right: 16, bottom: 32, left: 48 },
      tooltip: {
        trigger: "axis",
        backgroundColor: "#1a1f2e",
        borderColor: "#2a3040",
        textStyle: { color: "#f1f5f9", fontSize: 11 },
        formatter: (p: { name: string; value: number }[]) =>
          `${p[0].name}: <b>${p[0].value ?? "—"}</b> cases`,
      },
      xAxis: {
        type: "category",
        data: weeks,
        axisLine: { lineStyle: { color: "#2a3040" } },
        axisLabel: { color: "#64748b", fontSize: 10, interval: 7 },
        splitLine: { show: false },
      },
      yAxis: {
        type: "value",
        min: 0,
        axisLine: { show: false },
        axisLabel: { color: "#64748b", fontSize: 10 },
        splitLine: { lineStyle: { color: "#1e2535", type: "dashed" } },
      },
      series: [{
        type: "line",
        data,
        smooth: true,
        symbol: "none",
        lineStyle: { color, width: 2 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: color.replace(")", ",0.25)").replace("rgb", "rgba") },
            { offset: 1, color: "rgba(0,0,0,0)" },
          ]),
        },
      }],
    });

    const onResize = () => ch.resize();
    window.addEventListener("resize", onResize);
    return () => { window.removeEventListener("resize", onResize); ch.dispose(); };
  }, [series, disease, color]);

  return <div ref={elRef} className="w-full h-[220px]" />;
}

export default function DiseaseDetailPage() {
  const { iso3 } = useParams<{ iso3: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { disease, year: uiYear, week: uiWeek } = useUIStore();

  // Picker để query tuần backtest — null = dùng latest nowcast
  const [pickerYear, setPickerYear] = useState<number | null>(null);
  const [pickerWeek, setPickerWeek] = useState<number | null>(null);
  const isHistoricalMode = pickerYear !== null && pickerWeek !== null;

  // Nowcast: tuần mới nhất có dữ liệu dự báo
  const {
    forecast: nowcast,
    isLoading: nowcastLoading,
    isError: nowcastError,
  } = useNowcast(disease, iso3);

  // Backtest: dùng picker năm/tuần khi user chọn
  const {
    forecast: historicalForecast,
    isLoading: historicalLoading,
    isError: historicalError,
  } = useForecast(disease, iso3, pickerYear ?? 2019, pickerWeek ?? 1, {
    enabled: isHistoricalMode,
  });

  const forecast = isHistoricalMode ? historicalForecast : nowcast;
  const forecastLoading = isHistoricalMode ? historicalLoading : nowcastLoading;
  const forecastError = isHistoricalMode ? historicalError : (nowcastError && !historicalForecast);
  const isLatestMode = !isHistoricalMode && Boolean(nowcast);

  // week/year dùng cho display (header + prediction)
  const displayWeek = forecast?.as_of_iso_week ?? pickerWeek ?? uiWeek;
  const displayYear = forecast?.as_of_iso_year ?? pickerYear ?? uiYear;

  // input buffer cho picker (string để user gõ tự do)
  const [inputYear, setInputYear] = useState("");
  const [inputWeek, setInputWeek] = useState("");

  const validRange = VALID_YEARS[disease];
  const clearQueryCache = () => {
    queryClient.removeQueries({ queryKey: ["prediction", disease, iso3], exact: false });
    queryClient.removeQueries({ queryKey: ["forecast", disease, iso3], exact: false });
    queryClient.removeQueries({ queryKey: ["nowcast", disease, iso3], exact: false });
    queryClient.invalidateQueries({ queryKey: ["prediction", disease, iso3], exact: false });
    queryClient.invalidateQueries({ queryKey: ["forecast", disease, iso3], exact: false });
    queryClient.invalidateQueries({ queryKey: ["nowcast", disease, iso3], exact: false });
  };

  const applyPicker = () => {
    const y = parseInt(inputYear, 10);
    const w = parseInt(inputWeek, 10);
    if (y >= validRange.min && y <= validRange.max && w >= 1 && w <= 53) {
      clearQueryCache();
      setPickerYear(y);
      setPickerWeek(w);
    }
  };

  const resetPicker = () => {
    clearQueryCache();
    setPickerYear(null);
    setPickerWeek(null);
    setInputYear("");
    setInputWeek("");
  };

  if (!iso3) {
    return (
      <div className="flex-1 grid place-items-center bg-[var(--color-bg)]">
        <div className="max-w-[420px] bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-6 text-center">
          <div className="text-sm font-semibold text-[var(--color-text-1)]">Chưa chọn quốc gia</div>
          <div className="mt-2 text-xs text-[var(--color-text-3)]">
            Trang này chỉ hiển thị khi bạn chọn một quốc gia từ bản đồ hoặc danh sách cảnh báo.
          </div>
          <button
            onClick={() => navigate("/")}
            className="mt-4 h-[32px] px-4 rounded-md text-xs font-semibold border border-[var(--color-border)] bg-[var(--color-surface-3)] text-[var(--color-text-1)] hover:border-[var(--color-text-2)] transition-colors"
          >
            Quay lại bản đồ
          </button>
        </div>
      </div>
    );
  }

  const countryName = ECHARTS_COUNTRY_NAMES[iso3] ?? iso3;
  const d = DISEASES.find((x) => x.id === disease)!;
  const { prediction, isLoading: predictionLoading } = usePrediction(
    disease,
    iso3,
    displayYear,
    displayWeek,
  );
  const { history, isLoading: historyLoading, isError: historyError } = useHistory(
    disease,
    iso3,
    2010,
    2019,
  );
  const riskLevel = toRiskLevel(prediction?.risk_level);
  const riskDef = RISK_LEVELS[riskLevel];
  const predictedCases = prediction?.predicted_cases ?? null;
  const riskProbability =
    prediction?.risk_probability == null ? null : clampPercent(prediction.risk_probability * 100);
  const h1Forecast = forecast?.points.find((point) => point.horizon === 1) ?? forecast?.points[0];
  const modelConfidence = h1Forecast?.r2_cv == null ? null : clampPercent(h1Forecast.r2_cv * 100);
  const predictionInterval =
    prediction?.confidence_lo != null && prediction?.confidence_hi != null
      ? `${Math.round(prediction.confidence_lo).toLocaleString()}–${Math.round(prediction.confidence_hi).toLocaleString()} ca`
      : null;
  const predictedCasesLabel =
    predictedCases !== null ? Math.round(predictedCases).toLocaleString() : "—";
  const probabilityLabel = formatPercent(riskProbability);
  const confidenceLabel = formatPercent(modelConfidence);
  const { importance: featureImportance, isLoading: featureLoading, isError: featureError } =
    useFeatureImportance(disease, 1);
  const featureRows = useMemo<FeatureMetadata[]>(() => {
    if (!featureImportance) return [];
    const metadataByName = new Map(
      (featureImportance.feature_metadata ?? []).map((item) => [item.feature, item]),
    );

    if (featureImportance.importance?.length) {
      return featureImportance.importance.slice(0, 8).map((item) => ({
        feature: item.feature,
        display_name_vi: item.display_name_vi ?? metadataByName.get(item.feature)?.display_name_vi ?? null,
        description_vi: item.description_vi ?? metadataByName.get(item.feature)?.description_vi ?? null,
        source_type: item.source_type ?? metadataByName.get(item.feature)?.source_type ?? null,
      }));
    }

    return featureImportance.features.slice(0, 8).map((feature) => {
      const metadata = metadataByName.get(feature);
      return metadata ?? {
        feature,
        display_name_vi: null,
        description_vi: null,
        source_type: null,
      };
    });
  }, [featureImportance]);

  return (
    <div className="flex-1 overflow-y-auto bg-[var(--color-bg)] p-6">
      <div className="max-w-[860px] mx-auto flex flex-col gap-5">

        <button
          onClick={() => navigate("/")}
          className="self-start text-[var(--color-text-3)] hover:text-[var(--color-text-1)] text-xs"
        >
          ← Back to map
        </button>

        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-[var(--color-text-1)]">{countryName}</h1>
            <p className="mt-1 text-sm text-[var(--color-text-3)]">
              {d.label} · Tuần {String(displayWeek).padStart(2, "0")} · Năm {displayYear}
            </p>
          </div>
          <div
            className="px-4 py-2 rounded-lg text-sm font-bold text-white"
            style={{ backgroundColor: riskDef.color }}
          >
            {predictionLoading ? "Đang tải…" : `${riskDef.label}`}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-4">
            <div className="text-[10px] uppercase tracking-widest text-[var(--color-text-3)] mb-1">
              Số ca dự báo
            </div>
            <div className="text-2xl font-semibold text-[var(--color-text-1)] tabular-nums">
              {predictionLoading ? "…" : predictedCasesLabel}
            </div>
            <div className="mt-1 text-[11px] leading-relaxed text-[var(--color-text-3)]">
              Ước tính số ca trong tuần được chọn.
            </div>
          </div>

          <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-4">
            <div className="text-[10px] uppercase tracking-widest text-[var(--color-text-3)] mb-1">
              Xác suất rủi ro cao
            </div>
            <div className="relative mt-2 h-8 overflow-hidden rounded-full border border-[var(--color-border-soft)] bg-[var(--color-surface-3)]">
              <div
                className="absolute inset-y-0 left-0 rounded-full"
                style={{
                  width: `${riskProbability ?? 0}%`,
                  backgroundColor: riskDef.color,
                  minWidth: riskProbability && riskProbability > 0 ? "2.5rem" : "0",
                }}
              />
              <div className="absolute inset-0 grid place-items-center text-xs font-bold text-white drop-shadow">
                {predictionLoading ? "…" : probabilityLabel}
              </div>
            </div>
            <div className="mt-2 text-[11px] leading-relaxed text-[var(--color-text-3)]">
              P(High): khả năng thuộc nhóm quốc gia rủi ro cao.
            </div>
          </div>

          <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-4">
            <div className="text-[10px] uppercase tracking-widest text-[var(--color-text-3)] mb-1">
              Nhóm rủi ro
            </div>
            <div className="text-2xl font-semibold text-[var(--color-text-1)]">
              {predictionLoading ? "…" : riskDef.label}
            </div>
            <div className="mt-1 text-[11px] leading-relaxed text-[var(--color-text-3)]">
              {riskMeaning(riskLevel)}
            </div>
          </div>

          <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-4">
            <div className="text-[10px] uppercase tracking-widest text-[var(--color-text-3)] mb-1">
              Độ tin cậy mô hình
            </div>
            <div className="text-2xl font-semibold text-[var(--color-text-1)] tabular-nums">
              {forecastLoading ? "…" : confidenceLabel}
            </div>
            <div className="mt-1 text-[11px] leading-relaxed text-[var(--color-text-3)]">
              {predictionInterval
                ? `Khoảng dự báo: ${predictionInterval}.`
                : "Dựa trên R² cross-validation của mô hình h=1."}
            </div>
          </div>
        </div>

        <div className="bg-[var(--color-surface-2)] border border-[var(--color-border-soft)] rounded-xl px-4 py-3 text-[12px] leading-relaxed text-[var(--color-text-2)]">
          Diễn giải: mô hình dự báo khoảng <b className="text-[var(--color-text-1)]">{predictedCasesLabel}</b> ca.
          Xác suất <b className="text-[var(--color-text-1)]">{probabilityLabel}</b> nghĩa là khả năng quốc gia này rơi vào nhóm rủi ro cao trong tuần dự báo, không phải xác suất một người dân bất kỳ mắc bệnh.
        </div>

        <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-5">
          {/* Header: title + as-of label + backtest picker */}
          <div className="flex items-start justify-between gap-3 mb-4 flex-wrap">
            <div>
              <div className="text-[13px] font-semibold text-[var(--color-text-1)]">
                Dự báo 4 tuần · {d.label}
                {isLatestMode && (
                  <span className="ml-2 text-[10px] font-normal text-emerald-400">● mới nhất</span>
                )}
                {isHistoricalMode && (
                  <span className="ml-2 text-[10px] font-normal text-amber-400">● backtest</span>
                )}
              </div>
              {forecast && (
                <div className="mt-0.5 text-[11px] text-[var(--color-text-3)]">
                  Tính từ Tuần {String(forecast.as_of_iso_week).padStart(2, "0")}, Năm {forecast.as_of_iso_year}
                  {" "}→ Tuần {String(forecast.points[0]?.target_iso_week).padStart(2, "0")}–{String(forecast.points[3]?.target_iso_week).padStart(2, "0")}, Năm {forecast.points[3]?.target_iso_year}
                </div>
              )}
            </div>

            {/* Backtest picker */}
            <div className="flex flex-col items-end gap-1">
              <div className="flex items-end gap-1.5 text-[11px]">
                <label className="flex flex-col gap-1 text-[10px] uppercase tracking-wider text-[var(--color-text-3)]">
                  Tuần
                  <input
                    type="number"
                    placeholder="23"
                    min={1} max={53}
                    value={inputWeek}
                    onChange={(e) => setInputWeek(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && applyPicker()}
                    className="w-[56px] bg-[var(--color-surface-3)] border border-[var(--color-border)] rounded px-2 py-1 text-[var(--color-text-1)] text-center [appearance:textfield] outline-none"
                  />
                </label>
                <label className="flex flex-col gap-1 text-[10px] uppercase tracking-wider text-[var(--color-text-3)]">
                  Năm
                  <input
                    type="number"
                    placeholder="2026"
                    min={validRange.min} max={validRange.max}
                    value={inputYear}
                    onChange={(e) => setInputYear(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && applyPicker()}
                    className="w-[72px] bg-[var(--color-surface-3)] border border-[var(--color-border)] rounded px-2 py-1 text-[var(--color-text-1)] text-center [appearance:textfield] outline-none"
                  />
                </label>
                <button
                  onClick={applyPicker}
                  className="px-2 py-1 rounded bg-[var(--color-primary)] text-white hover:opacity-80 transition-opacity"
                >
                  Áp dụng
                </button>
                {isHistoricalMode && (
                  <button
                    onClick={resetPicker}
                    className="px-2 py-1 rounded bg-[var(--color-surface-3)] text-[var(--color-text-3)] hover:text-[var(--color-text-1)] transition-colors"
                  >
                    ✕
                  </button>
                )}
              </div>
              <div className="text-[10px] text-[var(--color-text-3)]">
                {validRange.hint}
              </div>
            </div>
          </div>

          {/* Model coverage info — thông tin validation của model cho năm dự báo */}
          {!forecastLoading && forecast?.data_coverage?.warning && (
            <div className="mb-3 px-3 py-2 rounded-lg bg-sky-950/40 border border-sky-700/50 text-sky-300 text-[11px] leading-relaxed">
              ℹ {forecast.data_coverage.warning}
            </div>
          )}

          {forecastLoading && (
            <div className="h-[260px] grid place-items-center text-[var(--color-text-3)] text-xs">
              Loading forecast…
            </div>
          )}
          {!forecastLoading && forecastError && (
            <div className="h-[260px] grid place-items-center text-center text-amber-400 text-xs gap-1">
              <div>
                Không có feature snapshot cho Tuần {String(pickerWeek ?? displayWeek).padStart(2, "0")}, Năm {pickerYear ?? displayYear}
              </div>
              <div className="text-[var(--color-text-3)]">
                {isHistoricalMode ? "Thử tuần/năm backtest khác" : "Cần cập nhật dữ liệu dự báo trước"}
              </div>
            </div>
          )}
          {!forecastLoading && !forecastError && forecast && forecast.points.length > 0 && (
            <ForecastChart points={forecast.points} disease={disease} />
          )}
        </div>

        <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-5">
          <div className="text-[13px] font-semibold text-[var(--color-text-1)] mb-4">
            52-week Trend · {d.label}
          </div>
          {historyLoading && (
            <div className="h-[220px] grid place-items-center text-[var(--color-text-3)] text-xs">
              Loading history…
            </div>
          )}
          {!historyLoading && historyError && (
            <div className="h-[220px] grid place-items-center text-[var(--color-text-3)] text-xs">
              Chưa có dữ liệu xu hướng từ API.
            </div>
          )}
          {!historyLoading && !historyError && history && history.points.length > 0 && (
            <TrendChart points={history.points} disease={disease} />
          )}
        </div>

        <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-5">
          <div className="text-[13px] font-semibold text-[var(--color-text-1)] mb-4">
            Biến ảnh hưởng chính
            <span className="ml-2 text-[11px] font-normal text-[var(--color-text-3)]">(feature importance, h=1)</span>
          </div>
          {featureLoading && (
            <div className="h-[120px] grid place-items-center text-[var(--color-text-3)] text-xs">
              Đang tải danh sách biến…
            </div>
          )}
          {!featureLoading && featureError && (
            <div className="h-[120px] grid place-items-center text-[var(--color-text-3)] text-xs">
              Chưa lấy được dữ liệu biến từ API analytics.
            </div>
          )}
          {!featureLoading && !featureError && featureRows.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {featureRows.map((metadata, idx) => (
                <div
                  key={metadata.feature}
                  className="flex items-center gap-3 rounded-md border border-[var(--color-border-soft)] bg-[var(--color-surface-2)] px-3 py-2 text-[12px]"
                >
                  <span className="w-5 tabular-nums text-[var(--color-text-3)]">
                    {String(idx + 1).padStart(2, "0")}
                  </span>
                  <span
                    className="h-4 w-1.5 rounded-full"
                    style={{
                      backgroundColor: metadata.source_type === "weather" ? "#10b981" : d.color,
                    }}
                  />
                  <FeatureTooltip metadata={metadata} className="flex-1" />
                  <span className="text-[10px] text-[var(--color-text-3)]">
                    {sourceTypeLabel(metadata.source_type)}
                  </span>
                </div>
              ))}
            </div>
          )}
          {!featureLoading && !featureError && featureRows.length === 0 && (
            <div className="h-[120px] grid place-items-center text-[var(--color-text-3)] text-xs">
              Chưa có dữ liệu biến từ API.
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
