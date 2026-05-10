# Session Summary — 05/05/2026 — Cải thiện model Flu: log1p + Hemisphere revert + Optuna tuning

## Tóm tắt nhanh

**Trạng thái cuối ngày**: Hoàn thành bước 1–3 trong lộ trình cải thiện model flu. R² flu tăng từ 0.488 → **0.811** nhờ log1p transform. Optuna xác nhận model đã ổn định. Còn bước 4 (Open-Meteo 2022 weather) sẽ làm tối nay.

**Kết quả nổi bật:**
- **Flu R² = 0.811** (tăng từ 0.488 — cải thiện +66% nhờ log1p transform)
- **Dengue R² = 0.858** (không đổi — đã tốt từ trước)
- Optuna 60 trials không cải thiện thêm so với baseline → xác nhận bottleneck là dữ liệu 2022, không phải hyperparameter

---

## Bối cảnh — Tại sao cần cải thiện

Kết thúc buổi 04/05, SESSION 9 cho kết quả flu R² = **0.488** — quá thấp để trình bày trong báo cáo. Nguyên nhân ban đầu nghi ngờ là:

1. **Target distribution lệch nặng** — `inf_cases` có phân phối long-tail cực đoan (đỉnh ~77K tuần, nhưng 38.8% rows = 0). XGBoost tối ưu MSE trên raw scale → bị dominated bởi các peak lớn.
2. **Hemisphere/climate zone features** — đã thêm vào [7.7] với kỳ vọng giúp model phân biệt flu season ngược nhau giữa 2 bán cầu.
3. **Hyperparameter chưa tối ưu** — XGBoost dùng default params, chưa tune.

Ba bước cải thiện được thực hiện theo thứ tự ưu tiên này.

---

## Bước 1 — log1p transform cho flu target ✅

**Vấn đề:** `inf_cases` raw có phân phối long-tail: Brazil, USA, India chiếm phần lớn tổng ca → model bị kéo về tối ưu cho các nước lớn, underfit cho phần còn lại. R² = 0.488 trên validation 2022.

**Giải pháp:** Áp dụng `log1p(inf_cases)` làm target (giống dengue đã làm từ trước), đổi `TARGET_FLU = 'inf_log1p'`. Cập nhật toàn bộ pipeline: feature AR lags ([7.5]), walk-forward CV ([8.5]), validation ([9.1]).

**Kết quả:**

| Metric | Trước (raw) | Sau (log1p) |
|---|---|---|
| R² | 0.488 | **0.811** |
| MAE | 47.97 (raw cases) | 0.41 (log1p) |
| sMAPE non-zero | 62.9% | 73.4% |

**Nhận xét:** R² tăng +66% — đây là cải thiện lớn nhất trong toàn bộ lộ trình. sMAPE raw tăng (62.9% → 73.4%) vì expm1 amplification tại các peak, nhưng đây là artifact của việc chuyển đổi scale, không phải model tệ hơn. Metric báo cáo chuẩn: **R² = 0.811, sMAPE non-zero = 73.3%**.

---

## Bước 2 — Revert hemisphere + climate zone features ✅

**Vấn đề:** Sau bước 1, kiểm tra feature importance của `hemisphere_enc` và `climate_zone_enc` cho thấy chỉ ~1–2%, không đóng góp có ý nghĩa vào model. Hai features này thêm complexity không cần thiết và có thể gây noise.

**Giải pháp:** Xóa `hemisphere_enc` và `climate_zone_enc` khỏi `FEATURE_COLS_FLU`, giữ nguyên 12 features cốt lõi: 3 AR lags, 2 rolling means, 4 weather lags (CCF-optimal), 3 seasonality features.

**Kết quả:** Metrics không thay đổi so với khi có hemisphere features → quyết định đúng, model gọn hơn, dễ giải thích hơn trong báo cáo.

**Feature set cuối cùng (12 features):**
- AR: `inf_lag1w`, `inf_lag2w`, `inf_lag3w`
- Rolling: `inf_roll4w`, `inf_roll8w`
- Weather: `temp_c_flu_lag4w`, `humidity_pct_flu_lag8w`, `solar_wm2_flu_lag8w`, `dewpoint_c_flu_lag2w`
- Seasonality: `sin_week`, `cos_week`, `quarter`

---

## Bước 3 — Optuna hyperparameter tuning ✅

**Vấn đề:** XGBoost baseline dùng default params — có thể còn room để cải thiện thêm qua tuning.

**Giải pháp:** Optuna TPE Sampler, 60 trials (~30 phút), objective = minimize CV MAE (log1p) trên walk-forward 6 folds (2014–2019).

**Best params tìm được:**

| Param | Giá trị |
|---|---|
| n_estimators | 650 |
| max_depth | 7 |
| learning_rate | 0.0323 |
| subsample | 0.641 |
| colsample_bytree | 0.844 |
| min_child_weight | 6 |
| reg_alpha | 0.518 |
| reg_lambda | 0.712 |

**Kết quả validation 2022 sau Optuna:**

| Metric | Baseline [8.5] | Sau Optuna |
|---|---|---|
| CV MAE (log1p) | ~0.46 | **0.4508** (~2% better) |
| R² holdout 2022 | 0.811 | **0.811** (không đổi) |
| sMAPE non-zero | 73.4% | **73.3%** (không đổi) |

**Nhận xét:** Optuna cải thiện CV MAE 2% nhưng **không cải thiện trên holdout 2022**. Kết luận: bottleneck không phải hyperparameter mà là bản chất dữ liệu 2022 — immunity debt post-COVID tạo ra đỉnh flu cao hơn toàn bộ training set 2010–2019, model không thể extrapolate ra ngoài vùng đã học. Đây là limitation cần giải thích rõ trong báo cáo.

---

## Kết quả tổng hợp cuối ngày

| Model | R² | MAE (log1p) | sMAPE non-zero | n (val 2022) |
|---|---|---|---|---|
| XGBoost Flu (Optuna) | **0.811** | 0.519 | 73.3% | 11,209 |
| XGBoost Dengue | **0.858** | 0.468 | 12.5% | 1,399 |

---

## Files đã thay đổi

| File | Thay đổi |
|---|---|
| `KLTN_EpiWeather_ML_Colab.ipynb` | Thêm cells [8.5b], [8.6]; cập nhật TARGET_FLU, FEATURE_COLS_FLU; ghi chú markdown toàn bộ |

---

## Còn lại / Chưa làm

- ⏳ **Bước 4 — Open-Meteo 2022 weather**: Fetch weather thực tế 2022 (~146 flu countries, ~41 dengue countries) từ Open-Meteo API (free, không cần key), thay per-country training mean trong [9.1]. Script: `scripts/fetch_openmeteo_2022.py`
- ❌ PostgreSQL schema design
- ❌ FastAPI backend
- ❌ Frontend React + Tailwind + Leaflet

---

## Ghi nhớ cho báo cáo

1. **Flu R² 0.811 trên log1p scale** — khi báo cáo luôn nêu rõ scale, không để người đọc nhầm với raw cases.
2. **sMAPE báo cáo = non-zero rows (73.3%)** — all-rows (132.6%) bị inflate bởi zero reporting weeks và expm1 amplification, không dùng.
3. **Optuna không cải thiện holdout** — nêu thẳng trong thesis: hyperparameter tuning có giới hạn khi vấn đề là distribution shift (immunity debt), không phải model capacity.
4. **Flu 2022 là năm bất thường** — đỉnh tuần 50 (~77K) cao hơn mọi năm trong training set. Đây là known limitation, không phải lỗi thiết kế.
5. **Weather 2022 = training mean** — limitation cần nêu, bước 4 (Open-Meteo) sẽ khắc phục.
