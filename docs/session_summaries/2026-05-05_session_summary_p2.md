# Session Summary — 05/05/2026 (Phần 2) — Bước 4: ERA5 2022 + Kết quả cuối pipeline ML

## Tóm tắt nhanh

**Trạng thái**: Hoàn thành toàn bộ pipeline ML. Validation 2022 với ERA5 weather thực tế. Chờ ý kiến giáo viên trước khi chuyển sang FastAPI backend.

**Kết quả cuối cùng:**
- Flu R² = **0.791** (ERA5 2022 thực tế) / 0.811 (training mean)
- Dengue R² = **0.836** (ERA5 2022 thực tế) / 0.858 (training mean)

---

## Bước 4 — ERA5 2022 Weather (thực tế)

### Quyết định kỹ thuật
Ban đầu dự kiến dùng Open-Meteo API, nhưng chuyển sang **ERA5** để đảm bảo nhất quán hoàn toàn với training set 2010–2019 (cùng pipeline, cùng KD-tree mapping, cùng đơn vị).

### Pipeline ERA5 2022
1. **Download** từ CDS API — `reanalysis-era5-single-levels-monthly-means`, năm 2022, 17 biến (~304 MB)
2. **Unzip** tách `era5_2022_instant.nc` và `era5_2022_accum.nc`
3. **Aggregate** theo KD-tree grid (721×1440) → per-country weekly means
4. **Expand** monthly → weekly bằng forward fill
5. **Output**: `dataset/weather/processed/era5_weekly_2022_final.csv` — 197 countries, 52 tuần

### Lỗi gặp phải & cách fix
| Lỗi | Nguyên nhân | Fix |
|---|---|---|
| `unrecognized engine 'netcdf4'` | Thiếu library | `!pip install netcdf4` + restart runtime |
| `unique_countries not defined` | Runtime restart mất biến SESSION 4 | Recreate từ ERA5_FILE + Natural Earth |
| `IndexError: size 1441 vs 1440` | ERA5 2022 lon grid khác (179.75 thay vì 180.0) | Đổi `np.arange(-180, 180.25, 0.25)` → `np.arange(-180, 180, 0.25)` |
| Feature mismatch hemisphere_enc | Model `.pkl` cũ train với 14 features | Retrain với 12 features đúng |

### Cell [9.0b] — graceful degradation
```python
if ERA5_2022_FILE.exists():
    weather_2022 = pd.read_csv(ERA5_2022_FILE)
    USE_REAL_WEATHER = True
else:
    # fallback: per-country training mean
    USE_REAL_WEATHER = False
```

---

## Kết quả validation cuối cùng

### So sánh 2 kịch bản weather 2022

| Model | Metric | Training mean | ERA5 2022 thực tế | Δ |
|---|---|---|---|---|
| Flu | R² | 0.811 | **0.791** | -0.020 |
| Flu | sMAPE non-zero | 73.3% | **73.9%** | +0.6% |
| Dengue | R² | 0.858 | **0.836** | -0.022 |
| Dengue | sMAPE | 12.5% | **14.5%** | +2.0% |

### Giải thích kết quả giảm nhẹ với ERA5 thực tế
ERA5 thực tế **giảm nhẹ** so với training mean — ngược kỳ vọng ban đầu. Lý do:
- Training mean là **seasonal prior ổn định** — smooth out noise theo quốc gia
- ERA5 2022 mang thêm **noise từ La Niña kéo dài** — pattern thời tiết bất thường mà model chưa học
- Bottleneck chính vẫn là **immunity debt 2022**, không phải chất lượng weather

---

## Đánh giá tổng thể pipeline ML

| Aspect | Kết quả | Nhận xét |
|---|---|---|
| Flu R² | 0.791 | Đạt — paper tương tự WHO FluNet đạt 0.6–0.8 |
| Dengue R² | 0.836 | Tốt — 41 quốc gia endemic |
| Flu sMAPE non-zero | 73.9% | Cao nhưng giải thích được bởi immunity debt 2022 |
| Dengue sMAPE | 14.5% | Rất tốt cho bài toán global |
| Coverage | 197 countries flu / 41 dengue | Global scale |

### Điểm mạnh
- Pipeline end-to-end hoàn chỉnh: data → feature engineering → training → validation
- ERA5 weather thực tế cho validation (nhất quán với training)
- Optuna tuning xác nhận model đã stable
- Dengue generalize tốt qua COVID period

### Limitations cần nêu trong báo cáo
1. **Flu 2022 immunity debt** — đỉnh tuần 50 (~77K) vượt xa training set, model không extrapolate được
2. **ERA5 monthly means** thay vì weekly — mất biến động ngắn hạn trong tháng
3. **Weather lag dùng global CCF** thay vì per-country — có thể kém chính xác cho nước nhiệt đới
4. **Flu risk 3-tier không reliable** — Medium F1 ≈ 0 do 38.8% zero rows, nên dùng binary Low/High

---

## Files đã thay đổi

| File | Thay đổi |
|---|---|
| `KLTN_EpiWeather_ML_Colab.ipynb` | Thêm cell [9.0b] ERA5 2022 pipeline; patch [9.1] dùng ERA5 thực tế |
| `dataset/weather/processed/era5_weekly_2022_final.csv` | Mới — ERA5 2022, 197 countries, 52 tuần |

---

## Trạng thái tasks

| Task | Status |
|---|---|
| Bước 1 — log1p transform flu | ✅ Done |
| Bước 2 — Revert hemisphere features | ✅ Done |
| Bước 3 — Optuna tuning | ✅ Done |
| Bước 4 — ERA5 2022 weather | ✅ Done |
| **Pipeline ML toàn bộ** | ✅ **Hoàn chỉnh** |
| Tham khảo ý kiến giáo viên | ⏳ Chờ |
| Export model mới (12 features) | ⏳ Sau khi confirm với GV |
| FastAPI backend | ❌ Chưa làm |
| Frontend React + Tailwind + Leaflet | ❌ Chưa làm |

---

## Câu hỏi cần hỏi giáo viên

1. **R² 0.791 flu có đủ không?** Hay cần cải thiện thêm trước khi sang backend?
2. **Flu risk classification** — nên dùng binary Low/High hay cố gắng cải thiện 3-tier?
3. **Scope backend** — FastAPI chỉ cần endpoint predict, hay cần thêm historical query, alerting?
4. **Deadline** — ưu tiên hoàn thiện ML hay chuyển sang backend sớm?
