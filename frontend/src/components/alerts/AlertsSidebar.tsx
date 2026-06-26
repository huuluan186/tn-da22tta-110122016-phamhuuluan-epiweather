import { useMemo, useState } from "react";
import { useDiseases } from "../../hooks/useDiseases";
import type { RiskEntry } from "../../types/api";
import type { DiseaseId } from "../../types/domain";
import AlertItem, { type AlertCountry } from "./AlertItem";

interface Props {
  entries: RiskEntry[];
  disease: DiseaseId;
  iso2ByIso3: ReadonlyMap<string, string>;
  selectedIso3?: string | null;
  onSelect?: (iso3: string) => void;
}

type SortOption = "score-desc" | "score-asc" | "name-asc" | "name-desc";

export default function AlertsSidebar({
  entries,
  disease,
  iso2ByIso3,
  selectedIso3,
  onSelect,
}: Props) {
  const [sortBy, setSortBy] = useState<SortOption>("score-desc");
  const { getDisease } = useDiseases();
  const activeDisease = getDisease(disease);

  const filtered = useMemo(() => {
    const list: AlertCountry[] = entries
      .filter((e) => e.risk !== "none")
      .map((e) => ({
        iso3: e.iso3,
        iso2: iso2ByIso3.get(e.iso3) ?? null,
        name: e.countryName,
        region: e.whoRegion ?? "",
        disease,
        timeAgo: "",
        risk: e.risk,
        score: e.score,
        predictedCases: e.predictedCases,
      }));

    if (sortBy === "score-desc") list.sort((a, b) => b.score - a.score);
    else if (sortBy === "score-asc") list.sort((a, b) => a.score - b.score);
    else if (sortBy === "name-asc") list.sort((a, b) => a.name.localeCompare(b.name));
    else if (sortBy === "name-desc") list.sort((a, b) => b.name.localeCompare(a.name));
    return list;
  }, [entries, disease, iso2ByIso3, sortBy]);

  const selectClass =
    "h-[26px] flex-1 min-w-[80px] bg-[var(--color-panel-inset)] border border-[var(--color-panel-border)] rounded-[5px] text-white text-[11px] px-1.5 cursor-pointer focus:outline-none focus:border-white";
  const labelClass =
    "text-[10px] text-slate-100 font-bold uppercase tracking-[.06em] whitespace-nowrap";

  return (
    <div className="flex-1 min-h-0 bg-transparent flex flex-col overflow-hidden border-t border-[var(--color-focus-border)]">
      <div className="px-4 py-3 border-b border-[var(--color-focus-border)] bg-[var(--color-focus-raised)] flex items-center justify-between">
        <h3 className="m-0 flex gap-2 items-center">
          <span className="dashboard-panel-title">Cảnh báo</span>
          <span className="bg-[var(--color-panel-inset)] border border-[var(--color-panel-border)] text-slate-100 text-[11px] px-[7px] py-px rounded-[10px]">
            {filtered.length}
          </span>
        </h3>
        <span className="text-[11px] font-medium text-slate-100">
          {activeDisease.label}
        </span>
      </div>

      <div className="px-3 py-2 border-b border-[var(--color-panel-border)] bg-[var(--color-panel-inset)] flex gap-1.5 items-center flex-wrap">
        <span className={labelClass}>Sắp xếp</span>
        <select
          className={selectClass}
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value as SortOption)}
        >
          <option value="score-desc">Mức độ: cao đến thấp</option>
          <option value="score-asc">Mức độ: thấp đến cao</option>
          <option value="name-asc">Tên quốc gia: A đến Z</option>
          <option value="name-desc">Tên quốc gia: Z đến A</option>
        </select>
      </div>

      <div className="flex-1 overflow-y-auto">
        {filtered.length === 0 && (
          <div className="p-6 text-center text-slate-100 text-xs">
            Không có cảnh báo nào khớp với bộ lọc hiện tại.
          </div>
        )}
        {filtered.map((item) => (
          <AlertItem
            key={item.iso3}
            item={item}
            isSelected={selectedIso3 === item.iso3}
            onSelect={onSelect}
          />
        ))}
      </div>
    </div>
  );
}
