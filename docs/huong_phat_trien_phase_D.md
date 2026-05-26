# Hướng phát triển Phase D — Nowcast Realtime + Multi-horizon Forecasting

Cập nhật: 21/05/2026  
Quyết định chốt sau buổi làm việc 21/05: không dùng proxy fake current-week.  
Hướng đúng: realtime data ingestion (A) + multi-horizon model (C).

---

## Bối cảnh và lý do pivot

Model hiện tại (SESSION 0-6, v5) được train trên 2010-2019. Inference trên chính tập train
không có giá trị — model đã thấy data đó. Để "dự báo tuần hiện tại" cần:
- Input feature vector từ data **ngoài** training distribution
- Multi-horizon target: predict cases tại t+h, không phải tại t (same week)

Tham chiếu literature: CDC FluSight (pull ILINet weekly → predict), Lowe et al 2014 Lancet ID
(rolling update dengue Brazil), WHO EWARS (endemic channel alert).

---

## Phase C — Multi-horizon Model (làm trước)

**Lý do C trước A:** Phase A cần biết feature schema của model. C define schema đó.

### C-1 — Training (SESSION 7 notebook, ~1 buổi)

Mở `notebooks/KLTN_EpiWeather_ML_v5.ipynb`, thêm SESSION 7.

**Chuẩn bị targets:**
```
# Với mỗi (iso3, iso_year, iso_week):
flu_log_h1 = flu_log shifted forward 1 tuần per iso3
flu_log_h2 = flu_log shifted forward 2 tuần per iso3
flu_log_h3 = flu_log shifted forward 3 tuần per iso3
flu_log_h4 = flu_log shifted forward 4 tuần per iso3
```

Feature set giữ nguyên 16 cột của lgbm_flu_regressor_v1 (không thêm bớt).  
Tương tự cho dengue (20 cột, target deng_log_h1..h4).

**Training:**
- Flu: 4 LightGBM Regressor, cùng best_params từ v1 (Optuna đã tune)
- Dengue: 4 Random Forest Regressor, cùng params từ v1
- Walk-forward CV 6 folds (val_year 2014-2019) — same scheme
- Metrics per horizon: RMSE, MAE, R²

**Kỳ vọng degradation curve (Lowe et al 2014 benchmark):**

| Horizon | Flu R² kỳ vọng | Dengue R² kỳ vọng |
|---|---|---|
| h=1 (1 tuần) | ~0.88-0.90 | ~0.90-0.93 |
| h=2 (2 tuần) | ~0.80-0.85 | ~0.82-0.88 |
| h=3 (3 tuần) | ~0.70-0.78 | ~0.72-0.80 |
| h=4 (4 tuần) | ~0.60-0.70 | ~0.62-0.72 |

Degradation là expected — signal đến từ AR lags bị "stale" hơn.

**Artifacts:**
```
ml_models/
  lgbm_flu_regressor_h1_v1.pkl + _features.json + _metrics.json
  lgbm_flu_regressor_h2_v1.pkl + ...
  lgbm_flu_regressor_h3_v1.pkl + ...
  lgbm_flu_regressor_h4_v1.pkl + ...
  rf_dengue_regressor_h1_v1.pkl + ...
  rf_dengue_regressor_h2_v1.pkl + ...
  rf_dengue_regressor_h3_v1.pkl + ...
  rf_dengue_regressor_h4_v1.pkl + ...
```

**Bảng so sánh BẮT BUỘC trong SESSION 7:**

| Disease | Model | h=1 R² | h=2 R² | h=3 R² | h=4 R² |
|---|---|---|---|---|---|
| Flu | LightGBM | ? | ? | ? | ? |
| Dengue | Random Forest | ? | ? | ? | ? |

### C-2 — Backend multi-horizon API (~0.5 buổi)

**ml_engine.py cập nhật:**
```python
_regressors[(disease, horizon)] = artifact  # horizon = 1,2,3,4
```

**Schema mới** (`schemas/prediction.py`):
```python
class ForecastPoint(BaseModel):
    horizon: int               # 1,2,3,4
    target_iso_year: int
    target_iso_week: int
    predicted_cases: float
    predicted_log: float
    risk_level: str            # Low/Medium/High từ classifier

class ForecastResponse(BaseModel):
    disease: str
    iso3: str
    as_of_year: int            # tuần "hiện tại" dùng làm input
    as_of_week: int
    points: list[ForecastPoint]
```

**Endpoint mới:**
```
GET /api/v1/forecast/{disease}/{iso3}?as_of_year=&as_of_week=
```

Returns 4-week trajectory. `as_of_week` = tuần mà ta có features thực tế.

---

## Phase A — Realtime Data Ingestion (sau C)

### A-1 — Data sync scripts (~1.5 buổi)

**scripts/sync_flunet.py**
- Pull từ WHO FluMart API (endpoint `https://xmart-api-public.who.int/FLUMART/VIW_FNT`)
- Filter: lấy tất cả countries trong training set, 8 tuần gần nhất
- INSERT INTO disease_cases ON CONFLICT UPDATE

**scripts/sync_openweather.py**
- OpenWeatherMap Historical Weather API hoặc Current + 7-day history
- 150 countries × 8 tuần past → ~1200 API calls (batch theo country centroid)
- INSERT INTO weather_observations

**Cron schedule (Phase 8):** chạy mỗi thứ Hai 8:00 ICT (FluNet publish Mon).

### A-2 — Feature builder service (~1 buổi)

**app/services/feature_builder.py**

```python
def build_features(
    db: Session,
    iso3: str,
    disease: str,
    as_of_year: int,
    as_of_week: int,
) -> dict[str, float] | None:
    """
    Assemble feature vector cho (iso3, disease, as_of_week).
    Trả None nếu thiếu quá nhiều lag windows (>50% features missing).

    Lấy từ DB:
      - disease_cases: AR lags flu_log_lag1/2/3, rollmean4/8
      - weather_observations: temp_c_lag3/7, humidity_pct_lag1/7, solar_wm2_lag7, dewpoint_c_lag1
      - Deterministic: iso_week_sin/cos, iso_year, HEMISPHERE_NH/SH
    """
```

Cache: 1h TTL per (iso3, disease, as_of_week) để tránh recompute khi risk-map gọi 150+ countries.

### A-3 — Nowcast endpoint (~0.5 buổi)

**GET /api/v1/nowcast/{disease}/{iso3}**
- Tìm `as_of_week` = tuần mới nhất có disease_cases trong DB cho iso3
- Gọi feature_builder → build feature vector
- Chạy multi-horizon model h=1..4
- Return ForecastResponse với badge `data_through: "2026-W19"` (honest label)

**GET /api/v1/risk-map/nowcast/{disease}**
- Gọi nowcast cho toàn bộ countries có data
- Return RiskMapResponse với `as_of_week` + `forecast_horizon=1` (nearest-term risk)
- Countries thiếu data → risk_level=null (không fake)

---

## Phase 4 — Frontend wiring (~0.5 buổi)

**hooks/useNowcast.ts** (thay useRiskMap cho current-week view):
```typescript
// Fetch /risk-map/nowcast/{disease}
// Badge: "Data through W{X} · Forecasting W{X+1}"
```

**DiseaseDetailPage** — chart 4-week trajectory:
- x-axis: W{X+1}, W{X+2}, W{X+3}, W{X+4}
- y-axis: predicted_cases
- Confidence band: confidence_lo/hi nếu có

**Honest label thay mock badge:**
```
W21 · 2026  [Data through W19 · Forecasting W20]
```

---

## Thứ tự bàn giao

| Phase | Effort | Prerequisite | Output |
|---|---|---|---|
| C-1 | 1 buổi (notebook) | Bạn chạy | 8 pkl artifacts h1-h4 |
| C-2 | 0.5 buổi (backend) | C-1 done | /forecast endpoint |
| DB seed | 0.5 buổi | C-2 | load_db_v2.py seeded |
| A-1 | 1.5 buổi (scripts) | OpenWeatherMap API key | weather_observations populated |
| A-2 | 1 buổi (backend) | A-1 | feature_builder service |
| A-3 | 0.5 buổi (backend) | A-2 + C-2 | /nowcast endpoint |
| Phase 4 | 0.5 buổi (frontend) | A-3 | Dashboard realtime |

**Tổng: ~5.5 buổi.**

---

## Câu chuyện khoa học cho báo cáo

**Input thật tuần T → predict cases tuần T+1, T+2, T+3, T+4**

Trích dẫn: CDC FluSight (Reich et al 2019), Lowe et al 2014 Lancet ID,
WHO EWARS endemic channel threshold (Bortman 1999).

Đóng góp của đề tài so với literature:
- Flu (global, 143 nước) thay vì chỉ US/Brazil
- Hybrid: regression dự báo số ca + classification risk level
- Multi-horizon comparison table (h=1..4) — ít đề tài Việt Nam làm
- Realtime ingestion pipeline (FluNet + ERA5T/OpenWeatherMap)
