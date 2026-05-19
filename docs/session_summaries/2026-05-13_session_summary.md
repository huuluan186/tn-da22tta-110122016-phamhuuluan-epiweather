# Session Summary — 13/05/2026 — Rà soát lại bài toán ML và quyết định đổi hướng từ Regression-then-Bucket sang Ordinal Classification với Endemic Channel labels

## Tóm tắt nhanh

**Trạng thái cuối ngày:** Sau khi đối chiếu **mô tả gốc của khoa**, **tên đề tài**, **literature operational (WHO EWARS, CDC FluSight, Wellcome Open Research 2024)** và **bản chất data thực**, kết luận: approach hiện tại (regression XGBoost → quantile bucketing → tier Low/Med/High) **không sai về output cuối**, nhưng **lệch về optimization target** — model đang tối ưu MSE trên số ca thay vì tối ưu F1 cho cảnh báo. Quyết định **làm lại SESSION 7–9 theo hướng Ordinal Multi-class Classification với Endemic Channel labels** (phong cách WHO EWARS đang vận hành thật tại Mexico/Brazil).

**Kết quả nổi bật:**
- **Rà soát 4 input authoritative**: tên đề tài, mô tả gốc khoa, literature, data thực — phát hiện đề cương chi tiết (do Claude tự draft trước đó) đã **over-spec** hơn mô tả gốc (thêm RMSE/MAE/R² mà mô tả gốc không yêu cầu)
- **Identify root cause cho Medium F1 ≈ 0**: KHÔNG phải bug, mà là *structural problem* — quantile threshold global bị Brazil dominate, và regression-then-bucket optimize sai metric
- **Chốt approach mới**: Ordinal Classification (XGBClassifier multi:softprob) với label từ Endemic Channel method (Bortman 1999, WHO EWARS)
- **Lộ trình implementation**: viết lại SESSION 7–9, giữ nguyên SESSION 1–5 (data + EDA + CCF còn nguyên giá trị)

---

## Bối cảnh — Vì sao cần rà soát lại

Tiếp nối session 10/05 (load_db.py + báo cáo Chương 3 xong). Sinh viên đặt câu hỏi sắc bén về architecture ML hiện tại:

1. *"Cách train đúng chưa? Output thực sự là phân loại hay hồi quy?"*
2. *"GVHD đã góp ý không nên chia data theo năm — có nên làm không?"*
3. *"Phân loại mức độ mà lại làm hồi quy, tôi đã xác định sai mục tiêu sao?"*
4. *"Dựa vào tên đề tài, mô tả gốc, paper... thì nên làm như nào mới hợp lý nhất?"*

Loạt câu hỏi này forced một cuộc rà soát từ first principles — không anchor vào đề cương đã ký (vì đề cương do Claude tự draft, không phải input authoritative).

---

## Phân tích — 4 input authoritative

### 1. Tên đề tài (semantic parse)
> *"Hệ thống **cảnh báo** **nguy cơ** dịch bệnh **theo mùa**"*

| Từ khóa | Hàm ý ML |
|---|---|
| cảnh báo | Output = action (warning), không phải số |
| nguy cơ | Probabilistic, có degree |
| theo mùa | Có baseline mùa để so sánh |

### 2. Mô tả gốc khoa
> *"đề xuất mô hình dự đoán... dự báo dịch bệnh **có thể diễn ra** theo từng giai đoạn/mùa/tháng... **cảnh báo khả năng diễn ra**... **cảnh báo mức độ**"*

**Cụm từ KHÔNG có trong mô tả gốc:**
- "dự báo số ca"
- "RMSE/MAE/R²"
- "regression"

→ Mô tả gốc yêu cầu **classification with probability**, không yêu cầu predict số ca.

### 3. Literature evidence (4 paper review 2024–2026)

| Hệ thống | Approach | Citation |
|---|---|---|
| WHO EWARS (Mexico, operational) | Probabilistic classification + Endemic Channel | Hussain-Alkhateeb et al. 2018, Lowe et al. 2016 |
| CDC FluSight | Probabilistic forecasting (ensemble) | Reich et al. 2019 |
| Wellcome Open Research 2024 (influenza) | **Ordinal classification per country-week** | medRxiv 2024 |
| Bangladesh dengue 2024 | Regression + threshold (hybrid) | PMC12063067 |

Số liệu papers: **21% classification, 76% regression, 3% hybrid**. Nhưng **operational systems** (đang chạy thật, không phải paper) đều dùng classification/probabilistic.

### 4. Data thực tế
- 64,949 rows × 27 cols, 172 nước
- Zero-inflated (~38.8% rows có 0 ca)
- Long-tail (Brazil 70% dengue)
- Strong seasonality + weather lag 2–14w

→ Data này **không phù hợp** với Gaussian MSE regression. Hợp hơn với ordinal classification trên label dịch tễ học.

---

## Kết luận quan trọng

### Approach cũ (đang dùng)
```
XGBRegressor → predicted_cases → quantile(0.33, 0.67) → tier Low/Med/High
```
**Vấn đề:**
1. **Optimize sai metric**: MSE thay vì F1
2. **Quantile global**: Brazil dominate → Medium F1 ≈ 0
3. **Không có ý nghĩa dịch tễ**: "top 33%" ≠ "bùng phát"
4. **Không có probability output**: chỉ có tier cứng

### Approach mới (chốt)
```
Endemic Channel labels (per-country, per-week-of-year)
  ↓
XGBClassifier (multi:softprob, num_class=3)
  ↓
P(Low), P(Medium), P(High) per (country, week, disease)
```

**Label generation (per Bortman 1999 / WHO EWARS):**
```
baseline = mean(cases, last 5 years, same ISO week)
sd       = std(cases, last 5 years, same ISO week)

label = Low    if cases < baseline
      = Medium if baseline ≤ cases < baseline + 2σ
      = High   if cases ≥ baseline + 2σ
```

**Vì sao đúng hơn:**
- ✅ Khớp tên đề tài (cảnh báo, nguy cơ, theo mùa)
- ✅ Khớp mô tả gốc khoa (khả năng diễn ra, mức độ)
- ✅ Khớp operational gold standard (WHO EWARS)
- ✅ Optimize đúng metric (cross-entropy → F1)
- ✅ Output có probability (đúng nghĩa "khả năng diễn ra")
- ✅ Per-country baseline tự khử Brazil dominance
- ✅ Cite được paper top (Lowe 2016, Wellcome 2024)

---

## Phản biện góp ý GVHD "không chia data theo năm"

GVHD đã góp ý: *"Không nên chia data theo năm để training và validation. Nên tận dụng sự đa dạng và biến hóa của dịch bệnh"*.

**Phản biện** (đã chuẩn bị để trao đổi với cô):
> Theo lý thuyết time-series forecasting (Bergmeir & Benítez 2012), nếu shuffle random giữa các tuần sẽ xảy ra **data leakage** — model nhìn tương lai để predict quá khứ, R² ảo cao nhưng không phản ánh deployment thật. Em đã giải quyết ý cô bằng **walk-forward cross-validation 6 folds (2014–2019)**: mỗi fold validate trên 1 năm khác nhau, bao gồm cả năm dịch lớn (2018 H1N1) lẫn năm bình thường (2016, 2017). Đây mới đúng nghĩa "tận dụng đa dạng" mà vẫn tôn trọng causality thời gian.

---

## Việc cần làm tiếp (lộ trình mới)

| Step | Time | Output |
|---|---|---|
| Viết notebook SESSION 7 mới — label generation (Endemic Channel) | 2 giờ | Cột `risk_label` trong master CSV |
| Viết SESSION 8 mới — train XGBClassifier với class_weight | 4 giờ | 2 model (.pkl): `xgb_flu_clf.pkl`, `xgb_dengue_clf.pkl` |
| Viết SESSION 9 mới — eval per-class F1, AUC, calibration | 2 giờ | `model_metrics_v2.json` |
| Update Chương 3 — section ML method | 2 giờ | Phần 3.5 viết lại |
| Update load_db.py — load classifier thay vì regressor | 1 giờ | DB có thêm `model_evaluations` row mới |
| **Tổng** | **~11 giờ** | Demo 1 với approach đúng (vẫn kịp 17/05) |

---

## Files cần thay đổi/tạo

| File | Hành động |
|---|---|
| `CLAUDE.md` | **Update** — mô tả đề tài mới + decisions mới |
| `docs/new_approach_rationale.md` | **Tạo mới** — giải thích chi tiết hướng mới, novelty |
| `docs/system_output_dashboard_spec.md` | **Tạo mới** — đặc tả output + FE/BE |
| `docs/chapter3_system_design.md` | **Update** — phần 3.5 (ML method) viết lại |
| `KLTN_EpiWeather_ML.ipynb` | **Update** — SESSION 7-9 viết lại |
| `models/xgb_flu_clf.pkl` | **Tạo mới** — classifier flu |
| `models/xgb_dengue_clf.pkl` | **Tạo mới** — classifier dengue |
| `models/model_metrics_v2.json` | **Tạo mới** — metrics classifier |

---

## Files đã thay đổi hôm nay

| File | Thay đổi |
|---|---|
| `docs/session_summaries/2026-05-13_session_summary.md` | Tạo mới (file này) |
| `CLAUDE.md` | Update mô tả + decisions |
| `docs/new_approach_rationale.md` | Tạo mới |
| `docs/system_output_dashboard_spec.md` | Tạo mới |

---

## Decisions đã chốt hôm nay

| Quyết định | Lý do |
|---|---|
| **Đổi từ regression-then-bucket sang ordinal classification** | Khớp tên đề tài + mô tả gốc + operational gold standard (WHO EWARS) |
| **Label generation: Endemic Channel (Bortman 1999)** | Per-country baseline tự khử Brazil dominance, có ý nghĩa dịch tễ |
| **Train classifier với class_weight='balanced'** | Imbalance Low/Med/High |
| **Bỏ log1p target** | Không cần khi đã chuyển sang classification |
| **Bỏ metric RMSE/MAE/R²** | Không phù hợp với classification; thay bằng macro-F1, AUC OvR, calibration |
| **Giữ nguyên SESSION 1–5** | Data integration + EDA + CCF analysis còn giá trị |
| **Giữ walk-forward CV** | Vẫn đúng cho classification time-series |

---

## Ghi nhớ cho buổi sau

- **Đừng quay lại regression** — đã quyết định, có literature support, có lý lẽ rõ
- **Đừng dùng quantile arbitrary** — luôn dùng Endemic Channel (same-week historical baseline)
- **Khi trao đổi với GVHD về temporal split** — đã có sẵn lý lẽ + paper cite (Bergmeir 2012)
- **Đề cương cũ** đã over-spec — không bị buộc chặt vào RMSE/MAE/R²; có thể chuyển sang classification-only nếu cần
- **Backend đã build sẵn** trong `backend/` — endpoint `/predict`, `/risk` cần refactor để return `probabilities` thay vì `predicted_cases + tier`
