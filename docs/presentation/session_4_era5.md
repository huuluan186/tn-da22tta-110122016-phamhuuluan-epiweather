# Session 4: Tải và Xử Lý Dữ Liệu Khí Hậu ERA5

---

## Bài toán: Dữ liệu thời tiết không theo quốc gia

Đây là phần kỹ thuật nhất của toàn bộ pipeline — và cũng là phần mà nhiều người hỏi nhiều nhất.

Vấn đề: Dữ liệu dịch bệnh (FluNet, OpenDengue) có cấu trúc rõ ràng — **mỗi hàng = 1 quốc gia × 1 tuần**. Nhưng dữ liệu thời tiết ERA5 lại được tổ chức hoàn toàn khác: **mỗi điểm = 1 tọa độ địa lý (lat, lon) × 1 thời điểm**. Toàn bộ bề mặt Trái Đất được chia thành lưới **721 × 1440 = 1,038,240 điểm**.

Mình cần chuyển từ *"thời tiết tại điểm (lat=10.25°, lon=106.75°)"* sang *"thời tiết của quốc gia VNM"*. Đây chính là bài toán spatial mapping.

---

## ERA5 là gì và tại sao dùng nó?

ERA5 là sản phẩm của ECMWF (European Centre for Medium-Range Weather Forecasts) — tổ chức dự báo thời tiết lớn nhất châu Âu. Điểm đặc biệt là ERA5 không phải chỉ đo thực tế, mà là **reanalysis data** — kết hợp hàng triệu quan trắc thực tế (vệ tinh, trạm mặt đất, thám không) với mô hình số trị để tái tạo lại trạng thái khí quyển trong quá khứ. Kết quả là dữ liệu **đồng nhất, không có lỗ hổng, toàn cầu**.

Tại sao không dùng OpenWeatherMap hay NOAA?
- OpenWeatherMap: chủ yếu dữ liệu trạm mặt đất → không đủ coverage cho 172 quốc gia
- NOAA: tốt nhưng không đồng nhất về độ phân giải và coverage ở các vùng nhiệt đới

ERA5 cho mình **17 biến khí hậu đồng nhất trên toàn cầu** — từ Greenland đến châu Phi Hạ Sahara. Đây là lý do chính.

---

## Setup CDS API — Trước khi chạy bất kỳ cell nào

ERA5 không có nút "Download" như FluNet hay OpenDengue. Mình phải dùng **CDS API** — giao tiếp với server của ECMWF bằng Python. Có 4 bước setup một lần duy nhất:

### Bước 1 — Đăng ký tài khoản CDS

Vào: **https://cds.climate.copernicus.eu/**

1. Click **"Register"** góc trên phải
2. Điền thông tin, xác nhận email
3. Đăng nhập vào

> Nếu chưa có tài khoản, bạn sẽ không thể chạy bất kỳ lệnh tải ERA5 nào — API key là bắt buộc.

### Bước 2 — Lấy API Key

1. Đăng nhập xong → click vào **tên tài khoản** góc trên phải
2. Chọn **"Your profile"**
3. Kéo xuống phần **"API key"**
4. Bạn sẽ thấy 2 giá trị:
   - **UID** (dãy số, ví dụ: `123456`)
   - **API key** (chuỗi dài, ví dụ: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`)

### Bước 3 — Tạo file cấu hình `.cdsapirc`

```python
import os
cds_key = "123456:xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"  # Thay bằng key của bạn
with open(os.path.expanduser("~/.cdsapirc"), "w") as f:
    f.write(f"url: https://cds.climate.copernicus.eu/api/v2\n")
    f.write(f"key: {cds_key}\n")
```

> **Bảo mật:** Không commit API key lên GitHub. Dùng Colab secrets (`userdata.get('CDS_KEY')`) hoặc nhập tay khi chạy.

---

## Cell 4.0 — Idempotent Guard

```python
if ERA5_FILE.exists():
    era5 = pd.read_csv(ERA5_FILE)
    print(f'ERA5 da co: {ERA5_FILE.name}')
    print(f'Shape: {era5.shape} | Countries: {era5["iso3"].nunique()} | Years: ...')
    print('SESSION 4 hoan thanh - skip xuong SESSION 5')
else:
    print('ERA5 chua co - can chay tu [4.1]')
```

**Output thực tế:**
```
ERA5 da co: era5_weekly_2010_2019_final.csv
Shape: (102440, 21) | Countries: 197 | Years: 2010-2019
SESSION 4 hoan thanh - skip xuong SESSION 5
```

Nếu file đã có → skip toàn bộ session. Xử lý ERA5 mất **2–3 giờ** — guard này là bắt buộc.

---

## Cell 4.1 — Download ERA5 qua CDS API + Unzip

ERA5 API trả về file ZIP chứa 2 NetCDF riêng biệt:
- `*avgua*` → **instant variables** (t2m, d2m, wind, cloud, pressure, BLH, TCWV)
- `*avgad*` → **accumulated variables** (precipitation, evaporation, radiation)

```python
for year in range(2010, 2020):
    with zipfile.ZipFile(nc_file) as z:
        for name in z.namelist():
            if 'avgua' in name:
                target = ERA5_RAW_DIR / f'era5_{year}_instant.nc'
            elif 'avgad' in name:
                target = ERA5_RAW_DIR / f'era5_{year}_accum.nc'
```

Tải theo từng năm riêng để có checkpoint — nếu năm 2015 lỗi, chỉ tải lại năm 2015, không mất 9 năm kia.

---

## Cell 4.2 — Inspect NetCDF variables

```python
ds_i = xr.open_dataset(ERA5_RAW_DIR / 'era5_2010_instant.nc', engine='netcdf4')
ds_a = xr.open_dataset(ERA5_RAW_DIR / 'era5_2010_accum.nc',   engine='netcdf4')
```

Bây giờ mình có 2 mảng 3 chiều: thời gian × vĩ độ × kinh độ. Mỗi điểm là giá trị biến khí hậu tại một vị trí vào một tháng.

---

## Cell 4.3 — Spatial Mapping: Pixel Mask Averaging (kỹ thuật chính)

### Ý tưởng

Với mỗi quốc gia, mình cần tổng hợp tất cả grid points nằm **trong biên giới** quốc gia đó thành 1 giá trị đại diện.

Cách làm: dùng **Natural Earth 50m shapefile** để tạo `grid_iso3` — một mảng shape `(721, 1440)` gán mỗi điểm lưới ERA5 vào quốc gia tương ứng. Sau đó với mỗi quốc gia, lấy **trung bình tất cả pixels** thuộc quốc gia đó.

```python
# Với mỗi time step, tính mean trên tất cả pixels của quốc gia
for iso3 in unique_countries:
    mask = (grid_iso3 == iso3)
    records.append({
        'iso3': iso3,
        'temp_c': float(t2m[i][mask].mean()),
        'precip_mm': float(tp[i][mask].mean()),
        # ...
    })
```

### Tại sao pixel averaging tốt hơn KD-tree nearest centroid?

| | KD-tree nearest centroid | Pixel mask averaging |
|---|---|---|
| Nguyên lý | 1 điểm duy nhất gần centroid nhất | Trung bình tất cả pixels trong biên giới |
| Brazil | 1 điểm ở giữa nước | Trung bình cả Amazon + Nam Brazil |
| Đảo nhỏ | Dễ miss nếu centroid nằm trên biển | Cover nếu có ít nhất 1 pixel trong biên giới |
| Coverage | ~154/172 quốc gia | **197 quốc gia** |

Pixel averaging phản ánh điều kiện khí hậu thực của cả quốc gia, không chỉ 1 điểm trung tâm.

### Unit conversion quan trọng

```python
t2m  = ds_i['t2m'].values  - 273.15   # Kelvin → Celsius (BẮT BUỘC)
d2m  = ds_i['d2m'].values  - 273.15
tp   = ds_a['tp'].values   * 1000      # m → mm
e    = ds_a['e'].values    * 1000 * (-1)  # ERA5 evap âm → đổi dấu
ssrd = ds_a['ssrd'].values / 86400     # J/m² → W/m²
```

Quên trừ 273.15 → nhiệt độ ~300°C → model train sai hoàn toàn. Cell sanity check ở SESSION 5 sẽ catch lỗi này.

**Output mỗi năm:**
```
✅ 2010: 2,364 rows, 197 countries
...
✅ 2019: 2,364 rows, 197 countries
```
2,364 = 197 countries × 12 tháng.

---

## Cell 4.4 — Expand Monthly → Weekly (forward fill)

ERA5 tải về ở mức **monthly**. FluNet dùng **ISO week**. Mình expand bằng forward fill:

```python
# Tạo full weekly grid 197 countries × 52 tuần × 10 năm
all_weeks = pd.DataFrame([
    {'iso3': iso3, 'iso_year': year, 'iso_week': week}
    for iso3 in era5_fixed['iso3'].unique()
    for year in range(2010, 2020)
    for week in range(1, 53)
])

# Merge monthly vào weekly grid, forward fill
era5_weekly = all_weeks.merge(era5_fixed, on=['iso3','iso_year','iso_week'], how='left')
era5_weekly[weather_cols] = era5_weekly.groupby('iso3')[weather_cols].ffill().bfill()
```

**Tại sao ffill thay vì linear interpolation?**

Thời tiết monthly mean đại diện cho cả tháng đó — giá trị tháng 1 áp dụng cho tất cả các tuần trong tháng 1. Forward fill đúng với ý nghĩa này. Linear interpolation sẽ tạo ra giá trị "chuyển tiếp" giữa tháng không có cơ sở thực tế.

**Output:**
```
Trước expand: (23,640, 21)   ← 197 countries × 120 tháng
Sau expand:  (102,440, 21)   ← 197 countries × 520 tuần
```

---

## Cell 4.5 — Re-merge thành Master Dataset

```python
master = flu_proc.merge(era5, on=['iso3','iso_year','iso_week'], how='left')
master = master.merge(dng,  on=['iso3','iso_year','iso_week'], how='left')
master.to_csv(MASTER_FILE, index=False)
```

**Output thực tế:**
```
master: (78,213, 25) | 172 countries
Có weather: 154 countries
✅ Saved → master_weekly_2010_2019.csv
```

FluNet anchor có 172 quốc gia. ERA5 có 197 quốc gia. Sau LEFT JOIN: 154/172 quốc gia FluNet có weather data — 18 quốc gia FluNet không có trong ERA5 shapefile (thường là lãnh thổ đặc biệt, không có biên giới rõ).

---

## Kết quả Session 4

**File output:** `era5_weekly_2010_2019_final.csv`

| Chỉ số | Giá trị |
|--------|---------|
| Số hàng | **102,440** (197 countries × 520 tuần) |
| Số cột | 21 (iso3, iso_year, iso_week + 17 biến khí hậu + 1 biến phụ) |
| Quốc gia (ERA5) | **197** |
| Quốc gia có weather (sau merge FluNet) | **154 / 172** |
| Giai đoạn | 2010–2019 |
| Thời gian xử lý | 2–3 giờ (chạy 1 lần duy nhất) |

**17 biến khí hậu:**
`temp_c`, `dewpoint_c`, `temp_min_c`, `temp_max_c`, `temp_range_c`, `humidity_pct`, `wind_ms`, `precip_mm`, `conv_precip_mm`, `ls_precip_mm`, `evap_mm`, `water_vapour`, `solar_wm2`, `uv_wm2`, `thermal_wm2`, `cloud_cover`, `msl_pa`, `blh_m`

Session tiếp theo — mình sẽ phân tích **độ trễ tối ưu** giữa thời tiết và dịch bệnh.

---

## Key Insights từ Session 4

**1. ERA5 là reanalysis — không phải chỉ đo thực tế**
Reanalysis kết hợp quan trắc + mô hình số trị → lấp đầy lỗ hổng không gian và thời gian → không có missing values trong ERA5. Lý do ERA5 có thể cover 197 quốc gia đồng đều.

**2. Pixel mask averaging tốt hơn KD-tree nearest centroid**
Approach thực tế dùng trung bình tất cả pixels trong biên giới quốc gia — không phải 1 điểm centroid. Kết quả: 197 countries thay vì ~154. Brazil lấy trung bình cả Amazon + Nam Brazil thay vì 1 điểm giữa nước.

**3. Unit conversion là bước dễ sai nhất**
`t2m - 273.15` (Kelvin → °C), `tp * 1000` (m → mm), `ssrd / 86400` (J/m² → W/m²), `e * (-1)` (ERA5 evap âm). Quên bất kỳ conversion nào → model train trên số vô nghĩa. Cell sanity check USA Jan/Jul ở SESSION 5 là lớp phòng thủ cuối.

**4. ffill cho monthly → weekly phản ánh đúng ý nghĩa data**
Monthly mean đại diện cho cả tháng → forward fill đúng hơn linear interpolation. Interpolation tạo ra giá trị "chuyển tiếp" không có cơ sở thực tế.

**5. 154/172 FluNet countries có weather — 18 miss là lãnh thổ đặc biệt**
ERA5 có đủ 197 quốc gia. 18 FluNet countries không có trong ERA5 shapefile thường là lãnh thổ đặc biệt (không phải quốc gia độc lập trong Natural Earth) — không phải lỗi processing.
