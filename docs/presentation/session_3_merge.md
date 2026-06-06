# Session 3: Ghép dữ liệu thành `master_weekly_v1.csv` (Notebook v5/v6)

> **Dùng khi demo lần 1:** Nếu bị hỏi dữ liệu từ nhiều nguồn ghép lại thế nào, dùng file này để trả lời. Điểm chính: chuẩn hóa tất cả về khóa `(iso3, iso_year, iso_week)`, kiểm tra coverage trước khi merge, sau đó tạo file master sạch không thiếu weather.
>
> **Mục tiêu thuyết trình:** Người chấm hiểu rằng merge không chỉ là `pd.merge`. Phải xử lý mã quốc gia, ngày/tuần ISO, coverage giữa nguồn bệnh và ERA5, rồi mới tạo dataset huấn luyện.

---

## Bản đọc khi thuyết trình

Sau Session 1-2, em có ba nguồn chính: FluNet, OpenDengue và ERA5. Ba nguồn này không cùng cấu trúc. FluNet đã có năm ISO và tuần ISO; OpenDengue có ngày bắt đầu kỳ báo cáo nên phải đổi sang tuần ISO; ERA5 sau xử lý cũng được đưa về năm-tuần ISO. Vì vậy trước khi ghép, em chuẩn hóa tất cả về cùng khóa: `iso3`, `iso_year`, `iso_week`.

Điểm quan trọng là không phải quốc gia nào có dữ liệu bệnh cũng có dữ liệu thời tiết ERA5 sau xử lý. Vì vậy em kiểm tra coverage trước khi merge. FluNet có 183 quốc gia trong giai đoạn xét, Dengue có 82 quốc gia, ERA5 có 197 quốc gia. Nhưng intersection giữa dữ liệu bệnh và ERA5 nhỏ hơn do một số đảo nhỏ, vùng lãnh thổ hoặc mã đặc biệt của WHO không match với dữ liệu địa lý.

Sau khi kiểm tra coverage, em merge dữ liệu bệnh với ERA5 bằng `inner join` để tạo tập huấn luyện sạch, tức là chỉ giữ những dòng vừa có ca bệnh vừa có thời tiết. Kết quả cuối cùng là `master_weekly_v1.csv` với 61,112 dòng, 27 cột, 163 quốc gia, giai đoạn 2010-2019. Đây là file trung tâm cho EDA, feature engineering và training.

---

## 1. Vấn đề: 3 nguồn, 3 cấu trúc khác nhau

| Nguồn | Khóa thời gian | Khóa quốc gia | Mức thời gian |
|---|---|---|---|
| FluNet | `ISO_YEAR`, `ISO_WEEK` | `COUNTRY_CODE` | Weekly |
| OpenDengue | `calendar_start_date` | `adm_0_iso` / `ISO_A0` | Tuần + tháng + năm |
| ERA5 sau xử lý | `iso_year`, `iso_week` | `iso3` | Monthly means broadcast xuống weekly |

Mục tiêu của Session 3:

```text
FluNet       -> iso3, iso_year, iso_week, influenza_total
OpenDengue  -> iso3, iso_year, iso_week, dengue_total
ERA5         -> iso3, iso_year, iso_week, weather columns
                         ↓
              master_weekly_v1.csv
```

---

## 2. Cell 3.1 — Chuẩn bị FluNet

FluNet có nhiều dòng cho cùng một quốc gia-tuần do nguồn báo cáo khác nhau. Notebook chuẩn hóa tên cột, tạo target cúm và cộng dồn theo `(iso3, iso_year, iso_week)`. Ở bước coverage này notebook giữ mã quốc gia gốc của WHO, nên các mã đặc biệt như `X09-X12` vẫn xuất hiện và sẽ bị loại khi inner join với ERA5 vì không có trong Natural Earth/ERA5.

```python
flu_m = flu.copy()
flu_m["iso3"] = flu_m["COUNTRY_CODE"]
flu_m["iso_year"] = flu_m["ISO_YEAR"].astype(int)
flu_m["iso_week"] = flu_m["ISO_WEEK"].astype(int)

flu_m["INF_A"] = flu_m["INF_A"].fillna(0)
flu_m["INF_B"] = flu_m["INF_B"].fillna(0)
flu_m["influenza_total"] = flu_m["INF_A"] + flu_m["INF_B"]

flu_m = (
    flu_m[flu_m["iso_year"].between(2010, 2019)]
    .groupby(["iso3", "iso_year", "iso_week"], as_index=False)
    .agg({
        "INF_A": "sum",
        "INF_B": "sum",
        "influenza_total": "sum",
        "HEMISPHERE": "first",
    })
)
```

**Lưu ý về UK:** WHO FluNet dùng `X09`, `X10`, `X11`, `X12` cho England, Scotland, Wales, Northern Ireland. Trong output notebook của Session 3, các mã này không match ERA5 nên nằm trong danh sách bị drop. Nếu muốn phục vụ UK country-level đầy đủ ở phiên bản sau, có thể thêm bước gộp `X09-X12 -> GBR` trước khi merge.

Kết quả dùng ở bước coverage:

```text
FluNet: 183 quốc gia
```

---

## 3. Cell 3.2 — Chuẩn bị OpenDengue

OpenDengue không dùng sẵn `iso_year`, `iso_week` như FluNet. Notebook parse ngày bắt đầu kỳ báo cáo rồi lấy ISO calendar.

```python
dengue_m = dengue.copy()
dengue_m["calendar_start_date"] = pd.to_datetime(
    dengue_m["calendar_start_date"],
    errors="coerce",
)

iso = dengue_m["calendar_start_date"].dt.isocalendar()
dengue_m["iso_year"] = iso.year.astype("Int64")
dengue_m["iso_week"] = iso.week.astype("Int64")

dengue_m = dengue_m.rename(columns={
    "adm_0_iso": "iso3",
    "ISO_A0": "iso3",
})

dengue_m = dengue_m[
    dengue_m["iso_year"].between(2010, 2019) &
    dengue_m["T_res"].isin(["Week", "Month"])
].copy()
```

Notebook giữ các dòng có độ phân giải tuần/tháng, bỏ dữ liệu year-level vì quá thô để merge theo tuần. Kết quả coverage:

```text
Dengue: 82 quốc gia
```

---

## 4. Cell 3.3 — Kiểm tra coverage trước khi merge

Trước khi merge, notebook kiểm tra số quốc gia của từng nguồn và intersection với ERA5. Đây là bước quan trọng để biết dòng nào sẽ mất khi yêu cầu phải có weather.

```python
flu_countries = set(flu_m["iso3"].dropna().unique())
dengue_countries = set(dengue_m["iso3"].dropna().unique())
era5_countries = set(era5["iso3"].dropna().unique())

flu_no_era5 = sorted(flu_countries - era5_countries)
dengue_no_era5 = sorted(dengue_countries - era5_countries)

print("Số quốc gia:")
print(f"  FluNet : {len(flu_countries)}")
print(f"  Dengue : {len(dengue_countries)}")
print(f"  ERA5   : {len(era5_countries)}")

print(f"Flu ∩ ERA5        : {len(flu_countries & era5_countries)} nước")
print(f"Flu KHÔNG có ERA5 : {len(flu_no_era5)} nước")
print(f"Dengue ∩ ERA5        : {len(dengue_countries & era5_countries)} nước")
print(f"Dengue KHÔNG có ERA5 : {len(dengue_no_era5)} nước")
print(f"Nước có CẢ flu + dengue: {len(flu_countries & dengue_countries)}")
```

Output notebook:

```text
Số quốc gia:
  FluNet : 183
  Dengue : 82
  ERA5   : 197

Flu ∩ ERA5         : 162 nước (sẽ có weather sau merge)
Flu KHÔNG có ERA5  : 21 nước → bị drop khi merge
  ['BLM', 'BMU', 'BRB', 'DMA', 'GLP', 'GRD', 'GUF', 'KNA', 'LIE',
   'MAF', 'MDV', 'MLT', 'MTQ', 'SGP', 'TCA', 'VGB', 'X09', 'X10',
   'X11', 'X12', 'XKX']

Dengue ∩ ERA5         : 52 nước
Dengue KHÔNG có ERA5  : 30 nước → bị drop khi merge
  ['ASM', 'BES', 'BLM', 'BMU', 'BRB', 'COK', 'CUW', 'DMA', 'FSM',
   'GLP', 'GRD', 'GUF', 'GUM', 'KNA', 'MAF', 'MHL', 'MNP', 'MSR',
   'MTQ', 'NIU', 'PCN', 'PLW', 'SGP', 'SXM', 'TCA', 'TKL', 'TON',
   'TUV', 'VGB', 'WLF']

Nước có CẢ flu + dengue (overlap): 56
```

Phân tích:

- Nhóm bị drop chủ yếu là đảo nhỏ/vùng lãnh thổ hoặc mã không chuẩn ISO3 trong nguồn bệnh.
- Đây không phải lỗi model; đây là giới hạn khi kết hợp surveillance data với dữ liệu địa lý/thời tiết.
- Sau bước này em biết trước mức mất dữ liệu: flu giữ khoảng 89% theo quốc gia có ERA5, dengue giữ khoảng 63% theo quốc gia có ERA5.

---

## 5. Cell 3.4 — Merge FluNet với ERA5

Với tập training, em dùng `inner join` để chỉ giữ dòng có cả số ca cúm và thời tiết. Mục tiêu là tạo dataset sạch, không có NaN trong weather columns.

```python
weather_cols = [
    "temp_c", "dewpoint_c", "temp_min_c", "temp_max_c", "temp_range_c",
    "humidity_pct", "wind_ms", "precip_mm", "conv_precip_mm",
    "ls_precip_mm", "evap_mm", "water_vapour", "solar_wm2",
    "uv_wm2", "thermal_wm2", "cloud_cover", "msl_pa", "blh_m",
]

flu_weather = flu_m.merge(
    era5,
    on=["iso3", "iso_year", "iso_week"],
    how="inner",
)

print("Shape sau merge:", flu_weather.shape)
print("NaN trong weather cols:", flu_weather[weather_cols].isna().sum().sum())
```

Output notebook:

```text
Shape sau merge: (59165, 25)
Số rows giữ lại: 59,165 / 88,728 (66.7%)
Unique countries: 154
Year range: 2010 – 2019
NaN trong weather cols: 0
```

Rows per year:

| Year | Rows |
|---:|---:|
| 2010 | 4,980 |
| 2011 | 5,633 |
| 2012 | 5,802 |
| 2013 | 5,827 |
| 2014 | 5,375 |
| 2015 | 5,553 |
| 2016 | 5,998 |
| 2017 | 6,460 |
| 2018 | 6,717 |
| 2019 | 6,820 |

Sample notebook:

| iso3 | iso_year | iso_week | influenza_total | temp_c | humidity_pct | precip_mm |
|---|---:|---:|---:|---:|---:|---:|
| ABW | 2017 | 1 | 11.0 | 26.674957 | 83.679543 | 4.146576 |
| ABW | 2017 | 2 | 0.0 | 26.674957 | 83.679543 | 4.146576 |
| ABW | 2017 | 3 | 3.0 | 26.674957 | 83.679543 | 4.146576 |

Điểm cần nói: thời tiết của các tuần trong cùng tháng giống nhau vì ERA5 input là monthly means broadcast xuống tuần.

---

## 6. Cell 3.5 — Merge OpenDengue với ERA5

Dengue cũng được merge với ERA5 bằng `inner join`, để chỉ giữ dòng có đủ ca dengue và weather.

```python
dengue_weather = dengue_m.merge(
    era5,
    on=["iso3", "iso_year", "iso_week"],
    how="inner",
)

print("Shape sau merge:", dengue_weather.shape)
print("NaN trong weather cols:", dengue_weather[weather_cols].isna().sum().sum())
```

Output notebook:

```text
Shape sau merge: (8362, 23)
Số rows giữ lại: 8,362 / 18,125 (46.1%)
Unique countries: 49
Year range: 2010 – 2019
NaN trong weather cols: 0
```

Rows per year:

| Year | Rows |
|---:|---:|
| 2010 | 193 |
| 2011 | 241 |
| 2012 | 504 |
| 2013 | 259 |
| 2014 | 361 |
| 2015 | 1,034 |
| 2016 | 1,209 |
| 2017 | 1,467 |
| 2018 | 1,594 |
| 2019 | 1,500 |

Top 5 nước nhiều rows nhất:

| iso3 | Rows |
|---|---:|
| LKA | 453 |
| NIC | 364 |
| PER | 364 |
| MYS | 313 |
| VIR | 313 |

Sample notebook:

| iso3 | iso_year | iso_week | dengue_total | case_definition_standardised | temp_c | humidity_pct |
|---|---:|---:|---:|---|---:|---:|
| LKA | 2010 | 16 | 428.0 | Total | 27.87365 | 80.888084 |
| LKA | 2010 | 15 | 610.0 | Total | 27.87365 | 80.888084 |
| LKA | 2010 | 14 | 254.0 | Total | 27.87365 | 80.888084 |

Phân tích:

- Dengue mất nhiều hơn flu vì OpenDengue có nhiều đảo/vùng nhiệt đới nhỏ không match ERA5 tốt.
- Từ 2015 trở đi rows tăng rõ vì coverage OpenDengue tốt hơn; đây là lý do các session sau ưu tiên training dengue 2015-2019.

---

## 7. Cell 3.6 — Combine flu + dengue + ERA5

Sau khi đã chuẩn hóa flu và dengue, notebook outer join hai bệnh để giữ tất cả dòng có ít nhất một bệnh. Sau đó inner join với ERA5 để master cuối có đủ weather.

```python
disease = flu_m.merge(
    dengue_m[[
        "iso3", "iso_year", "iso_week",
        "dengue_total", "case_definition_standardised",
    ]],
    on=["iso3", "iso_year", "iso_week"],
    how="outer",
)

print("Sau OUTER JOIN flu+dengue:", disease.shape)
print("Rows có flu:", disease["influenza_total"].notna().sum())
print("Rows có dengue:", disease["dengue_total"].notna().sum())
print("Rows có CẢ 2:", (
    disease["influenza_total"].notna() &
    disease["dengue_total"].notna()
).sum())

master = disease.merge(
    era5,
    on=["iso3", "iso_year", "iso_week"],
    how="inner",
)

master.to_csv(PROCESSED / "master_weekly_v1.csv", index=False)
```

Output notebook:

```text
Sau OUTER JOIN flu+dengue: (95278, 9)
  Rows có flu  : 88,728
  Rows có dengue: 18,125
  Rows có CẢ 2 : 11,575

Sau INNER JOIN với ERA5 → master: (61112, 27)
  Rows có flu (sau ERA5)   : 59,165
  Rows có dengue (sau ERA5): 8,362

[SAVED] /content/drive/MyDrive/KLTN/dataset/processed/master_weekly_v1.csv
        Shape: (61112, 27), Size: 20.9MB
```

Ý nghĩa:

- `outer join flu+dengue`: không bỏ mất dòng chỉ có flu hoặc chỉ có dengue.
- `inner join ERA5`: master training phải có đủ weather, nên các dòng không có ERA5 bị loại.
- File `master_weekly_v1.csv` là đầu vào của Session 4 EDA và Session 5 feature engineering.

---

## 8. Cell 3.7 — Reload từ disk và sanity check

Sau khi lưu, notebook đọc lại file từ disk để đảm bảo file thật sự được ghi đúng.

```python
master = pd.read_csv(PROCESSED / "master_weekly_v1.csv")

print("Reload từ disk:", master.shape)
print("Columns:", list(master.columns))

print(master.isna().sum()[master.isna().sum() > 0])

has_flu = master["influenza_total"].notna()
has_dengue = master["dengue_total"].notna()

print("Chỉ flu:", (has_flu & ~has_dengue).sum())
print("Chỉ dengue:", (~has_flu & has_dengue).sum())
print("Cả 2 bệnh:", (has_flu & has_dengue).sum())
```

Output notebook:

```text
Reload từ disk: (61112, 27)
Columns (27):
['iso3', 'iso_year', 'iso_week', 'INF_A', 'INF_B', 'influenza_total',
 'HEMISPHERE', 'dengue_total', 'case_definition_standardised',
 'temp_c', 'dewpoint_c', 'temp_min_c', 'temp_max_c', 'temp_range_c',
 'humidity_pct', 'wind_ms', 'precip_mm', 'conv_precip_mm',
 'ls_precip_mm', 'evap_mm', 'water_vapour', 'solar_wm2',
 'uv_wm2', 'thermal_wm2', 'cloud_cover', 'msl_pa', 'blh_m']

NaN per column:
INF_A                            1947
INF_B                            1947
influenza_total                  1947
HEMISPHERE                       1947
dengue_total                    52750
case_definition_standardised    52750

Coverage breakdown:
  Chỉ flu     : 52,750 rows
  Chỉ dengue  : 1,947 rows
  Cả 2 bệnh   : 6,415 rows
  TỔNG        : 61,112 rows

Year range: 2010 – 2019
Unique countries: 163
```

Phân tích NaN:

- NaN ở `dengue_total` là bình thường: các dòng chỉ có flu.
- NaN ở `influenza_total`, `INF_A`, `INF_B`, `HEMISPHERE` là bình thường: các dòng chỉ có dengue.
- Weather columns không NaN vì master đã inner join với ERA5.

Sanity check Brazil 2018:

```python
bra2018 = master[(master["iso3"] == "BRA") & (master["iso_year"] == 2018)]
print("Rows:", len(bra2018))
print("Tổng flu 2018:", bra2018["influenza_total"].sum())
print("Tổng dengue 2018:", bra2018["dengue_total"].sum())
print("Temp range:", bra2018["temp_c"].min(), bra2018["temp_c"].max())

bra2018[bra2018["iso_week"] == 20][[
    "iso3", "iso_year", "iso_week",
    "influenza_total", "dengue_total",
    "temp_c", "humidity_pct", "precip_mm",
]]
```

Output notebook:

```text
Sanity check — Brazil 2018:
  Rows: 52 (kỳ vọng 52 tuần)
  Tổng flu 2018: 7012
  Tổng dengue 2018: 470269
  Temp range: 23.5 – 26.4°C
```

Sample row Brazil 2018 W20:

| iso3 | iso_year | iso_week | influenza_total | dengue_total | temp_c | humidity_pct | precip_mm |
|---|---:|---:|---:|---:|---:|---:|---:|
| BRA | 2018 | 20 | 568.0 | 11126.0 | 24.159164 | 77.554405 | 4.232549 |

Ý nghĩa sanity check:

- Brazil có đủ 52 tuần trong năm 2018.
- Cùng một row có cả ca flu, ca dengue và weather.
- Nhiệt độ nằm trong khoảng hợp lý với Brazil.

---

## 9. Lỗi quan trọng đã sửa

### Bug 1: Path `dataset/epidemic/processed/` vs `dataset/processed/`

Ban đầu có lúc lưu master vào `dataset/epidemic/processed/`, nhưng master là dữ liệu cross-domain gồm bệnh và thời tiết.

**Fix:** chuyển output lên `dataset/processed/master_weekly_v1.csv`.

### Bug 2: Linux case-sensitive `Dataset` vs `dataset`

Drive cũ dùng `Dataset/`, trong khi notebook dùng `dataset/`. Colab/Linux phân biệt hoa thường nên dễ lỗi file not found.

**Fix:** thống nhất lowercase `dataset/` trong notebook và tài liệu.

---

## Ý chính Session 3

1. Merge phải chuẩn hóa về cùng khóa `(iso3, iso_year, iso_week)`.
2. Coverage check trước merge giúp biết chính xác nước nào sẽ bị drop vì không có ERA5.
3. Flu giữ 59,165 / 88,728 rows sau khi yêu cầu có ERA5; dengue giữ 8,362 / 18,125 rows.
4. Master cuối có 61,112 rows, 27 columns, 163 countries, 2010-2019.
5. Weather columns không NaN; NaN chỉ nằm ở bệnh còn lại khi row chỉ có flu hoặc chỉ có dengue.
6. `master_weekly_v1.csv` là file trung tâm cho EDA, feature engineering và training.

---

## Câu nói thuyết trình cho Session 3

> "Sau Session 1-2 em có ba nguồn riêng: FluNet, OpenDengue và ERA5. Session 3 chuẩn hóa tất cả về cùng khóa `iso3, iso_year, iso_week` rồi merge thành file master."
>
> "Trước khi merge, em kiểm tra coverage: FluNet có 183 nước, Dengue 82 nước, ERA5 197 nước. Nhưng không phải nước nào có bệnh cũng có ERA5. Flu thiếu ERA5 21 nước, dengue thiếu ERA5 30 nước, chủ yếu là đảo nhỏ hoặc mã đặc biệt."
>
> "Em outer join flu và dengue để giữ dòng có ít nhất một bệnh, sau đó inner join với ERA5 để master cuối không thiếu weather. Kết quả là `master_weekly_v1.csv`: 61,112 rows, 27 columns, 163 quốc gia, giai đoạn 2010-2019."
>
> "NaN trong master là có chủ đích: dòng chỉ có flu thì dengue_total NaN, dòng chỉ có dengue thì influenza_total NaN. Nhưng weather columns không NaN, vì training cần đầy đủ đặc trưng thời tiết."
>
> "Sanity check Brazil 2018 có đủ 52 tuần, tổng flu 7,012, dengue 470,269, và sample W20 có cả flu, dengue, nhiệt độ, độ ẩm, mưa. Đây là bằng chứng merge đúng theo quốc gia-tuần."
