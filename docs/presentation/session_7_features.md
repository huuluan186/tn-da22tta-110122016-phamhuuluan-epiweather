# Session 7: Feature Engineering

---

## Feature Engineering là gì và tại sao quan trọng?

Model XGBoost không "hiểu" rằng "ca cúm tuần này liên quan đến ca cúm tuần trước". Mình phải **tự tay tạo ra các cột** thể hiện mối quan hệ đó. Đây là feature engineering — biến dữ liệu thô thành ngôn ngữ mà model có thể học.

Một feature tốt = model đơn giản hơn + kết quả tốt hơn.

---

## Cell 7.0 — Idempotent Guard + Load Master

```python
master = pd.read_csv(MASTER_FILE)

if FEATURES_FLU_FILE.exists() and FEATURES_DENGUE_FILE.exists():
    print("✓ Feature files da ton tai — skip feature engineering")
    features_flu    = pd.read_csv(FEATURES_FLU_FILE)
    features_dengue = pd.read_csv(FEATURES_DENGUE_FILE)
    print(f"  flu: {features_flu.shape} | dengue: {features_dengue.shape}")
else:
    print("Chua co feature files — se tao moi")
```

Feature engineering cho toàn bộ master dataset mất khoảng **10–15 phút**. Guard này đảm bảo chỉ chạy một lần. Nếu muốn regenerate (ví dụ: thêm feature mới), xóa file CSV rồi chạy lại.

---

## Cell 7.0b — Tạo Country Climate Zones

```python
# Tạo bảng phân loại climate zone dựa trên centroid latitude
CLIMATE_FILE = PROCESSED / 'country_climate_zones.csv'

if CLIMATE_FILE.exists():
    climate_df = pd.read_csv(CLIMATE_FILE)
else:
    world = gpd.read_file(WORLD_FILE)  # Natural Earth 50m shapefile
    world['centroid_lat'] = world.geometry.centroid.y

    def get_hemisphere(lat): return 'S' if lat < 0 else 'N'
    def get_climate_zone(lat):
        a = abs(lat)
        if a < 23.5:  return 'tropical'
        elif a < 60:  return 'temperate'
        else:         return 'cold'

    climate_df['hemisphere_enc']   = (climate_df['hemisphere'] == 'S').astype(int)
    climate_df['climate_zone_enc'] = climate_df['climate_zone'].map(
        {'tropical': 0, 'temperate': 1, 'cold': 2})
    climate_df.to_csv(CLIMATE_FILE, index=False)
```

Tạo bảng phân loại climate zone từ centroid latitude:
- `hemisphere_enc`: 0 = Bắc bán cầu, 1 = Nam bán cầu
- `climate_zone_enc`: 0 = tropical (|lat| < 23.5°), 1 = temperate (< 60°), 2 = cold (≥ 60°)

Hai features này giúp model phân biệt flu season bán cầu Nam (peak tháng 6–8) với Bắc bán cầu (peak tháng 11–1) và phân biệt tropical vs temperate pattern.

---

## Cell 7.1 — Sort Data + Setup

```python
master_sorted = master.sort_values(['iso3', 'iso_year', 'iso_week']).reset_index(drop=True)
df_feat = master_sorted.copy()
df_feat['inf_log1p'] = np.log1p(df_feat['inf_cases'])

# Merge hemisphere + climate zone
climate_df = pd.read_csv(CLIMATE_FILE)
df_feat = df_feat.merge(climate_df[['iso3','hemisphere_enc','climate_zone_enc']],
                        on='iso3', how='left')
```

**PHẢI sort theo `[iso3, iso_year, iso_week]` trước khi tạo lag features.** Nếu không sort, `shift(1)` sẽ lấy nhầm row từ quốc gia khác — tuần cuối cùng của ABW sẽ làm lag cho tuần đầu của AGO. Dùng groupby trong bước tiếp theo đảm bảo an toàn tuyệt đối.

`inf_log1p = np.log1p(inf_cases)` — tính target ở đây để dùng làm lag source. Lý do dùng log1p: nén phân phối, cân bằng contribution của mọi quốc gia khi tính AR features.

---

## Cell 7.1b — WHO Region Encoding

```python
meta_flu = pd.read_csv(RAW / 'VIW_FNT.csv',
                       usecols=['COUNTRY_CODE', 'WHOREGION'],
                       low_memory=False)
iso_region = (meta_flu
              .drop_duplicates('COUNTRY_CODE')
              .rename(columns={'COUNTRY_CODE': 'iso3', 'WHOREGION': 'who_region'}))

REGION_MAP = {'AFR': 0, 'AMR': 1, 'EMR': 2, 'EUR': 3, 'SEAR': 4, 'WPR': 5}
iso_region['who_region_enc'] = (iso_region['who_region']
                                .map(REGION_MAP)
                                .fillna(-1).astype(int))

df_feat = df_feat.merge(iso_region[['iso3', 'who_region_enc']],
                        on='iso3', how='left')
df_feat['who_region_enc'] = df_feat['who_region_enc'].fillna(-1).astype(int)
```

**Tại sao cần WHO region:**

Sin/cos tuần capture **khi nào** trong năm. WHO region capture **ở đâu** trên thế giới. Hai features này bổ sung cho nhau.

Ví dụ: tuần 6 (cuối tháng 1) — sin/cos như nhau cho USA và AUS. Nhưng USA (EUR region) đang giữa mùa đông, AUS (WPR) đang giữa mùa hè. WHO region giúp model phân biệt hai trường hợp này.

**Tại sao lấy từ FluNet `WHOREGION` column** thay vì hard-code? Vì cùng nguồn với dữ liệu bệnh, đảm bảo nhất quán 100% với country coverage. `WHO_REGION_LOOKUP` dict được giữ lại để dùng ở risk classification [9.3b].

**Coverage:** 172/172 quốc gia — không missing.

---

## Cell 7.2 — Autoregressive (AR) Lag Features: Influenza

```python
for lag in LAG_FLU:  # [1, 2, 3]
    col = f'inf_lag{lag}w'
    df_feat[col] = df_feat.groupby('iso3')[TARGET_FLU].shift(lag)

flu_lag_cols = [f'inf_lag{l}w' for l in LAG_FLU]
```

Đây là nhóm features **quan trọng nhất** — chiếm ~70% feature importance trong XGBoost Flu.

**Tại sao groupby iso3 trước khi shift?** Nếu shift toàn bộ DataFrame, giá trị cuối cùng của ABW sẽ trở thành giá trị đầu tiên của AGO (quốc gia tiếp theo trong alphabet). Mình phải shift **trong phạm vi từng quốc gia riêng**.

NaN ở lag đầu của mỗi quốc gia là bình thường — sẽ được dropna ở bước cuối [7.7].

---

## Cell 7.3 — AR Lag Features: Dengue

```python
for lag in LAG_DENGUE:  # [6, 8, 10, 12, 14]
    col = f'dengue_lag{lag}w'
    df_feat[col] = df_feat.groupby('iso3')[TARGET_DENGUE].shift(lag)
```

**Tại sao Dengue dùng lag 6, 8, 10, 12, 14 thay vì 1, 2, 3?**

Dengue có **chu kỳ lây truyền chậm hơn** và mùa dịch kéo dài nhiều tháng. Lag 6–14 tuần capture được "bộ nhớ dài hạn" của dịch — nếu 3 tháng trước có dịch lớn, nguy cơ hiện tại vẫn còn cao. 5 lag features giúp model học được shape của signal ở nhiều độ trễ khác nhau.

---

## Cell 7.4 — Rolling Mean Features

```python
for window in [4, 8]:
    df_feat[f'inf_roll{window}w'] = (
        df_feat.groupby('iso3')[TARGET_FLU]
        .transform(lambda x: x.shift(1).rolling(window, min_periods=2).mean())
    )
    df_feat[f'dengue_roll{window}w'] = (
        df_feat.groupby('iso3')[TARGET_DENGUE]
        .transform(lambda x: x.shift(1).rolling(window, min_periods=2).mean())
    )
```

**Hai điểm quan trọng:**

**1. `.shift(1)` trước khi rolling:** Đây là để tránh **data leakage**. Nếu rolling mean bao gồm giá trị của tuần hiện tại (t), model sẽ "biết trước" target trong quá trình training. `.shift(1)` đảm bảo rolling mean chỉ dùng thông tin từ tuần t-1 trở về trước.

**2. Tại sao cần rolling mean khi đã có AR lags?** AR lag capture giá trị cụ thể tuần t-1, t-2 — có thể bị ảnh hưởng bởi outlier. Rolling mean smooths out noise — nếu 4 tuần qua trung bình vẫn cao, đó là signal ổn định hơn.

---

## Cell 7.5 — Weather Lag Features (từ CCF Session 6)

```python
WEATHER_LAGS_FLU = {'temp_c': 4, 'humidity_pct': 8, 'solar_wm2': 8, 'dewpoint_c': 2}
WEATHER_LAGS_DEN = {'temp_c': 0, 'humidity_pct': 2, 'dewpoint_c': 0, 'precip_mm': 0}

for var, lag in WEATHER_LAGS_FLU.items():
    if lag == 0:
        df_feat[f'{var}_flu_lag0w'] = df_feat[var]
    else:
        df_feat[f'{var}_flu_lag{lag}w'] = df_feat.groupby('iso3')[var].shift(lag)

for var, lag in WEATHER_LAGS_DEN.items():
    if lag == 0:
        df_feat[f'{var}_dengue_lag0w'] = df_feat[var]
    else:
        df_feat[f'{var}_dengue_lag{lag}w'] = df_feat.groupby('iso3')[var].shift(lag)
```

Mỗi biến có **1 lag tối ưu riêng** từ CCF Session 6 — không cross-product nhiều lags.

**Flu — 4 weather features:**
- `temp_c_flu_lag4w`: nhiệt độ 4 tuần trước (CCF peak r = −0.41)
- `humidity_pct_flu_lag8w`: độ ẩm 8 tuần trước
- `solar_wm2_flu_lag8w`: bức xạ mặt trời 8 tuần trước (mạnh nhất)
- `dewpoint_c_flu_lag2w`: dewpoint 2 tuần trước

**Dengue — 4 weather features (lag 0–2):**
- `temp_c_dengue_lag0w`: nhiệt độ tức thời
- `humidity_pct_dengue_lag2w`: độ ẩm 2 tuần trước
- `dewpoint_c_dengue_lag0w`: dewpoint tức thời
- `precip_mm_dengue_lag0w`: lượng mưa tức thời

**Lưu ý:** Phiên bản cũ thêm cả 17 biến raw + các lag features — gây multicollinearity (temp_c vs temp_min vs temp_max vs dewpoint_c). Phiên bản mới chỉ giữ lag features từ CCF — mỗi biến đúng 1 lag tối ưu — gọn và diễn giải được rõ ràng.

---

## Cell 7.6 — Seasonal Encoding

```python
df_feat['sin_week'] = np.sin(2 * np.pi * df_feat['iso_week'] / 52)
df_feat['cos_week'] = np.cos(2 * np.pi * df_feat['iso_week'] / 52)
df_feat['quarter']  = ((df_feat['iso_week'] - 1) // 13 + 1).clip(1, 4)
```

**Tại sao sin/cos thay vì dùng số tuần trực tiếp (1–52)?**

Nếu dùng số tuần trực tiếp, model sẽ thấy tuần 52 và tuần 1 "cách nhau" 51 đơn vị — trong khi thực tế chúng liên tiếp nhau (cuối năm → đầu năm mới). Sin/cos giải quyết vấn đề này: tuần 52 và tuần 1 cho giá trị sin/cos gần nhau, phản ánh **tính liên tục của mùa vụ**.

`quarter` là feature bổ sung — chia năm thành 4 quý (Q1: tuần 1–13, ...). Granularity thô hơn, có thể capture macro-seasonal trend.

---

## Cell 7.7 — Split thành 2 feature sets và lưu (Force Overwrite)

```python
base_id_cols = ['iso3', 'iso_year', 'iso_week']

flu_feature_cols = (
    flu_lag_cols +
    ['inf_roll4w', 'inf_roll8w'] +
    weather_lag_flu_cols +
    ['sin_week', 'cos_week', 'quarter'] +
    ['who_region_enc']
)

dengue_feature_cols = (
    dengue_lag_cols +
    ['dengue_roll4w', 'dengue_roll8w'] +
    weather_lag_den_cols +
    ['sin_week', 'cos_week', 'quarter'] +
    ['who_region_enc']
)

features_flu = (
    df_feat[base_id_cols + flu_feature_cols + [TARGET_FLU]]
    .dropna(subset=flu_feature_cols + [TARGET_FLU])
    .query(f'iso_year >= @TRAIN_START and iso_year <= @TRAIN_END')
    .copy()
)

features_dengue = (
    df_feat[base_id_cols + dengue_feature_cols + [TARGET_DENGUE]]
    .dropna(subset=dengue_feature_cols + [TARGET_DENGUE])
    .query(f'iso_year >= @TRAIN_START and iso_year <= @TRAIN_END and dengue_log1p > 0')
    .copy()
)

# Force overwrite — data mới từ SESSION 4, phải re-build
features_flu.to_csv(FEATURES_FLU_FILE, index=False)
features_dengue.to_csv(FEATURES_DENGUE_FILE, index=False)
```

**Lưu ý quan trọng:** Cell này **force overwrite** (không có idempotent guard) vì data mới từ SESSION 4 và lag features mới từ [7.5] khác hoàn toàn phiên bản trước. Bỏ `WEATHER_VARS` raw (17 biến lag0) khỏi feature set để tránh multicollinearity.

**Dengue filter `dengue_log1p > 0`:** Chỉ giữ các hàng có dịch thực sự — hàng = 0 là quốc gia non-endemic, không có tín hiệu để học.

**Output kỳ vọng:**
```
Flu features: (~44,000 rows, ~16 columns)
  13 features + 3 ID cols + 1 target
Dengue features: (~1,400 rows, ~18 columns)
  15 features + 3 ID cols + 1 target
```

**Tại sao Dengue ít rows hơn nhiều?** Chỉ 41 quốc gia endemic, lag tới 14 tuần (mất 14 hàng đầu mỗi nước), filter `> 0` loại bỏ tuần không có dịch.

---

## Tổng kết: Feature Set Cuối Cùng

**Flu (12 features):**
- AR lags: `inf_lag1w`, `inf_lag2w`, `inf_lag3w`
- Rolling: `inf_roll4w`, `inf_roll8w`
- Weather (CCF-optimal): `temp_c_flu_lag4w`, `humidity_pct_flu_lag8w`, `solar_wm2_flu_lag8w`, `dewpoint_c_flu_lag2w`
- Seasonal: `sin_week`, `cos_week`, `quarter`
- Geographic: `who_region_enc`

**Dengue (14 features):**
- AR lags: `dengue_lag6w`, `dengue_lag8w`, `dengue_lag10w`, `dengue_lag12w`, `dengue_lag14w`
- Rolling: `dengue_roll4w`, `dengue_roll8w`
- Weather: `temp_c_dengue_lag0w`, `humidity_pct_dengue_lag2w`, `dewpoint_c_dengue_lag0w`, `precip_mm_dengue_lag0w`
- Seasonal: `sin_week`, `cos_week`, `quarter`
- Geographic: `who_region_enc`

Session 8 tiếp theo: **huấn luyện model từ 2 file CSV này**.

---

## Key Insights từ Session 7

**1. `groupby('iso3')` trước `shift()` là critical — không phải tiểu tiết**
Nếu shift toàn bộ DataFrame, tuần cuối của Albania trở thành tuần đầu của Algeria — cross-country leakage hoàn toàn. Model sẽ học được pattern giả tạo (ảnh hưởng xuyên quốc gia) và cho kết quả tốt trong training nhưng vô nghĩa trong thực tế. Bug này khó debug vì metric vẫn có vẻ ổn.

**2. `.shift(1)` trước rolling mean là nguyên tắc phòng chống data leakage**
Rolling mean tính trung bình 4 tuần — nếu bao gồm tuần hiện tại (t), model "biết" một phần target khi training. `.shift(1)` đẩy window về t-4 đến t-1. Không làm bước này, R² training sẽ inflate và không phản ánh thực tế.

**3. sin/cos tuần giải quyết tính liên tục thời gian vòng lặp**
Nếu dùng số tuần 1–52 thẳng, model thấy tuần 52 và tuần 1 "xa nhau 51 bậc". Trong thực tế chúng liên tiếp. Sin/cos map tuần 52 và tuần 1 vào 2 điểm gần nhau trên vòng tròn đơn vị — model học được tính seasonal liên tục.

**4. Dengue 1,435 rows vs Flu 44,000 rows — imbalanced dataset size**
Flu có nhiều quốc gia × nhiều tuần non-zero. Dengue chỉ 41 quốc gia × tuần có dịch × filter `>0` × mất 14 hàng đầu (lag tối đa). Sự chênh lệch này giải thích tại sao Dengue không chạy Optuna (overfitting risk cao trên dataset nhỏ).

**5. AR features sẽ dominate feature importance — đây là thiết kế có chủ ý**
Khi viết features, mình đặt AR lags làm nhóm đầu tiên. Model XGBoost với AR lags thực chất là "AR model với seasonal correction từ weather". Weather không directly predict ca bệnh — nó modulate timing và amplitude của AR trend. Kết quả session 8 sẽ confirm điều này.
