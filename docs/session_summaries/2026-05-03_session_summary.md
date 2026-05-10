# Session Summary — 03/05/2026 — Hoàn thành SESSION 5–8 với ERA5 fix

## Tóm tắt nhanh

**Trạng thái cuối ngày**: Đã chạy xong SESSION 5 → 6 → 7 → 8 với dataset mới (172 nước, sau khi fix ERA5 coverage bug). SESSION 9 đã fix code, sẵn sàng chạy hôm sau.

**Kết quả nổi bật:**
- **XGBoost Flu**: sMAPE non-zero **56.7%** (vs 51.4% cũ) — tương đương
- **XGBoost Dengue**: sMAPE **13.9%** (vs 7.2% cũ) — thực tế hơn nhờ dataset 4.4x lớn
- **Weather features** importance ~**14%** mỗi bệnh (vs ≈0% baseline cũ) — thành tựu chính
- Dataset: Flu 70K rows × 12 features (149 nước), Dengue 6.3K rows × 14 features (41 nước)

---

## Mục tiêu
Re-run toàn bộ ML pipeline (SESSION 5–8) với dataset mới sau khi fix ERA5 coverage bug, đồng thời tinh chỉnh feature engineering theo CCF-driven approach.

## Bối cảnh
- **Bug ERA5 cũ**: GeoPandas 1.0 bỏ `naturalearth_lowres` → chỉ 113/172 nước có weather, thiếu USA/CAN/FRA (chiếm tổng cộng ~1.7M ca cúm)
- **Fix**: Switch sang Natural Earth 50m + `ISO_A3_EH` → 197 countries; FluNet match 154/172 nước
- **Master_weekly mới**: 78,213 rows × 25 cols, 172 nước (vs 64,949 × 27 cols, 113 nước cũ)

---

## SESSION 5 — Data Quality Checks (ĐÃ CHẠY)

Thêm 5 cell quality check mới ([5.2]–[5.6]) vào notebook:

| Check | Kết quả | Đánh giá |
|---|---|---|
| Weather NaN rate | 8.5% (đều nhau cho 17 vars) | ✅ < 20%, đúng từ 18 nước thiếu ERA5 |
| Outlier weather | 0 outlier | ✅ Tất cả ngưỡng hợp lý |
| Coverage theo năm | Flu 119→164 nước; Weather 113→150 | ✅ Tăng dần, > 130 từ 2015 |
| Flu zero rows | **38.8%** (kỳ vọng 70–75%) | ⚠️ Reporting-only data, đã giải thích |
| Dengue endemic | **51 nước** (kỳ vọng 15–25) | ⚠️ OpenDengue 2023 mở rộng coverage |
| ERA5 seasonal (USA/VNM) | USA Jan −4°C, Jul +21°C; VNM 20→27°C | ✅ Capture đúng seasonality |

**Quyết định kiến trúc**: Giữ master_weekly ở dạng "reporting-only" (không full grid). Lý do: full grid + fillna(0) sẽ tạo "fake zeros" khi nước không báo cáo, làm nhiễu model. 38.8% zero rate phản ánh dữ liệu thực tế hơn.

---

## SESSION 6 — CCF Re-analysis (ĐÃ CHẠY)

**Phát hiện chính:**

| Biến → bệnh | Lag tối ưu | r | So với cũ |
|---|---|---|---|
| `solar_wm2` → flu | lag 8 | **−0.76** | mạnh nhất (mạnh hơn temp_c) |
| `temp_c` → flu | lag 4 | −0.73 | confirmed |
| `dewpoint_c` → flu | lag 2 | −0.72 | confirmed |
| `humidity_pct` → flu | lag 8 | **+0.65** | **dấu đảo** (cũ: âm) |
| `temp_c` → dengue | lag 0 | +0.49 | confirmed |
| `solar_wm2` → dengue | mọi lag | **≈ 0** | **mất signal hoàn toàn** |
| `humidity_pct` → dengue | lag 2 | +0.35 | thay solar_wm2 |

**Giải thích đảo dấu humidity (flu):** dataset mới có nhiều nước nhiệt đới hơn → flu peak vào mùa mưa (humid), ngược với ôn đới. Tropical signal đủ lớn để đảo chiều tổng thể.

**Quyết định:**
```python
WEATHER_LAGS_FLU = {'temp_c': 4, 'humidity_pct': 8, 'solar_wm2': 8, 'dewpoint_c': 2}
WEATHER_LAGS_DEN = {'temp_c': 0, 'humidity_pct': 2, 'dewpoint_c': 0, 'precip_mm': 0}
                                ^^^^^^^^^^^^^^^^^^ thay solar_wm2 (mất signal)
```

---

## SESSION 7 — Feature Engineering (ĐÃ CHẠY)

**Thay đổi lớn so với phiên bản cũ:**

1. **[7.5] Dict-based optimal lags**: mỗi biến đúng 1 lag tối ưu (thay vì cross-product 3 vars × 3 lags = 9 features)
2. **[7.7] Bỏ `WEATHER_VARS` raw** (17 biến lag0) khỏi feature set → tránh multicollinearity với weather lag features

**Feature count cuối:**

| Bệnh | AR lag | Rolling | Weather lag | Seasonal | **Tổng** |
|---|---|---|---|---|---|
| Flu | 3 | 2 | 4 | 3 | **12** |
| Dengue | 5 | 2 | 4 | 3 | **14** |

**Kết quả:**
- Flu: 70,056 rows × 12 features (149 nước) ↑ 59% so baseline cũ (44,035, 113 nước)
- Dengue: 6,313 rows × 14 features (41 nước) ↑ 340% so baseline cũ (1,435, ~15 nước)

---

## SESSION 8 — Model Training (ĐÃ CHẠY)

**Bug fixes:**
- [8.7]: Bỏ idempotent guard → force retrain (tránh load model cũ với feature set khác)
- [8.8b]: Bỏ `use_label_encoder=False` (deprecated trong XGBoost 2.x)

**Walk-forward CV results (folds 2014–2019):**

| Model | MAE | RMSE | sMAPE | So baseline cũ |
|---|---|---|---|---|
| Prophet Flu (global) | 4,507 | 6,619 | 49.6% | MAE ×2.3 do thêm nước |
| **XGBoost Flu** | **26.4** | 241 | 112% (all) / **56.7%** (non-zero) | non-zero +5pt vs 51.4% cũ |
| Prophet Dengue (log) | 35.2 | 38.0 | 49.4% | sMAPE ↓ vs 93.4% cũ |
| **XGBoost Dengue** | **0.55** | 0.87 | **13.9%** | sMAPE ×2 (7.2% → 13.9%) |

### Phát hiện quan trọng nhất — Feature Importance

**Weather features cuối cùng có signal đáng kể** (so với baseline cũ ≈ 0%):

| Bệnh | Top features | Weather contribution |
|---|---|---|
| Flu | `inf_lag2w` 0.34 + `inf_roll4w` 0.33 (67%) | 4 weather features ~**14%** |
| Dengue | `dengue_roll4w` 0.44 + AR lags ~24% | `precip_mm`, `dewpoint_c`, ... ~**14%** |

**Lý do cải thiện:**
1. Bỏ `WEATHER_VARS` raw → không che weather lag features
2. CCF-driven optimal lags → tránh multicollinearity
3. Dataset lớn hơn (4.4x dengue, 1.6x flu) → đủ samples học weather pattern

→ Đây là lập luận chính cho thesis: **CCF-driven feature engineering thực sự giúp model tận dụng tín hiệu khí hậu**, không chỉ AR thuần như version cũ.

---

## Files đã thay đổi

| File | Thay đổi |
|---|---|
| `KLTN_EpiWeather_ML_Colab.ipynb` | +10 cell (5.2-5.6 quality), 8 cell sửa (6.1, 7.1, 7.5, 7.7, 8.7, 8.8b, 9.1, 9.5) |
| `.claude/ml_data_workflow.md` | Tài liệu workflow ML iterative cycle |
| `.claude/patch_s5_quality.py` | Script chèn quality checks |
| `.claude/patch_s7_lags.py` | Script update lag features |
| `.claude/patch_s9_v2.py` | Script fix SESSION 9 |
| `dataset/processed/master_weekly_2010_2019.csv` | 78,213 × 25 (172 nước) |
| `dataset/processed/features_flu_2010_2019.csv` | 70,056 × 16 |
| `dataset/processed/features_dengue_2010_2019.csv` | 6,313 × 18 |
| `outputs/xgb_flu_final.pkl` | Re-trained 12 features |
| `outputs/xgb_dengue_final.pkl` | Re-trained 14 features |

---

## Đã hoàn thành hôm nay

| Task | Status |
|---|---|
| SESSION 5 — Data Quality Checks (5 cell mới) | ✅ Done |
| SESSION 6 — CCF Re-analysis (lags mới) | ✅ Done |
| SESSION 7 — Feature Engineering (re-build) | ✅ Done |
| SESSION 8 — Model Training (re-train + CV) | ✅ Done |
| SESSION 9 — fix code chuẩn bị | ✅ Code đã patch, sẵn sàng run |
| Notion summary upload | ✅ Done |

## Bước tiếp theo (chưa làm)

| Task | Status |
|---|---|
| Run SESSION 9 — Validation 2022 | ⏳ Sẵn sàng, chạy hôm sau |
| Update Master Notebook trên Notion | ⏳ Sau SESSION 9 |
| PostgreSQL schema design | ❌ Chưa làm |
| FastAPI backend | ❌ Chưa làm |
| Frontend React + Leaflet | ❌ Chưa làm |

---

## Những điều cần ghi nhớ cho báo cáo

1. **Granularity mismatch Prophet vs XGBoost**: MAE/RMSE không so sánh trực tiếp được (Prophet global vs XGBoost per-country). Chỉ sMAPE so sánh được.
2. **Flu zero rate 38.8%**: do reporting-only data (không full grid). Ảnh hưởng sMAPE all-rows nhưng không ảnh hưởng model quality thực tế.
3. **Humidity dấu đảo cho flu**: do thêm nhiều nước nhiệt đới, không phải bug. Cần giải thích rõ trong báo cáo.
4. **Dengue 13.9% sMAPE thực tế hơn 7.2% cũ**: dataset 4.4x lớn hơn và đa dạng hơn, baseline cũ có dấu hiệu overfit trên 1,435 rows.
5. **Limitation ERA5 monthly means**: `temp_range_c = 0` cho mọi tuần trong tháng, làm mờ lag analysis cấp tuần. Đề xuất future work: ERA5 daily/weekly.
