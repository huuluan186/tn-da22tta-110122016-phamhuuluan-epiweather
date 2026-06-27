import { useDiseases } from "../../hooks/useDiseases";
import type { DiseaseId } from "../../types/domain";

interface Props {
  value: DiseaseId;
  onChange: (id: DiseaseId) => void;
}

export default function DiseaseTabs({ value, onChange }: Props) {
  const { diseases } = useDiseases();

  return (
    <div className="flex flex-col gap-1">
      {diseases.map((d) => {
        const active = value === d.id;
        return (
          <button
            key={d.id}
            onClick={() => onChange(d.id)}
            className={`flex items-center gap-2.5 px-2.5 py-2 rounded-md text-left text-sm font-medium transition-colors border ${
              active
                ? "bg-[#245b8f] text-white border-[#60a5fa]"
                : "bg-[var(--color-panel-inset)] text-slate-100 border-[var(--color-panel-border)] hover:bg-[var(--color-panel-raised)] hover:text-white"
            }`}
          >
            <span className="w-2.5 h-2.5 rounded-sm shrink-0" style={{ background: d.color }} />
            <span className="flex-1">{d.label}</span>
          </button>
        );
      })}
    </div>
  );
}
