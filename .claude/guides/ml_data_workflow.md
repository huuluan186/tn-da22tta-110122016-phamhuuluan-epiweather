# ML Data Workflow — Quy trình chuẩn cho KLTN

## Nguyên tắc cốt lõi

ML không phải chạy thẳng từ data → model. Đây là **vòng lặp**:

```
Data thô
  ↓
[1] Load & Sanity check     ← phát hiện lỗi → fix nguồn
  ↓
[2-3] ERA5 process + Merge  ← tạo master_weekly.csv
  ↓
[4] EDA + Correlation       ← signal yếu → xem lại features
  ↓
[5] Feature Engineering     ← feature tệ → quay lại [4]
  ↓
[6] Train model (4 reg + 1 cls + Optuna) ← kém → quay lại [5] hoặc [1]
  ↓
[7] Validate + Export       ← overfit/underfit → quay lại [6] hoặc [5]
  ↓
Deploy
```

**Không bao giờ bỏ qua bước kiểm tra** — lỗi data phát hiện muộn tốn gấp 10 lần thời gian fix.

---

## SESSION 1 — Kiểm tra chất lượng data (sau mỗi lần update)

### 5.1 Missing rate

```python
# Tỷ lệ NaN từng cột
miss = master.isnull().mean().sort_values(ascending=False) * 100
print(miss[miss > 0])

# Số nước có đủ weather
has_weather = (master.groupby('iso3')['temp_c'].count() > 0).sum()
print(f'Nước có weather: {has_weather}/{master["iso3"].nunique()}')
```

**Ngưỡng chấp nhận:** weather NaN < 20% tổng rows; target (inf_cases, dengue_log1p) NaN = 0.

### 5.2 Phân phối giá trị — phát hiện outlier

```python
# Kiểm tra giá trị bất thường
weather_cols = ['temp_c','humidity_pct','precip_mm','solar_wm2','dewpoint_c']
master[weather_cols].describe()

# Ngưỡng hợp lý:
# temp_c: -50 đến +50°C
# humidity_pct: 0 đến 100%
# precip_mm: 0 đến 2000 mm/tháng
# solar_wm2: 0 đến 400 W/m²
```

Nếu thấy giá trị ngoài ngưỡng → kiểm tra lại đơn vị trong ERA5 processing.

### 5.3 Coverage theo năm × quốc gia

```python
# Heatmap coverage: năm × quốc gia (có data không?)
pivot = master.groupby(['iso_year','iso3'])['inf_cases'].count().unstack(fill_value=0)
print(f'Năm có đủ data (>100 nước): {(pivot > 0).sum(axis=1)[lambda x: x > 100].index.tolist()}')
```

**Kỳ vọng:** 2010–2019 đều có >120 nước báo cáo cúm.

### 5.4 Sanity check target

```python
# Influenza: tỷ lệ zero rows
zero_flu = (master['inf_cases'] == 0).mean() * 100
print(f'Flu zero rows: {zero_flu:.1f}%')  # kỳ vọng ~70-75%

# Dengue: chỉ endemic countries mới có data
dengue_countries = master[master['dengue_log1p'] > 0]['iso3'].nunique()
print(f'Dengue endemic countries: {dengue_countries}')  # kỳ vọng ~15-25
```

### 5.5 Kiểm tra ERA5 monthly means

```python
# Verify temp_range_c = 0 (limitation của monthly means)
print(f'temp_range_c = 0: {(master["temp_range_c"] == 0).mean()*100:.1f}%')

# Verify USA tháng 1 vs tháng 7 khác nhau (seasonal check)
usa = master[master['iso3'] == 'USA']
jan = usa[usa['iso_week'].between(1, 4)]['temp_c'].mean()
jul = usa[usa['iso_week'].between(27, 30)]['temp_c'].mean()
print(f'USA Jan avg: {jan:.1f}°C | Jul avg: {jul:.1f}°C')
# Kỳ vọng: Jan ≈ -5 đến 5°C, Jul ≈ 20-25°C
```

---

## SESSION 4 — Phân tích tương quan (EDA trên master file, chạy lại nếu data thay đổi lớn)

**Khi nào cần chạy lại CCF:**
- ERA5 thay đổi coverage đáng kể (thêm >30 nước) → chạy lại
- ERA5 đổi từ weekly sang monthly means → chạy lại để xác nhận lags còn đúng không
- Target thay đổi cách tính → luôn chạy lại

**Khi nào bỏ qua (dùng lại kết quả cũ):**
- Chỉ fix lỗi nhỏ (1-2 nước)
- Không đổi cách tính weather

**CCF lags hiện tại (từ EDA cũ):**
```python
WEATHER_LAGS_FLU = {'temp_c': 4, 'humidity_pct': 8, 'solar_wm2': 8, 'dewpoint_c': 2}
WEATHER_LAGS_DEN = {'temp_c': 0, 'solar_wm2': 4, 'dewpoint_c': 0, 'precip_mm': 0}
```
→ Sau khi thêm USA/CAN vào data, nên **chạy lại SESSION 4 (EDA)** để xác nhận lags còn đúng.

---

## SESSION 5 — Feature Engineering

**Checklist trước khi chạy:**
- [ ] `master_weekly_2010_2019.csv` đã được update
- [ ] CCF lags đã xác nhận (hoặc dùng lại lags cũ một cách có lý do)
- [ ] Xóa feature files cũ: `features_flu_2010_2019.csv`, `features_dengue_2010_2019.csv`

**Kiểm tra output:**
```python
# Sau khi chạy [5.3]
print(f'Flu rows: {flu_feat.shape[0]}')     # kỳ vọng tăng từ 44,035 (có thêm USA/CAN)
print(f'Dengue rows: {dengue_feat.shape[0]}') # kỳ vọng ~1,435 (ít thay đổi)
print(f'NaN trong features: {flu_feat.isnull().sum().sum()}')  # phải = 0
```

---

## SESSION 6 — Model Training

Train + so sánh 4 regressors (XGBoost, LightGBM, RandomForest, Prophet) + 1 classifier (XGBClassifier),
sau đó Optuna tune top 1-2 model.

**Baseline comparison (kỳ vọng so sánh):**
| Model | Flu R² mục tiêu | Dengue R² mục tiêu | Ghi chú |
|---|---|---|---|
| Naive (same-week-last-year) | ~0.0–0.2 | ~0.5–0.7 | Floor — model phải vượt cái này |
| Prophet | ~0.2–0.4 | ~0.6–0.75 | Seasonality baseline |
| XGBoost Regressor | > 0.5 | > 0.79 | Top candidate |
| LightGBM Regressor | > 0.5 | > 0.79 | So sánh với XGBoost |
| Random Forest Regressor | ~0.4–0.5 | ~0.7–0.8 | Robust baseline |

Nếu kết quả **tệ hơn** Prophet → quay lại SESSION 1 kiểm tra data.

---

## SESSION 7 — Validation & Export

**So sánh với baseline:**
| Metric | Baseline | Target |
|---|---|---|
| Influenza R² | 0.152 | > 0.20 |
| Dengue R² | 0.790 | ≥ 0.79 |
| Classification macro-F1 | - | > 0.50 |

---

## Checklist nhanh trước khi train

```
□ master_weekly: NaN weather < 20%?
□ master_weekly: coverage > 130 nước?
□ ERA5 USA Jan < 0°C, Jul > 15°C? (sanity check)
□ inf_cases zero rows ~70-75%?
□ Feature files: không có NaN?
□ CCF lags đã verify với data mới?
```

Nếu tất cả ✅ → proceed to SESSION 6 (Model Training).
