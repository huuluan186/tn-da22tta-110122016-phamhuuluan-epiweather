# Đặc tả Output Hệ thống + Dashboard FE/BE
## Hệ thống cảnh báo nguy cơ dịch bệnh KLTN — EpiWeather

**Ngày chốt:** 13/05/2026
**Phiên bản:** v2.0 (theo approach Ordinal Classification + Endemic Channel)

---

## 1. Output cuối cùng — Khái niệm tổng quát

Hệ thống nhận một **(quốc gia, tuần, bệnh)** và trả về **mức cảnh báo + xác suất + ngữ cảnh dịch tễ**. Một dự đoán đầy đủ gồm 3 lớp thông tin:

### Lớp 1 — Cảnh báo cốt lõi (cho user thường)
- **Predicted Level** ∈ {Low, Medium, High}
- **Confidence** (xác suất của level cao nhất, 0–1)
- **Trend indicator** (so với tuần trước: ↑↓→)

### Lớp 2 — Phân phối xác suất (cho user kỹ thuật + dashboard)
- **P(Low)**, **P(Medium)**, **P(High)** — cộng = 1
- **Calibration score** (độ tin cậy của xác suất)

### Lớp 3 — Ngữ cảnh dịch tễ (cho explainability)
- **Endemic baseline**: mean ± SD lịch sử cùng tuần các năm trước
- **Current observation** (nếu là tuần đã xảy ra)
- **Top contributing features** (SHAP values, e.g., "humidity 8 tuần trước cao bất thường")
- **Historical comparison**: cùng tuần năm trước Level gì

---

## 2. Format Output chuẩn (JSON Schema)

### 2.1. Single prediction response

```json
{
  "request": {
    "iso3": "VN",
    "iso_year": 2024,
    "iso_week": 30,
    "disease": "influenza"
  },
  "prediction": {
    "level": "High",
    "confidence": 0.57,
    "probabilities": {
      "low":    0.12,
      "medium": 0.31,
      "high":   0.57
    },
    "trend": {
      "direction": "rising",
      "delta_from_prev_week": 0.18
    }
  },
  "context": {
    "endemic_baseline": {
      "method": "Bortman_5year_rolling",
      "years_used": [2018, 2019, 2022, 2023, 2024],
      "mean": 1240.5,
      "sd": 380.2,
      "thresholds": {
        "low_to_medium": 1240.5,
        "medium_to_high": 2000.9
      }
    },
    "historical_comparison": {
      "same_week_last_year": {
        "level": "Medium",
        "actual_cases": 1180
      },
      "same_week_2y_ago": {
        "level": "Low",
        "actual_cases": 820
      }
    },
    "top_features": [
      {"feature": "humidity_lag8w", "shap_value": 0.42, "direction": "↑"},
      {"feature": "temp_c_lag4w", "shap_value": -0.31, "direction": "↓"},
      {"feature": "cases_lag1w", "shap_value": 0.28, "direction": "↑"}
    ]
  },
  "meta": {
    "model_version": "v2.0_ordinal_clf",
    "predicted_at": "2024-07-22T10:30:00Z",
    "weather_source": "ERA5_historical",
    "data_freshness_days": 7
  }
}
```

### 2.2. Map response (bulk cho global view)

```json
{
  "week": "2024-W30",
  "disease": "influenza",
  "generated_at": "2024-07-22T10:30:00Z",
  "predictions": [
    {"iso3": "VN", "level": "High", "p_high": 0.57},
    {"iso3": "TH", "level": "Medium", "p_high": 0.34},
    {"iso3": "BR", "level": "Low", "p_high": 0.08},
    "..."
  ]
}
```

---

## 3. Backend Specification (FastAPI)

### 3.1. Tech stack
- **Framework:** FastAPI 0.115+
- **ORM:** SQLAlchemy 2.0 + asyncpg
- **DB:** PostgreSQL 16 (schema 5 tầng đã có — xem `docs/database_schema_v2.md`)
- **ML serving:** Joblib loading XGBClassifier .pkl
- **Caching:** Redis (optional, cho `/risk/map` heavy queries)
- **Docs:** OpenAPI auto-generated tại `/docs`

### 3.2. Cấu trúc thư mục backend (đã có một phần)

```
backend/
├── app/
│   ├── main.py                  # FastAPI app entry
│   ├── config.py                # Settings (DB URL, model paths, env vars)
│   ├── database.py              # SQLAlchemy session
│   ├── models/                  # ORM models (đã có)
│   │   ├── geography.py
│   │   ├── disease.py
│   │   ├── observation.py
│   │   ├── prediction.py
│   │   └── mlops.py
│   ├── schemas/                 # Pydantic response models
│   │   ├── country.py
│   │   ├── disease.py
│   │   └── prediction.py
│   ├── crud/                    # DB query layer
│   │   ├── countries.py
│   │   ├── diseases.py
│   │   └── predictions.py
│   ├── services/                # Business logic
│   │   ├── prediction_service.py    # Build features + call model
│   │   └── risk_service.py          # Endemic channel + thresholds
│   ├── ml/                      # ML inference
│   │   └── loader.py            # Load .pkl, cache models in memory
│   └── routers/                 # API endpoints
│       ├── health.py
│       ├── countries.py
│       ├── diseases.py
│       ├── predictions.py
│       └── risk.py
├── Dockerfile
├── requirements.txt
└── .env.example
```

### 3.3. API Endpoints

#### Group A — Reference data (catalog)
| Method | Path | Mô tả | Response |
|---|---|---|---|
| GET | `/api/v1/countries` | List 197 nước với region | `[{iso3, name, who_region, has_flu_data, has_dengue_data}]` |
| GET | `/api/v1/diseases` | List bệnh hỗ trợ | `[{code, name, num_countries, coverage_pct}]` |
| GET | `/api/v1/weather-variables` | List 17 biến ERA5 | `[{name, unit, description}]` |

#### Group B — Predictions (core)
| Method | Path | Mô tả | Cache |
|---|---|---|---|
| GET | `/api/v1/risk` | Single prediction (country + week + disease) | 1h |
| GET | `/api/v1/risk/map` | Bulk: tất cả nước cho 1 (week, disease) — cho choropleth | 6h |
| GET | `/api/v1/risk/forecast` | Multi-week ahead forecast (next 4 weeks) | 1h |
| POST | `/api/v1/risk/batch` | Batch prediction từ array of requests | - |

#### Group C — Country detail (deep-dive)
| Method | Path | Mô tả |
|---|---|---|
| GET | `/api/v1/country/{iso3}/timeline?disease=flu&from=2020&to=2025` | Historical + predicted timeline |
| GET | `/api/v1/country/{iso3}/seasonality?disease=flu` | Average pattern theo week_of_year |
| GET | `/api/v1/country/{iso3}/weather?from=2024-W30&to=2024-W40` | Weather history + forecast |

#### Group D — Disease deep-dive
| Method | Path | Mô tả |
|---|---|---|
| GET | `/api/v1/disease/{code}/global-trend?from=2024-W01` | Global aggregated trend |
| GET | `/api/v1/disease/{code}/top-risk?week=2024-W30&limit=20` | Top 20 nước nguy cơ cao nhất |
| GET | `/api/v1/disease/{code}/feature-importance` | SHAP global importance từ model |
| GET | `/api/v1/disease/{code}/ccf` | CCF heatmap data (lag × variable) |

#### Group E — Model meta & explainability
| Method | Path | Mô tả |
|---|---|---|
| GET | `/api/v1/model/info` | Model version, train date, metrics |
| GET | `/api/v1/model/calibration?disease=flu` | Reliability diagram data |
| GET | `/api/v1/model/confusion-matrix?disease=flu` | Confusion matrix on 2022 validation |
| GET | `/api/v1/explain` | SHAP explanation cho 1 prediction cụ thể |

#### Group F — System health
| Method | Path | Mô tả |
|---|---|---|
| GET | `/health` | Liveness probe |
| GET | `/health/ready` | Readiness probe (DB + model loaded) |
| GET | `/api/v1/data-freshness` | Last data update per source |

### 3.4. Inference pipeline (server-side)

```python
# Pseudo-code for /api/v1/risk endpoint
async def predict_risk(iso3: str, year: int, week: int, disease: str):
    # 1. Validate input
    country = await crud.get_country(iso3)
    disease_obj = await crud.get_disease(disease)
    
    # 2. Try cache first
    cached = await redis.get(f"risk:{iso3}:{year}:{week}:{disease}")
    if cached: return cached
    
    # 3. Fetch features
    weather = await crud.get_weather(iso3, year, week, lag_weeks=8)
    ar_features = await crud.get_disease_lags(iso3, disease, year, week)
    endemic = await services.compute_endemic_baseline(iso3, disease, week)
    
    # 4. Build feature vector
    X = services.build_feature_vector(
        weather, ar_features, endemic, year, week, country.who_region_enc
    )
    
    # 5. Predict
    model = ml.loader.get_classifier(disease)  # cached in-memory
    proba = model.predict_proba(X)[0]  # [P(L), P(M), P(H)]
    
    # 6. Build response
    response = {
        "level": ["Low", "Medium", "High"][np.argmax(proba)],
        "confidence": float(np.max(proba)),
        "probabilities": {"low": proba[0], "medium": proba[1], "high": proba[2]},
        "endemic_baseline": endemic,
        "top_features": services.shap_top_k(model, X, k=3),
        ...
    }
    
    # 7. Cache + persist
    await redis.setex(cache_key, 3600, response)
    await crud.insert_prediction_log(response)  # for analytics
    
    return response
```

### 3.5. Background jobs (cron / scheduled)

| Job | Frequency | Mục đích |
|---|---|---|
| `refresh_weather_data` | Daily 02:00 UTC | Pull OpenWeatherMap → DB `weather_observations` |
| `refresh_disease_surveillance` | Weekly Monday 06:00 UTC | Pull WHO FluNet API → `disease_cases` |
| `batch_predict_all_countries` | Weekly Tuesday 08:00 UTC | Pre-compute predictions for next 4 weeks, all countries |
| `refresh_endemic_baselines` | Yearly 01-Jan | Re-compute endemic channel với data năm vừa kết thúc |
| `db_quality_check` | Daily 03:00 UTC | Coverage, missing-rate alerts → `data_quality_checks` |

---

## 4. Frontend Specification (React + Tailwind + Leaflet + Recharts)

### 4.1. Tech stack
- **Framework:** React 18 + TypeScript + Vite
- **Styling:** Tailwind CSS 4
- **Map:** Leaflet.js + react-leaflet (choropleth)
- **Charts:** Recharts (line, bar, heatmap)
- **State:** TanStack Query (React Query) cho data fetching + cache
- **Routing:** React Router 7
- **Geo data:** Natural Earth 50m country polygons (TopoJSON)

### 4.2. Page structure

```
/                          → Home (Global Map dashboard)
/country/:iso3             → Country detail page
/disease/:code             → Disease deep-dive page
/explain                   → ML explainability page
/about                     → About + methodology
```

### 4.3. Page 1 — Global Map Dashboard (`/`)

**Layout:**

```
┌────────────────────────────────────────────────────────────────────┐
│ Header: KLTN EpiWeather │ Bệnh ▼ │ Tuần ▼ │ Light/Dark   │
├────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────────────────────────┐  ┌─────────────────────┐ │
│  │                                        │  │ Top 10 Risk Today    │ │
│  │      🗺️  GLOBAL MAP (Leaflet)         │  │ ─────────────────── │ │
│  │      Choropleth: P(High) intensity    │  │ 🔴 VN   High  0.78  │ │
│  │      Hover: country name + level      │  │ 🔴 TH   High  0.72  │ │
│  │      Click: → country detail page     │  │ 🟡 MY   Med   0.58  │ │
│  │                                        │  │ 🟡 ID   Med   0.51  │ │
│  │      Legend: 🟢 Low 🟡 Med 🔴 High    │  │ ⚪ BR   Low   0.12  │ │
│  │                                        │  │ ...                  │ │
│  └──────────────────────────────────────┘  └─────────────────────┘ │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Global trend (line chart, Recharts)                            │  │
│  │ X: tuần (last 52w) │ Y: # countries at High level             │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Coverage stats: Flu 170 nước | Dengue 43 nước | Last update… │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
```

**Tính năng:**
- Choropleth tô màu theo `P(High)`: gradient 🟢 → 🟡 → 🔴
- Filter: chọn bệnh (Influenza / Dengue), tuần (current / past / forecast next 4w)
- Hover tooltip: `{country} — {level} — P(High)={x}`
- Click country → navigate to `/country/:iso3?disease=flu`
- Sidebar Top 10: ranked by `P(High)` desc
- Footer chart: Time-series #countries-at-high last 52 weeks

### 4.4. Page 2 — Country Detail (`/country/:iso3`)

**Layout:**

```
┌────────────────────────────────────────────────────────────────────┐
│ ← Back │ 🇻🇳 Vietnam (VN) │ Bệnh: [Influenza ▼]                  │
├────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────────────────────┐  ┌────────────────────────┐  │
│  │ Current Risk Card                 │  │ Forecast Next 4 weeks    │  │
│  │ ─────────────────────────────────│  │ ───────────────────────│  │
│  │ Tuần 30/2024:  🔴 HIGH            │  │ W31 → 🔴 0.62           │  │
│  │ Confidence: 57%                  │  │ W32 → 🟡 0.45           │  │
│  │ ▮▮▮▮▮▮▮▮▯▯ P(High) 57%           │  │ W33 → 🟡 0.38           │  │
│  │ ▮▮▮▮▯▯▯▯▯▯ P(Med)  31%           │  │ W34 → ⚪ 0.21           │  │
│  │ ▮▮▯▯▯▯▯▯▯▯ P(Low)  12%           │  │                          │  │
│  └─────────────────────────────────┘  └────────────────────────┘  │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Historical timeline (Recharts AreaChart)                       │  │
│  │ - Y1: Actual cases (gray bars)                                 │  │
│  │ - Y2: Endemic baseline ± 2σ (shaded band)                      │  │
│  │ - Color highlight: weeks classified High (red bars)            │  │
│  │ - Last 5 years + forecast band                                 │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌──────────────────────────────────┐  ┌────────────────────────┐  │
│  │ Seasonality pattern (heatmap)     │  │ Top features (SHAP)      │  │
│  │ Y: year, X: week of year          │  │ humidity_lag8w  ↑ 0.42   │  │
│  │ Color: risk level                 │  │ temp_c_lag4w    ↓ 0.31   │  │
│  └──────────────────────────────────┘  └────────────────────────┘  │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Weather context (current vs baseline)                          │  │
│  │ - Temperature, Humidity, Solar — last 12 weeks                │  │
│  │ - Hilight tuần weather drives risk                             │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
```

**Tính năng chuyên sâu:**
- Risk card lớn với 3 stacked progress bars cho P(L/M/H)
- 4-week ahead forecast với confidence interval
- Timeline 5 năm + endemic band (mô phỏng EWARS dashboard Mexico)
- Seasonality heatmap (year × week_of_year, color = avg risk)
- SHAP top features explain "vì sao tuần này High"
- Weather panel showing weather context

### 4.5. Page 3 — Disease Deep-dive (`/disease/:code`)

```
┌────────────────────────────────────────────────────────────────────┐
│ Influenza A+B — Global Surveillance                                  │
├────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Global aggregated trend (53 weeks)                             │  │
│  │ - Total cases by region (WHO regions stacked area chart)       │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌──────────────────────────────────┐  ┌────────────────────────┐  │
│  │ Top 20 high-risk countries (bar)  │  │ CCF Heatmap              │  │
│  │ X: P(High)  Y: country            │  │ Y: weather var  X: lag    │  │
│  └──────────────────────────────────┘  └────────────────────────┘  │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Model performance (validation 2022)                            │  │
│  │ - Macro-F1, per-class P/R/F1 table                             │  │
│  │ - Confusion matrix (3×3)                                       │  │
│  │ - Calibration plot (reliability diagram)                       │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
```

### 4.6. Page 4 — ML Explainability (`/explain`)

Trang dành cho user kỹ thuật / GVHD reviewer:
- Global feature importance (SHAP summary plot)
- Model hyperparams + training config
- Walk-forward CV results per fold
- Endemic channel methodology explanation
- Pipeline diagram + data flow

### 4.7. Component reusability

| Component | Dùng ở | Mô tả |
|---|---|---|
| `<RiskBadge level confidence />` | Tất cả trang | Pill 🟢🟡🔴 với confidence % |
| `<ProbabilityBar p_low p_med p_high />` | Country detail, popups | 3 stacked progress bars |
| `<EndemicBand actual baseline_mean baseline_sd />` | Timeline charts | Recharts với shaded band |
| `<CountrySelector onChange />` | Header, country picker | Autocomplete searchable |
| `<WeekPicker year week onChange />` | Header | ISO week navigator |
| `<ChoroplethMap data colorBy onCountryClick />` | Home | Leaflet wrapper |

### 4.8. UX guidelines

- **Color coding nhất quán toàn site:**
  - 🟢 Low = `#10b981` (emerald-500)
  - 🟡 Medium = `#f59e0b` (amber-500)
  - 🔴 High = `#ef4444` (red-500)
- **Loading states**: skeleton screen + react-loading-skeleton
- **Empty states**: "No data for this country yet" với CTA
- **Error states**: retry button + error code
- **Tooltips**: methodology explanations on hover (e.g., "Endemic baseline là gì?")
- **Accessibility**: WCAG AA contrast, keyboard nav, screen reader friendly
- **Internationalization**: i18n hooks chuẩn bị, default Vietnamese, fallback English

---

## 5. Deployment Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        USER BROWSER                                │
└───────────────────────────────┬──────────────────────────────────┘
                                │ HTTPS
                  ┌─────────────▼─────────────┐
                  │   Nginx (reverse proxy)    │
                  │   - Static files (React)   │
                  │   - /api/* → FastAPI       │
                  └─────────────┬─────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
   ┌────▼────────┐      ┌──────▼──────┐         ┌─────▼─────┐
   │   FastAPI   │      │   FastAPI   │   ...   │  FastAPI  │
   │  (worker 1) │      │  (worker 2) │         │ (worker N)│
   └────┬────────┘      └──────┬──────┘         └─────┬─────┘
        │                       │                       │
        └───────────────────────┼───────────────────────┘
                                │
            ┌───────────────────┼───────────────────────┐
            │                                            │
       ┌────▼─────┐                              ┌──────▼──────┐
       │PostgreSQL│                              │    Redis     │
       │ + schemas│                              │  (cache LRU) │
       └──────────┘                              └─────────────┘
                                │
                  ┌─────────────▼─────────────┐
                  │   Cron jobs (separate)     │
                  │   - Daily weather refresh  │
                  │   - Weekly batch predict   │
                  └────────────────────────────┘
```

**Docker Compose services:**
| Service | Image | Port | Purpose |
|---|---|---|---|
| `nginx` | nginx:alpine | 80, 443 | Reverse proxy + static serve |
| `frontend` | (build → static) | - | React production build, served by nginx |
| `backend` | python:3.11 + FastAPI | 8000 | API workers (gunicorn + uvicorn) |
| `db` | postgres:16 | 5432 | Main database |
| `redis` | redis:7-alpine | 6379 | Response cache |
| `cron` | python:3.11 + custom | - | Background jobs |

---

## 6. User Stories — What Dashboard Can Do

### Persona 1 — Cán bộ y tế công cộng quốc gia
1. **"Tuần tới Việt Nam có nguy cơ cúm cao không?"**
   → Search VN → Country detail page → Forecast 4 weeks → Risk badge
2. **"Toàn cầu tuần này nước nào nguy cơ cao nhất?"**
   → Home page → Top 10 sidebar → Click country
3. **"So với mùa cúm năm ngoái VN năm nay nặng hơn không?"**
   → Country detail → Timeline 5 năm → Endemic band so sánh

### Persona 2 — Nhà nghiên cứu/Sinh viên
1. **"Variable thời tiết nào quan trọng nhất với dengue?"**
   → Disease deep-dive Dengue → CCF heatmap + Feature importance
2. **"Model accuracy 2022 ra sao?"**
   → Disease deep-dive → Model performance section → Confusion matrix
3. **"Vì sao tuần này Thái Lan được dự đoán High?"**
   → Country detail TH → SHAP top features panel

### Persona 3 — Du khách / công chúng
1. **"Tôi sắp đi Brazil tuần sau có cần lo dengue không?"**
   → Search BR + Dengue + week ahead → Risk badge
2. **"Bệnh sốt xuất huyết là gì? Lan như nào?"**
   → Disease page Dengue → About section + global trend

---

## 7. MVP Scope vs Future Work

### MVP (Demo lần cuối, tuần 8)
- ✅ Global map (Home) với 2 bệnh: Flu + Dengue
- ✅ Country detail page với timeline + endemic band + 4-week forecast
- ✅ Disease deep-dive với feature importance + CCF
- ✅ API: 14 endpoints (Group A, B, C, D rút gọn)
- ✅ DB đầy đủ schema 5 tầng (đã có)
- ✅ Docker Compose deploy

### Future Work (sau bảo vệ)
- LSTM/Transformer cho time-series (so sánh ensemble)
- Real-time OpenWeatherMap integration + automated refresh
- Bệnh thêm: RSV, COVID-19, Malaria
- Mobile app (React Native)
- Push notification cho high-risk alerts
- User auth + saved watchlist
- CI/CD pipeline (GitHub Actions)
- MLOps: model retraining cron + A/B testing

---

## 8. Định nghĩa "Done" cho Dashboard

Dashboard được coi là **hoàn thành (Done)** khi đáp ứng đủ:

1. ✅ Home page load < 2s với data 197 nước
2. ✅ Choropleth map tô màu chính xác theo `P(High)`
3. ✅ Country detail page show được data 5 năm + 4-week forecast
4. ✅ Tất cả 14 MVP endpoints respond đúng schema
5. ✅ Mobile responsive (breakpoint 768px / 1024px)
6. ✅ Cả 2 bệnh (Flu + Dengue) hoạt động đầy đủ
7. ✅ Loading + error states cho mọi page
8. ✅ Methodology tooltip / About page giải thích Endemic Channel
9. ✅ Docker Compose `up -d` build từ đầu trong < 5 phút
10. ✅ README có hướng dẫn deploy + screenshot
