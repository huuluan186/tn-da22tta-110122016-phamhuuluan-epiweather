import { DISEASES } from "../../constants";
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
      className={`px-4 py-4 border-b border-[var(--color-border-soft)] last:border-b-0 ${
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
      <SideSection label="Disease">
        <DiseaseTabs value={props.disease} onChange={props.setDisease} />
      </SideSection>

      <SideSection label="Reporting Week">
        <WeekPicker
          year={props.year}
          week={props.week}
          onYearChange={props.setYear}
          onWeekChange={props.setWeek}
        />
      </SideSection>

      <SideSection label="WHO Region">
        <RegionFilter
          value={props.regions}
          onToggle={props.toggleRegion}
          disease={props.disease}
          week={props.week}
        />
      </SideSection>

      <SideSection label={`Summary · ${activeDisease.label}`} flex>
        <SummaryStats disease={props.disease} week={props.week} />
      </SideSection>
    </aside>
  );
}
