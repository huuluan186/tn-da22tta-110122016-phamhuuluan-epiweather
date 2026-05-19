import * as echarts from "echarts";
import { useEffect, useMemo, useRef, useState } from "react";
import { RISK_LEVELS } from "../../constants";
import { ALL_ISO3, ECHARTS_COUNTRY_NAMES, mockRiskScore } from "../../lib/mockRisk";
import type { DiseaseId } from "../../types/domain";

let mapRegistered = false;

async function ensureWorldMap() {
  if (mapRegistered) return;
  const res = await fetch("/world.json");
  if (!res.ok) throw new Error(`Failed to load world map: ${res.status}`);
  const geoJson = await res.json();
  echarts.registerMap("world", geoJson);
  mapRegistered = true;
}

interface MapDataItem {
  name: string;
  value: number;
  risk: keyof typeof RISK_LEVELS;
}

function buildOption(data: MapDataItem[]) {
  return {
    backgroundColor: "transparent",
    tooltip: {
      trigger: "item",
      backgroundColor: "#1a1f2e",
      borderColor: "#2a3040",
      textStyle: { color: "#f1f5f9", fontFamily: "Inter" },
      formatter: (p: { name: string; value: number; data?: MapDataItem }) => {
        if (!p.value && p.value !== 0) return `<b>${p.name}</b><br/>No data available`;
        const r = p.data?.risk ?? "none";
        const badge = `<span style="display:inline-block;margin-right:6px;font-size:10px;font-weight:bold;padding:2px 6px;border-radius:3px;background:${RISK_LEVELS[r].color};color:white;">${RISK_LEVELS[r].label}</span>`;
        return `<b>${p.name}</b><br/><br/>${badge} <span style="font-weight:bold;font-size:14px;">${p.value}</span> / 100`;
      },
    },
    visualMap: {
      min: 0,
      max: 100,
      inRange: { color: ["#2a3040", "#22c55e", "#f59e0b", "#ef4444", "#dc2626"] },
      show: false,
    },
    series: [
      {
        type: "map",
        map: "world",
        roam: true,
        scaleLimit: { min: 1, max: 8 },
        itemStyle: { areaColor: "#2a3040", borderColor: "#1a1f2e", borderWidth: 0.5 },
        emphasis: {
          itemStyle: { areaColor: "#3b82f6", borderColor: "#ffffff", borderWidth: 1 },
          label: { show: false },
        },
        data,
      },
    ],
  };
}

interface Props {
  disease: DiseaseId;
  week: number;
  onCountrySelect: (echartName: string) => void;
}

export default function WorldMap({ disease, week, onCountrySelect }: Props) {
  const elRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<echarts.ECharts | null>(null);
  const [ready, setReady] = useState(false);

  const mapData = useMemo<MapDataItem[]>(() => {
    return ALL_ISO3.filter((iso3) => ECHARTS_COUNTRY_NAMES[iso3]).map((iso3) => {
      const p = mockRiskScore(iso3, disease, week);
      return { name: ECHARTS_COUNTRY_NAMES[iso3], value: p.score, risk: p.risk };
    });
  }, [disease, week]);

  // Keep a ref so the init effect can read latest mapData without being in its deps
  const mapDataRef = useRef(mapData);
  useEffect(() => {
    mapDataRef.current = mapData;
  });

  // Load GeoJSON once
  useEffect(() => {
    let mounted = true;
    ensureWorldMap()
      .then(() => mounted && setReady(true))
      .catch((err) => console.error("World map load failed:", err));
    return () => {
      mounted = false;
    };
  }, []);

  // Init chart after map is registered
  useEffect(() => {
    if (!ready || !elRef.current) return;
    const ch = echarts.init(elRef.current);
    chartRef.current = ch;

    ch.setOption(buildOption(mapDataRef.current));

    ch.on("click", (params: { name?: string }) => {
      if (params.name) onCountrySelect(params.name);
    });

    const onResize = () => ch.resize();
    window.addEventListener("resize", onResize);

    return () => {
      window.removeEventListener("resize", onResize);
      ch.dispose();
      chartRef.current = null;
    };
  }, [ready, onCountrySelect]);

  // Update data when disease/week changes (chart already initialized)
  useEffect(() => {
    chartRef.current?.setOption({ series: [{ data: mapData }] }, { replaceMerge: ["series"] });
  }, [mapData]);

  return (
    <div className="w-full h-full relative">
      {!ready && (
        <div className="absolute inset-0 grid place-items-center text-[var(--color-text-3)] text-xs">
          Đang tải bản đồ thế giới…
        </div>
      )}
      <div ref={elRef} className="w-full h-full" />
    </div>
  );
}
