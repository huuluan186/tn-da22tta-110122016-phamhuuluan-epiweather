# Tài liệu kỹ thuật: Thu thập và Tiền xử lý Dữ liệu

> **Phục vụ:** Chương 3 (Thiết kế pipeline ETL) và Chương 4 (Kết quả đạt được)
> **Sinh viên:** Phạm Hữu Luân — MSSV 110122016 — DA22TTA — Đại học Trà Vinh

---

## SESSION 4 — Thu thập và xử lý dữ liệu khí hậu ERA5

### 4.1 Nguồn dữ liệu ERA5

**ERA5** (Fifth generation ECMWF atmospheric reanalysis) là bộ dữ liệu khí hậu lịch sử toàn cầu
do Trung tâm Dự báo Thời tiết Tầm trung Châu Âu (ECMWF) sản xuất và phân phối miễn phí
qua Copernicus Climate Data Store (CDS).

| Đặc điểm | Giá trị |
|---|---|
| Độ phân giải không gian | 0.25° × 0.25° (~27 km tại xích đạo) |
| Độ phân giải thời gian | Hourly (tổng hợp thành weekly trong pipeline) |
| Phủ sóng | Toàn cầu, 1940 – hiện tại |
| Truy cập | CDS API (miễn phí, cần đăng ký tài khoản) |
| Phương pháp | Data assimilation — kết hợp mô hình số trị với quan trắc thực tế |

**Lý do chọn ERA5** so với các nguồn khác:
- Phủ sóng toàn cầu đồng nhất — phù hợp bài toán 172 quốc gia
- Reanalysis data: độ chính xác cao hơn interpolation đơn thuần nhờ data assimilation
- Miễn phí, API ổn định, cộng đồng khoa học sử dụng rộng rãi
- Có đủ các biến liên quan đến cả bệnh hô hấp (nhiệt độ, độ ẩm) và vector-borne (mưa, nhiệt độ đất)

---

### 4.2 Các biến khí hậu được chọn (18 biến)

Chọn theo lý thuyết y học: nhóm hô hấp (Influenza) và nhóm vector-borne (Dengue, Malaria).

#### Nhóm nhiệt độ

| Tên cột (CSV) | Biến ERA5 gốc | Đơn vị | Lý do chọn |
|---|---|---|---|
| `temp_c` | 2m_temperature | °C | Nhiệt độ bề mặt — ảnh hưởng trực tiếp tới sự sống sót của virus Influenza |
| `dewpoint_c` | 2m_dewpoint_temperature | °C | Điểm sương — proxy cho độ ẩm tuyệt đối |
| `temp_min_c` | Daily min của 2m_temp | °C | Đêm lạnh thúc đẩy lây truyền Influenza |
| `temp_max_c` | Daily max của 2m_temp | °C | Nhiệt độ ban ngày ảnh hưởng hoạt động muỗi |
| `temp_range_c` | temp_max - temp_min | °C | Biên độ nhiệt — stress sinh lý lên hệ miễn dịch |

#### Nhóm độ ẩm và mưa

| Tên cột (CSV) | Biến ERA5 gốc | Đơn vị | Lý do chọn |
|---|---|---|---|
| `humidity_pct` | Relative humidity (tính từ temp + dewpoint) | % | Độ ẩm tương đối — môi trường sống của aerosol virus |
| `precip_mm` | total_precipitation | mm | Lượng mưa tổng — điều kiện sinh sản của muỗi Aedes |
| `conv_precip_mm` | convective_precipitation | mm | Mưa dông — tạo vũng nước đọng đột ngột |
| `ls_precip_mm` | large_scale_precipitation | mm | Mưa diện rộng — ngập lụt, lan rộng ổ muỗi |
| `water_vapour` | total_column_water_vapour | kg/m² | Tổng hơi nước trong cột khí quyển |
| `evap_mm` | total_evaporation | mm | Bốc hơi — chỉ số khô hạn hay ẩm ướt |

#### Nhóm gió và áp suất

| Tên cột (CSV) | Biến ERA5 gốc | Đơn vị | Lý do chọn |
|---|---|---|---|
| `wind_ms` | sqrt(u10² + v10²) từ 10m_u/v_component | m/s | Tốc độ gió — phát tán aerosol, di chuyển muỗi |
| `msl_pa` | mean_sea_level_pressure | Pa | Áp suất khí quyển — hệ thống thời tiết quy mô lớn |

#### Nhóm bức xạ và mây

| Tên cột (CSV) | Biến ERA5 gốc | Đơn vị | Lý do chọn |
|---|---|---|---|
| `solar_wm2` | surface_solar_radiation_downwards | W/m² | Bức xạ mặt trời — UV diệt khuẩn, ảnh hưởng vitamin D |
| `uv_wm2` | surface_net_solar_radiation | W/m² | Tia UV thực tế sau hấp thụ khí quyển |
| `thermal_wm2` | surface_thermal_radiation_downwards | W/m² | Bức xạ nhiệt — đảo nhiệt đô thị |
| `cloud_cover` | total_cloud_cover | 0–1 | Mây che phủ — giảm UV, tăng ẩm |

#### Nhóm khác

| Tên cột (CSV) | Biến ERA5 gốc | Đơn vị | Lý do chọn |
|---|---|---|---|
| `blh_m` | boundary_layer_height | m | Chiều cao lớp biên khí quyển — ảnh hưởng khuếch tán ô nhiễm và aerosol |

---

### 4.3 Quy trình tải dữ liệu

```
CDS API (cdsapi library)
    → Download NetCDF4 theo từng năm (2010, 2011, ..., 2019)
    → Lưu checkpoint: era5_weekly_era5_YYYY_checkpoint.csv
    → Concat 10 năm → era5_weekly_2010_2019_final.csv
```

**Tải theo năm** để:
1. Tránh timeout nếu request quá lớn
2. Checkpoint từng năm — nếu bị ngắt giữa chừng, chỉ cần tải lại năm bị lỗi
3. Dễ kiểm tra chất lượng từng năm trước khi merge

Kết quả checkpoint đã có:
```
era5_weekly_era5_2010_checkpoint.csv → era5_weekly_era5_2019_checkpoint.csv
era5_weekly_2010_2019_final.csv  (concat 10 năm)
```

---

### 4.4 Spatial mapping: Lưới ERA5 → Quốc gia (KD-tree)

ERA5 cung cấp dữ liệu trên lưới tọa độ địa lý (latitude × longitude), không phân chia theo ranh giới quốc gia. Pipeline cần map dữ liệu lưới sang mã quốc gia `iso3` để có thể join với dữ liệu dịch bệnh.

**Phương pháp: KD-tree Nearest Centroid**

```
1. Lấy centroid (lat, lon) của mỗi quốc gia từ Natural Earth 50m shapefile
2. Xây dựng KD-tree từ tất cả ~1,038,240 điểm lưới ERA5
   (721 vĩ độ × 1440 kinh độ = toàn cầu 0.25°)
3. Với mỗi centroid quốc gia: truy vấn KD-tree → tìm điểm lưới gần nhất
4. Lấy toàn bộ time series của điểm lưới đó làm đại diện cho quốc gia
```

**Kết quả:** 158/172 quốc gia (92%) có dữ liệu ERA5.

**14 quốc gia không map được** chủ yếu là:
- Đảo nhỏ không có centroid đủ rõ ràng (ví dụ: Nauru, Tuvalu, San Marino)
- Lãnh thổ không độc lập hoặc thiếu trong shapefile Natural Earth 50m

**Hạn chế đã biết:** Nearest centroid không phản ánh đa dạng khí hậu trong lãnh thổ quốc gia lớn
(ví dụ: Brazil — khí hậu Amazon khác miền Nam; Nga — khí hậu Siberia khác vùng Tây). Đây là
điểm có thể cải thiện trong tương lai bằng cách lấy trung bình có trọng số theo diện tích dân số.

---

### 4.5 Aggregate từ hourly sang weekly ISO

ERA5 gốc ở độ phân giải hourly. Pipeline thực hiện aggregate:

| Loại biến | Phương pháp aggregate | Lý do |
|---|---|---|
| Nhiệt độ, độ ẩm, áp suất, gió | Mean theo tuần | Giá trị trung bình đại diện điều kiện chung |
| Mưa, bốc hơi | Sum theo tuần | Lượng tích lũy quan trọng hơn trung bình |
| Bức xạ, mây | Mean theo tuần | Phơi nhiễm tích lũy |

**Key:** `iso3 + iso_year + iso_week` (theo chuẩn ISO 8601)

---

### 4.6 Kết quả

| Chỉ số | Giá trị |
|---|---|
| File output | `era5_weekly_2010_2019_final.csv` |
| Số hàng | ~820,000 (158 quốc gia × 10 năm × ~52 tuần) |
| Số cột | 21 (iso3, iso_year, iso_week + 18 biến khí hậu) |
| Coverage | 158/172 quốc gia (91.9%) |
| Thời gian xử lý | ~2–3 giờ (download + spatial mapping) |

---

## SESSION 5 — Tiền xử lý và tích hợp dữ liệu

### 5.1 Tổng quan các nguồn dữ liệu đầu vào

| Nguồn | Mô tả | Giai đoạn | Số quốc gia | Granularity |
|---|---|---|---|---|
| WHO FluNet | Ca Influenza A+B từ hệ thống GISRS | 1995–2026 | 189 | Weekly |
| OpenDengue v1.3 | Ca Dengue tổng hợp từ nhiều nguồn | 1990–2023 | ~60 | Weekly/Monthly |
| ERA5 weekly | Khí hậu lịch sử (SESSION 4) | 2010–2019 | 158 | Weekly |
| WHO GHO | Ca Malaria (ước tính hàng năm) | 2000–2022 | ~100 | Annual → interpolate weekly |

---

### 5.2 Tiền xử lý WHO FluNet (Influenza)

**Lọc theo thời gian:** Chỉ lấy 2010–2019 (training period đã chốt).

**Tính target `inf_cases`:**
```python
inf_cases = INF_A.fillna(0) + INF_B.fillna(0)
```

> **Quyết định:** Dùng `INF_A + INF_B` thay vì `INF_ALL` vì `INF_ALL` có missing rate 44%.
> `fillna(0)` vì WHO FluNet cho phép quốc gia báo cáo gián đoạn — tuần không có dữ liệu
> có nghĩa là "không gửi báo cáo", không phải "không có ca bệnh". Trong ngữ cảnh
> training, giá trị 0 tốt hơn là NaN vì model cần học được "tuần bình thường" có ca thấp.

**Loại bỏ cột không dùng:**
- `PARAINFLUENZA`: missing 85.5% — không đủ dữ liệu để học pattern
- `RSV_PROCESSED`: khác đơn vị so với `RSV` (corr=0.729 nhưng scale khác nhau)
  → chỉ giữ `RSV` (raw counts)

**UK special case:** WHO FluNet không có mã tổng hợp `GBR` cho Vương quốc Anh.
Dữ liệu UK được báo cáo qua các mã vùng `X09` (England), `X10` (Wales),
`X11` (Scotland), `X12` (Northern Ireland). Pipeline gộp 4 mã này và gán `iso3 = 'GBR'`.

**Standardize key:**
```
COUNTRY_CODE → iso3
ISO_YEAR     → iso_year
ISO_WEEK     → iso_week
```

---

### 5.3 Tiền xử lý OpenDengue (Dengue)

**Lọc granularity:**
```python
dengue = dengue[dengue['T_res'].isin(['Week', 'Month'])]
```
Loại bỏ `T_res = 'Year'` vì không đủ độ phân giải cho weekly model.

**Parse date:** OpenDengue sử dụng định dạng không nhất quán (`MM/DD/YYYY`):
```python
date_parsed = pd.to_datetime(calendar_start_date, format='mixed', dayfirst=False)
```
Dùng `format='mixed'` thay vì hardcode format để xử lý các dòng có định dạng khác nhau
trong cùng một file.

**Tính ISO week:** Từ `date_parsed` → ISO 8601 week.

**Log transform target:**
```python
dengue_log1p = np.log1p(dengue_total)
```
> **Lý do:** Brazil chiếm ~70% tổng ca Dengue toàn cầu (>10 triệu ca trong 2010–2019).
> Nếu dùng raw scale, model sẽ bị dominated bởi Brazil và không học được pattern
> của các quốc gia khác. `log1p` nén phân phối, cho phép model học được cả Brazil
> lẫn các nước có ca thấp hơn nhiều.

**Aggregate về weekly:**
```python
dengue_proc = dengue_proc.groupby(['iso3','iso_year','iso_week']).agg(
    dengue_total=('dengue_total', 'sum'),
    dengue_log1p=('dengue_log1p', 'mean')
)
```

---

### 5.4 Tiền xử lý ERA5

Rename columns về key chung (`iso_year`, `iso_week`), lọc 2010–2019.
File đã ở dạng weekly từ SESSION 4 — không cần xử lý thêm.

---

### 5.5 Chiến lược merge

**FluNet làm anchor** cho LEFT JOIN vì:
- FluNet có coverage tốt nhất (189 quốc gia, 1995–2026, weekly)
- Đây là target chính của model Influenza
- Giữ nguyên tất cả 172 quốc gia × 10 năm × 52 tuần = ~89,440 rows lý thuyết

```
FluNet (172 countries)
    LEFT JOIN ERA5        → ~92% rows có weather data
    LEFT JOIN Dengue      → ~11% rows có dengue > 0 (endemic countries)
    LEFT JOIN Malaria     → ~54% rows có malaria data
```

Sau merge:
```python
dengue_total = dengue_total.fillna(0)
dengue_log1p = dengue_log1p.fillna(0)
malaria_cases = malaria_cases.fillna(0)
```
Lý do `fillna(0)` sau merge: quốc gia không có trong OpenDengue = không phải endemic
country → dengue = 0 là đúng, không phải missing.

---

### 5.6 Quyết định loại trừ năm 2020–2021

COVID-19 làm thay đổi hoàn toàn pattern dịch bệnh truyền nhiễm thông thường:

| Bệnh | Ảnh hưởng của COVID-19 |
|---|---|
| Influenza | Gần như biến mất 2020–2021 do giãn cách xã hội, đeo khẩu trang, hạn chế di chuyển |
| Dengue | Underreporting do hệ thống y tế quá tải, một số nước giảm giám sát |
| Malaria | Gián đoạn chương trình phòng chống, thiếu thuốc và màn ngủ do đứt gãy chuỗi cung ứng |

Nếu đưa 2020–2021 vào training, model sẽ học pattern COVID-disrupted thay vì
seasonal normal — dẫn đến dự báo sai cho năm bình thường.

> **Quyết định chốt:** Train 2010–2019, exclude 2020–2021, validate 2022.
> Validate 2022 là **post-COVID generalization test**: model train trước COVID
> có predict được năm 2022 (dịch bệnh phục hồi gần bình thường) không?
> Đây là bằng chứng mạnh về khả năng tổng quát hóa của model.

---

### 5.7 Kết quả tích hợp

| Chỉ số | Giá trị |
|---|---|
| File output | `master_weekly_2010_2019.csv` |
| Shape | 64,949 rows × 27 columns |
| Quốc gia | 172 |
| Giai đoạn | 2010–2019 (tuần ISO) |

**Missing rate sau merge:**

| Cột | Missing | Giải thích |
|---|---|---|
| `inf_cases` | 0.0% | FluNet là anchor, đã fillna(0) |
| `temp_c` (và ERA5 vars) | 30.8% | 14 quốc gia ERA5 không map được |
| `dengue_total` | 88.9% | Chỉ endemic countries có data — bình thường |
| `malaria_cases` | 46.5% | WHO GHO không cover tất cả quốc gia |

---

## Tóm tắt quyết định thiết kế

| Quyết định | Lý do | Tác động |
|---|---|---|
| ERA5 thay vì NOAA/OpenWeatherMap historical | Coverage toàn cầu, reanalysis, miễn phí | Đồng nhất 158 quốc gia |
| KD-tree nearest centroid | Đơn giản, nhanh, đủ chính xác cho quốc gia level | 14 quốc gia đảo nhỏ bị miss |
| `INF_A + INF_B` thay vì `INF_ALL` | INF_ALL missing 44% | Target đầy đủ hơn |
| `fillna(0)` cho inf_cases sau filter | Missing = không báo cáo, không phải = 0 ca thực | Giữ nguyên pattern báo cáo thực tế |
| Log1p cho Dengue target | Brazil dominated 70% tổng ca | Model học được pattern các nước nhỏ |
| Bỏ PARAINFLUENZA | Missing 85.5% | Tránh nhiễu feature |
| Bỏ RSV_PROCESSED | Khác đơn vị với RSV | Tránh redundant feature không consistent |
| Gộp UK X09–X12 → GBR | WHO không có mã tổng hợp | UK có đủ dữ liệu như các quốc gia khác |
| Exclude 2020–2021 | COVID làm lệch pattern bình thường | Training set sạch, không bị disrupted |
| Validate 2022 | Post-COVID generalization test | Đánh giá robustness thực tế của model |
| FluNet là anchor LEFT JOIN | Coverage tốt nhất, target chính | Giữ đủ 172 quốc gia trong training set |
| Weekly ISO 8601 | Chuẩn quốc tế, tránh vấn đề tuần 53 | Key nhất quán giữa 4 nguồn |

---

*Tài liệu kỹ thuật — KLTN 2026 — Phạm Hữu Luân*
