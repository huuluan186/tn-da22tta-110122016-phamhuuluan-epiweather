# Pipeline Diagram — Review Notes & Prompt V3

Ngày review: 2026-05-20

---

## 1. Checklist chỉnh sửa

> Nguồn đối chiếu: `docs/session_summaries/2026-05-17_session_summary.md` (notebook v5, SESSION 4+6 — kết quả mới nhất)

### Chỉ số / số liệu cần confirm

| Nội dung trong ảnh | Trạng thái | Số đúng (session 17/05) |
|---|---|---|
| `Flu R²=0.811` | ❌ Sai — số cũ | **Flu R²=0.902** (LightGBM, walk-forward CV 6 folds) |
| `Med-F1=0.52` | ⚠️ Gần đúng | Flu macro-F1=**0.542** (XGBClassifier) / Dengue=0.475 |
| `XGBoost ★` | ❌ Sai model | Flu production = **LightGBM** (R²=0.902), Dengue = **Random Forest** (R²=0.936) |
| `PostgreSQL 15` | ⚠️ Bỏ version | Ghi "PostgreSQL" là đủ — version không cần trong diagram |
| `Walk-forward CV 6 folds, 2014–2019` | ✅ Đúng | val_year 2014→2019, expanding window |
| `AR lags 1w/2w/4w` | ✅ Đúng | log1p_cases_lag1w/lag2w/lag3w (lag3 không phải lag4) |
| `Flu: temp4w/hum8w` | ❌ Sai lag | **Flu CCF đúng:** solar lag7 (r=-0.41), temp lag3 (r=-0.37), humidity lag7 (r=+0.31) |
| `Dengue: hum2w` | ❌ Thiếu | **Dengue CCF đúng:** temp lag11 (r=+0.31), dewpoint lag8, precip lag6 |
| `KD-tree` | ✅ Đúng | ERA5 → iso3 centroid, O(log n), 197 countries |
| `XGBoost ★, LightGBM, RF, Prophet, XGBClassifier` | ✅ Đúng | 5 models so sánh — đủ cả |

### Tóm tắt kết quả đúng nhất (notebook v5, session 17/05)

**Regression (target: log1p(cases)):**
| Model | Flu R² | Dengue R² |
|---|---|---|
| Naive baseline | 0.560 | 0.487 |
| Prophet | 0.429 | -0.282 |
| XGBoost | 0.901 | 0.931 |
| **LightGBM ★ (Flu)** | **0.902** | 0.931 |
| **Random Forest ★ (Dengue)** | 0.899 | **0.936** |

**Classification (XGBClassifier, macro-F1):**
| Disease | macro-F1 |
|---|---|
| Flu | **0.542** ± 0.027 |
| Dengue | 0.475 ± 0.035 (chưa đạt, đang cải thiện) |

### Mũi tên cần thêm label

| Mũi tên hiện tại | Label nên thêm |
|---|---|
| WHO FluNet → Data Validation | "VIW_FNT.csv (~1.2M rows)" |
| OpenDengue → Data Validation | "National_extract_V1_3.csv" |
| ERA5 → Data Validation | "10 × NetCDF (6.2 GB)" |
| OpenWeatherMap → Data Validation | "REST JSON (7-day forecast)" |
| Data Validation → Intelligence Engine | "Validated weekly CSVs" |
| Intelligence Engine → ML Training | "features_flu_v3.csv / features_dengue_v1.csv (13/15 features)" |
| ML Training → PostgreSQL | "INSERT predictions, model_versions, risk_thresholds" |
| PostgreSQL → FastAPI | "SQL queries + Materialized View (~50ms)" |
| FastAPI → React Frontend | "JSON response (risk_level, predicted_cases, prob_high)" |
| FastAPI → MLOps Monitor | "api_request_logs (endpoint, latency_ms)" |
| MLOps Monitor → Data Validation | "Scheduled Retraining Trigger (drift detected)" |
| Intelligence Engine → FastAPI | "Real-time feature vector (Online path)" |

### Layout

- **Vấn đề hiện tại:** 8 cột ngang → quá rộng, khó đọc khi in A4
- **Đề xuất:** Chia 2 hàng:
  - Hàng trên: Data Sources → Validation+ETL → Intelligence Engine → ML Training
  - Hàng dưới: PostgreSQL → FastAPI → React Frontend → MLOps Monitor
  - Mũi tên chính đi từ trái sang phải theo từng hàng
  - Mũi tên nối hàng trên → hàng dưới: ML Training → PostgreSQL (xuống)
  - Feedback loop: MLOps Monitor → (mũi tên vòng về) → Data Validation

---

## 2. Prompt V3 — Gửi cho AI gen ảnh

> **[Số liệu cập nhật từ session_summary 17/05/2026 — notebook v5]**
>
> **[COPY ĐOẠN NÀY]**
>
> Redesign the following system architecture diagram for a research system called **EpiWeather** (Seasonal Epidemic Risk Forecasting). The previous version was too wide (8 columns horizontal). The new layout must be **2-row rectangular grid** (4 blocks per row), fitting a 16:9 landscape format.
>
> ---
>
> **LAYOUT (2 rows × 4 columns):**
>
> **TOP ROW (left → right):**
> - Block 1: DATA SOURCES
> - Block 2: DATA VALIDATION + ETL
> - Block 3: INTELLIGENCE ENGINE (Core)
> - Block 4: ML TRAINING
>
> **BOTTOM ROW (left → right, aligned under top row):**
> - Block 5: PostgreSQL (under Block 4, connected by vertical arrow going DOWN)
> - Block 6: FastAPI REST API (under Block 3)
> - Block 7: React Frontend (under Block 2)
> - Block 8: MLOps Monitor (under Block 1)
>
> **Main data flow:**
> Top row: Block 1 → Block 2 → Block 3 → Block 4
> Vertical bridge: Block 4 ↓ Block 5
> Bottom row: Block 5 → Block 6 → Block 7 → Block 8
> Feedback loop: Block 8 → dashed arrow curving back up to Block 2
>
> ---
>
> **ARROW LABELS (REQUIRED — every arrow must have a text label):**
> - Block 1 → Block 2: "VIW_FNT.csv / National_extract.csv / ERA5 NetCDF / OWM JSON"
> - Block 2 → Block 3: "Validated weekly CSVs (flu + dengue + weather)"
> - Block 3 → Block 4: "Feature sets: 13 features (flu) / 15 features (dengue)"
> - Block 4 ↓ Block 5: "INSERT predictions, model versions, risk thresholds"
> - Block 5 → Block 6: "SQL queries + Materialized View (~50ms)"
> - Block 6 → Block 7: "JSON: risk_level, predicted_cases, prob_high"
> - Block 7 → Block 8: "api_request_logs: endpoint, latency, status"
> - Block 8 ↗ Block 2: "Retraining Trigger (drift detected)" — dashed arrow
> - Block 3 → Block 6: "Real-time feature vector" — diagonal arrow labeled "Online path"
>
> ---
>
> **BLOCK CONTENT:**
>
> **Block 1 — DATA SOURCES** (blue header):
> - WHO FluNet (document icon) — CSV, 197 countries, weekly
> - OpenDengue v1.3 (document icon) — CSV, 102 countries
> - ERA5 ECMWF (cloud icon) — Copernicus API, 17 climate vars
> - OpenWeatherMap (cloud icon, light blue badge "ONLINE") — real-time forecast
>
> **Block 2 — DATA VALIDATION + ETL** (green header):
> - Automated Quality Checks: Schema · Missing · Range · Temporal
> - PASS / FAIL diamond decision
> - Three ETL processes: Flu ETL · Dengue ETL · ERA5 ETL (KD-tree)
>
> **Block 3 — INTELLIGENCE ENGINE (CORE)** (purple header, bold border, highlighted):
> - A. Temporal Disease Dynamics — AR lags lag1w/lag2w/lag3w, log1p transform
> - B. Delayed Climate Response — CCF-based lag discovery, Flu: solar7w/temp3w/hum7w, Dengue: temp11w/dewpoint8w/precip6w
> - C. Geographic Adaptation — who_region_enc, week_sin/cos, per-country endemic context
>
> **Block 4 — ML TRAINING** (indigo header):
> - Walk-forward CV — 6 folds, 2014–2019
> - Model Benchmark: Naive, Prophet, XGBoost, LightGBM ★ (Flu), RF ★ (Dengue), XGBClassifier
> - Best result badge (green): Flu R²=0.902 (LightGBM), Dengue R²=0.936 (RF), Flu macro-F1=0.542
>
> **Block 5 — PostgreSQL** (orange header, cylinder database icon):
> - Partitioned by iso_year
> - JSONB weather observations
> - Materialized View for fast API queries
> - 5-tier schema: countries, cases, weather, models, MLOps
>
> **Block 6 — FastAPI REST API** (red header, server rack icon):
> - GET /risk-map — choropleth JSON for 197 countries
> - POST /predict — real-time ML inference
> - GET /history — weekly trend time-series
>
> **Block 7 — React Frontend** (teal header):
> - Global Risk Map (Leaflet choropleth)
> - Trend Charts (Recharts, Actual vs Predicted)
> - Alert Feed + SHAP Explainability
>
> **Block 8 — MLOps Monitor** (amber dashed border):
> - Drift Detection (RMSE monitoring)
> - Retraining Trigger
>
> ---
>
> **VISUAL STYLE:**
> - White background, clean flat design, no 3D shadows
> - Each block: rounded corners (12px), colored header badge with number + label
> - Generous whitespace: 32px+ padding inside blocks, 24px gap between blocks
> - Arrow labels: small gray italic text on each arrow line
> - Gray arrows = Offline batch flow | Blue arrows = Online real-time flow | Dashed arrows = Feedback/monitoring
> - Legend box bottom-left with 3 arrow types explained
> - Bottom full-width gold-border box: "Research Novelty & Contributions" with 5 bullet points
> - Font: Inter or Roboto, sans-serif
> - No emojis in the main diagram (icons only in legend and novelty box)

---

## 3. Prompt ngắn hơn — nếu AI không hỗ trợ prompt dài

> Redesign EpiWeather system architecture diagram with 2-row layout (4 blocks per row, not 8 columns). TOP ROW: Data Sources → Data Validation+ETL → Intelligence Engine (CORE, purple highlighted) → ML Training. BOTTOM ROW (right-to-left reading): PostgreSQL (cylinder) → FastAPI (server icon) → React Frontend → MLOps Monitor. Every arrow must have a text label describing what data flows through it. Use gray arrows for offline batch flow, blue arrows for online real-time flow, dashed arrows for feedback loops. White background, flat design, rounded blocks with colored headers, 16:9 landscape. Add a gold-border "Research Novelty" box at the bottom.
