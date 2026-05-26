import { useMemo, useState } from "react";
import { DISEASES } from "../../constants";
import type { RiskEntry } from "../../types/api";
import type { DiseaseId } from "../../types/domain";
import AlertItem, { type AlertCountry } from "./AlertItem";

interface Props {
  entries: RiskEntry[];
  disease: DiseaseId;
}

export default function AlertsSidebar({ entries, disease }: Props) {
  const [sortBy, setSortBy] = useState<"score" | "name">("score");

  const filtered = useMemo(() => {
    const list: AlertCountry[] = entries
      .filter((e) => e.risk !== "none")
      .map((e) => ({
        iso3: e.iso3,
        iso2: e.iso3.slice(0, 2),
        name: e.countryName,
        region: e.whoRegion ?? "",
        disease,
        timeAgo: "",
        risk: e.risk,
        score: e.score,
        predictedCases: e.predictedCases,
      }));

    if (sortBy === "score") list.sort((a, b) => b.score - a.score);
    else if (sortBy === "name") list.sort((a, b) => a.name.localeCompare(b.name));
    return list;
  }, [entries, disease, sortBy]);

  const selectClass =
    "h-[26px] flex-1 min-w-[80px] bg-[var(--color-surface-3)] border border-[var(--color-border)] rounded-[5px] text-[var(--color-text-1)] text-[11px] px-1.5 cursor-pointer focus:outline-none focus:border-[var(--color-text-3)]";
  const labelClass =
    "text-[10px] text-[var(--color-text-3)] font-semibold uppercase tracking-[.06em] whitespace-nowrap";

  return (
    <div className="flex-1 min-h-0 bg-[var(--color-surface)] flex flex-col overflow-hidden">
      <div className="px-4 py-3.5 border-b border-[var(--color-border-soft)] flex items-center justify-between">
        <h3 className="m-0 text-[13px] font-semibold flex gap-2 items-center">
          Cảnh báo
          <span className="bg-[var(--color-surface-3)] text-[var(--color-text-1)] text-[11px] px-[7px] py-px rounded-[10px]">
            {filtered.length}
          </span>
        </h3>
        <span className="text-[11px] text-[var(--color-text-3)]">
          {DISEASES.find((d) => d.id === disease)?.label}
        </span>
      </div>

      <div className="px-3 py-2 border-b border-[var(--color-border-soft)] bg-[var(--color-surface-2)] flex gap-1.5 items-center flex-wrap">
        <span className={labelClass}>Sắp xếp</span>
        <select
          className={selectClass}
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value as "score" | "name")}
        >
          <option value="score">Theo điểm (rủi ro cao nhất trước)</option>
          <option value="name">Theo tên (A→Z)</option>
        </select>
      </div>

      <div className="flex-1 overflow-y-auto">
        {filtered.length === 0 && (
          <div className="p-6 text-center text-[var(--color-text-3)] text-xs">
            Không có cảnh báo nào khớp với bộ lọc hiện tại.
          </div>
        )}
        {filtered.map((item) => (
          <AlertItem key={item.iso3} item={item} />
        ))}
      </div>
    </div>
  );
}
