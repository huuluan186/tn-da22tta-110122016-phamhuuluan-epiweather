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
	};
}
