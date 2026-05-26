import { NavLink } from "react-router-dom";
import PulseDot from "../common/PulseDot";
import Logo from "./Logo";

interface Props {
  week: number;
  year: number;
}

const ROUTES = [
  { label: "Bản đồ rủi ro", to: "/" },
  { label: "Phân tích", to: "/analytics" },
  { label: "Chi tiết quốc gia", to: "/country" },
] as const;

export default function TopNav({ week, year }: Props) {
  return (
    <header className="h-[56px] flex items-center gap-8 px-5 border-b border-[var(--color-border)] bg-[var(--color-surface)] shrink-0">
      <Logo />

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

      <div className="ml-auto flex items-center gap-2 px-3 py-1.5 bg-[var(--color-surface-2)] border border-[var(--color-border)] rounded-md text-xs font-medium tabular-nums">
        <PulseDot />
        <span className="text-[var(--color-text-3)]">REALTIME</span>
        <span className="text-[var(--color-text-1)]">
          Tuần {String(week).padStart(2, "0")} · {year}
        </span>
      </div>
    </header>
  );
}
