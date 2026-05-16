# data_decisions.md — Data Sources & Quyết định

## Disease Data Sources

| Nguồn | File | Nội dung | Trạng thái |
|---|---|---|---|
| WHO FluNet | `VIW_FNT.csv` | Influenza A/B, RSV, Parainfluenza — 189 quốc gia, weekly | ✅ Đã có |
| OpenDengue v1.3 | `National_extract_V1_3.csv` | Dengue — 102 quốc gia, weekly/monthly | ✅ Đã có |
| ECDC ERVISS | `sentinelTestsDetectionsPositivity.csv` | Influenza+RSV EU/EEA | ✅ Đã có |
| ECDC ERVISS | `ILIARIRates.csv` | ILI rate EU/EEA theo age group | ✅ Đã có |

## Weather Data Sources

| Nguồn | File | Nội dung | Trạng thái |
|---|---|---|---|
| ERA5 ECMWF | `era5_raw/era5_{year}/` | 17 biến khí hậu, 1°×1°, 2010–2019 | ✅ Đã download |
| ERA5 processed | `era5_weekly_2010_2019_final.csv` | Aggregate về weekly+iso3 | ✅ Đã process |
| OpenWeatherMap | API (key có sẵn) | Realtime weather | Dùng cho production |

## ERA5 Variables (17 biến)

```python
ERA5_VARIABLES = {
    # Nhiệt độ (4)
    '2m_temperature',                    # → temp_c
    '2m_dewpoint_temperature',           # → dewpoint_c → humidity_pct
    'minimum_2m_temperature_since_previous_post_processing',  # → temp_min
    'maximum_2m_temperature_since_previous_post_processing',  # → temp_max

    # Gió (2) → tính wind_speed = sqrt(u²+v²)
    '10m_u_component_of_wind',           # → u10
    '10m_v_component_of_wind',           # → v10

    # Mưa / Ẩm (5)
    'total_precipitation',               # → precip_mm (SUM theo tuần)
    'convective_precipitation',          # → conv_precip_mm
    'large_scale_precipitation',         # → ls_precip_mm
    'total_column_water_vapour',         # → water_vapour
    'evaporation',                       # → evap_mm (lấy abs())

    # Bức xạ (3)
    'surface_solar_radiation_downwards', # → solar_wm2
    'downward_uv_radiation_at_the_surface',  # → uv_wm2
    'surface_thermal_radiation_downwards',   # → thermal_wm2

    # Mây / Áp suất / Khác (3)
    'total_cloud_cover',                 # → cloud_cover
    'surface_pressure',                  # → pressure_pa
    'mean_sea_level_pressure',           # → msl_pa
    'boundary_layer_height',             # → blh_m
}
```

## Lag Time (từ AI review + literature)

| Bệnh | Lag | Biến mạnh nhất | Non-linear |
|---|---|---|---|
| Influenza | 1–3 tuần | RH < 60% | U-shaped RH, optimal 5–20°C |
| RSV | 1–4 tuần | Temperature (bimodal) | Peak 2–6°C và 24–30°C |
| Parainfluenza | 1–3 tuần | RH + Temp kết hợp | Threshold 15–25°C |
| Dengue | **6–14 tuần** | Total precipitation | Optimal 24–32°C, >50mm/tuần |

## Merge Key
```
iso3 + ISO_YEAR + ISO_WEEK
```

## ERA5 Limitation đã biết
KD-tree nearest centroid map được 158/172 quốc gia (92%).
Các quốc gia bị miss chủ yếu là đảo nhỏ và lãnh thổ đặc biệt.
**Đã chấp nhận** — ghi chú vào báo cáo như hạn chế kỹ thuật.
Hướng cải thiện: Natural Earth 10m + polygon buffer.

---

## ML Approach (16/05/2026)

Hybrid: Regression + Classification, so sánh.

| Nhánh | Models | Target | Metrics | Dùng cho |
|---|---|---|---|---|
| Regression | XGBoost, LightGBM, RF | log1p(case_count) | RMSE, MAE, R² | Dashboard trend |
| Classification | XGBClassifier | Endemic channel | macro-F1, AUC | Bản đồ cảnh báo |
| Baseline | Prophet, Naive | case_count | RMSE, R² | Benchmark |

Optuna: tune top 1-2 regression model, 60 trials.

Label classification (endemic channel, Bortman 1999):
- Low = cases < mean(training years, same ISO week)
- Medium = mean <= cases < mean + 2 sigma
- High = cases >= mean + 2 sigma
