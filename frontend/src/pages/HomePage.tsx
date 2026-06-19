import { useEffect, useMemo, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import AlertsSidebar from "../components/alerts/AlertsSidebar";
import MapLegend from "../components/map/MapLegend";
import MapThemeToggle from "../components/map/MapThemeToggle";
import WorldMap from "../components/map/WorldMap";
import { MAP_THEME_STORAGE_KEY, type MapTheme } from "../components/map/mapTheme";
import RiskMapSidebar from "../components/sidebar/RiskMapSidebar";
import { RISK_LEVELS, WHO_REGIONS } from "../constants";
import { useCountries } from "../hooks/useCountries";
import { useDiseases } from "../hooks/useDiseases";
import { useForecast, useNowcast } from "../hooks/useForecast";
import { usePrediction } from "../hooks/usePrediction";
import { useLatestRiskMap, useRiskMap } from "../hooks/useRiskMap";
import { ECHARTS_COUNTRY_NAMES, ISO3_BY_ECHARTS_NAME } from "../lib/mockRisk";
import { useUIStore } from "../store/uiStore";
import type { RiskEntry } from "../types/api";
import type { DiseaseId } from "../types/domain";

type Applied = { year: number; week: number } | null;

export default function HomePage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const {
    disease,
    setDisease,
    year,
    setYear,
    week,
    setWeek,
    regions,
    toggleRegion,
    selectedIso3,
    setSelectedIso3,
    riskLevels,
    toggleRiskLevel,
    setLatest,
  } = useUIStore();

  const [isRightOpen, setIsRightOpen] = useState(true);
  const [isLeftOpen, setIsLeftOpen] = useState(true);
  const [isDetailOpen, setIsDetailOpen] = useState(true);
  const [mapTheme, setMapTheme] = useState<MapTheme>(() => {
    const saved = window.localStorage.getItem(MAP_THEME_STORAGE_KEY);
    return saved === "light" ? "light" : "dark";
  });
  // Collapsible sections in right sidebar country detail
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    info: true,
    stats: true,
    forecast: true,
  });
  const toggleSection = (key: string) =>
    setExpandedSections((prev) => ({ ...prev, [key]: !prev[key] }));

  // applied = null → dùng latest (mặc định); != null → dùng backtest
  const [applied, setApplied] = useState<Applied>(null);
  const { getDisease } = useDiseases();
  const activeDisease = getDisease(disease);
  const isHistorical = applied !== null;

  useEffect(() => {
    if (selectedIso3) setIsDetailOpen(true);
  }, [selectedIso3]);

  useEffect(() => {
    window.localStorage.setItem(MAP_THEME_STORAGE_KEY, mapTheme);
  }, [mapTheme]);

  // Khi user đổi disease, reset applied về null (latest mode) để tránh
  // hiển thị bản đồ flu năm cũ đè lên dengue
  const prevDiseaseRef = useRef(disease);
  useEffect(() => {
    if (prevDiseaseRef.current !== disease) {
      prevDiseaseRef.current = disease;
      setApplied(null);
    }
  }, [disease]);

  // Ref để track xem đã sync year/week cho disease này chưa
  // Tránh effect ghi đè khi user bấm mũi tên đổi tuần
  const syncedForDiseaseRef = useRef<DiseaseId | null>(null);

  // Latest mode (always fetch — dùng làm default + fallback)
  const latest = useLatestRiskMap(disease, { enabled: !isHistorical });

  // Backtest mode (chỉ fetch khi user apply picker)
  const historical = useRiskMap(disease, applied?.year ?? 2019, applied?.week ?? 1, {
    enabled: isHistorical,
  });

  const active = isHistorical ? historical : latest;
  const entries = active.entries;
  const activeYear = isHistorical ? applied!.year : latest.meta?.year ?? year;
  const activeWeek = isHistorical ? applied!.week : latest.meta?.week ?? week;

  // Đồng bộ year/week của picker với latest.meta CHỈ MỘT LẦN cho mỗi disease.
  // Sau khi sync xong, user toàn quyền đổi tuần qua picker — effect KHÔNG ghi đè.
  // (Trước đây sync mỗi render → user bấm mũi tên xong bị revert ngay)
  // Đồng thời cập nhật store.latestYear/latestWeek mỗi khi API trả về,
  // để TopNav luôn phản ánh tuần mới nhất thực sự có data.
  const latestYear = latest.meta?.year;
  const latestWeek = latest.meta?.week;
  useEffect(() => {
    if (latestYear !== undefined && latestWeek !== undefined) {
      setLatest(latestYear, latestWeek);
      if (syncedForDiseaseRef.current !== disease) {
        syncedForDiseaseRef.current = disease;
        if (latestYear !== year) setYear(latestYear);
        if (latestWeek !== week) setWeek(latestWeek);
      }
    }
  }, [disease, latestYear, latestWeek, year, week, setYear, setWeek, setLatest]);

  const isDirty =
    !isHistorical
      ? year !== (latest.meta?.year ?? year) || week !== (latest.meta?.week ?? week)
      : year !== applied!.year || week !== applied!.week;

  const { countries } = useCountries();
  const countryRegionMap = useMemo(() => {
    const map = new Map<string, string>();
    countries.forEach((c) => {
      if (c.who_region) map.set(c.iso3, c.who_region);
    });
    return map;
  }, [countries]);
  const selectedCountry = useMemo(
    () => (selectedIso3 ? countries.find((c) => c.iso3 === selectedIso3) ?? null : null),
    [countries, selectedIso3],
  );
  const selectedRegionLabel = useMemo(() => {
    if (!selectedCountry?.who_region) return null;
    return WHO_REGIONS.find((r) => r.id === selectedCountry.who_region)?.label ?? null;
  }, [selectedCountry]);

  const entriesWithRegion = useMemo<RiskEntry[]>(() => {
    return entries.map((e) => {
      if (e.whoRegion) return e;
      const region = countryRegionMap.get(e.iso3) ?? null;
      return { ...e, whoRegion: region };
    });
  }, [entries, countryRegionMap]);

  const filteredEntries = useMemo(() => {
    let out = entriesWithRegion;
    if (regions.length) {
      out = out.filter((e) => e.whoRegion && regions.includes(e.whoRegion));
    }
    if (riskLevels.length) {
      out = out.filter((e) => e.risk && riskLevels.includes(e.risk));
    }
    return out;
  }, [entriesWithRegion, regions, riskLevels]);

  // Selected country detail — backtest thì dùng forecast, latest thì dùng nowcast
  const { prediction, isLoading: predictionLoading } = usePrediction(
    disease,
    selectedIso3 ?? undefined,
    activeYear,
    activeWeek,
  );
  const histForecast = useForecast(disease, selectedIso3 ?? undefined, activeYear, activeWeek);
  const nowcast = useNowcast(disease, !isHistorical ? selectedIso3 ?? undefined : undefined);
  const forecast = isHistorical ? histForecast.forecast : nowcast.forecast;
  const forecastLoading = isHistorical ? histForecast.isLoading : nowcast.isLoading;

  const selectedName = selectedIso3
    ? selectedCountry?.country_name ?? ECHARTS_COUNTRY_NAMES[selectedIso3] ?? selectedIso3
    : null;
  const riskKey = (() => {
    const raw = prediction?.risk_level?.toLowerCase() ?? "";
    if (raw === "high" || raw === "medium" || raw === "low") return raw;
    return "none";
  })() as keyof typeof RISK_LEVELS;
  const riskLabel = RISK_LEVELS[riskKey].label;
  const riskColor = RISK_LEVELS[riskKey].color;

  const clearDetailQueryCache = () => {
    if (!selectedIso3) return;
    queryClient.removeQueries({ queryKey: ["prediction", disease, selectedIso3], exact: false });
    queryClient.removeQueries({ queryKey: ["forecast", disease, selectedIso3], exact: false });
    queryClient.removeQueries({ queryKey: ["nowcast", disease, selectedIso3], exact: false });
    queryClient.invalidateQueries({ queryKey: ["prediction", disease, selectedIso3], exact: false });
    queryClient.invalidateQueries({ queryKey: ["forecast", disease, selectedIso3], exact: false });
    queryClient.invalidateQueries({ queryKey: ["nowcast", disease, selectedIso3], exact: false });
  };

  const applyHistorical = () => {
    clearDetailQueryCache();
    setApplied({ year, week });
  };
  const resetToLatest = () => {
    clearDetailQueryCache();
    setApplied(null);
    if (latest.meta) {
      setYear(latest.meta.year);
      setWeek(latest.meta.week);
    }
  };

  return (
    <div className="flex flex-1 h-full min-h-0 overflow-hidden">
      <RiskMapSidebar
        disease={disease}
        setDisease={setDisease}
        year={year}
        setYear={setYear}
        week={week}
        setWeek={setWeek}
        regions={regions}
        toggleRegion={toggleRegion}
        entries={filteredEntries}
        regionEntries={entriesWithRegion}
        onApply={applyHistorical}
        onResetLatest={resetToLatest}
        isApplying={active.isFetching}
        isDirty={isDirty}
        isHistorical={isHistorical}
        riskLevels={riskLevels}
        toggleRiskLevel={toggleRiskLevel}
        isOpen={isLeftOpen}
        onToggle={() => setIsLeftOpen((v) => !v)}
      />

      <div className="flex-1 min-h-0 bg-[var(--color-bg)] overflow-hidden flex flex-col">
        <div className="px-5 py-3.5 border-b border-[var(--color-border)]">
          <div className="flex items-center justify-between">
            <h2 className="m-0 text-[15px] font-semibold">
              Bản đồ rủi ro toàn cầu · {activeDisease.label}
            </h2>
            <div className="flex items-center gap-2 text-xs text-[var(--color-text-3)]">
              {isHistorical ? (
                <span className="px-2 py-0.5 rounded-full bg-amber-500/15 text-amber-300 font-semibold tracking-wide">
                  BACKTEST
                </span>
              ) : (
                <span className="px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-300 font-semibold tracking-wide">
                  MỚI NHẤT
                </span>
              )}
              <span className="grid min-w-[72px] gap-0.5 text-right leading-tight">
                <span className="text-[var(--color-text-1)]">Tuần {String(activeWeek).padStart(2, "0")}</span>
                <span>Năm {activeYear}</span>
              </span>
              <MapThemeToggle theme={mapTheme} onChange={setMapTheme} />
              {active.isFetching && (
                <span className="text-[var(--color-text-3)] animate-pulse">· đang cập nhật</span>
              )}
            </div>
          </div>
          <div className="mt-1 text-xs text-[var(--color-text-2)]">
            {regions.length ? `Vùng: ${regions.join(", ")}` : "Tất cả vùng"} · {filteredEntries.length} quốc gia
            {active.isError && <span className="ml-2 text-[var(--color-risk-high)]">Lỗi API</span>}
          </div>
        </div>

        <div className="flex-1 min-h-0 relative">
          {active.isLoading && (
            <div className="absolute inset-0 grid place-items-center bg-[var(--color-bg)]/50 z-10 backdrop-blur-sm">
                <div className="text-[var(--color-text-3)] text-xs animate-pulse">
                    Đang tải bản đồ…</div>
                </div>
          )}
          <WorldMap
            entries={filteredEntries}
            theme={mapTheme}
            onCountrySelect={(echartsName) => {
              const iso3 = ISO3_BY_ECHARTS_NAME[echartsName];
              if (!iso3) return;
              setSelectedIso3(iso3);
            }}
          />
          <MapLegend theme={mapTheme} />
        </div>
      </div>

      <aside
        className={`hidden lg:flex shrink-0 border-l border-[var(--color-border)] bg-[var(--color-surface)] flex-col min-h-0 transition-all ${
          isRightOpen ? "w-[360px]" : "w-[44px]"
        }`}
      >
        <div className="flex items-center justify-between px-3 pt-3 pb-2 border-b border-[var(--color-border-soft)]">
          {isRightOpen && (
            <div className="text-[10px] font-semibold tracking-[0.08em] text-[var(--color-text-3)] uppercase">
              Quốc gia đã chọn
            </div>
          )}
          <button
            onClick={() => setIsRightOpen((v) => !v)}
            aria-label={isRightOpen ? "Thu gọn panel" : "Mở rộng panel"}
            className="ml-auto w-7 h-7 grid place-items-center rounded-md border border-[var(--color-border)] text-[var(--color-text-2)] hover:text-[var(--color-text-1)] hover:border-[var(--color-text-2)] transition-colors"
          >
            {isRightOpen ? "›" : "‹"}
          </button>
        </div>

        {!isRightOpen && (
          <div className="flex-1 grid place-items-center text-[10px] text-[var(--color-text-3)] tracking-[0.2em] rotate-90">
            CHI TIẾT
          </div>
        )}

        {isRightOpen && (
          <div className="px-4 pt-2 pb-4 border-b border-[var(--color-border-soft)] overflow-y-auto">
            {!selectedIso3 && (
              <div className="text-xs text-[var(--color-text-3)] space-y-2">
                <div>Chưa chọn quốc gia. Bạn có thể bấm trên bản đồ hoặc chọn từ danh sách cảnh báo.</div>
                <div className="text-[11px] text-[var(--color-text-2)]">
                  {activeDisease.label}: {activeDisease.description}
                </div>
              </div>
            )}
            {selectedIso3 && (
              <div className="flex flex-col gap-2">
                {/* Header — always visible */}
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <div className="text-sm font-semibold text-[var(--color-text-1)]">{selectedName}</div>
                    <div className="text-[11px] text-[var(--color-text-3)]">
                      {selectedIso3} · {activeDisease.label}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <div
                      className="px-2 py-0.5 rounded-md text-[10px] font-bold text-white shrink-0"
                      style={{ backgroundColor: riskColor }}
                    >
                      {predictionLoading ? "…" : riskLabel}
                    </div>
                    <button
                      onClick={() => setIsDetailOpen((v) => !v)}
                      aria-label={isDetailOpen ? "Thu gọn chi tiết" : "Mở chi tiết"}
                      className="w-6 h-6 grid place-items-center rounded-md border border-[var(--color-border)] text-[var(--color-text-2)] hover:text-[var(--color-text-1)] hover:border-[var(--color-text-2)] transition-colors"
                    >
                      {isDetailOpen ? "˅" : "˄"}
                    </button>
                  </div>
                </div>

                {isDetailOpen && (
                  <>
                    {/* Section: Thông tin */}
                    <div className="border border-[var(--color-border-soft)] rounded-lg overflow-hidden">
                      <button
                        onClick={() => toggleSection("info")}
                        className="w-full flex items-center justify-between px-2.5 py-1.5 bg-[var(--color-surface-2)] hover:bg-[var(--color-surface-3)] transition-colors text-left"
                      >
                        <span className="text-[10px] font-semibold uppercase tracking-[0.06em] text-[var(--color-text-3)]">
                          Thông tin
                        </span>
                        <span
                          className="text-[var(--color-text-3)] text-[10px]"
                          style={{
                            display: "inline-block",
                            transform: expandedSections.info ? "rotate(180deg)" : "rotate(0deg)",
                            transition: "transform 0.2s ease",
                          }}
                        >
                          ▼
                        </span>
                      </button>
                      <div
                        style={{
                          maxHeight: expandedSections.info ? "300px" : "0px",
                          overflow: "hidden",
                          transition: "max-height 0.25s ease",
                        }}
                      >
                        <div className="px-2.5 py-2 flex flex-col gap-2">
                          <div className="text-[11px] text-[var(--color-text-2)] leading-relaxed">
                            {activeDisease.description}
                          </div>
                          <div className="grid grid-cols-2 gap-2">
                            <div className="p-2 bg-[var(--color-surface-2)] border border-[var(--color-border-soft)] rounded-md">
                              <div className="text-[10px] uppercase text-[var(--color-text-3)]">Vùng WHO</div>
                              <div className="text-sm font-semibold">
                                {selectedRegionLabel ?? selectedCountry?.who_region ?? "—"}
                              </div>
                            </div>
                            <div className="p-2 bg-[var(--color-surface-2)] border border-[var(--color-border-soft)] rounded-md">
                              <div className="text-[10px] uppercase text-[var(--color-text-3)]">Tọa độ</div>
                              <div className="text-sm font-semibold tabular-nums">
                                {selectedCountry?.latitude != null && selectedCountry?.longitude != null
                                  ? `${selectedCountry.latitude.toFixed(2)}, ${selectedCountry.longitude.toFixed(2)}`
                                  : "—"}
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Section: Dự báo hiện tại */}
                    <div className="border border-[var(--color-border-soft)] rounded-lg overflow-hidden">
                      <button
                        onClick={() => toggleSection("stats")}
                        className="w-full flex items-center justify-between px-2.5 py-1.5 bg-[var(--color-surface-2)] hover:bg-[var(--color-surface-3)] transition-colors text-left"
                      >
                        <span className="text-[10px] font-semibold uppercase tracking-[0.06em] text-[var(--color-text-3)]">
                          Dự báo tuần đang xem
                        </span>
                        <span
                          className="text-[var(--color-text-3)] text-[10px]"
                          style={{
                            display: "inline-block",
                            transform: expandedSections.stats ? "rotate(180deg)" : "rotate(0deg)",
                            transition: "transform 0.2s ease",
                          }}
                        >
                          ▼
                        </span>
                      </button>
                      <div
                        style={{
                          maxHeight: expandedSections.stats ? "200px" : "0px",
                          overflow: "hidden",
                          transition: "max-height 0.25s ease",
                        }}
                      >
                        <div className="px-2.5 py-2">
                          <div className="grid grid-cols-2 gap-2">
                            <div className="p-2 bg-[var(--color-surface-2)] border border-[var(--color-border-soft)] rounded-md">
                              <div className="text-[10px] uppercase text-[var(--color-text-3)]">Số ca dự báo</div>
                              <div className="text-sm font-semibold tabular-nums">
                                {predictionLoading
                                  ? "…"
                                  : prediction?.predicted_cases !== null && prediction?.predicted_cases !== undefined
                                  ? Math.round(prediction.predicted_cases).toLocaleString()
                                  : "—"}
                              </div>
                            </div>
                            <div className="p-2 bg-[var(--color-surface-2)] border border-[var(--color-border-soft)] rounded-md">
                              <div className="text-[10px] uppercase text-[var(--color-text-3)]">Tuần</div>
                              <div className="text-sm font-semibold tabular-nums">
                                {String(activeWeek).padStart(2, "0")}/{activeYear}
                              </div>
                            </div>
                          </div>
                          {/* Giải thích: risk_level (classifier) độc lập với predicted_cases (regressor) */}
                          {prediction?.risk_level && prediction.risk_level.toLowerCase() === "high" && (
                            <div className="mt-2 px-2 py-1.5 rounded-md bg-red-500/10 border border-red-500/20 text-[10px] text-red-300 leading-relaxed">
                              <span className="font-semibold">⚠ Lưu ý:</span> Mức rủi ro CAO phản ánh pattern mùa vụ/khí hậu do model phân loại (XGBoost) dự đoán — độc lập với số ca tuyệt đối. Số ca thấp nhưng pattern điều kiện thuận lợi cho dịch bệnh vẫn cho kết quả High.
                            </div>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Section: Forecast 4 tuần */}
                    <div className="border border-[var(--color-border-soft)] rounded-lg overflow-hidden">
                      <button
                        onClick={() => toggleSection("forecast")}
                        className="w-full flex items-center justify-between px-2.5 py-1.5 bg-[var(--color-surface-2)] hover:bg-[var(--color-surface-3)] transition-colors text-left"
                      >
                        <span className="text-[10px] font-semibold uppercase tracking-[0.06em] text-[var(--color-text-3)]">
                          Dự báo 4 tuần tới {isHistorical ? "(backtest)" : "(mới nhất)"}
                        </span>
                        <span
                          className="text-[var(--color-text-3)] text-[10px]"
                          style={{
                            display: "inline-block",
                            transform: expandedSections.forecast ? "rotate(180deg)" : "rotate(0deg)",
                            transition: "transform 0.2s ease",
                          }}
                        >
                          ▼
                        </span>
                      </button>
                      <div
                        style={{
                          maxHeight: expandedSections.forecast ? "300px" : "0px",
                          overflow: "hidden",
                          transition: "max-height 0.3s ease",
                        }}
                      >
                        <div className="px-2.5 py-2">
                          {forecastLoading && (
                            <div className="text-xs text-[var(--color-text-3)] animate-pulse">Đang tải…</div>
                          )}
                          {!forecastLoading && (!forecast || forecast.points.length === 0) && (
                            <div className="text-xs text-[var(--color-text-3)]">Chưa có dữ liệu dự báo.</div>
                          )}
                          {!forecastLoading && forecast && forecast.points.length > 0 && (
                            <>
                              <div className="flex flex-col gap-1 text-[11px]">
                                {forecast.points.map((p) => (
                                  <div key={p.horizon} className="flex justify-between items-center text-[var(--color-text-2)] py-0.5">
                                    <span>Tuần {String(p.target_iso_week).padStart(2, "0")}/{p.target_iso_year}</span>
                                    <span className="text-[var(--color-text-1)] tabular-nums font-medium">
                                      {Math.round(p.predicted_cases).toLocaleString()} ca
                                    </span>
                                  </div>
                                ))}
                              </div>
                              {/* Note giải thích: forecast dùng regressor, risk dùng classifier — hai model khác nhau */}
                              <div className="mt-2 pt-2 border-t border-[var(--color-border-soft)] text-[10px] text-[var(--color-text-3)] leading-relaxed">
                                <span className="font-semibold text-[var(--color-text-2)]">ℹ Về mức rủi ro vs số ca:</span>{" "}
                                Số ca dự báo (model hồi quy LightGBM/RF) và mức rủi ro % (model phân loại XGBoost) là{" "}
                                <span className="text-[var(--color-text-1)] font-semibold">hai model độc lập</span>.
                                Rủi ro cao dù ít ca = pattern mùa vụ/thời tiết thuận lợi cho dịch bùng phát.
                              </div>
                            </>
                          )}
                        </div>
                      </div>
                    </div>

                    <button
                      onClick={() => navigate(`/country/${selectedIso3}`)}
                      className="h-[30px] rounded-md text-xs font-semibold border border-[var(--color-border)] bg-[var(--color-surface-3)] text-[var(--color-text-1)] hover:border-[var(--color-text-2)] transition-colors"
                    >
                      Xem chi tiết →
                    </button>
                  </>
                )}
              </div>
            )}
          </div>
        )}

        {isRightOpen && (
          <AlertsSidebar
            entries={filteredEntries}
            disease={disease}
            selectedIso3={selectedIso3}
            onSelect={setSelectedIso3}
          />
        )}
      </aside>
    </div>
  );
}
