import type { MapTheme } from "./mapTheme";

interface Props {
	theme: MapTheme;
	onChange: (theme: MapTheme) => void;
}

export default function MapThemeToggle({ theme, onChange }: Props) {
	const isLight = theme === "light";

	return (
		<div
			className={`flex shrink-0 items-center gap-0.5 rounded-lg border p-1 shadow-sm ${
				isLight
					? "border-map-light-surface-border bg-map-light-surface"
					: "border-map-dark-surface-border bg-map-dark-surface text-map-dark-muted"
			}`}
			role="group"
			aria-label="Chọn nền bản đồ"
		>
			<button
				type="button"
				aria-label="Chuyển nền bản đồ sang chế độ tối"
				aria-pressed={theme === "dark"}
				title="Chế độ tối"
				onClick={() => onChange("dark")}
				className={`grid h-7 w-7 place-items-center rounded-md transition-colors ${
					theme === "dark"
						? "bg-slate-100 text-slate-900 shadow-sm"
						: "text-slate-600 hover:bg-slate-400/40 hover:text-slate-900"
				}`}
			>
				<svg
					width="15"
					height="15"
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
					strokeWidth="2"
					strokeLinecap="round"
					strokeLinejoin="round"
					aria-hidden="true"
				>
					<path d="M21 12.8A9 9 0 1 1 11.2 3 7 7 0 0 0 21 12.8Z" />
				</svg>
			</button>
			<button
				type="button"
				aria-label="Chuyển nền bản đồ sang chế độ sáng"
				aria-pressed={theme === "light"}
				title="Chế độ sáng"
				onClick={() => onChange("light")}
				className={`grid h-7 w-7 place-items-center rounded-md transition-colors ${
					theme === "light"
						? "bg-slate-700 text-amber-300 shadow-sm"
						: "text-slate-400 hover:bg-slate-800 hover:text-amber-300"
				}`}
			>
				<svg
					width="16"
					height="16"
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
					strokeWidth="2"
					strokeLinecap="round"
					strokeLinejoin="round"
					aria-hidden="true"
				>
					<circle cx="12" cy="12" r="4" />
					<path d="M12 2v2M12 20v2M4.93 4.93l1.42 1.42M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.42-1.42M17.66 6.34l1.41-1.41" />
				</svg>
			</button>
		</div>
	);
}
