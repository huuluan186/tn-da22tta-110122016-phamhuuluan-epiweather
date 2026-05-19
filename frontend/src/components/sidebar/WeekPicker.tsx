import Icon from "../common/Icon";

interface Props {
  year: number;
  week: number;
  onYearChange: (y: number) => void;
  onWeekChange: (w: number) => void;
}

const YEARS = Array.from({ length: 17 }, (_, i) => 2010 + i);

export default function WeekPicker({ year, week, onYearChange, onWeekChange }: Props) {
  const pct = (week / 52) * 100;

  return (
    <div>
      <div className="flex items-center gap-1.5 mb-2">
        <select
          value={year}
          onChange={(e) => onYearChange(Number(e.target.value))}
          className="flex-1 h-[30px] bg-[var(--color-surface-2)] border border-[var(--color-border)] rounded-md text-[var(--color-text-1)] text-xs font-semibold px-2 text-center cursor-pointer focus:outline-none focus:border-[var(--color-text-3)]"
        >
          {YEARS.map((y) => (
            <option key={y} value={y}>{y}</option>
          ))}
        </select>
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={() => onWeekChange(Math.max(1, week - 1))}
          className="w-8 h-8 grid place-items-center bg-[var(--color-surface-2)] border border-[var(--color-border)] rounded-md text-[var(--color-text-2)] hover:text-[var(--color-text-1)] hover:border-[var(--color-text-3)]"
        >
          <Icon name="chevron-left" size={14} />
        </button>
        <div className="flex-1 h-8 bg-[var(--color-surface-2)] border border-[var(--color-border)] rounded-md flex items-center justify-center text-xs font-semibold">
          W{String(week).padStart(2, "0")}
        </div>
        <button
          onClick={() => onWeekChange(Math.min(52, week + 1))}
          className="w-8 h-8 grid place-items-center bg-[var(--color-surface-2)] border border-[var(--color-border)] rounded-md text-[var(--color-text-2)] hover:text-[var(--color-text-1)] hover:border-[var(--color-text-3)]"
        >
          <Icon name="chevron-right" size={14} />
        </button>
      </div>

      <div className="mt-2 h-1 bg-[var(--color-surface-2)] rounded-sm overflow-hidden relative">
        <div
          className="absolute inset-y-0 left-0 rounded-sm bg-gradient-to-r from-[#3b82f6] to-[#8b5cf6] transition-[width] duration-200"
          style={{ width: `${pct}%` }}
        />
      </div>
      <div className="mt-1 flex justify-between text-[10px] text-[var(--color-text-3)] tabular-nums">
        <span>W01</span>
        <span>W{String(week).padStart(2, "0")} / 52</span>
        <span>W52</span>
      </div>
    </div>
  );
}
