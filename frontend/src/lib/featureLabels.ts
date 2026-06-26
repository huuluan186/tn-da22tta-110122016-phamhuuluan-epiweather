const CLIMATE_LABELS: Record<string, string> = {
  temp_c: "Nhiệt độ trung bình",
  humidity_pct: "Độ ẩm không khí",
  precip_mm: "Lượng mưa",
  solar_wm2: "Bức xạ mặt trời",
  dewpoint_c: "Nhiệt độ điểm sương",
};

export function climateFeatureLabel(feature: string): string {
  const match = feature.match(/^(temp_c|humidity_pct|precip_mm|solar_wm2|dewpoint_c)(?:_lag(\d+))?$/);
  if (!match) return feature;

  const [, variable, lag] = match;
  const label = CLIMATE_LABELS[variable] ?? feature;
  return lag ? `${label} · trễ ${lag} tuần` : label;
}