import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import AlertsSidebar from "../components/alerts/AlertsSidebar";
import MapLegend from "../components/map/MapLegend";
import WorldMap from "../components/map/WorldMap";
import RiskMapSidebar from "../components/sidebar/RiskMapSidebar";
import { DISEASES, RISK_LEVELS } from "../constants";
import { useCountries } from "../hooks/useCountries";
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

  // applied = null → dùng latest (mặc định); != null → dùng historical
  const [applied, setApplied] = useState<Applied>(null);
  const activeDisease = DISEASES.find((d) => d.id === disease)!;
  const isHistorical = applied !== null;

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

  // Historical mode (chỉ fetch khi user apply picker)
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
  // để TopNav "REALTIME" luôn phản ánh tuần mới nhất thực sự có data.
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

  // Selected country detail — historical thì dùng forecast, latest thì dùng nowcast
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

  const selectedName = selectedIso3 ? (ECHARTS_COUNTRY_NAMES[selectedIso3] ?? selectedIso3) : null;
  const riskKey = (() => {
    const raw = prediction?.risk_level?.toLowerCase() ?? "";
    if (raw === "high" || raw === "medium" || raw === "low") return raw;
    return "none";
  })() as keyof typeof RISK_LEVELS;
  const riskLabel = RISK_LEVELS[riskKey].label;
  const riskColor = RISK_LEVELS[riskKey].color;

  const applyHistorical = () => setApplied({ year, week });
  const resetToLatest = () => {
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
                  LỊCH SỬ
                </span>
              ) : (
                <span className="px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-300 font-semibold tracking-wide">
                  MỚI NHẤT
                </span>
              )}
              <span>
                Tuần {String(activeWeek).padStart(2, "0")} · {activeYear}
              </span>
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
            onCountrySelect={(echartsName) => {
              const iso3 = ISO3_BY_ECHARTS_NAME[echartsName];
              if (!iso3) return;
              setSelectedIso3(iso3);
            }}
          />
          <MapLegend />
        </div>
      </div>

      <aside className="hidden lg:flex w-[360px] shrink-0 border-l border-[var(--color-border)] bg-[var(--color-surface)] flex-col min-h-0">
        <div className="px-4 pt-3 pb-4 border-b border-[var(--color-border-soft)]">
          <div className="text-[10px] font-semibold tracking-[0.08em] text-[var(--color-text-3)] uppercase mb-2.5">
            Quốc gia đã chọn
          </div>
          {!selectedIso3 && (
            <div className="text-xs text-[var(--color-text-3)]">
              Chọn một quốc gia trên bản đồ để xem chi tiết.
            </div>
          )}
          {selectedIso3 && (
            <div className="flex flex-col gap-3">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <div className="text-sm font-semibold text-[var(--color-text-1)]">{selectedName}</div>
                  <div className="text-[11px] text-[var(--color-text-3)]">
                    {selectedIso3} · {activeDisease.label}
                  </div>
                </div>
                <div
                  className="px-2 py-0.5 rounded-md text-[10px] font-bold text-white"
                  style={{ backgroundColor: riskColor }}
                >
                  {predictionLoading ? "…" : riskLabel}
                </div>
              </div>

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

              <div className="border border-[var(--color-border-soft)] rounded-md p-2 bg-[var(--color-surface-2)]">
                <div className="text-[10px] uppercase text-[var(--color-text-3)] mb-1">
                  Dự báo 4 tuần tới {isHistorical ? "(lịch sử)" : "(realtime)"}
                </div>
                {forecastLoading && (
                  <div className="text-xs text-[var(--color-text-3)] animate-pulse">Đang tải…</div>
                )}
                {!forecastLoading && (!forecast || forecast.points.length === 0) && (
                  <div className="text-xs text-[var(--color-text-3)]">Chưa có dữ liệu dự báo.</div>
                )}
                {!forecastLoading && forecast && forecast.points.length > 0 && (
                  <div className="flex flex-col gap-1 text-[11px]">
                    {forecast.points.map((p) => (
                      <div key={p.horizon} className="flex justify-between text-[var(--color-text-2)]">
                        <span>
                          Tuần {String(p.target_iso_week).padStart(2, "0")}/{p.target_iso_year}
                        </span>
                        <span className="text-[var(--color-text-1)] tabular-nums">
                          {Math.round(p.predicted_cases).toLocaleString()} ca
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <button
                onClick={() => navigate(`/country/${selectedIso3}`)}
                className="h-[30px] rounded-md text-xs font-semibold border border-[var(--color-border)] bg-[var(--color-surface-3)] text-[var(--color-text-1)] hover:border-[var(--color-text-2)] transition-colors"
              >
                Xem chi tiết →
              </button>
            </div>
          )}
        </div>

        <AlertsSidebar entries={filteredEntries} disease={disease} />
      </aside>
    </div>
  );
}
