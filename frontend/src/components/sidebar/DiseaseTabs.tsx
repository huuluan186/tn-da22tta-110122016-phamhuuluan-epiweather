import { DISEASES } from "../../constants";
import type { DiseaseId } from "../../types/domain";

interface Props {
  value: DiseaseId;
  onChange: (id: DiseaseId) => void;
}

export default function DiseaseTabs({ value, onChange }: Props) {
  return (
    <div className="flex flex-col gap-1">
      {DISEASES.map((d) => {
        const active = value === d.id;
        return (
          <button
            key={d.id}
            onClick={() => onChange(d.id)}
            className={`flex items-center gap-2.5 px-2.5 py-2 rounded-md text-left text-sm font-medium transition-colors border ${
              active
                ? "bg-[var(--color-surface-3)] text-[var(--color-text-1)] border-[var(--color-border)]"
                : "bg-transparent text-[var(--color-text-2)] border-transparent hover:bg-[var(--color-surface-3)] hover:text-[var(--color-text-1)]"
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
