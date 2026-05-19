import { useMemo, useState } from "react";
import { DISEASES, RISK_ORDER } from "../../constants";
import { mockRiskScore } from "../../lib/mockRisk";
import type { DiseaseId, RiskLevel } from "../../types/domain";
import AlertItem, { type AlertCountry } from "./AlertItem";

const ALERT_COUNTRIES: AlertCountry[] = [
  { iso3: "BRA", iso2: "BR", name: "Brazil", region: "AMRO", disease: "dengue", timeAgo: "1 h ago" },
  { iso3: "USA", iso2: "US", name: "United States", region: "AMRO", disease: "flu", timeAgo: "3 h ago" },
  { iso3: "JPN", iso2: "JP", name: "Japan", region: "WPRO", disease: "flu", timeAgo: "5 h ago" },
  { iso3: "IND", iso2: "IN", name: "India", region: "SEARO", disease: "dengue", timeAgo: "6 h ago" },
  { iso3: "VNM", iso2: "VN", name: "Vietnam", region: "WPRO", disease: "dengue", timeAgo: "8 h ago" },
  { iso3: "DEU", iso2: "DE", name: "Germany", region: "EURO", disease: "flu", timeAgo: "9 h ago" },
  { iso3: "GBR", iso2: "GB", name: "United Kingdom", region: "EURO", disease: "flu", timeAgo: "10 h ago" },
  { iso3: "MEX", iso2: "MX", name: "Mexico", region: "AMRO", disease: "dengue", timeAgo: "12 h ago" },
  { iso3: "IDN", iso2: "ID", name: "Indonesia", region: "SEARO", disease: "dengue", timeAgo: "14 h ago" },
  { iso3: "PHL", iso2: "PH", name: "Philippines", region: "WPRO", disease: "dengue", timeAgo: "16 h ago" },
  { iso3: "NGA", iso2: "NG", name: "Nigeria", region: "AFRO", disease: "flu", timeAgo: "18 h ago" },
  { iso3: "ZAF", iso2: "ZA", name: "South Africa", region: "AFRO", disease: "flu", timeAgo: "20 h ago" },
  { iso3: "KOR", iso2: "KR", name: "South Korea", region: "WPRO", disease: "flu", timeAgo: "22 h ago" },
  { iso3: "PER", iso2: "PE", name: "Peru", region: "AMRO", disease: "dengue", timeAgo: "1 d ago" },
  { iso3: "THA", iso2: "TH", name: "Thailand", region: "SEARO", disease: "dengue", timeAgo: "1 d ago" },
];

interface Props {
  week: number;
}

export default function AlertsSidebar({ week }: Props) {
  const [filterDisease, setFilterDisease] = useState<"all" | DiseaseId>("all");
  const [filterRisk, setFilterRisk] = useState<"all" | RiskLevel>("all");
  const [sortBy, setSortBy] = useState<"risk" | "score" | "name">("risk");

  const filtered = useMemo(() => {
    let list = ALERT_COUNTRIES.map((item) => ({
      ...item,
      profile: mockRiskScore(item.iso3, item.disease, week),
    }));
    if (filterDisease !== "all") list = list.filter((a) => a.disease === filterDisease);
    if (filterRisk !== "all") list = list.filter((a) => a.profile.risk === filterRisk);
    if (sortBy === "risk") list.sort((a, b) => RISK_ORDER[b.profile.risk] - RISK_ORDER[a.profile.risk]);
    else if (sortBy === "score") list.sort((a, b) => b.profile.score - a.profile.score);
    else if (sortBy === "name") list.sort((a, b) => a.name.localeCompare(b.name));
    return list;
  }, [week, filterDisease, filterRisk, sortBy]);

  const selectClass =
    "h-[26px] flex-1 min-w-[80px] bg-[var(--color-surface-3)] border border-[var(--color-border)] rounded-[5px] text-[var(--color-text-1)] text-[11px] px-1.5 cursor-pointer focus:outline-none focus:border-[var(--color-text-3)]";
  const labelClass =
    "text-[10px] text-[var(--color-text-3)] font-semibold uppercase tracking-[.06em] whitespace-nowrap";

  return (
    <aside className="w-[380px] shrink-0 border-l border-[var(--color-border)] bg-[var(--color-surface)] flex flex-col overflow-hidden">
      <div className="px-4 py-3.5 border-b border-[var(--color-border-soft)] flex items-center justify-between">
        <h3 className="m-0 text-[13px] font-semibold flex gap-2 items-center">
          Active Alerts
          <span className="bg-[var(--color-surface-3)] text-[var(--color-text-1)] text-[11px] px-[7px] py-px rounded-[10px]">
            {filtered.length}
          </span>
        </h3>
      </div>

      <div className="px-3 py-2 border-b border-[var(--color-border-soft)] bg-[var(--color-surface-2)] flex gap-1.5 items-center flex-wrap">
        <span className={labelClass}>Disease</span>
        <select
          className={selectClass}
          value={filterDisease}
          onChange={(e) => setFilterDisease(e.target.value as "all" | DiseaseId)}
        >
          <option value="all">All</option>
          {DISEASES.map((d) => (
            <option key={d.id} value={d.id}>{d.label}</option>
          ))}
        </select>
      </div>
      <div className="px-3 py-2 border-b border-[var(--color-border-soft)] bg-[var(--color-surface-2)] flex gap-1.5 items-center flex-wrap">
        <span className={labelClass}>Risk</span>
        <select
          className={selectClass}
          value={filterRisk}
          onChange={(e) => setFilterRisk(e.target.value as "all" | RiskLevel)}
        >
          <option value="all">All levels</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
        <span className={`${labelClass} ml-1`}>Sort</span>
        <select
          className={selectClass}
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value as "risk" | "score" | "name")}
        >
          <option value="risk">By Risk</option>
          <option value="score">By Score</option>
          <option value="name">By Name</option>
        </select>
      </div>

      <div className="flex-1 overflow-y-auto">
        {filtered.length === 0 && (
          <div className="p-6 text-center text-[var(--color-text-3)] text-xs">
            No alerts match the current filters.
          </div>
        )}
        {filtered.map((item) => (
          <AlertItem key={item.iso3} item={item} week={week} />
        ))}
      </div>
    </aside>
  );
}
