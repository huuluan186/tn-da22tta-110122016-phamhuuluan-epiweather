import { DISEASES } from "../../constants";
import type { RiskEntry } from "../../types/api";
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
  regions: string[];
  toggleRegion: (id: string) => void;
  entries: RiskEntry[];
  regionEntries: RiskEntry[];
  onApply: () => void;
  onResetLatest: () => void;
  isApplying: boolean;
  isDirty: boolean;
  isHistorical: boolean;
  riskLevels: string[];
  toggleRiskLevel: (level: string) => void;
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
      className={`px-4 pt-3 pb-4 border-b border-[var(--color-border-soft)] last:border-b-0 ${
        flex ? "flex-1" : ""
      }`}
    >
      <div className="text-[10px] font-semibold tracking-[0.08em] text-[var(--color-text-3)] uppercase mb-2.5">
        {label}
      </div>
      {children}
    </div>
  );
}

export default function RiskMapSidebar(props: Props) {
  const activeDisease = DISEASES.find((d) => d.id === props.disease)!;

  return (
    <aside className="w-[280px] shrink-0 border-r border-[var(--color-border)] bg-[var(--color-surface)] overflow-y-auto flex flex-col">
      <SideSection label="Bệnh">
        <DiseaseTabs value={props.disease} onChange={props.setDisease} />
      </SideSection>

      <SideSection label="Lịch sử / Realtime">
        <WeekPicker
          disease={props.disease}
          year={props.year}
          week={props.week}
          onYearChange={props.setYear}
          onWeekChange={props.setWeek}
        />
        <div className="mt-3 flex gap-2">
          <button
            onClick={props.onApply}
            disabled={props.isApplying || !props.isDirty}
            title={
              props.isApplying
                ? "Đang tải dữ liệu…"
                : !props.isDirty
                ? "Đổi Năm hoặc Tuần ở trên rồi nhấn để xem dự báo tuần khác"
                : "Tải bản đồ tuần đã chọn"
            }
            className={`flex-1 h-[34px] rounded-md text-xs font-semibold tracking-wide border transition-colors ${
              props.isApplying || !props.isDirty
                ? "bg-[var(--color-surface-2)] text-[var(--color-text-3)] border-[var(--color-border)] cursor-not-allowed"
                : "bg-[#3b82f6] text-white border-[#3b82f6] hover:bg-[#2563eb]"
            }`}
          >
            {props.isApplying
              ? "Đang dự báo…"
              : !props.isDirty
              ? "Đang xem tuần hiện tại"
              : "Dự báo tuần đã chọn"}
          </button>
          {props.isHistorical && (
            <button
              onClick={props.onResetLatest}
              disabled={props.isApplying}
              title="Quay về tuần mới nhất"
              className="h-[34px] px-3 rounded-md text-xs font-semibold border border-[var(--color-border)] bg-[var(--color-surface-3)] text-[var(--color-text-2)] hover:text-[var(--color-text-1)] transition-colors"
            >
              ⟲ Mới nhất
            </button>
          )}
        </div>
      </SideSection>

      <SideSection label="Vùng WHO">
        <RegionFilter
          value={props.regions}
          onToggle={props.toggleRegion}
          entries={props.regionEntries}
          riskLevels={props.riskLevels}
          onToggleRiskLevel={props.toggleRiskLevel}
        />
      </SideSection>

      <SideSection label={`Tóm tắt · ${activeDisease.label}`} flex>
        <SummaryStats disease={props.disease} week={props.week} entries={props.entries} />
      </SideSection>
    </aside>
  );
}
