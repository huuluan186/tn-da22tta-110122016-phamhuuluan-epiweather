# Hành Trình Cải Thiện Model — Từ R²=0.488 đến R²=0.791

---

## Overview: 6 lần cải thiện theo thứ tự thời gian

| # | Thay đổi | Flu R² | Dengue R² | Flu Macro F1 |
|---|---------|--------|-----------|-------------|
| 0 | **Baseline** (raw target, no tuning) | 0.488 | ~0.80 | — |
| 1 | **+log1p transform** | 0.811 | ~0.80 | — |
| 2 | +hemisphere_enc (thử → revert) | 0.811 | ~0.80 | — |
| 3 | **+Optuna 60 trials** | 0.811 | ~0.80 | — |
| 4 | **+ERA5 2022 real weather** | 0.791 | 0.836 | — |
| 5 | **+WHO region encoding** | 0.791 | **0.849** | — |
| 6 | **+Per-country quantile thresholds** | 0.791 | 0.849 | **0.72** |

---

## Cải thiện #1: Log1p transform — GAME CHANGER (+66% R²)

**Ngữ cảnh:** Sau khi train model đầu tiên, mình nhận thấy predictions cho USA, India, Brazil khá tốt nhưng cho hầu hết quốc gia còn lại thì kém.

**Nguyên nhân:** MSE loss bình phương sai số. USA có thể 80,000 ca, sai 5,000 ca = MSE contribution 25,000,000. Vietnam có thể 30 ca, sai 10 ca = MSE contribution 100. Model tập trung giảm MSE của USA, bỏ qua Vietnam.

**Fix:** `inf_log1p = np.log1p(inf_cases)` — nén phân phối, cân bằng contribution của mọi quốc gia.

**Kết quả:** R² từ **0.488 → 0.811** — tăng 66%. Đây là cải thiện lớn nhất trong toàn bộ dự án.

**Bài học:** Trước khi thử bất kỳ kỹ thuật ML phức tạp nào, hãy check phân phối của target variable. Long-tail distribution = log transform.

---

## Cải thiện #2: Hemisphere Encoding — Thất bại có giá trị

**Ngữ cảnh:** Flu season ngược nhau giữa Bắc và Nam bán cầu. Mình nghĩ thêm `hemisphere_enc` (North=1, South=-1, Equatorial=0) sẽ giúp model phân biệt.

```python
master['hemisphere_enc'] = master['iso3'].apply(lambda x: 
    1 if centroid_lat[x] > 23.5 else 
    (-1 if centroid_lat[x] < -23.5 else 0)
)
```

**Kết quả:** R² 0.811 → 0.811 (không thay đổi). Feature importance = ~1–2%.

**Tại sao không cải thiện?** XGBoost đã học được hemisphere effect gián tiếp qua:
- `who_region_enc`: Europe = Bắc, Americas có cả Bắc và Nam
- `sin_week` + `cos_week`: Model học được rằng tuần 6 của EUR = đỉnh dịch, tuần 6 của AUS = mùa hè
- AR lags: pattern lịch sử của từng quốc gia đã encode "khi nào quốc gia này có dịch"

Khi xóa hemisphere_enc đi, model không bị ảnh hưởng vì nó đã có đủ thông tin từ features khác.

**Verdict:** Revert. Bài học: **Thêm feature không phải lúc nào cũng tốt hơn**. Redundant features có thể làm tăng noise.

---

## Cải thiện #3: Optuna Hyperparameter Tuning — Modest improvement

**Ngữ cảnh:** Sau khi fix target, mình tuning hyperparameters để tối ưu hơn.

**60 trials Optuna, 45 phút training:**
- CV MAE: 0.460 → **0.4508** (−2%)
- R² không đổi đáng kể (vẫn ~0.811 trên training)

**Tại sao chỉ cải thiện 2%?** Mình nghĩ ban đầu cải thiện sẽ lớn hơn. Nhưng sau khi phân tích, mình nhận ra: bottleneck của model không phải hyperparameters — mà là **distribution shift**.

Model train 2010–2019 validate 2022. Giai đoạn 2022 có La Niña + hậu COVID immunity debt (nhiều người chưa nhiễm cúm 2020–2021 nên dễ bị hơn). Đây là những yếu tố **không có trong training data** — dù tuning hyperparameters tốt đến đâu cũng không capture được.

**Bài học:** Khi performance không cải thiện đáng kể dù tuning, hãy kiểm tra xem vấn đề có phải ở data/distribution shift không — không phải ở model.

---

## Cải thiện #4: ERA5 2022 thực tế thay vì training mean

**Ngữ cảnh:** Ban đầu mình validate bằng cách dùng **trung bình thời tiết 2010–2019** cho năm 2022 (vì chưa tải ERA5 2022). Kết quả: Flu R² = 0.811.

Sau đó mình tải ERA5 2022 thực tế và validate lại: Flu R² = **0.791** (−2%).

**Tại sao chấp nhận metrics thấp hơn?**

Vì 0.811 là **metrics ảo** — trong production, API sẽ nhận weather data thực tế, không phải mean. Nếu report 0.811 nhưng production thực tế là 0.791, đó là misleading.

Đây là quyết định về **scientific integrity**: báo cáo số thật, không phải số đẹp.

---

## Cải thiện #5: WHO Region Encoding — Dengue breakthrough

**Thêm `who_region_enc`** (6 vùng WHO) vào cả flu và dengue features.

**Kết quả:**
- Flu: R² không đổi (2% feature importance — không đủ lớn)
- **Dengue: R² từ 0.836 → 0.849** (+1.3%)

**Tại sao Dengue cải thiện nhiều hơn Flu?**

Dengue chỉ có 41 quốc gia endemic — và chúng tập trung rõ ràng theo vùng: Đông Nam Á (WPR, SEAR), châu Mỹ Latin (AMR). Pattern dengue ở Brazil rất khác ở Thái Lan. WHO region encode thông tin này hiệu quả hơn lat/lon đơn thuần.

WHO region đứng **thứ 2 về feature importance** với 19% trong Dengue model.

---

## Cải thiện #6: Per-Country Quantile Thresholds — Risk classification từ 0.40 lên 0.72

Đây là cải thiện gây ấn tượng nhất khi demo vì nó chuyển từ "không dùng được" sang "production-ready".

**Vấn đề root cause:** 73% flu rows = 0 → global Q33 = Q67 = 0 → Medium band biến mất.

**Giải pháp:** Tính Q33/Q67 riêng cho từng quốc gia, chỉ trên **các tuần nonzero** (các tuần có dịch thực sự).

```
Vietnam: Q33=1.2, Q67=3.5  (log1p scale)
USA:     Q33=6.8, Q67=9.2
Nigeria: Q33=0.7, Q67=1.8
```

Mỗi nước có "ngưỡng nguy cơ" riêng phù hợp với quy mô dịch của nước đó.

**Kết quả:**
- Flu Medium F1: 0.06 → **0.52** (+0.46)
- Flu Macro F1: 0.40 → **0.72** (+0.32)

**Bài học:** Khi classification metrics tệ, đừng vội thay model. Hãy kiểm tra threshold strategy trước.

---

## Tổng kết: Lessons Learned

1. **Distribution của target quan trọng hơn architecture của model.** Log transform cải thiện 66% R² — không một hyperparameter nào làm được vậy.

2. **Thêm feature không phải lúc nào cũng tốt.** Hemisphere encoding — intuitive nhưng không có ích vì model đã biết qua các features khác.

3. **Metrics consistency > metrics đẹp.** ERA5 thực làm giảm R² 2% — nhưng đó là số thật.

4. **Domain knowledge quan trọng để debug.** Risk classification collapse vì đặc thù của dịch bệnh mùa vụ (73% zero). Fix không phải là ML trick — là hiểu bài toán.

5. **XGBoost + log1p + walk-forward CV = strong baseline** cho bài toán dịch tễ học tabular. Không cần deep learning phức tạp.
