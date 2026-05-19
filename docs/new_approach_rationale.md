# Hướng tiếp cận mới — Ordinal Classification với Endemic Channel
## Tài liệu so sánh approach cũ ↔ mới và tính mới so với các công trình đã công bố

**Ngày chốt:** 13/05/2026
**Áp dụng cho:** SESSION 7–9 của notebook KLTN_EpiWeather_ML

---

## 1. Tổng hợp approach mới — End-to-End Pipeline

### 1.1. Sơ đồ pipeline hoàn chỉnh

```
┌──────────────────────────────────────────────────────────────────────────┐
│ NGUỒN DỮ LIỆU                                                              │
│  - WHO FluNet (cases weekly, 170 nước)                                     │
│  - OpenDengue v1.3 (cases weekly, 43 nước)                                 │
│  - ECDC ERVISS (validation, EU/EEA, 2021+)                                 │
│  - ERA5 ECMWF (17 weather variables, 1°×1° grid, monthly)                  │
│  - OpenWeatherMap API (realtime, deployment phase)                         │
└──────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌──────────────────────────────────────────────────────────────────────────┐
│ TẦNG 1 — ETL & DATA INTEGRATION (đã làm xong — SESSION 1-4)               │
│  - KD-tree spatial mapping ERA5 grid → iso3                                │
│  - Merge weekly trên (iso3, ISO_year, ISO_week)                            │
│  - Forward-fill weather tối đa 2 tuần                                      │
│  → master_weekly_2010_2019.csv (64,949 rows × 27 cols, 172 nước)           │
└──────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌──────────────────────────────────────────────────────────────────────────┐
│ TẦNG 2 — EDA & CCF ANALYSIS (đã làm xong — SESSION 5-6)                   │
│  - Seasonality decomposition, geographic concentration                     │
│  - Cross-Correlation Function (CCF) per country, aggregate by median       │
│  → Lag-optimal: Flu {temp:4w, hum:8w, sol:8w, dew:2w}                      │
│              Dengue {temp:0w, hum:2w, sol:4w, prec:0w}                     │
└──────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌──────────────────────────────────────────────────────────────────────────┐
│ TẦNG 3 — ENDEMIC CHANNEL LABEL GENERATION (MỚI — SESSION 7)               │
│  Per-country per-week-of-year baseline (5-year rolling):                   │
│    baseline[c, w] = mean(cases[c, same_w, year-1..year-5])                 │
│    sd[c, w]       = std(cases[c, same_w, year-1..year-5])                  │
│  Ordinal label (3 mức):                                                    │
│    Low    = cases < baseline                                               │
│    Medium = baseline ≤ cases < baseline + 2σ                               │
│    High   = cases ≥ baseline + 2σ                                          │
│  Reference: Bortman M. (1999) OPS; Lowe et al. (2016) Lancet Planet Health │
└──────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌──────────────────────────────────────────────────────────────────────────┐
│ TẦNG 4 — FEATURE ENGINEERING (refine — SESSION 7)                         │
│  Per row (iso3, ISO_year, ISO_week):                                       │
│    - Weather lag (CCF-optimal): temp_c_lag4, humidity_lag8, ...            │
│    - Autoregressive: cases_lag1, cases_lag2, cases_lag4                    │
│    - Seasonal: sin(2π·week/52), cos(2π·week/52)                            │
│    - Region: who_region_enc                                                │
│    - Endemic baseline (feature): baseline_mean, baseline_sd                │
│  → features_flu_v2.csv, features_dengue_v2.csv                             │
└──────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌──────────────────────────────────────────────────────────────────────────┐
│ TẦNG 5 — MODEL TRAINING (MỚI — SESSION 8)                                 │
│  XGBClassifier (objective='multi:softprob', num_class=3)                   │
│    - 2 model độc lập: xgb_flu_clf.pkl, xgb_dengue_clf.pkl                  │
│    - Walk-forward CV: val_year ∈ {2014, 2015, ..., 2019}                   │
│    - Class weight: 'balanced' để xử lý imbalance                           │
│    - Hyperparams: n_est=500, max_depth=6, lr=0.05, subsample=0.8           │
│  Reference: Wellcome Open Research 2024 (ordinal influenza classification) │
└──────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌──────────────────────────────────────────────────────────────────────────┐
│ TẦNG 6 — EVALUATION (MỚI — SESSION 9)                                     │
│  Validation set: 2022 (post-COVID generalization test)                     │
│  Metrics:                                                                  │
│    - Per-class Precision, Recall, F1                                       │
│    - Macro-F1 (treat all 3 classes equally — quan trọng vì imbalance)      │
│    - ROC-AUC One-vs-Rest cho mỗi class                                     │
│    - Confusion matrix per country group (high/low income)                  │
│    - Calibration plot: P(High) predicted vs observed frequency             │
│  Export: model_metrics_v2.json, confusion matrices, reliability diagrams   │
└──────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌──────────────────────────────────────────────────────────────────────────┐
│ TẦNG 7 — INFERENCE PIPELINE (PRODUCTION)                                  │
│  Input: (country, target_week, disease)                                    │
│  Steps:                                                                    │
│    1. Fetch weather (ERA5 historical hoặc OpenWeatherMap realtime)         │
│    2. Compute features (weather lag + AR lag + endemic baseline)           │
│    3. Predict: clf.predict_proba(X) → [P(Low), P(Med), P(High)]            │
│    4. Calibrate (optional: Platt/isotonic) → probabilities tin cậy hơn    │
│  Output: 3-tuple probabilities + argmax tier + confidence                  │
└──────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌──────────────────────────────────────────────────────────────────────────┐
│ TẦNG 8 — BACKEND API (FastAPI)                                             │
│  GET /api/v1/risk?country=VN&week=2024-W30&disease=flu                     │
│   → { country, week, disease,                                              │
│       probabilities: {low, medium, high},                                   │
│       predicted_level, confidence,                                         │
│       endemic_baseline: {mean, sd} }                                       │
│  GET /api/v1/risk/map?week=2024-W30  → array cho map choropleth            │
│  GET /api/v1/country/{iso3}/timeline?disease=flu&from=2024&to=2025         │
└──────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌──────────────────────────────────────────────────────────────────────────┐
│ TẦNG 9 — FRONTEND DASHBOARD (React + Tailwind)                            │
│  Global map: choropleth Leaflet, color = P(High) intensity                 │
│  Country detail: timeline P(level) over time, history vs baseline          │
│  Disease deep-dive: feature importance, CCF heatmap, calibration plot      │
└──────────────────────────────────────────────────────────────────────────┘
```

### 1.2. Output cuối cùng (1 record cho mỗi country × week × disease)

```json
{
  "iso3": "VN",
  "iso_year": 2024,
  "iso_week": 30,
  "disease": "influenza",
  "probabilities": {
    "low":    0.12,
    "medium": 0.31,
    "high":   0.57
  },
  "predicted_level": "High",
  "confidence":      0.57,
  "endemic_baseline": {
    "mean": 1240,
    "sd":   380,
    "method": "Bortman_5year_rolling"
  },
  "model_version": "v2.0_ordinal_clf",
  "predicted_at":  "2024-07-22T10:30:00Z"
}
```

---

## 2. So sánh approach cũ ↔ mới

| Khía cạnh | Approach CŨ (Regression-then-Bucket) | Approach MỚI (Ordinal Classification + Endemic Channel) | Tại sao đổi? |
|---|---|---|---|
| **Task formulation** | Regression dự đoán `log1p(cases)` rồi cắt quantile thành tier | Multi-class classification dự đoán trực tiếp risk level | Tên đề tài + mô tả gốc khoa nói rõ là **cảnh báo mức độ**, không phải dự đoán số ca |
| **Target column** | `inf_log1p`, `dengue_log1p` (continuous) | `risk_label ∈ {0, 1, 2}` ↔ {Low, Med, High} (ordinal) | Optimize đúng metric (cross-entropy → F1) thay vì gián tiếp qua MSE |
| **Định nghĩa "High"** | Quantile global 0.67 của prediction | Cases ≥ baseline + 2σ (per-country, per-week-of-year) | Per-country tự khử Brazil dominance; có ý nghĩa dịch tễ (Bortman 1999); cite được paper |
| **Loss function** | MSE trên `log1p(cases)` | Multi-class cross-entropy với `class_weight='balanced'` | Cross-entropy tối ưu trực tiếp F1; class_weight xử lý imbalance Low/Med/High |
| **Output cho user** | `predicted_cases` (số) + `tier` (cứng) | `P(Low), P(Medium), P(High)` (probabilistic) + tier | Mô tả gốc khoa nói *"khả năng diễn ra"* → cần probability output |
| **Model file** | XGBRegressor | XGBClassifier (multi:softprob) | Khớp task formulation |
| **Metrics chính** | RMSE, MAE, R² (regression) + P/R/F1 (classification gián tiếp) | Macro-F1, AUC OvR, per-class F1, calibration ECE | RMSE/MAE/R² không meaningful cho classification task |
| **Vấn đề Medium F1 ≈ 0** | Quantile global → Brazil chiếm hết High → Medium trống | Endemic channel per-country → mỗi nước có baseline riêng → Medium có rows | Root cause là threshold lệch, không phải data issue |
| **Xử lý zero-inflated** | log1p compress nhưng vẫn bias toward zero | Class Low naturally cover các tuần ≈ 0; classifier không bị bias | Data 38.8% zero rows hợp classification hơn Gaussian regression |
| **Feature `log1p(cases)`** | Có (làm target) | Bỏ; thay bằng `cases_lag1`, `cases_lag2`, `cases_lag4` (AR features) | Classifier dùng AR features trực tiếp được, không cần log transform target |
| **Cite được paper** | Yếu (chỉ general XGBoost forecasting) | Mạnh: Bortman 1999, Lowe 2016, Wellcome 2024, EWARS Mexico | Có literature backbone cho Chương 2 |

---

## 3. Tính mới của đề tài so với các công trình đã công bố

So sánh đề tài KLTN với 7 công trình tiêu biểu trong literature epidemic ML 2012–2024:

### 3.1. Bảng so sánh các công trình tiền nhiệm

| Công trình | Bệnh | Phạm vi | Approach | Lag time | Multi-disease | Operational | Probability output |
|---|---|---|---|---|---|---|---|
| Brady et al. 2012 (PLOS NTD) | Dengue | Vùng nhiệt đới | Regression linear, temp + rainfall | Đề cập | Single | ❌ | ❌ |
| Hii et al. 2012 (PLOS NTD) | Dengue | Singapore | Poisson regression | Có | Single | ❌ | Có CI |
| Reich et al. 2019 (PNAS) | Flu | US | Ensemble (CDC FluSight) | Không weather | Single | ✅ | ✅ |
| Lowe et al. 2016 (Lancet) | Dengue | Ecuador | DLNM + INLA Bayesian | DLNM lag | Single | ✅ EWARS | ✅ |
| Hussain-Alkhateeb 2018 (Front Pub Health) | Dengue | Mexico, BR, MY | EWARS DLNM | DLNM lag | Single | ✅ EWARS | ✅ |
| Srivatsan et al. 2025 (ICITSM) | 5 viruses hô hấp | Global | ML comparison | Không CCF | Single each | ❌ | ❌ |
| Wellcome OR 2024 | Flu | Country-level | Ordinal classifier | Có | Single | ❌ | ✅ |
| Bangladesh dengue 2024 (PMC) | Dengue | Bangladesh | LightGBM regression | Có | Single | ❌ | ❌ |

### 3.2. Đóng góp mới của đề tài KLTN

| # | Tính mới | Đối chiếu với prior work | Mức độ mới |
|---|---|---|---|
| **1** | **Multi-disease unified pipeline** — 1 hệ thống thống nhất cho Influenza + Dengue với cùng kiến trúc | Prior work làm từng bệnh riêng (Brady chỉ dengue, FluSight chỉ flu, Wellcome chỉ flu) | ⭐⭐⭐ Đáng kể |
| **2** | **Phạm vi global 197 nước** với KD-tree ERA5 mapping | EWARS chỉ làm Mexico/Ecuador/Brazil; FluSight chỉ US; Wellcome country-level nhưng không global. Brady global nhưng chỉ correlation | ⭐⭐⭐⭐ Mới quan trọng |
| **3** | **CCF-driven lag selection per disease** dùng làm feature lag, không hardcode | EWARS dùng DLNM (more complex); papers thường hardcode lag (e.g., 4 weeks); KLTN data-driven per disease | ⭐⭐ Cải tiến |
| **4** | **Endemic Channel ordinal classification** thay cho EWARS binary | EWARS chỉ alarm/no-alarm; Wellcome ordinal nhưng quantile arbitrary; KLTN combines: ordinal classes + epidemic-channel thresholds | ⭐⭐⭐ Hybrid mới |
| **5** | **Open-source full pipeline + Docker Compose** | EWARS Mexico là closed-system của WHO; CDC FluSight là collaboration ensemble; KLTN deployable đầy đủ | ⭐⭐ Engineering value |
| **6** | **Tích hợp ERA5 reanalysis (17 vars) + OpenWeatherMap realtime** | Prior work thường chỉ dùng 2–5 weather vars (temp + rainfall); KLTN 17 vars (humidity, dewpoint, solar, wind, pressure...) | ⭐⭐ Feature richness |
| **7** | **Probabilistic output cho global map visualization** | EWARS dashboard chỉ Mexico; FluSight no map; Brady no dashboard. KLTN: map + timeline + drilldown | ⭐⭐⭐ UX/Decision support |

### 3.3. Vị trí của KLTN trên landscape research

```
                    Single-country, single-disease, no weather
                    (ARIMA traditional surveillance)
                              ▲
                              │
   Single-country,            │            Single-country,
   single-disease,            │            single-disease,
   weather correlation        │            weather + ML
   (Brady 2012)               │            (Lowe 2016 EWARS Ecuador)
                              │
   ─────────────────────────  │  ─────────────────────────
                              │
   Multi-country,             │            Multi-country,
   single-disease,            │            multi-disease,
   weather + ML               │            weather + ML
   (Hussain-Alkhateeb 2018)   │            (KLTN ← VỊ TRÍ)
                              │
                              ▼
                    Global, multi-disease, full weather, operational
                    (chưa có công trình nào)
```

**Insight**: KLTN occupy ô **bottom-right** — góc còn thiếu trong literature. Không claim là "world-first" (vì có thể có grey literature), nhưng **trong các công trình peer-reviewed mà em đã review, chưa có công trình nào kết hợp đồng thời:**
- Multi-disease (Flu + Dengue)
- Global coverage (197 nước)
- ERA5 17 weather variables
- Ordinal classification với endemic channel
- Probabilistic output cho map
- Deployable full-stack (open-source)

### 3.4. Các hạn chế còn lại (để phòng thủ phản biện)

| Hạn chế | Lý do | Cách phòng thủ trong báo cáo |
|---|---|---|
| Không dùng DLNM như EWARS | DLNM phức tạp, cần INLA, không scale tốt với XGBoost | Trade-off: XGBoost cho phép feature importance, deployment đơn giản hơn |
| ERA5 monthly chứ không weekly | ERA5 reanalysis dataset thực ra hourly nhưng dataset gốc dùng monthly | Đề xuất future work: dùng ERA5 daily aggregated weekly |
| 2 model riêng flu/dengue, không joint | Cơ chế sinh học khác biệt | Trade-off đã giải thích trong Chương 3 |
| Không có ensemble như FluSight | Single model XGBoost | Đề xuất future work: ensemble (XGB + LightGBM + CatBoost) |
| ECDC chỉ dùng validation | Chỉ có từ 2021, không đủ train | Giải thích trong Chương 3 |

---

## 4. References (cập nhật cho Chương 2)

Thêm vào reference list (ngoài [1]–[6] đã có trong đề cương):

```
[7] Bortman, M. "Elaboración corredores o canales endémicos mediante 
    planillas de cálculo." Boletín Epidemiológico OPS, vol. 20, no. 1, 
    pp. 1-3, 1999.

[8] Lowe, R. et al. "Climate services for health: predicting the 
    evolution of the 2016 dengue season in Machala, Ecuador." 
    Lancet Planetary Health, vol. 1, no. 4, e142-e151, 2017.

[9] Hussain-Alkhateeb, L. et al. "Early warning and response system 
    (EWARS) for dengue outbreaks: Recent advancements towards widespread 
    applications in critical settings." Frontiers in Public Health, 
    vol. 6, 2018.

[10] Reich, N. G. et al. "A collaborative multiyear, multimodel assessment 
     of seasonal influenza forecasting in the United States." PNAS, 
     vol. 116, no. 8, pp. 3146-3154, 2019.

[11] Bergmeir, C. & Benítez, J. M. "On the use of cross-validation for 
     time series predictor evaluation." Information Sciences, vol. 191, 
     pp. 192-213, 2012.

[12] Hii, Y. L. et al. "Forecast of dengue incidence using temperature 
     and rainfall." PLOS Neglected Tropical Diseases, vol. 6, no. 11, 
     e1908, 2012.

[13] Cinaglia, P. et al. "Forecasting influenza incidence as an ordinal 
     variable using machine learning." Wellcome Open Research, 9:11, 2024.
```

---

## 5. Risk register — Những vấn đề tiềm ẩn với approach mới

| Risk | Khả năng | Mitigation |
|---|---|---|
| Endemic channel cần ≥5 năm warm-up → mất 2010–2014 data train | Cao | Train từ 2015 trở đi (vẫn có 5 năm 2015–2019 cho training) |
| Class High có thể rất ít sample (chỉ ~10–15% rows) | Cao | `class_weight='balanced'`; consider SMOTE; report per-class metrics rõ ràng |
| Calibration kém (P(High)=0.8 nhưng thực tế chỉ 30%) | Trung bình | Platt scaling hoặc isotonic regression sau training; vẽ reliability diagram |
| Endemic baseline thay đổi theo COVID era | Trung bình | Loại 2020–2021 khỏi baseline calculation; rolling 5-year tự thích nghi sau |
| Một số nước nhỏ < 5 năm data | Trung bình | Fallback: dùng regional baseline (WHO region) thay vì country baseline |
| GVHD chất vấn vì sao bỏ regression | Cao | Đã chuẩn bị: literature support + parse semantic mô tả gốc + WHO EWARS reference |
