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
] as const;

export default function TopNav({ week, year }: Props) {
	return (
		<header className="app-chrome h-[56px] flex items-center gap-8 px-5 border-b shrink-0 overflow-hidden">
			<Logo />

			<nav className="flex gap-0.5">
				{ROUTES.map((r) => (
					<NavLink
						key={r.to}
						to={r.to}
						end={r.to === "/"}
						className={({ isActive }) =>
							`px-3.5 py-2 rounded-md text-[13px] font-medium border cursor-pointer transition-colors ${
								isActive
									? "text-white bg-[var(--color-panel-raised)] border-[var(--color-panel-border)]"
									: "text-slate-300 border-transparent hover:text-white hover:bg-white/10 hover:border-white/15"
							}`
						}
					>
						{r.label}
					</NavLink>
				))}
			</nav>

			<div className="ml-auto flex items-center gap-2 px-3 py-1.5 bg-[var(--color-panel-inset)] border border-[var(--color-panel-border)] rounded-md text-xs font-medium tabular-nums">
				<PulseDot />
				<span className="text-[var(--color-text-3)]">MỚI NHẤT</span>
				<span className="flex flex-col text-right leading-tight text-[var(--color-text-1)]">
					<span>Tuần {String(week).padStart(2, "0")}</span>
					<span className="text-[10px] text-slate-300">Năm {year}</span>
				</span>
			</div>
		</header>
	);
}
