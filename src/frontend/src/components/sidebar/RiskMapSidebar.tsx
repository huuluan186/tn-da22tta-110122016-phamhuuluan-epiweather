import { useDiseases } from "../../hooks/useDiseases";
import type { RiskEntry, RiskMapPeriod } from "../../types/api";
import type { DiseaseId } from "../../types/domain";
import DiseaseTabs from "./DiseaseTabs";
import RegionFilter from "./RegionFilter";
import SummaryStats from "./SummaryStats";
import WeekPicker from "./WeekPicker";

interface Props {
  disease: DiseaseId;
  setDisease: (d: DiseaseId) => void;
  year: number;
  setYear: (y: number) => void;
  week: number;
  setWeek: (w: number) => void;
  latestYear?: number;
  latestWeek?: number;
  periods?: RiskMapPeriod[];
  activeYear: number;
  activeWeek: number;
  regions: string[];
  toggleRegion: (id: string) => void;
  entries: RiskEntry[];
  regionEntries: RiskEntry[];
  totalReportingCountries: number;
  onApply: () => void;
  onResetLatest: () => void;
  isApplying: boolean;
  isDirty: boolean;
  isHistorical: boolean;
  riskLevels: string[];
  toggleRiskLevel: (level: string) => void;
  isOpen: boolean;
  onToggle: () => void;
}

function SideSection({
  label,
  flex,
  children,
}: {
  label: string;
  flex?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div
      className={`px-4 pt-3 pb-4 border-b border-[var(--color-panel-border)] last:border-b-0 ${
        flex ? "flex-1" : ""
      }`}
    >
      <div className="dashboard-section-title mb-2.5">
        {label}
      </div>
      {children}
    </div>
  );
}

export default function RiskMapSidebar(props: Props) {
  const { getDisease } = useDiseases();
  const activeDisease = getDisease(props.disease);
  const selectedWeekLabel = `Tuần ${String(props.week).padStart(2, "0")} · Năm ${props.year}`;
  const applyTitle = props.isApplying
    ? "Đang tải dữ liệu dự báo"
    : props.isDirty
    ? "Tải dữ liệu dự báo cho tuần/năm đã chọn"
    : props.isHistorical
    ? "Đang hiển thị tuần đã áp dụng"
    : "Đang hiển thị tuần mới nhất có dữ liệu dự báo";
  const applyLabel = props.isApplying
    ? "Đang tải..."
    : props.isDirty
    ? "Dự báo tuần đã chọn"
    : props.isHistorical
    ? `Đang xem ${selectedWeekLabel}`
    : "Đang xem tuần mới nhất";

  return (
    <aside
      className={`shrink-0 border-r border-[var(--color-panel-border)] bg-[var(--color-panel)] overflow-y-auto flex flex-col transition-all ${
        props.isOpen ? "w-[280px]" : "w-[44px]"
      }`}
    >
      <div className="flex items-center justify-between px-3 pt-3 pb-2 border-b border-[var(--color-panel-border)] bg-[var(--color-panel-raised)]">
        {props.isOpen && (
          <div className="dashboard-panel-title">
            Bộ lọc
          </div>
        )}
        <button
          onClick={props.onToggle}
          aria-label={props.isOpen ? "Thu gọn bộ lọc" : "Mở rộng bộ lọc"}
          className="ml-auto w-7 h-7 grid place-items-center rounded-md border border-[var(--color-panel-border)] bg-[var(--color-panel-inset)] text-white hover:border-white hover:bg-[var(--color-panel-raised)] transition-colors"
        >
          {props.isOpen ? "‹" : "›"}
        </button>
      </div>

      {!props.isOpen && (
        <div className="flex-1 grid place-items-center text-[10px] font-bold text-slate-100 tracking-[0.2em] rotate-90">
          BỘ LỌC
        </div>
      )}

      {props.isOpen && (
        <>
          <SideSection label="Bệnh">
            <DiseaseTabs value={props.disease} onChange={props.setDisease} />
          </SideSection>

          <SideSection label="Thời điểm dự báo">
            <WeekPicker
              disease={props.disease}
              year={props.year}
              week={props.week}
              latestYear={props.latestYear}
              latestWeek={props.latestWeek}
              periods={props.periods}
              onYearChange={props.setYear}
              onWeekChange={props.setWeek}
            />
            <div className="mt-3 flex gap-2">
              <button
                onClick={props.onApply}
                disabled={props.isApplying || !props.isDirty}
                title={applyTitle}
                className={`flex-1 h-[34px] rounded-md text-xs font-semibold tracking-wide border transition-colors ${
                  props.isApplying || !props.isDirty
                    ? "bg-[var(--color-panel-inset)] text-slate-400 border-[var(--color-panel-border)] cursor-not-allowed"
                    : "bg-[#3b82f6] text-white border-[#3b82f6] hover:bg-[#2563eb]"
                }`}
              >
                {applyLabel}
              </button>
              {props.isHistorical && (
                <button
                  onClick={props.onResetLatest}
                  disabled={props.isApplying}
                  title="Quay về tuần mới nhất"
                  className="h-[34px] px-3 rounded-md text-xs font-semibold border border-[var(--color-panel-border)] bg-[var(--color-panel-inset)] text-white hover:border-white hover:bg-[var(--color-panel-raised)] transition-colors"
                >
                  ⟲ Mới nhất
                </button>
              )}
            </div>
          </SideSection>

          <SideSection label="Quốc gia theo khu vực">
            <RegionFilter
              value={props.regions}
              onToggle={props.toggleRegion}
              entries={props.regionEntries}
              riskLevels={props.riskLevels}
              onToggleRiskLevel={props.toggleRiskLevel}
            />
          </SideSection>

          <SideSection label={`Tóm tắt · ${activeDisease.label}`} flex>
            <SummaryStats
              disease={props.disease}
              year={props.activeYear}
              week={props.activeWeek}
              entries={props.entries}
              totalReportingCountries={props.totalReportingCountries}
            />
          </SideSection>
        </>
      )}
    </aside>
  );
}
