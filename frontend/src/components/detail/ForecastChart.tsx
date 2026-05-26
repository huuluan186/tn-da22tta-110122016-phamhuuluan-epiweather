import * as echarts from "echarts";
import { useEffect, useRef } from "react";
import type { ForecastPoint } from "../../types/api";

interface Props {
  points: ForecastPoint[];
  disease: "flu" | "dengue";
}

export default function ForecastChart({ points, disease }: Props) {
  const elRef = useRef<HTMLDivElement>(null);
  const color = disease === "flu" ? "#3b82f6" : "#f59e0b";

  useEffect(() => {
    if (!elRef.current || points.length === 0) return;
    const ch = echarts.init(elRef.current);

    const xLabels = points.map(
      (p) => `W${String(p.target_iso_week).padStart(2, "0")}/${p.target_iso_year}`,
    );
    const cases = points.map((p) => p.predicted_cases);
    const r2 = points.map((p) => p.r2_cv ?? 0);

    // Confidence band — RMSE log scale, convert ngược về cases
    // Lower: expm1(log - rmse), Upper: expm1(log + rmse)
    const lower = points.map((p) =>
      Math.max(0, Math.expm1(Math.max(0, p.predicted_log - (p.rmse_cv ?? 0)))),
    );
    const upper = points.map((p) =>
      Math.expm1(Math.max(0, p.predicted_log + (p.rmse_cv ?? 0))),
    );

    ch.setOption({
      backgroundColor: "transparent",
      grid: { top: 20, right: 20, bottom: 56, left: 64 },
      tooltip: {
        trigger: "axis",
        backgroundColor: "#1a1f2e",
        borderColor: "#2a3040",
        textStyle: { color: "#f1f5f9", fontSize: 11 },
        formatter: (params: { dataIndex: number }[]) => {
          const i = params[0].dataIndex;
          const p = points[i];
          return [
            `<b>${xLabels[i]}</b> (h=${p.horizon})`,
            `Predicted: <b>${p.predicted_cases.toLocaleString()}</b> cases`,
            `Range: ${Math.round(lower[i]).toLocaleString()} – ${Math.round(upper[i]).toLocaleString()}`,
            `R² CV: ${(r2[i] * 100).toFixed(1)}%`,
            `Model: ${p.model_version}`,
          ].join("<br/>");
        },
      },
      xAxis: {
        type: "category",
        data: xLabels,
        axisLine: { lineStyle: { color: "#2a3040" } },
        axisLabel: { color: "#64748b", fontSize: 10 },
        splitLine: { show: false },
      },
      yAxis: {
        type: "value",
        name: "Cases (predicted)",
        nameTextStyle: { color: "#64748b", fontSize: 10 },
        axisLine: { show: false },
        axisLabel: { color: "#64748b", fontSize: 10 },
        splitLine: { lineStyle: { color: "#1e2535", type: "dashed" } },
      },
      series: [
        {
          name: "Upper",
          type: "line",
          data: upper,
          lineStyle: { opacity: 0 },
          stack: "confidence-band",
          symbol: "none",
          areaStyle: { color: "rgba(0,0,0,0)" },
        },
        {
          name: "Range",
          type: "line",
          data: lower.map((v, i) => upper[i] - v),
          lineStyle: { opacity: 0 },
          stack: "confidence-band",
          symbol: "none",
          areaStyle: {
            color: color.startsWith("#")
              ? `${color}33` // ~20% opacity
              : color,
          },
        },
        {
          name: "Predicted",
          type: "line",
          data: cases,
          smooth: true,
          symbol: "circle",
          symbolSize: 8,
          lineStyle: { color, width: 2.5 },
          itemStyle: { color, borderColor: "#0a0f1c", borderWidth: 2 },
          z: 10,
        },
      ],
    });

    const onResize = () => ch.resize();
    window.addEventListener("resize", onResize);
    return () => {
      window.removeEventListener("resize", onResize);
      ch.dispose();
    };
  }, [points, disease, color]);

  return <div ref={elRef} className="w-full h-[260px]" />;
}
