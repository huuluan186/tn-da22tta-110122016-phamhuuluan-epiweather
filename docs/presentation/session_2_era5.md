# Session 2: Dữ liệu thời tiết ERA5

> **Dùng khi demo lần 1:** Trình bày theo thứ tự: vì sao chọn ERA5 → tải qua CDS API → xử lý lưới bằng KD-tree → chuyển đơn vị/biến dẫn xuất → broadcast tháng xuống tuần → lưu checkpoint/final CSV → verify chất lượng.

## Bản đọc khi thuyết trình

Ở session này, em xử lý dữ liệu thời tiết. Bài toán cần dữ liệu theo dạng `(quốc gia, năm ISO, tuần ISO)`, nhưng ERA5 ban đầu là dữ liệu lưới toàn cầu. Vì vậy session này biến dữ liệu khí hậu thô thành file thời tiết theo quốc gia-tuần để các session sau merge với dữ liệu bệnh.

---

## 1. Chọn ERA5 và khai báo đường dẫn

Em chọn ERA5 vì đây là dữ liệu reanalysis của ECMWF, có độ phủ toàn cầu, đồng nhất giữa các quốc gia và phù hợp cho nghiên cứu nhiều năm. OpenWeatherMap dễ gọi hơn nhưng dữ liệu lịch sử dài hạn bị giới hạn/có phí, không phù hợp để lấy nhiều quốc gia trong 10 năm.

Trong notebook, em khai báo rõ thư mục raw NetCDF và file output processed:

```python
from pathlib import Path

BASE = Path("/content/drive/MyDrive/KLTN")
WEATHER_DIR = BASE / "data" / "weather"
ERA5_RAW = WEATHER_DIR / "era5_raw"
WEATHER_PROCESSED = WEATHER_DIR / "processed"

ERA5_RAW.mkdir(parents=True, exist_ok=True)
WEATHER_PROCESSED.mkdir(parents=True, exist_ok=True)

ERA5_FILE = WEATHER_PROCESSED / "era5_weekly_2010_2019_final.csv"
```

File cuối cùng của session:

```text
data/weather/processed/era5_weekly_2010_2019_final.csv
```

---

## 2. Lấy dữ liệu qua CDS API

ERA5 không được tải thủ công từng file. Em dùng Copernicus Climate Data Store API (`cdsapi`). Trước khi tải cần đăng ký tài khoản CDS, accept terms của dataset và tạo file `~/.cdsapirc`.

```python
# [2.A] Tạo file ~/.cdsapirc cho CDS API, chạy 1 lần khi setup
from pathlib import Path
import os
import cdsapi

CDS_API_KEY = "PASTE-YOUR-CDS-API-KEY-HERE"
CDS_API_URL = "https://cds.climate.copernicus.eu/api"

cdsapirc = Path(os.path.expanduser("~")) / ".cdsapirc"
cdsapirc.write_text(f"url: {CDS_API_URL}\nkey: {CDS_API_KEY}\n")

c = cdsapi.Client()
```

Sau khi setup API key, notebook tải ERA5 monthly means cho 2010-2019. Cell này đặt `DOCUMENTATION_ONLY = True` để không vô tình tải lại 6.2GB; khi chạy thật thì đổi thành `False`.

```python
# [2.B] Download ERA5 NetCDF raw từ CDS API
DOCUMENTATION_ONLY = True

if not DOCUMENTATION_ONLY:
    import cdsapi
    c = cdsapi.Client()

    ERA5_VARIABLES = [
        "2m_temperature",
        "2m_dewpoint_temperature",
        "minimum_2m_temperature_since_previous_post_processing",
        "maximum_2m_temperature_since_previous_post_processing",
        "10m_u_component_of_wind",
        "10m_v_component_of_wind",
        "total_precipitation",
        "convective_precipitation",
        "large_scale_precipitation",
        "total_column_water_vapour",
        "evaporation",
        "surface_solar_radiation_downwards",
        "surface_thermal_radiation_downwards",
        "total_cloud_cover",
        "mean_sea_level_pressure",
        "boundary_layer_height",
        "volumetric_soil_water_layer_1",
    ]

    for year in range(2010, 2020):
        out_nc = ERA5_RAW / f"era5_{year}.nc"
        if out_nc.exists():
            print(f"[SKIP] {out_nc.name} already exists")
            continue

        c.retrieve(
            "reanalysis-era5-single-levels-monthly-means",
            {
                "product_type": "monthly_averaged_reanalysis",
                "variable": ERA5_VARIABLES,
                "year": str(year),
                "month": [f"{m:02d}" for m in range(1, 13)],
                "time": "00:00",
                "format": "netcdf",
            },
            str(out_nc),
        )
```

Kết quả bước này là các file NetCDF raw theo năm, tổng khoảng 6.2GB. Trong workspace hiện tại không lưu raw NetCDF để tránh nặng repo; phần đã xử lý nằm ở `data/weather/processed/`.

---

## 3. Đọc NetCDF và ánh xạ điểm lưới về quốc gia

ERA5 là lưới toàn cầu, không có sẵn cột quốc gia. Em dùng Natural Earth để lấy centroid quốc gia, build KD-tree, rồi gán mỗi điểm lưới ERA5 về quốc gia có centroid gần nhất. Đây là đánh đổi giữa tốc độ và độ chính xác, phù hợp với dashboard cấp quốc gia.

**Natural Earth là gì?** Đây là bộ dữ liệu địa lý public, thường dùng trong bản đồ và GIS. Trong đồ án, em dùng file biên giới quốc gia từ Natural Earth 50m đã chuẩn hóa thành `world_50m_fixed.gpkg`. File này cung cấp polygon của từng quốc gia và mã ISO3 (`ISO_A3`). Từ polygon đó, notebook tính centroid, tức là điểm đại diện gần trung tâm hình học của quốc gia.

Ví dụ dễ hiểu:

| Quốc gia | Polygon Natural Earth | Centroid dùng trong notebook | ISO3 |
|---|---|---|---|
| Thailand | Biên giới Thái Lan | Một điểm đại diện gần trung tâm Thái Lan | `THA` |
| Brazil | Biên giới Brazil | Một điểm đại diện trong lãnh thổ Brazil | `BRA` |
| United States | Biên giới Hoa Kỳ | Một điểm đại diện của Hoa Kỳ | `USA` |

**KD-tree là gì?** KD-tree là cấu trúc dữ liệu để tìm điểm gần nhất trong không gian nhiều chiều. Ở đây không gian chỉ có 2 chiều: kinh độ và vĩ độ. Thay vì với mỗi điểm lưới ERA5 phải so khoảng cách tới toàn bộ quốc gia bằng vòng lặp chậm, KD-tree cho phép hỏi nhanh: "điểm lưới này gần centroid quốc gia nào nhất?"

Luồng ánh xạ cụ thể:

```text
ERA5 grid cell: (lon=100.25, lat=13.75)
        ↓ query KD-tree
Centroid gần nhất trong Natural Earth: Thailand
        ↓ lấy mã ISO3
grid cell này được gán iso3 = "THA"
```

```python
# [2.C.1] Load NetCDF + country centroid, build KD-tree
import xarray as xr
import geopandas as gpd
import pandas as pd
import numpy as np
from scipy.spatial import cKDTree

world = gpd.read_file(BASE / "data" / "world_50m_fixed.gpkg")
world["lon"] = world.geometry.centroid.x
world["lat"] = world.geometry.centroid.y

tree = cKDTree(world[["lon", "lat"]].values)
iso3_lookup = world["ISO_A3"].values

ds = xr.open_dataset(ERA5_RAW / "era5_2010.nc")

lon2d, lat2d = np.meshgrid(ds.longitude.values, ds.latitude.values)
grid_points = np.column_stack([lon2d.ravel(), lat2d.ravel()])

dist, idx = tree.query(grid_points, k=1)
grid_iso3 = iso3_lookup[idx]
```

Sau đoạn này, mỗi grid cell ERA5 đã có một mã `iso3` gần nhất. Từ đó em có thể aggregate các điểm lưới theo quốc gia.

Ví dụ minh họa nhỏ với 3 điểm lưới giả lập:

```python
demo_grid = pd.DataFrame({
    "lon": [100.25, -47.75, -95.25],
    "lat": [13.75, -15.75, 39.75],
})

dist, idx = tree.query(demo_grid[["lon", "lat"]].values, k=1)
demo_grid["nearest_iso3"] = iso3_lookup[idx]
demo_grid["distance_degree"] = dist
demo_grid
```

Kỳ vọng về mặt trực giác:

```text
(100.25, 13.75)  -> gần Thái Lan hoặc vùng lân cận Đông Nam Á
(-47.75, -15.75) -> gần Brazil
(-95.25, 39.75)  -> gần United States
```

Điểm quan trọng khi trình bày: đây không phải là "dự đoán quốc gia" bằng ML, mà chỉ là bài toán địa lý nearest-neighbor để gắn mã quốc gia cho điểm lưới thời tiết.

```python
# [2.C.2] Ví dụ flatten một biến ERA5 rồi gắn ISO3
temp = ds["t2m"].values.reshape(ds["time"].shape[0], -1)

rows = []
for t_idx, t in enumerate(ds["time"].values):
    df_t = pd.DataFrame({
        "iso3": grid_iso3,
        "t2m": temp[t_idx],
    })
    df_t["year"] = pd.Timestamp(t).year
    df_t["month"] = pd.Timestamp(t).month
    rows.append(df_t)

grid_weather_df = pd.concat(rows, ignore_index=True)
```

---

## 4. Aggregate theo quốc gia-tháng

Sau khi grid cell đã có `iso3`, em lấy trung bình các điểm lưới thuộc cùng quốc gia trong cùng tháng. Đây là bước chuyển từ dữ liệu lưới sang dữ liệu quốc gia.

Ví dụ tường minh:

```text
Trước aggregate:
iso3  year  month  grid_cell  temp_c
THA   2010  1      A          25.1
THA   2010  1      B          25.6
THA   2010  1      C          24.8

Sau aggregate:
iso3  year  month  temp_c
THA   2010  1      25.17
```

Ý nghĩa: một quốc gia có thể nhận nhiều điểm lưới ERA5. Mô hình không cần từng điểm lưới riêng lẻ, mà cần một giá trị đại diện cấp quốc gia, nên notebook lấy trung bình theo quốc gia-tháng.

```python
# [2.C.3] Aggregate grid cell -> country-month
monthly_country = (
    grid_weather_df
    .groupby(["iso3", "year", "month"], as_index=False)
    .mean(numeric_only=True)
)
```

Với pipeline đầy đủ, bước này được thực hiện cho tất cả 17 biến ERA5. Một số nước/đảo nhỏ hoặc mã giả của WHO không match tốt với dữ liệu địa lý, đây là limitation đã ghi nhận khi merge với dữ liệu bệnh.

Vì sao có limitation với đảo nhỏ? ERA5 có độ phân giải 0.25° hoặc bản monthly notebook xử lý trên lưới thưa hơn, nên các đảo rất nhỏ có thể không có điểm lưới đại diện tốt. Ngoài ra một số mã trong FluNet như `X09`, `X10`, `X11`, `X12` là mã riêng cho các vùng của UK, không phải ISO3 chuẩn trong Natural Earth.

---

## 5. Chuyển đơn vị và tạo biến dẫn xuất

ERA5 trả nhiều biến theo đơn vị khí tượng gốc: Kelvin, mét, vector gió `u/v`. Notebook chuyển về đơn vị dễ dùng cho mô hình: Celsius, mm, %, m/s.

Ví dụ:

| Biến ERA5 gốc | Đơn vị gốc | Biến sau xử lý | Đơn vị dùng cho model |
|---|---:|---|---:|
| `t2m` | Kelvin | `temp_c` | °C |
| `d2m` | Kelvin | `dewpoint_c` | °C |
| `tp` | mét nước | `precip_mm` | mm |
| `u10`, `v10` | m/s | `wind_ms` | m/s |
| `t2m` + `d2m` | Kelvin | `humidity_pct` | % |

```python
# [2.C.4] Unit conversion + derived variables
def kelvin_to_celsius(k):
    return k - 273.15

def compute_humidity_pct(temp_c, dewpoint_c):
    # August-Roche-Magnus approximation
    es = 6.112 * np.exp((17.67 * temp_c) / (temp_c + 243.5))
    e = 6.112 * np.exp((17.67 * dewpoint_c) / (dewpoint_c + 243.5))
    return 100 * e / es

monthly_country["temp_c"] = kelvin_to_celsius(monthly_country["t2m"])
monthly_country["dewpoint_c"] = kelvin_to_celsius(monthly_country["d2m"])
monthly_country["humidity_pct"] = compute_humidity_pct(
    monthly_country["temp_c"],
    monthly_country["dewpoint_c"],
)
monthly_country["wind_ms"] = np.sqrt(
    monthly_country["u10"] ** 2 + monthly_country["v10"] ** 2
)
monthly_country["precip_mm"] = monthly_country["tp"] * 1000
```

Điểm cần nói rõ: notebook dùng dataset `reanalysis-era5-single-levels-monthly-means`, nên đây là tín hiệu khí hậu theo tháng. Nếu nâng cấp sang daily/hourly thì mưa nên cộng theo tuần, còn nhiệt độ/độ ẩm lấy trung bình tuần.

---

## 6. Broadcast dữ liệu tháng xuống tuần ISO

Các session sau cần key `(iso3, iso_year, iso_week)`, trong khi ERA5 đang ở tháng. Vì vậy notebook broadcast giá trị tháng xuống các tuần ISO thuộc tháng đó. Đây là hạn chế kỹ thuật đã ghi rõ: file có dạng weekly để merge với bệnh, nhưng nguồn ERA5 bản này là monthly means.

```python
# [2.C.5] Broadcast country-month -> country-week
weekly_rows = []

for _, row in monthly_country.iterrows():
    days = pd.date_range(
        start=f"{int(row.year)}-{int(row.month):02d}-01",
        periods=pd.Period(f"{int(row.year)}-{int(row.month):02d}").days_in_month,
        freq="D",
    )
    iso_weeks = days.isocalendar()[["year", "week"]].drop_duplicates()

    for _, iw in iso_weeks.iterrows():
        out = row.to_dict()
        out["iso_year"] = int(iw["year"])
        out["iso_week"] = int(iw["week"])
        weekly_rows.append(out)

era5_weekly_year = pd.DataFrame(weekly_rows)
```

Sau bước này, dữ liệu đã sẵn sàng merge với FluNet/OpenDengue ở Session 3.

---

## 7. Lưu checkpoint theo năm và file final

Vì xử lý ERA5 khá nặng, notebook lưu checkpoint theo từng năm. Nếu Colab bị ngắt giữa chừng thì chỉ chạy lại năm chưa xong, không mất toàn bộ.

```python
# [2.C.6] Save checkpoint từng năm
year_out = WEATHER_PROCESSED / f"era5_weekly_era5_{year}_checkpoint.csv"
era5_weekly_year.to_csv(year_out, index=False)
```

Các checkpoint hiện có trong workspace:

```text
data/weather/processed/era5_weekly_era5_2010_checkpoint.csv
data/weather/processed/era5_weekly_era5_2011_checkpoint.csv
...
data/weather/processed/era5_weekly_era5_2019_checkpoint.csv
```

Sau đó concat tất cả checkpoint thành file cuối:

```python
# [2.C.7] Concat checkpoint -> final CSV
all_years = []
for year in range(2010, 2020):
    p = WEATHER_PROCESSED / f"era5_weekly_era5_{year}_checkpoint.csv"
    all_years.append(pd.read_csv(p))

era5_final = pd.concat(all_years, ignore_index=True)
era5_final.to_csv(
    WEATHER_PROCESSED / "era5_weekly_2010_2019_final.csv",
    index=False,
)
```

File output cuối:

```text
data/weather/processed/era5_weekly_2010_2019_final.csv
```

---

## 8. Verify file đã xử lý

Sau khi có file final, notebook load lại để kiểm tra shape, số quốc gia, missing values và sanity check mùa vụ.

```python
# [2.D] Verify processed ERA5 file
era5 = pd.read_csv("data/weather/processed/era5_weekly_2010_2019_final.csv")

print("ERA5 shape:", era5.shape)
print("Countries:", era5["iso3"].nunique())
print("Missing cells:", era5.isna().sum().sum())
```

Kết quả dùng trong thuyết trình:

- 102,440 dòng = 197 quốc gia × khoảng 520 tuần.
- 21 cột = khóa thời gian/quốc gia + 17 biến khí hậu + biến dẫn xuất.
- Không có NaN trong file ERA5 processed.

Notebook còn kiểm tra mùa vụ đơn giản để bắt lỗi unit conversion:

```python
# [2.E] Seasonal sanity check
usa = era5[era5["iso3"] == "USA"].copy()
usa_jan = usa[usa["iso_week"].between(1, 5)]["temp_c"].mean()
usa_jul = usa[usa["iso_week"].between(27, 31)]["temp_c"].mean()

print(f"USA Jan temp: {usa_jan:.1f} C")
print(f"USA Jul temp: {usa_jul:.1f} C")
print("PASS" if usa_jan < usa_jul else "FAIL")
```

Ý nghĩa: Mỹ tháng 1 lạnh hơn tháng 7 là sanity check cơ bản. Nếu fail thì có thể sai chuyển đơn vị, sai trục thời gian hoặc sai mapping.

---

## Khi bị hỏi sâu hơn

**Vì sao không dùng OpenWeatherMap?**

OpenWeatherMap dễ gọi API hơn, nhưng dữ liệu lịch sử dài hạn thường bị giới hạn hoặc tốn phí. Đồ án cần nhiều năm dữ liệu, nhiều quốc gia và cách đo tương đối đồng nhất, nên ERA5 phù hợp hơn.

**Vì sao không cắt theo biên giới quốc gia cho chính xác?**

Polygon mask chính xác hơn nhưng chậm hơn nhiều khi chạy 10 năm × 17 biến toàn cầu. KD-tree centroid assignment là đánh đổi thực dụng cho grain quốc gia-tuần.

**Vì sao file weekly nhưng nguồn là monthly means?**

Notebook dùng ERA5 monthly averaged để giảm dung lượng và thời gian xử lý. File được đưa về weekly để merge với dữ liệu bệnh theo tuần. Đây là limitation; hướng nâng cấp là dùng ERA5 daily/hourly rồi aggregate tuần đúng nghĩa.

**Hạn chế của cách làm này là gì?**

Dữ liệu cấp quốc gia không phản ánh khác biệt vùng miền trong cùng một nước. Đảo nhỏ và mã giả của WHO có thể không match tốt với centroid/geospatial database. Đây là hạn chế chấp nhận được trong bản mẫu KLTN.

---

## Ý chính cần nhớ

1. ERA5 được chọn vì đồng nhất toàn cầu và phù hợp nghiên cứu.
2. Dữ liệu thời tiết phải được chuyển từ lưới toàn cầu sang quốc gia-tuần.
3. Notebook lấy ERA5 qua CDS API, không tải thủ công.
4. KD-tree centroid assignment map grid cell về `iso3`, rồi aggregate theo quốc gia.
5. File hiện tại dùng monthly means broadcast xuống tuần; cần nói rõ đây là hạn chế.
6. Output chính là `data/weather/processed/era5_weekly_2010_2019_final.csv`.
