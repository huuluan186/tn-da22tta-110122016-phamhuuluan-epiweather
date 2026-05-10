# Mô tả Dataset — KLTN EpiWeather ML

**Sinh viên:** Phạm Hữu Luân | MSSV: 110122016 | Lớp: DA22TTA  
**Đề tài:** Xây dựng hệ thống cảnh báo nguy cơ dịch bệnh theo mùa dựa trên dữ liệu y tế và thời tiết toàn cầu

---

## Tổng quan

Có 2 file dataset đã qua feature engineering, sẵn sàng đưa vào huấn luyện mô hình:

| File | Bệnh | Số hàng | Số cột | Quốc gia | Giai đoạn |
|---|---|---|---|---|---|
| `features_flu_2010_2019.csv` | Influenza (cúm) | 70.056 | 17 (3 id + 13 features + 1 target) | 149 | 2010–2019 |
| `features_dengue_2010_2019.csv` | Dengue (sốt xuất huyết) | 6.313 | 19 (3 id + 15 features + 1 target) | 41 | 2010–2019 |

> Số hàng sau khi loại bỏ NaN (dropna): các hàng đầu mỗi quốc gia bị loại do AR lag và rolling mean cần warm-up tối đa 14 tuần. Flu còn 149/172 quốc gia sau 2 bước lọc: 18 quốc gia không map được ERA5 (đảo nhỏ), 5 quốc gia quá ít dữ liệu bệnh. Dengue chỉ có 41 quốc gia vùng nhiệt đới.

---

## 1. features_flu_2010_2019.csv

### Cột định danh (Identifier)

| Cột | Kiểu | Mô tả |
|---|---|---|
| `iso3` | string | Mã quốc gia ISO 3166-1 alpha-3 (VD: `VNM`, `USA`, `BRA`) |
| `iso_year` | int | Năm theo lịch ISO (2010–2019) |
| `iso_week` | int | Tuần theo lịch ISO (1–53) |

### Cột target (Biến mục tiêu)

| Cột | Kiểu | Mô tả |
|---|---|---|
| `inf_log1p` | float | `log1p(INF_A + INF_B)` — tổng ca cúm A+B đã transform log1p để chuẩn hóa phân phối long-tail |

### Features — AR Lags (Autoregressive)

| Cột | Mô tả |
|---|---|
| `inf_lag1w` | Ca cúm log1p tuần trước (t-1) |
| `inf_lag2w` | Ca cúm log1p 2 tuần trước (t-2) |
| `inf_lag3w` | Ca cúm log1p 3 tuần trước (t-3) |

### Features — Rolling Mean

| Cột | Mô tả |
|---|---|
| `inf_roll4w` | Trung bình trượt 4 tuần của ca cúm log1p |
| `inf_roll8w` | Trung bình trượt 8 tuần của ca cúm log1p |

### Features — Weather Lags (CCF-optimal)

Lag time xác định bằng Cross-Correlation Function (CCF) giữa biến khí hậu và ca bệnh.

| Cột | Biến gốc | Lag | Tương quan CCF | Mô tả |
|---|---|---|---|---|
| `temp_c_flu_lag4w` | Nhiệt độ trung bình (°C) | 4 tuần | r = −0,73 | Nhiệt độ thấp → cúm tăng sau 4 tuần |
| `humidity_pct_flu_lag8w` | Độ ẩm tương đối (%) | 8 tuần | — | Độ ẩm ảnh hưởng sự sống sót của virus |
| `solar_wm2_flu_lag8w` | Bức xạ mặt trời (W/m²) | 8 tuần | r = −0,76 | Ánh sáng UV thấp → miễn dịch giảm |
| `dewpoint_c_flu_lag2w` | Nhiệt độ điểm sương (°C) | 2 tuần | — | Chỉ số độ ẩm tuyệt đối |

### Features — Seasonality (Mùa vụ)

| Cột | Mô tả |
|---|---|
| `sin_week` | `sin(2π × iso_week / 52)` — encode tuần dạng chu kỳ |
| `cos_week` | `cos(2π × iso_week / 52)` — encode tuần dạng chu kỳ |
| `quarter` | Quý trong năm (1–4), tính từ iso_week |

### Features — Geographic

| Cột | Mô tả |
|---|---|
| `who_region_enc` | Mã số vùng WHO: AFR=0, AMR=1, EMR=2, EUR=3, SEAR=4, WPR=5, Unknown=−1 |

---

## 2. features_dengue_2010_2019.csv

### Cột định danh (Identifier)

| Cột | Kiểu | Mô tả |
|---|---|---|
| `iso3` | string | Mã quốc gia ISO 3166-1 alpha-3 |
| `iso_year` | int | Năm theo lịch ISO (2010–2019) |
| `iso_week` | int | Tuần theo lịch ISO (1–53) |

### Cột target (Biến mục tiêu)

| Cột | Kiểu | Mô tả |
|---|---|---|
| `dengue_log1p` | float | `log1p(dengue_cases)` — ca dengue đã transform log1p (Brazil chiếm ~70% tổng ca toàn cầu) |

### Features — AR Lags (Autoregressive)

Dengue dùng lag dài hơn cúm vì chu kỳ muỗi sinh sản chậm hơn.

| Cột | Mô tả |
|---|---|
| `dengue_lag6w` | Ca dengue log1p 6 tuần trước |
| `dengue_lag8w` | Ca dengue log1p 8 tuần trước |
| `dengue_lag10w` | Ca dengue log1p 10 tuần trước |
| `dengue_lag12w` | Ca dengue log1p 12 tuần trước |
| `dengue_lag14w` | Ca dengue log1p 14 tuần trước |

### Features — Rolling Mean

| Cột | Mô tả |
|---|---|
| `dengue_roll4w` | Trung bình trượt 4 tuần của ca dengue log1p |
| `dengue_roll8w` | Trung bình trượt 8 tuần của ca dengue log1p |

### Features — Weather Lags (CCF-optimal)

| Cột | Biến gốc | Lag | Mô tả |
|---|---|---|---|
| `temp_c_dengue_lag0w` | Nhiệt độ trung bình (°C) | 0 tuần | Ảnh hưởng ngay đến hoạt động muỗi Aedes |
| `humidity_pct_dengue_lag2w` | Độ ẩm tương đối (%) | 2 tuần | Độ ẩm cao → muỗi sinh sản nhiều hơn |
| `dewpoint_c_dengue_lag0w` | Nhiệt độ điểm sương (°C) | 0 tuần | Chỉ số độ ẩm tuyệt đối |
| `precip_mm_dengue_lag0w` | Lượng mưa (mm) | 0 tuần | Mưa nhiều → đọng nước → ổ muỗi |

### Features — Seasonality (Mùa vụ)

| Cột | Mô tả |
|---|---|
| `sin_week` | `sin(2π × iso_week / 52)` |
| `cos_week` | `cos(2π × iso_week / 52)` |
| `quarter` | Quý trong năm (1–4) |

### Features — Geographic

| Cột | Mô tả |
|---|---|
| `who_region_enc` | Mã số vùng WHO (feature importance ~19% cho dengue — tín hiệu mạnh nhất sau AR lags) |

---

## Nguồn dữ liệu gốc

| Nguồn | Nội dung | Độ phủ |
|---|---|---|
| WHO FluNet (`VIW_FNT.csv`) | Ca cúm A, B theo tuần | 172 quốc gia, 2010–2019 |
| PAHO / WHO Dengue (`National_extract_V1_3.csv`) | Ca dengue theo tuần | 41 quốc gia, 2010–2019 |
| ERA5 — ECMWF (NetCDF) | 17 biến khí hậu, lưới 0,25°×0,25° | Toàn cầu, 2010–2019 |

**Spatial mapping ERA5 → quốc gia:** KD-tree nearest-neighbor từ centroid quốc gia (Natural Earth 50m) đến lưới ERA5. Kết quả: 154/172 quốc gia ánh xạ thành công (~90% coverage).

---

## Lưu ý kỹ thuật

- **Exclude 2020–2021:** COVID-19 làm gián đoạn pattern báo cáo — bị loại khỏi training.
- **Validation set:** ERA5 + bệnh năm 2022 (dữ liệu thực, không dùng trong training).
- **Missing = 0:** Các tuần không có báo cáo được fillna(0) — quy ước WHO (không báo cáo ≠ không có ca bệnh).
- **Log1p transform:** Áp dụng cho cả 2 target để chuẩn hóa phân phối long-tail trước khi đưa vào XGBoost.

---

## Hạn chế dữ liệu (Limitations)

### 1. Báo cáo không liên tục — Dengue

Lý thuyết: 41 quốc gia × 52 tuần × 10 năm = **21.320 rows**.
Thực tế sau dropna: **6.313 rows** (~30% so với lý thuyết).

Nguyên nhân:
- Không phải quốc gia nào cũng báo cáo đủ 52 tuần/năm (VD: BRA chỉ 258 rows, LKA 450 rows trong 10 năm).
- Báo cáo thưa ở giai đoạn đầu: năm 2010 chỉ có 144 rows toàn bộ 41 quốc gia, năm 2019 có 1.102 rows.
- AR lag tối đa 14 tuần → 14 hàng đầu mỗi quốc gia bị loại do không đủ lịch sử (dropna).

### 2. Báo cáo không liên tục — Influenza

Lý thuyết: 172 quốc gia × 52 tuần × 10 năm = **89.440 rows**.
Thực tế sau dropna: **70.056 rows**, còn **149/172 quốc gia** (23 quốc gia bị loại do thiếu dữ liệu liên tục).

### 3. Missing = 0 (quy ước WHO)

Các tuần không có báo cáo được `fillna(0)` — tức là không báo cáo được coi là 0 ca. Đây là quy ước của WHO FluNet, không có nghĩa thực sự không có ca bệnh. Điều này làm tăng tỷ lệ zero rows (~38,8% cho flu), ảnh hưởng đến sMAPE all-rows.

### 4. Distribution shift năm 2022 — Influenza

Đỉnh dịch tuần 50/2022 (~77.000 ca) cao gấp 2,5 lần bất kỳ tuần nào trong tập training 2010–2019 do immunity debt sau COVID-19. Model không thể dự báo chính xác các đỉnh bất thường này vì pattern chưa từng xuất hiện trong training. Đây là limitation cố hữu của mọi model học từ dữ liệu lịch sử, không phải lỗi kỹ thuật.

### 5. ERA5 spatial mapping

172 quốc gia có trong WHO FluNet, nhưng chỉ **154/172 quốc gia ánh xạ được ERA5 weather** (~90% coverage). Sau dropna còn **149 quốc gia** trong features_flu. Tóm tắt quá trình lọc:

```
172 quốc gia WHO FluNet
→ -18 không map được ERA5 (đảo nhỏ: Malta, Singapore, Maldives, các đảo Caribbean...)
= 154 quốc gia có weather data
→ -5  quá ít dữ liệu bệnh, dropna loại hết (AIA, ATG, BHS, CYM, GUY — chỉ 2–8 rows)
= 149 quốc gia trong features_flu_2010_2019.csv
```
