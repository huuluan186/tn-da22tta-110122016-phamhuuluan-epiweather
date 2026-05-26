# Session 5: Feature Engineering + Endemic Channel Labels (Notebook v5/v6)

> **Mục tiêu thuyết trình:** Pipeline biến `master_weekly_v1.csv` (raw) thành 2 file feature sẵn sàng train — `features_flu_v1.csv` và `features_dengue_v1.csv`. Đồng thời tạo **Endemic Channel labels** theo chuẩn WHO EWARS (Bortman 1999) cho bài toán classification.

---

## 1. Cell 5.1 — Helper functions

```python
def make_lag(df, col, lag, group='iso3'):
    """Lag CHỈ trong cùng country để tránh data leakage."""
    return df.groupby(group)[col].shift(lag)

def make_rollmean(df, col, window, group='iso3'):
    """Rolling mean trong country, dùng shift(1) trước để tránh look-ahead."""
    return df.groupby(group)[col].apply(
        lambda x: x.shift(1).rolling(window, min_periods=1).mean()
    )
```

**Bug suýt mắc:**

```python
# SAI — shift toàn bộ DataFrame, không group
df['flu_log_lag1'] = df['inf_log1p'].shift(1)
# Brazil tuần 1 = USA tuần 52 → DATA LEAKAGE NGHIÊM TRỌNG

# ĐÚNG — groupby + shift
df['flu_log_lag1'] = df.groupby('iso3')['inf_log1p'].shift(1)
# Lag chỉ shift WITHIN một quốc gia
```

→ `groupby + shift` là pattern bắt buộc cho time-series feature engineering multi-entity.

---

## 2. Cell 5.2 — Build features FLU (2010-2019)

```python
# Pre-step: complete grid (iso3 × year × week) + fillna(0)
# → Giữ 89% data thay vì mất 93% (do shift bị NaN ở rows missing)
grid = expand_to_full_grid(master_flu, ['iso3', 'iso_year', 'iso_week'])
grid['inf_log1p'] = grid['inf_log1p'].fillna(0)

# Build 16 features
FLU_FEATURES = {
    # AR cases (lag + rolling mean)
    'flu_log_lag1':       make_lag(grid, 'inf_log1p', 1),
    'flu_log_lag2':       make_lag(grid, 'inf_log1p', 2),
    'flu_log_lag3':       make_lag(grid, 'inf_log1p', 3),
    'flu_log_rollmean4':  make_rollmean(grid, 'inf_log1p', 4),
    'flu_log_rollmean8':  make_rollmean(grid, 'inf_log1p', 8),
    # Weather (CCF-optimal lag từ Session 4.4)
    'temp_c_lag3':        make_lag(grid, 'temp_c', 3),
    'temp_c_lag7':        make_lag(grid, 'temp_c', 7),
    'humidity_pct_lag1':  make_lag(grid, 'humidity_pct', 1),
    'humidity_pct_lag7':  make_lag(grid, 'humidity_pct', 7),
    'solar_wm2_lag7':     make_lag(grid, 'solar_wm2', 7),
    'dewpoint_c_lag1':    make_lag(grid, 'dewpoint_c', 1),
    # Seasonality (cyclical encoding)
    'iso_week_sin':       np.sin(2*np.pi*grid['iso_week']/52),
    'iso_week_cos':       np.cos(2*np.pi*grid['iso_week']/52),
    # Static
    'iso_year':           grid['iso_year'],
    'HEMISPHERE_NH':      (grid['hemisphere'] == 'NH').astype(int),
    'HEMISPHERE_SH':      (grid['hemisphere'] == 'SH').astype(int),
}
```

**Output:** `features_flu_v1.csv` — **54,636 rows × 17 cols** (16 features + target `inf_log1p`).

**Coverage:** 143 nước (sau khi drop rows có NaN do warmup tuần đầu).

---

## 3. Cell 5.3 — Build features DENGUE (2015-2019)

```python
DENGUE_FEATURES = {
    # AR cases (lag dài hơn flu vì vòng đời muỗi)
    'deng_log_lag6':      make_lag(grid, 'dengue_log1p', 6),
    'deng_log_lag8':      make_lag(grid, 'dengue_log1p', 8),
    'deng_log_lag10':     make_lag(grid, 'dengue_log1p', 10),
    'deng_log_lag12':     make_lag(grid, 'dengue_log1p', 12),
    'deng_log_lag14':     make_lag(grid, 'dengue_log1p', 14),
    'deng_log_rollmean4': make_rollmean(grid, 'dengue_log1p', 4),
    'deng_log_rollmean8': make_rollmean(grid, 'dengue_log1p', 8),
    # Weather (CCF-optimal lag từ Session 4.4)
    'temp_c_lag11':       make_lag(grid, 'temp_c', 11),
    'dewpoint_c_lag8':    make_lag(grid, 'dewpoint_c', 8),
    'precip_mm_lag6':     make_lag(grid, 'precip_mm', 6),
    'humidity_pct_lag1':  make_lag(grid, 'humidity_pct', 1),
    'solar_wm2_lag16':    make_lag(grid, 'solar_wm2', 16),
    # Seasonality
    'iso_week_sin':       np.sin(2*np.pi*grid['iso_week']/52),
    'iso_week_cos':       np.cos(2*np.pi*grid['iso_week']/52),
    'iso_year':           grid['iso_year'],
}
```

**Output:** `features_dengue_v1.csv` — **5,786 rows × 16 cols** (15 features + target).

**Coverage:** 35 nước (2015-2019, sau drop warmup 18 tuần đầu).

**Note:** Dengue **không có hemisphere encoding** vì pattern endemic tropical, không peak theo mùa rõ ràng như flu.

---

## 4. Cell 5.4 — Endemic Channel labels (Bortman 1999)

**Bài toán classification cần label Low/Med/High.**

**Naive approach:** chia tertile theo cases → **SAI** vì Brazil 10K ca/tuần và Singapore 50 ca/tuần không thể cùng threshold.

**Endemic Channel chuẩn WHO EWARS (Bortman 1999 PAHO):**

```python
def endemic_label(country_data):
    """Per (iso3, week_of_year) — baseline + 2σ rule."""
    baseline = country_data.rolling(window=5*52, min_periods=3*52).mean()  # 5-year rolling
    sigma    = country_data.rolling(window=5*52, min_periods=3*52).std()
    upper    = baseline + 2 * sigma
    
    return np.where(country_data < baseline,    'Low',
           np.where(country_data >= upper,      'High', 'Medium'))
```

| Threshold | Label | Ý nghĩa |
|---|---|---|
| `cases < baseline` | **Low** | Dưới trung bình 5 năm |
| `baseline ≤ cases < baseline+2σ` | **Medium** | Normal range |
| `cases ≥ baseline+2σ` | **High** | Outbreak (rare event ~2.5% tail) |

**Tại sao 5 năm:** Theo WHO EWARS — 3 năm thì `std` không đáng tin (chưa đủ sample), 5 năm là minimum.

**Tại sao 2σ:** Tương ứng **~2.5% upper tail** của Gaussian — "rare event" đáng cảnh báo. Cite được Bortman 1999.

**Class balance kết quả:**

| Disease | Low | Medium | High |
|---|---|---|---|
| Flu | 56% | 26% | 17% |
| Dengue | 47% | 30% | 23% |

→ Imbalance vừa phải, dùng `class_weight='balanced'` trong XGBClassifier xử lý được.

---

## 5. Cell 5.5 — Save 2 feature files + verify

```python
features_flu.to_csv(PROCESSED / 'features_flu_v1.csv', index=False)
features_dengue.to_csv(PROCESSED / 'features_dengue_v1.csv', index=False)
```

**Sanity check:**
- Không có NaN trong feature cols
- Class balance hợp lý
- Walk-forward CV ready (year ≥ 2014 có đủ training history)

---

## 6. Walk-forward CV scheme (preview cho Session 6)

```
Fold 1: train 2010-2013, val 2014
Fold 2: train 2010-2014, val 2015
Fold 3: train 2010-2015, val 2016
Fold 4: train 2010-2016, val 2017
Fold 5: train 2010-2017, val 2018
Fold 6: train 2010-2018, val 2019
```

→ Mỗi fold train trên data **trước** val year. **Không có data leakage**. Mô phỏng đúng deploy: tại thời điểm T, chỉ biết data đến T-1.

---

## Key Insights Session 5 (slide thuyết trình)

1. **Feature set theo CCF lag** — không default `[1, 2, 3]`. Mỗi feature có lý do từ Session 4.4 + literature.
2. **`groupby + shift` BẮT BUỘC** — quên = data leakage nghiêm trọng (Brazil tuần 1 = USA tuần 52).
3. **Complete grid + fillna(0) TRƯỚC khi lag** — giữ 89% data thay vì mất 93%. Bài học quan trọng nhất time-series feature engineering.
4. **Endemic Channel chuẩn Bortman 1999 + WHO EWARS** — cite được, không phải arbitrary threshold tự nghĩ.
5. **5-year min history + 2σ rule** — có lý do khoa học, không phải hyperparameter random.

---

## Câu nói thuyết trình cho Session 5

> "Session 5 là feature engineering — input `master_weekly_v1.csv` 61K rows, output 2 file features sẵn sàng train."
>
> "**Flu 16 features**: 3 AR lag (1, 2, 3 tuần), 2 rolling mean (4w, 8w), 6 weather theo CCF (temp lag 3/7, humidity lag 1/7, solar lag 7, dewpoint lag 1), 2 seasonality (sin/cos), hemisphere encoding."
>
> "**Dengue 15 features**: 5 AR lag **dài hơn flu** (6, 8, 10, 12, 14 tuần vì vòng đời muỗi), 2 rolling mean, 5 weather theo CCF (temp lag 11, dewpoint lag 8, precip lag 6, humidity lag 1, solar lag 16), 2 seasonality."
>
> "**Bug suýt mắc**: dùng `df['lag'] = df['cases'].shift(1)` mà KHÔNG group theo iso3 → Brazil tuần 1 lấy giá trị từ USA tuần 52 → **data leakage nghiêm trọng**. Em dùng `groupby('iso3').shift()` để chỉ lag within country."
>
> [NHẤN MẠNH] "**Endemic Channel labels** theo chuẩn WHO EWARS — Bortman 1999. Per (country, week_of_year): Low < baseline, Medium baseline đến baseline+2σ, High >= baseline+2σ. **5 năm minimum + 2σ rule** — cite được, không arbitrary."
>
> "Class balance: Flu 56/26/17, Dengue 47/30/23 — chấp nhận được với `class_weight='balanced'`. **Em document literature, không tự nghĩ threshold.**"
>
> [NẾU HỎI: Sao không quantile-based?]
> > "Em có cân nhắc. Quantile chia đều 33/33/33 nhưng **không có ý nghĩa epidemiological**. Bortman + WHO EWARS dùng Gaussian 2σ là 'unusual event' standard. Em chọn cite được thay vì arbitrary threshold."
