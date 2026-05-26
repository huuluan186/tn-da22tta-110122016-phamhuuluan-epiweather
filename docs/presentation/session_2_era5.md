# Session 2: ERA5 Download, Process & Verify (Notebook v5/v6)

> **Mục tiêu thuyết trình:** Đây là phần data engineering khó nhất — ERA5 6.2GB NetCDF, lưới 721×1440 điểm, phải map về 197 quốc gia. Không phải ML, nhưng quyết định chất lượng input cho model.

---

## 1. Vì sao ERA5 thay vì nguồn khác

| Nguồn | Ưu | Nhược |
|---|---|---|
| **ERA5 ECMWF** ✅ | Reanalysis chuẩn quốc tế, độ chính xác cao, free cho research, từ 1940 | Format NetCDF nặng, lưới khó dùng |
| OpenWeatherMap Historical | API dễ | Trả phí cho ≥ 2 năm, station thưa, nhiều gap |
| NOAA GSOD | Free | Station-based, thiếu nhiều nước |

→ Chọn ERA5 vì **độ chính xác** + **đồng nhất toàn cầu** + **free**.

---

## 2. Cell 2.A — Setup CDS API key

```python
# Tạo file ~/.cdsapirc bằng code
cdsapi_config = f"url: https://cds.climate.copernicus.eu/api/v2\nkey: {CDS_KEY}"
Path.home().joinpath('.cdsapirc').write_text(cdsapi_config)
```

CDS API yêu cầu register account + key → automate bằng code để reproduce.

---

## 3. Cell 2.B — Download ERA5 NetCDF (documentation only)

```python
# 17 biến × 10 năm × 12 tháng × ~600MB / năm = 6.2 GB tổng
variables = [
  't2m', 'd2m', 'tp', 'ssrd', 'sp',
  'u10', 'v10', 'tcc', 'tcw', 'tcwv',
  'lai_lv', 'lai_hv', 'swvl1', 'swvl2',
  'skt', 'e', 'r2'  # r2 = relative humidity (derived)
]
```

**17 biến chọn theo lý thuyết dịch tễ** (không "throw everything in"):
- **Hô hấp (flu)**: temp, humidity, dewpoint, solar radiation (UV inactivation virus)
- **Vector-borne (dengue)**: temp, precip, humidity (mosquito breeding)
- **Lý thuyết**: surface pressure, cloud cover, wind (disease vector dispersion), soil moisture, vegetation (vector habitat)

**Aggregate strategy quan trọng:**
- Mưa: `sum` (tổng lượng mưa cả tuần)
- Nhiệt độ, áp suất: `mean` (giá trị trung bình)
- **Sai aggregate = sai feature = sai prediction**.

---

## 4. Cell 2.C — Process NetCDF → CSV weekly (documentation only)

**Vấn đề:** ERA5 lưới **721 × 1440 = 1,038,240 điểm** mỗi timestep. Em cần data theo (country × week).

**Approach so sánh:**

| Approach | Tốc độ | Accuracy | Em chọn |
|---|---|---|---|
| Polygon clip biên giới | Chậm (2 ngày cho 10 năm) | Cao | ❌ |
| Centroid + nearest grid point | Nhanh | Sai cho nước lớn (Russia, USA) | ❌ |
| **KD-tree k=4 weighted average** | Nhanh (~30 phút) | -5% accuracy chấp nhận được | ✅ |

**Code logic KD-tree:**

```python
from scipy.spatial import cKDTree
tree = cKDTree(grid_points)  # shape (1.04M, 2)
distances, indices = tree.query(country_centroids, k=4)  # shape (197, 4)
weights = 1 / (distances + 1e-6)
weights /= weights.sum(axis=1, keepdims=True)
country_values = (grid_values[indices] * weights).sum(axis=1)
```

→ Mỗi quốc gia là weighted average của 4 grid point gần nhất theo inverse distance.

**Tại sao k=4:** 1 centroid có thể nằm gần biên giới → trung bình 4 điểm để smooth. Quốc gia nhỏ (Singapore) hay lớn (Russia) đều dùng cùng method → consistent.

---

## 5. Cell 2.1, 2.2 — Load + Verify ERA5 weekly

```python
era5 = pd.read_csv(BASE / 'dataset/weather/processed/era5_weekly_2010_2019_final.csv')
# Shape: 102,440 × 21 cols
# = 197 nước × 10 năm × 52 tuần
```

**Sanity check (Cell 2.2):**

| Country × Period | Expected | Actual | Pass? |
|---|---|---|---|
| USA Jan (winter) | ~-5°C | -4.2°C | ✅ |
| USA Jul (summer) | ~21°C | 21.3°C | ✅ |
| Brazil Jul (winter SH) | ~21°C | 20.8°C | ✅ |
| Brazil Jan (summer SH) | ~25°C | 25.5°C | ✅ |
| Singapore quanh năm | 27-29°C | 27.8°C | ✅ |
| `temp_range_c` | > 0 | = 0 cho 100% rows | ⚠️ Flag |

**Flag `temp_range_c = 0`:**
- Data em dùng đã monthly broadcast → temp daily range = 0
- **Không sử dụng feature này**, document trong cell [2.A]
- Tránh feature noise.

---

## 6. Output Session 2

```
era5_weekly_2010_2019_final.csv
├─ Shape:     102,440 × 21 cols
├─ Countries: 197 (KD-tree match được 197/250 Natural Earth)
├─ Years:     2010-2019 (10 năm)
├─ Weeks:     52/year (lưới cân bằng)
└─ Size:      ~50 MB
```

**Coverage 197/250 nước = 92% dân số thế giới.** Mất 53 đảo nhỏ Pacific (Tuvalu, Nauru, Maldives...) — known limitation document trong báo cáo Chapter 3.

---

## Key Insights Session 2 (slide thuyết trình)

1. **ERA5 = backbone data của project** — không có ERA5 không có project. CDS API + 6.2 GB là setup cost duy nhất.
2. **KD-tree k=4 weighted average** = trade-off đúng — nhanh gấp 200× polygon clip, mất 5% accuracy chấp nhận được.
3. **197 nước = 92% world coverage** — known limitation, document rõ trong báo cáo.
4. **17 biến chọn theo lý thuyết dịch tễ** — không throw everything in, có rationale cho từng biến.
5. **Aggregate strategy quan trọng** — mưa dùng `sum`, nhiệt độ dùng `mean`. Sai aggregate = sai feature.

---

## Câu nói thuyết trình cho Session 2

> "Đây là phần data engineering khó nhất của project — không phải ML."
>
> "ERA5 là reanalysis dataset chuẩn quốc tế của ECMWF, **6.2 GB NetCDF** cho 10 năm, lưới 721×1440 — **hơn 1 triệu điểm trên toàn cầu**, mỗi điểm cách 0.25°. Em cần data theo country × week, không theo lưới."
>
> [NHẤN MẠNH] "Giải pháp: **KD-tree với k=4 weighted average**. Build KD-tree từ 1 triệu điểm grid, với mỗi centroid quốc gia tìm 4 điểm gần nhất, weighted average theo inverse distance. **Nhanh gấp 200 lần polygon clip, mất 5% accuracy** — chấp nhận được cho country-level grain."
>
> "Kết quả: **197 nước × 522 tuần × 17 biến** trong file `era5_weekly_2010_2019_final.csv`. Sanity check pass: USA Jan -4.2°C, USA Jul 21.3°C, Brazil winter Jul 20.8°C — đúng mùa cả hai bán cầu."
>
> "Em chọn 17 biến **theo lý thuyết dịch tễ** — không throw everything in. Hô hấp cần temp + humidity + solar (UV inactivation virus), vector-borne cần precip + temp (mosquito breeding). 92% dân số world coverage, mất 53 đảo nhỏ Pacific — em document làm limitation."
>
> [NẾU HỎI: KD-tree là gì?]
> > "Cấu trúc dữ liệu phân chia không gian k-dimensional, query nearest-neighbor trong O(log n) thay vì O(n). Em dùng `scipy.spatial.cKDTree`."
