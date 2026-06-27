import * as echarts from "echarts";
import { useEffect, useMemo, useRef } from "react";
import type { HistoryPoint } from "../../types/api";

// Tái hiện Hình 4.4 trong notebook: heatmap số ca theo tuần (cột) × năm (hàng),
// 2010-2019, để thấy quy luật mùa vụ lặp lại. Dùng số ca thực tế (actual_cases);
// tuần nào không có báo cáo thì để trống.
const YEAR_START = 2010;
const YEAR_END = 2019;
const WEEKS = 53;

// Thang màu YlOrRd giống cmap notebook, đủ sáng để rõ trên nền tối/máy chiếu.
const YL_OR_RD = [
	"#fffbcc",
	"#fee391",
	"#fec44f",
	"#fb9a29",
	"#ec7014",
	"#cc4c02",
	"#993404",
	"#662506",
];

interface Props {
	points: HistoryPoint[];
	disease: "flu" | "dengue";
}

export default function SeasonalHeatmap({ points, disease }: Props) {
	const elRef = useRef<HTMLDivElement>(null);

	const { years, data, max } = useMemo(() => {
		const yearSet = new Set<number>();
		for (const p of points) {
			if (p.iso_year >= YEAR_START && p.iso_year <= YEAR_END) yearSet.add(p.iso_year);
		}
		const years = [...yearSet].sort((a, b) => a - b);
		const yearIndex = new Map(years.map((y, i) => [y, i]));

		const data: [number, number, number][] = [];
		let max = 0;
		for (const p of points) {
			if (p.iso_year < YEAR_START || p.iso_year > YEAR_END) continue;
			const value = p.actual_cases;
			if (value == null) continue;
			const yi = yearIndex.get(p.iso_year);
			if (yi == null) continue;
			data.push([p.iso_week - 1, yi, value]);
			if (value > max) max = value;
		}
		return { years, data, max };
	}, [points]);

	useEffect(() => {
		if (!elRef.current || years.length === 0) return;
		const ch = echarts.init(elRef.current);

		ch.setOption({
			backgroundColor: "transparent",
			grid: { top: 8, right: 12, bottom: 56, left: 48 },
			tooltip: {
				position: "top",
				backgroundColor: "#1a1f2e",
				borderColor: "#334155",
				textStyle: { color: "#f1f5f9", fontSize: 11 },
				formatter: (p: { data: [number, number, number] }) => {
					const [wi, yi, v] = p.data;
					return `Năm ${years[yi]} · Tuần ${String(wi + 1).padStart(2, "0")}<br/><b>${Math.round(v).toLocaleString("vi-VN")}</b> ca`;
				},
			},
			xAxis: {
				type: "category",
				data: Array.from({ length: WEEKS }, (_, i) => i + 1),
				name: "Tuần ISO",
				nameLocation: "middle",
				nameGap: 26,
				nameTextStyle: { color: "#cbd5e1", fontSize: 11 },
				splitArea: { show: false },
				axisLine: { lineStyle: { color: "#64748b" } },
				axisLabel: { color: "#cbd5e1", fontSize: 10, interval: 3 },
				axisTick: { show: false },
			},
			yAxis: {
				type: "category",
				data: years.map(String),
				axisLine: { lineStyle: { color: "#64748b" } },
				axisLabel: { color: "#cbd5e1", fontSize: 11 },
				axisTick: { show: false },
				splitArea: { show: false },
			},
			visualMap: {
				min: 0,
				max: Math.max(max, 1),
				calculable: true,
				orient: "horizontal",
				left: "center",
				bottom: 4,
				itemWidth: 16,
				itemHeight: 200,
				textStyle: { color: "#cbd5e1", fontSize: 10 },
				inRange: { color: YL_OR_RD },
			},
			series: [
				{
					name: "Số ca",
					type: "heatmap",
					data,
					progressive: 0,
					itemStyle: { borderColor: "#0f172a", borderWidth: 0.5 },
					emphasis: { itemStyle: { borderColor: "#e2e8f0", borderWidth: 1 } },
				},
			],
		});

		const onResize = () => ch.resize();
		window.addEventListener("resize", onResize);
		return () => {
			window.removeEventListener("resize", onResize);
			ch.dispose();
		};
	}, [years, data, max, disease]);

	if (years.length === 0) {
		return (
			<div className="h-[260px] grid place-items-center text-[var(--color-text-3)] text-xs">
				Chưa có dữ liệu lịch sử 2010-2019 cho quốc gia này.
			</div>
		);
	}

	return <div ref={elRef} className="w-full h-[260px]" />;
}
