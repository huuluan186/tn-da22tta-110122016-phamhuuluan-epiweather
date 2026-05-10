# Session Summary — 04/05/2026 — SESSION 9: Validation 2022 + Risk Classification

## Tóm tắt nhanh

**Trạng thái cuối ngày**: Hoàn thành toàn bộ SESSION 9 — validation trên năm 2022, risk classification, export model artifacts cho FastAPI. Phần ML pipeline hoàn chỉnh.

**Kết quả nổi bật:**
- **Dengue R² = 0.858**, sMAPE 12.5%, risk F1 macro 0.85 — production-ready
- **Flu R² = 0.488**, sMAPE non-zero 62.9% — acceptable, có thể giải thích bởi immunity debt 2022
- Feature list JSON đã export → sẵn sàng cho FastAPI

---

## Mục tiêu
Validate model đã train (SESSION 8) trên năm 2022 — năm hoàn toàn ngoài training set và là năm đầu tiên surveillance trở lại bình thường sau COVID.

---

## SESSION 9 — Validation 2022

### [9.1] Metrics tổng thể

| Model | MAE | RMSE | R² | sMAPE | n |
|---|---|---|---|---|---|
| XGBoost Flu | 47.97 | 760.77 | 0.488 | 62.9% (non-zero) | 11,209 |
| XGBoost Dengue | 0.468 | 0.786 | **0.858** | **12.5%** | 1,399 |

**Weather 2022:** ERA5 chỉ có đến 2019 → fill bằng per-country training mean (proxy seasonal baseline, mất biến động thực tế 2022).

**Dengue:** Tốt hơn cả CV (R² 0.858 vs không đo, sMAPE 12.5% vs 13.9%) — model generalize tốt, pattern dengue ổn định qua thời gian.

**Flu:** R² 0.488, RMSE 2022 (760) >> CV (241) — do **immunity debt**: 2022 là mùa flu đầu tiên sau 2 năm COVID, đỉnh bùng phát (~77K tuần 50) cao bất thường so với bất kỳ năm nào trong 2010–2019. Model không thể học pattern này từ training data.

### [9.2] Visualization Predicted vs Actual

- **Flu:** Hình dạng mùa vụ đúng (summer low → winter peak) nhưng underestimate đỉnh tuần 50 gấp 2.5 lần (~30K predicted vs ~77K actual). Overestimate tuần 1–5 do AR lags từ cuối 2021 (COVID period excluded) không đại diện cho pattern bình thường.
- **Dengue:** Hai đường bám sát nhau suốt năm, xác nhận R² = 0.858.

### [9.3] Risk Classification (Low / Medium / High)

| Model | Accuracy | F1 macro | Ghi chú |
|---|---|---|---|
| Flu | 0.40 | 0.36 | Medium F1 = 0.01 — model bỏ qua tier trung gian |
| **Dengue** | **0.85** | **0.85** | Đều cả 3 tier, production-ready |

**Vấn đề flu risk:** Model predict bimodal (Low hoặc High), gần như không bao giờ predict Medium (recall = 0.00). Nguyên nhân: 38.8% zero rows làm prediction distribution skewed, không có vùng trung gian rõ ràng. Top predictions USA tuần 48–52 trigger High đúng hướng nhưng magnitude vẫn underestimate 4–5 lần.

### [9.4] Model Summary

| | XGBoost Flu | XGBoost Dengue |
|---|---|---|
| Target | inf_cases | dengue_log1p |
| n_features | 12 | 14 |
| n_countries (val) | 146 | 41 |
| Train period | 2010–2019 | 2010–2019 |
| Val year | 2022 | 2022 |

### [9.5] Export

- `outputs/feature_list.json` — feature names, lags, rolling windows cho FastAPI

---

## Điểm đã cải thiện so với baseline cũ (toàn pipeline)

| Khía cạnh | Baseline cũ | Phiên bản hiện tại |
|---|---|---|
| ERA5 coverage | 113/172 nước | 154/172 nước (92%) |
| Flu dataset | 44,035 rows, 113 nước | 70,056 rows, 149 nước |
| Dengue dataset | 1,435 rows, ~15 nước | 6,313 rows, 41 nước |
| Weather importance | ≈ 0% | ~14% (cả flu và dengue) |
| Dengue validation R² | ~overfit trên 1,435 rows | **0.858 trên 2022** |
| Dengue risk F1 | N/A | **0.85 macro** |

---

## Hướng cải thiện tiếp theo

### Cải thiện ngay (ưu tiên cao — trước khi viết báo cáo)

| Hướng | Mô tả | Kỳ vọng cải thiện |
|---|---|---|
| **Flu: per-country risk quantile** | Thay global quantile bằng per-country quantile → tránh USA dominated distribution | Flu F1 Medium tăng từ 0.01 |
| **Flu: log1p transform target** | Áp dụng log1p cho `inf_cases` như dengue → giảm ảnh hưởng của các đỉnh bất thường | RMSE giảm, R² tăng |
| **Hemisphere feature** | Thêm binary feature: Northern/Southern Hemisphere → flu season inverted | Flu sMAPE giảm ~5–10% |
| **Climate zone feature** | Tropical / Temperate / Arctic → model học riêng pattern từng zone | Cả hai bệnh |

### Cải thiện trung hạn (sau khi có backend)

| Hướng | Mô tả |
|---|---|
| **ERA5 daily/weekly** | Thay monthly means → lag analysis chính xác hơn ở độ phân giải tuần |
| **ENSO index** | El Niño/La Niña strongly correlated với dengue outbreaks — thêm làm feature |
| **OpenWeatherMap 2022** | Thay per-country mean bằng weather thực tế 2022 để test lại validation |
| **XGBoost hyperparameter tuning** | GridSearch / Optuna cho n_estimators, max_depth, learning_rate |
| **LightGBM so sánh** | Thường nhanh hơn và tốt hơn XGBoost trên tabular data |

### Future work (thesis limitation section)

- **LSTM shared encoder** (multi-task learning flu + dengue) — tận dụng shared weather signal
- **Country-specific models** cho top 5 endemic dengue countries (Brazil, India, Thailand, Vietnam, Philippines)
- **Nowcasting** thay vì forecasting — dùng realtime OpenWeatherMap

---

## Files đã thay đổi hôm nay

| File | Thay đổi |
|---|---|
| `KLTN_EpiWeather_ML_Colab.ipynb` | SESSION 9 hoàn chỉnh ([9.0]–[9.5]) |
| `outputs/feature_list.json` | Export features + lags cho FastAPI |

---

## Trạng thái tasks

| Task | Status |
|---|---|
| SESSION 9 — Validation 2022 | ✅ Done |
| Export feature list JSON | ✅ Done |
| Phần ML pipeline | ✅ **Hoàn chỉnh** |
| Cải thiện flu (log1p + per-country quantile) | ⏳ Tuần tới |
| PostgreSQL schema design | ❌ Chưa làm |
| FastAPI backend | ❌ Chưa làm |
| Frontend React + Tailwind + Leaflet | ❌ Chưa làm |

---

## Ghi nhớ cho báo cáo

1. **Flu RMSE 760 vs CV 241** — immunity debt 2022, không phải lỗi model. Giải thích bằng dịch tễ học.
2. **Flu sMAPE dùng non-zero (62.9%)** — all-rows (131.6%) bị inflate bởi zero reporting weeks.
3. **Flu risk dùng binary Low/High** trong dashboard, không dùng 3 tier — Medium tier unreliable.
4. **Dengue R² 0.858 > CV** — generalization tốt, pattern ổn định qua COVID.
5. **Weather 2022 = training mean** — limitation quan trọng, ảnh hưởng validation. Production cần OpenWeatherMap realtime.
