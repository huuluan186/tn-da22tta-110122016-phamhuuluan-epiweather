import { NavLink } from "react-router-dom";
import Icon from "../common/Icon";
import PulseDot from "../common/PulseDot";

interface Props {
  week: number;
  year: number;
}

const ROUTES = [
  { label: "Risk Map", to: "/" },
  { label: "Analytics", to: "/analytics" },
  { label: "Country Detail", to: "/country" },
] as const;

export default function TopNav({ week, year }: Props) {
  return (
    <header className="h-14 flex items-center gap-8 px-5 border-b border-[var(--color-border)] bg-[var(--color-surface)] shrink-0">
      <div className="flex items-center gap-2.5 font-bold text-[15px] tracking-tight">
        <span className="w-[26px] h-[26px] rounded-md bg-gradient-to-br from-[#3b82f6] to-[#8b5cf6] grid place-items-center" />
        EpiWatch
      </div>

      <nav className="flex gap-0.5">
        {ROUTES.map((r) => (
          <NavLink
            key={r.to}
            to={r.to}
            end={r.to === "/"}
            className={({ isActive }) =>
              `px-3.5 py-2 rounded-md text-[13px] font-medium cursor-pointer transition-colors ${
                isActive
                  ? "text-[var(--color-text-1)] bg-[var(--color-surface-3)]"
                  : "text-[var(--color-text-2)] hover:text-[var(--color-text-1)] hover:bg-[var(--color-surface-3)]"
              }`
            }
          >
            {r.label}
          </NavLink>
        ))}
      </nav>

      <div className="ml-auto flex items-center gap-4">
        <div className="flex items-center gap-2 px-3 py-1.5 bg-[var(--color-surface-2)] border border-[var(--color-border)] rounded-md text-xs font-medium tabular-nums">
          <PulseDot />
          <span className="text-[var(--color-text-3)]">LIVE</span>
          <span className="text-[var(--color-text-1)]">
            W{String(week).padStart(2, "0")} · {year}
          </span>
        </div>
        <button className="w-8 h-8 grid place-items-center rounded-md text-[var(--color-text-2)] hover:bg-[var(--color-surface-3)] hover:text-[var(--color-text-1)]">
          <Icon name="search" />
        </button>
        <div className="w-7 h-7 rounded-full bg-gradient-to-br from-[#3b82f6] to-[#8b5cf6] grid place-items-center text-[11px] font-semibold text-white">
          DR
        </div>
      </div>
    </header>
  );
}
