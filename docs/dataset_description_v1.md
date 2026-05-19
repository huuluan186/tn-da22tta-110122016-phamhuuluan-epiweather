# MÔ TẢ DATASET — KLTN EpiWeather v1

**Sinh viên:** Phạm Hữu Luân — MSSV 110122016 — DA22TTA
**Đề tài:** Xây dựng hệ thống cảnh báo nguy cơ dịch bệnh theo mùa dựa trên dữ liệu y tế và thời tiết toàn cầu
**Phiên bản:** v1 — 17/05/2026

---

## 1. Tổng quan các file dataset

| File | Số dòng | Số cột | Dung lượng | Mục đích sử dụng |
|---|---|---|---|---|
| `master_weekly_v1.csv` | 61.112 | 27 | 20,9 MB | Dataset tích hợp gốc, dùng làm nguồn cho feature engineering và EDA |
| `features_flu_v1.csv` | 55.208 | 21 | 14,8 MB | Bộ feature dùng để huấn luyện mô hình dự báo và phân loại cúm |
| `features_dengue_v1.csv` | 5.926 | 20 | 1,6 MB | Bộ feature dùng để huấn luyện mô hình dự báo và phân loại sốt xuất huyết |

**Key chung của cả 3 file:** `iso3` (mã quốc gia ISO Alpha-3) + `iso_year` (năm theo lịch ISO 8601) + `iso_week` (tuần ISO, từ 1 đến 52)

---

## 2. master_weekly_v1.csv — Dataset tích hợp

Mỗi dòng đại diện cho một bộ ba (quốc gia, năm ISO, tuần ISO). Dataset gộp ba nguồn dữ liệu: cúm (WHO FluNet), sốt xuất huyết (OpenDengue v1.3) và khí hậu (ERA5 ECMWF).

### 2.1. Cột định danh (3 cột)

| Tên cột | Kiểu | Mô tả |
|---|---|---|
| `iso3` | string | Mã quốc gia chuẩn ISO Alpha-3 (ví dụ: VNM, USA, BRA) |
| `iso_year` | integer | Năm theo chuẩn ISO 8601 (2010-2019) |
| `iso_week` | integer | Số tuần ISO trong năm (1-52) |

### 2.2. Cột dữ liệu cúm — nguồn WHO FluNet (4 cột)

| Tên cột | Kiểu | Mô tả |
|---|---|---|
| `INF_A` | float | Số ca dương tính với virus cúm A trong tuần |
| `INF_B` | float | Số ca dương tính với virus cúm B trong tuần |
| `influenza_total` | float | Tổng số ca cúm = INF_A + INF_B (đã xử lý giá trị thiếu = 0). Đây là target gốc của bài toán dự báo cúm |
| `HEMISPHERE` | string | Bán cầu chứa quốc gia (NH = Bắc bán cầu, SH = Nam bán cầu). Quan trọng cho mùa cúm |

### 2.3. Cột dữ liệu sốt xuất huyết — nguồn OpenDengue v1.3 (2 cột)

| Tên cột | Kiểu | Mô tả |
|---|---|---|
| `dengue_total` | float | Số ca sốt xuất huyết được báo cáo trong tuần. NaN nếu quốc gia không báo cáo bệnh này |
| `case_definition_standardised` | string | Loại định nghĩa ca bệnh (Total, Suspected, Confirmed, …). Đã chọn theo thứ tự ưu tiên Total > Suspected > Confirmed khi merge |

### 2.4. Cột dữ liệu khí hậu — nguồn ERA5 ECMWF (18 cột)

Tất cả biến khí hậu được lấy trung bình theo tháng và broadcast xuống tuần. Đã ánh xạ từ lưới tọa độ 0,25° × 0,25° sang mã quốc gia iso3 bằng KD-tree.

**Nhiệt độ (5 cột):**

| Tên cột | Đơn vị | Mô tả |
|---|---|---|
| `temp_c` | °C | Nhiệt độ trung bình tại độ cao 2m |
| `dewpoint_c` | °C | Nhiệt độ điểm sương (dùng tính độ ẩm tương đối) |
| `temp_min_c` | °C | Nhiệt độ tối thiểu trong tuần |
| `temp_max_c` | °C | Nhiệt độ tối đa trong tuần |
| `temp_range_c` | °C | Biên độ nhiệt = temp_max_c − temp_min_c |

**Gió và độ ẩm (2 cột):**

| Tên cột | Đơn vị | Mô tả |
|---|---|---|
| `humidity_pct` | % | Độ ẩm tương đối (tính từ temp_c và dewpoint_c theo công thức August–Roche–Magnus) |
| `wind_ms` | m/s | Tốc độ gió tại độ cao 10m, tính từ thành phần u10 và v10 |

**Lượng mưa và bốc hơi (4 cột):**

| Tên cột | Đơn vị | Mô tả |
|---|---|---|
| `precip_mm` | mm | Tổng lượng mưa |
| `conv_precip_mm` | mm | Lượng mưa đối lưu (giông, dông) |
| `ls_precip_mm` | mm | Lượng mưa quy mô lớn (front, low-pressure system) |
| `evap_mm` | mm | Lượng nước bốc hơi |

**Bức xạ mặt trời (3 cột):**

| Tên cột | Đơn vị | Mô tả |
|---|---|---|
| `solar_wm2` | W/m² | Bức xạ mặt trời tổng cộng tại mặt đất |
| `uv_wm2` | W/m² | Bức xạ tia cực tím |
| `thermal_wm2` | W/m² | Bức xạ nhiệt từ khí quyển xuống mặt đất |

**Khí quyển khác (4 cột):**

| Tên cột | Đơn vị | Mô tả |
|---|---|---|
| `water_vapour` | kg/m² | Tổng hơi nước trong cột khí quyển |
| `cloud_cover` | 0–1 | Tỉ lệ mây bao phủ (0 = quang đãng, 1 = mây phủ kín) |
| `msl_pa` | Pa | Áp suất khí quyển quy về mực nước biển |
| `blh_m` | m | Độ cao lớp ranh giới khí quyển (boundary layer) |

---

## 3. features_flu_v1.csv — Bộ feature cho mô hình cúm

Được tạo từ `master_weekly_v1.csv` bằng quá trình feature engineering. Mỗi dòng tương ứng với một mẫu huấn luyện hoặc dự báo.

**Phạm vi:** 146 quốc gia, giai đoạn 2010-2019. Số dòng giảm so với master file do loại bỏ những tuần đầu không đủ lịch sử để tính lag.

### 3.1. Cột định danh và target (5 cột)

| Tên cột | Kiểu | Mô tả |
|---|---|---|
| `iso3` | string | Mã quốc gia ISO Alpha-3 |
| `iso_week` | integer | Tuần ISO (1-52) |
| `influenza_total` | float | Target gốc (số ca cúm) |
| `flu_log` | float | Target đã transform log1p, dùng cho regression. Giúp giảm độ lệch phân phối |
| `flu_risk_class` | categorical | Nhãn phân loại Low/Medium/High theo endemic channel Bortman 1999. Là target cho mô hình phân loại |

### 3.2. Cột AR lag (3 cột) — đặc trưng tự hồi quy theo thời gian

| Tên cột | Mô tả |
|---|---|
| `flu_log_lag1` | log1p(số ca cúm) của 1 tuần trước |
| `flu_log_lag2` | log1p(số ca cúm) của 2 tuần trước |
| `flu_log_lag3` | log1p(số ca cúm) của 3 tuần trước |

### 3.3. Cột Rolling mean (2 cột) — đặc trưng trung bình trượt

| Tên cột | Mô tả |
|---|---|
| `flu_log_rollmean4` | Trung bình log1p(số ca) qua 4 tuần gần nhất (tính từ t-1 trở về trước) |
| `flu_log_rollmean8` | Trung bình log1p(số ca) qua 8 tuần gần nhất |

### 3.4. Cột Weather lag (6 cột) — đặc trưng thời tiết có độ trễ

Dựa trên kết quả phân tích Cross-Correlation Function (CCF) ở SESSION 4 EDA:

| Tên cột | Mô tả | Tham chiếu |
|---|---|---|
| `temp_c_lag3` | Nhiệt độ trung bình 3 tuần trước | CCF lag 3, r=-0,37 |
| `temp_c_lag7` | Nhiệt độ trung bình 7 tuần trước | Bổ sung |
| `humidity_pct_lag1` | Độ ẩm 1 tuần trước | CCF lag 1 |
| `humidity_pct_lag7` | Độ ẩm 7 tuần trước | CCF lag 7, r=+0,31 |
| `solar_wm2_lag7` | Bức xạ mặt trời 7 tuần trước | CCF lag 7, r=-0,41 (predictor mạnh nhất) |
| `dewpoint_c_lag1` | Điểm sương 1 tuần trước | CCF lag 1 |

Biến `precip_mm` đã loại khỏi flu features do CCF chỉ cho r=0,057 (không có tín hiệu).

### 3.5. Cột mã hóa thời gian và bán cầu (5 cột)

| Tên cột | Mô tả |
|---|---|
| `iso_week_sin` | sin(2π × iso_week / 52) — cyclic encoding |
| `iso_week_cos` | cos(2π × iso_week / 52) — cyclic encoding |
| `iso_year` | Năm dạng số nguyên, capture xu hướng dài hạn |
| `HEMISPHERE_NH` | One-hot: 1 nếu thuộc Bắc bán cầu, 0 nếu không |
| `HEMISPHERE_SH` | One-hot: 1 nếu thuộc Nam bán cầu, 0 nếu không |

---

## 4. features_dengue_v1.csv — Bộ feature cho mô hình sốt xuất huyết

Cấu trúc tương tự `features_flu_v1.csv` nhưng dùng lag dài hơn (chu kỳ sinh học của muỗi truyền bệnh ~ 2-3 tháng).

**Phạm vi:** 37 quốc gia, giai đoạn 2015-2019. Đã loại bỏ 9 quốc gia có coverage < 30 tuần/năm: ATG, CYM, GTM, HTI, SDN, SUR, TWN, VCT, WSM.

### 4.1. Cột định danh và target (5 cột)

| Tên cột | Mô tả |
|---|---|
| `iso3` | Mã quốc gia ISO Alpha-3 |
| `iso_week` | Tuần ISO |
| `dengue_total` | Target gốc (số ca sốt xuất huyết) |
| `deng_log` | Target đã transform log1p, dùng cho regression |
| `dengue_risk_class` | Nhãn phân loại Low/Medium/High |

### 4.2. Cột AR lag (5 cột)

| Tên cột | Mô tả |
|---|---|
| `deng_log_lag6` | log1p(số ca dengue) của 6 tuần trước |
| `deng_log_lag8` | 8 tuần trước |
| `deng_log_lag10` | 10 tuần trước |
| `deng_log_lag12` | 12 tuần trước |
| `deng_log_lag14` | 14 tuần trước |

### 4.3. Cột Rolling mean (2 cột)

| Tên cột | Mô tả |
|---|---|
| `deng_log_rollmean4` | Trung bình trượt 4 tuần |
| `deng_log_rollmean8` | Trung bình trượt 8 tuần |

### 4.4. Cột Weather lag (5 cột)

Theo CCF SESSION 4:

| Tên cột | Mô tả | Tham chiếu |
|---|---|---|
| `temp_c_lag11` | Nhiệt độ 11 tuần trước | CCF r=+0,31, khớp Lowe 2014 |
| `dewpoint_c_lag8` | Điểm sương 8 tuần trước | CCF r=+0,31 |
| `precip_mm_lag6` | Lượng mưa 6 tuần trước | Chu kỳ sinh sản muỗi |
| `humidity_pct_lag1` | Độ ẩm 1 tuần trước | Effect tức thời |
| `solar_wm2_lag16` | Bức xạ mặt trời 16 tuần trước | Proxy mùa |

### 4.5. Cột mã hóa thời gian (3 cột)

| Tên cột | Mô tả |
|---|---|
| `iso_week_sin` | sin cyclic encoding |
| `iso_week_cos` | cos cyclic encoding |
| `iso_year` | Năm dạng số nguyên |

---

## 5. Endemic channel — Định nghĩa nhãn phân loại nguy cơ

Áp dụng phương pháp Bortman 1999 (chuẩn WHO EWARS):

Với mỗi tổ hợp (`iso3`, `iso_week`), tính từ training years:
- `baseline_mean` = trung bình số ca lịch sử
- `baseline_std` = độ lệch chuẩn

Nhãn được gán theo công thức:
- **Low**: số ca < baseline_mean
- **Medium**: baseline_mean ≤ số ca < baseline_mean + 2 × baseline_std
- **High**: số ca ≥ baseline_mean + 2 × baseline_std (ngưỡng cảnh báo bùng phát)

Training years:
- Flu: 2010-2018 (val 2019)
- Dengue: 2015-2018 (val 2019)

---

## 6. Tham khảo

[1] R. Lowe et al., "Dengue outlook for the World Cup in Brazil: an early warning model framework driven by real-time seasonal climate forecasts", *Lancet Infect. Dis.*, vol. 14, no. 7, pp. 619-626, Jul. 2014.

[2] J. Shaman and M. Kohn, "Absolute humidity modulates influenza survival, transmission, and seasonality", *PNAS*, vol. 106, no. 9, pp. 3243-3248, 2009.

[3] M. Bortman, "Elaboración de corredores o canales endémicos", *Boletín Epidemiológico de la OPS*, 1999.

[4] World Health Organization, "FluNet — Global Influenza Surveillance and Response System".

[5] OpenDengue Project, "OpenDengue v1.3 — Global dengue surveillance data".

[6] H. Hersbach et al., "The ERA5 global reanalysis", *Quarterly Journal of the Royal Meteorological Society*, vol. 146, no. 730, pp. 1999-2049, Jul. 2020.
