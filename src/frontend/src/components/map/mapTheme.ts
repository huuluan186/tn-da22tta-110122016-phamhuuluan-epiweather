import type { RiskLevel } from "../../types/domain";

export type MapTheme = "dark" | "light";

export const MAP_THEME_STORAGE_KEY = "epiwatch-map-theme";

export interface MapThemePalette {
	canvas: string;
	land: string;
	border: string;
	riskBorder: string;
	emphasis: string;
	emphasisBorder: string;
	tooltipBackground: string;
	tooltipBorder: string;
	tooltipText: string;
	surface: string;
	surfaceBorder: string;
	mutedText: string;
	riskColors: Record<RiskLevel, string>;
}

export const MAP_THEME_PALETTES: Record<MapTheme, MapThemePalette> = {
	dark: {
		canvas: "var(--color-map-dark-ocean)",
		land: "var(--color-map-dark-land)",
		border: "var(--color-map-dark-border)",
		riskBorder: "var(--color-map-dark-risk-border)",
		emphasis: "var(--color-map-dark-emphasis)",
		emphasisBorder: "var(--color-map-dark-emphasis-border)",
		tooltipBackground: "var(--color-map-dark-tooltip)",
		tooltipBorder: "var(--color-map-dark-tooltip-border)",
		tooltipText: "var(--color-map-dark-text)",
		surface: "var(--color-map-dark-surface)",
		surfaceBorder: "var(--color-map-dark-surface-border)",
		mutedText: "var(--color-map-dark-muted)",
		riskColors: {
			none: "var(--color-map-dark-risk-none)",
			low: "var(--color-map-dark-risk-low)",
			medium: "var(--color-map-dark-risk-med)",
			high: "var(--color-map-dark-risk-high)",
		},
	},
	light: {
		canvas: "var(--color-map-light-ocean)",
		land: "var(--color-map-light-land)",
		border: "var(--color-map-light-border)",
		riskBorder: "var(--color-map-light-risk-border)",
		emphasis: "var(--color-map-light-emphasis)",
		emphasisBorder: "var(--color-map-light-emphasis-border)",
		tooltipBackground: "var(--color-map-light-tooltip)",
		tooltipBorder: "var(--color-map-light-tooltip-border)",
		tooltipText: "var(--color-map-light-text)",
		surface: "var(--color-map-light-surface)",
		surfaceBorder: "var(--color-map-light-surface-border)",
		mutedText: "var(--color-map-light-muted)",
		riskColors: {
			none: "var(--color-map-light-risk-none)",
			low: "var(--color-map-light-risk-low)",
			medium: "var(--color-map-light-risk-med)",
			high: "var(--color-map-light-risk-high)",
		},
	},
};

export function resolveMapThemePalette(theme: MapTheme): MapThemePalette {
	const rootStyles = getComputedStyle(document.documentElement);
	const resolveColor = (color: string) => {
		const token = color.match(/^var\((--[^)]+)\)$/)?.[1];
		return token ? rootStyles.getPropertyValue(token).trim() : color;
	};
	const palette = MAP_THEME_PALETTES[theme];

	return {
		canvas: resolveColor(palette.canvas),
		land: resolveColor(palette.land),
		border: resolveColor(palette.border),
		riskBorder: resolveColor(palette.riskBorder),
		emphasis: resolveColor(palette.emphasis),
		emphasisBorder: resolveColor(palette.emphasisBorder),
		tooltipBackground: resolveColor(palette.tooltipBackground),
		tooltipBorder: resolveColor(palette.tooltipBorder),
		tooltipText: resolveColor(palette.tooltipText),
		surface: resolveColor(palette.surface),
		surfaceBorder: resolveColor(palette.surfaceBorder),
		mutedText: resolveColor(palette.mutedText),
		riskColors: {
			none: resolveColor(palette.riskColors.none),
			low: resolveColor(palette.riskColors.low),
			medium: resolveColor(palette.riskColors.medium),
			high: resolveColor(palette.riskColors.high),
		},
	};
}
