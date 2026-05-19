# Session 6: Phân Tích Độ Trễ Thời Tiết → Dịch Bệnh

---

## Câu hỏi trung tâm của session này

**"Thời tiết tuần này ảnh hưởng đến số ca bệnh tuần nào?"**

Nghe đơn giản, nhưng đây là câu hỏi khoa học rất thực chất. Virus cúm không xuất hiện ngay khi nhiệt độ giảm — cần có **thời gian ủ bệnh**, thời gian lây truyền, thời gian tích lũy trong cộng đồng. Muỗi Aedes không sinh sản ngay khi trời mưa — cần 1–2 tuần để trứng nở, lên ấu trùng, thành muỗi trưởng thành.

Nếu mình dùng lag sai (ví dụ: dùng nhiệt độ tuần này để dự báo ca bệnh tuần này = lag 0), model sẽ **capture noise thay vì signal thật**.

---

## Cell 6.0 — RESTART CELL: Load Master, Filter Train Sets

```python
master = pd.read_csv(MASTER_FILE)

flu_train = master[
    (master['iso_year'] >= TRAIN_START) &
    (master['iso_year'] <= TRAIN_END) &
    (master[TARGET_FLU].notna())
].copy()

dengue_train = master[
    (master['iso_year'] >= TRAIN_START) &
    (master['iso_year'] <= TRAIN_END) &
    (master[TARGET_DENGUE] > 0)
].copy()

print(f"flu_train: {flu_train.shape}")
print(f"dengue_train: {dengue_train.shape}")
```

Load lại data từ CSV để đảm bảo session independence. Filter `dengue_log1p > 0` loại bỏ các tuần không có dịch, giữ lại signal thực sự.

---

## Cell 6.1 — Disease Cross-Correlation Heatmap

```python
disease_cols = ['inf_cases', 'rsv_cases', 'dengue_total', 'dengue_log1p']
corr_disease = master[disease_cols].corr()

sns.heatmap(corr_disease, annot=True, fmt='.2f', cmap='coolwarm', center=0, vmin=-1, vmax=1)
ax.set_title('Disease cross-correlation (lag=0)')
```

Heatmap correlation giữa các bệnh — Influenza, RSV, Dengue. Kỳ vọng: Influenza và RSV có seasonal overlap (mùa đông), trong khi Dengue không correlate với các bệnh hô hấp.

---

## Cell 6.2 — Weather × Influenza Correlation (Lag=0)

```python
weather_inf_corr = flu_train[WEATHER_VARS + [TARGET_FLU]].corr()[[TARGET_FLU]].drop(TARGET_FLU)
weather_inf_corr = weather_inf_corr.sort_values(TARGET_FLU, ascending=False)

sns.heatmap(weather_inf_corr, annot=True, fmt='.2f', cmap='RdYlBu_r',
            center=0, vmin=-1, vmax=1)
ax.set_title('Weather x Influenza — Correlation (lag=0)')
```

**Kết quả tương quan tức thời (lag=0):**
- `temp_c`: âm tính mạnh — mùa đông lạnh, nhiều cúm
- `solar_wm2`: âm tính — ít nắng tử ngoại, virus sống lâu hơn
- `humidity_pct`: tương quan dương — ngược với trực giác (độ ẩm cao giúp aerosol lơ lửng lâu hơn ở vùng nhiệt đới)
- `precip_mm`: gần 0 — mưa ít liên quan đến cúm

Nhưng đây là lag=0. Liệu lag khác có correlation cao hơn không?

---

## Cell 6.3 — CCF: Influenza vs Temp & Humidity (Lag 0–8)

```python
def lag_corr(series_x, series_y, max_lag=12):
    return [series_x.shift(lag).corr(series_y) for lag in range(0, max_lag + 1)]

flu_weekly = flu_train.groupby(['iso_year','iso_week'])[[TARGET_FLU,'temp_c','humidity_pct']].mean()
lags = list(range(0, 9))
corr_temp  = lag_corr(flu_weekly['temp_c'], flu_weekly[TARGET_FLU], max_lag=8)
corr_humid = lag_corr(flu_weekly['humidity_pct'], flu_weekly[TARGET_FLU], max_lag=8)

# Bar chart: màu đỏ = âm tính, xanh = dương tính
for lag in lags:
    ax.bar(lag, corr, color='red' if corr < 0 else 'blue')
```

**Nhìn vào đường CCF của `temp_c` với `inf_log1p`:**
- Lag=0: corr = khoảng −0.31
- Lag=2: corr tăng dần
- **Lag=4: corr = PEAK** ← điểm cao nhất

→ **Nhiệt độ tuần T có correlation cao nhất với ca cúm tuần T+4.**

**Lý giải sinh học:** Nhiệt độ thấp → virus sống lâu trong không khí → lây nhiễm tăng → sau ~1 tuần ủ bệnh + ~3 tuần lây truyền và tích lũy trong cộng đồng → đỉnh ca bệnh. Tổng ~4 tuần.

**CCF tối ưu cho Flu:**

| Biến thời tiết | Lag tối ưu | Giải thích |
|---------------|-----------|-----------|
| `temp_c` | **4 tuần** | Nhiệt độ thấp → virus sống lâu → ủ bệnh → lây truyền |
| `humidity_pct` | **8 tuần** | Độ ẩm tác động dài hạn hơn qua nhiều thế hệ lây truyền |
| `solar_wm2` | **8 tuần** | Tia UV diệt khuẩn — ít nắng cuối thu → dịch đỉnh đầu đông |
| `dewpoint_c` | **2 tuần** | Điểm sương phản ánh điều kiện aerosol tức thì hơn |

---

## Cell 6.4 — CCF: Dengue vs Precip & Temp (Lag 0–16)

```python
dengue_weekly = dengue_train.groupby(['iso_year','iso_week'])[[TARGET_DENGUE,'precip_mm','temp_c']].mean()
lags_d = list(range(0, 17))
corr_precip = lag_corr(dengue_weekly['precip_mm'], dengue_weekly[TARGET_DENGUE], max_lag=16)
corr_temp_d = lag_corr(dengue_weekly['temp_c'], dengue_weekly[TARGET_DENGUE], max_lag=16)

# Vùng highlight lag 6-14 (LAG_DENGUE zone)
ax.axvspan(6, 14, alpha=0.12, color='green', label='LAG_DENGUE zone')
```

Dengue phân tích lag tới **16 tuần** — xa hơn nhiều so với cúm (8 tuần). Vì mosquito breeding cycle chậm hơn cơ chế lây qua đường hô hấp.

**CCF tối ưu cho Dengue:**

| Biến thời tiết | Lag tối ưu | Giải thích |
|---------------|-----------|-----------|
| `precip_mm` | **0 tuần** | Mưa hiện tại đã tích lũy từ tuần trước → nước đọng hiện tại |
| `temp_c` | **0 tuần** | Nhiệt độ ảnh hưởng trực tiếp tốc độ sinh sản của muỗi |
| `humidity_pct` | **2 tuần** | Độ ẩm tác động qua chu kỳ sinh sản muỗi (~2 tuần) |
| `dewpoint_c` | **0 tuần** | Liên quan trực tiếp với điều kiện hơi nước tạo ổ muỗi |

Dengue có lag ngắn (0–2 tuần) vì **muỗi phản ứng nhanh** với điều kiện thời tiết, trong khi cúm cần thời gian tích lũy lây truyền trong cộng đồng (~4–8 tuần).

---

## Cell 6.5 — Summary Heatmap: Top Weather Vars × Lag Points × 2 Diseases

```python
top_vars = ['temp_c', 'humidity_pct', 'precip_mm', 'solar_wm2', 'dewpoint_c']
lag_points = [0, 2, 4, 8, 12]

for dis_name, df in disease_map.items():
    weekly = df.groupby(['iso_year','iso_week'])[top_vars + [dis_name]].mean()
    corr_mat = []
    for var in top_vars:
        row = [weekly[var].shift(lag).corr(weekly[dis_name]) for lag in lag_points]
        corr_mat.append(row)
    sns.heatmap(corr_df, annot=True, fmt='.2f', cmap='RdYlBu_r', center=0, vmin=-0.6, vmax=0.6)
```

**Output:** 2 heatmap cạnh nhau (5 biến × 5 lag points) cho Flu và Dengue.

Bảng này là **scientific justification** cho toàn bộ feature engineering ở Session 7:
- Influenza: signal rõ nhất ở lag 2–4 tuần với `temp_c`, lag 8 với `humidity_pct`, `solar_wm2`
- Dengue: signal rõ nhất ở lag 0–2 tuần với `precip_mm`, `temp_c`

---

## Tóm tắt Lag Features Sẽ Dùng

**Cho Flu:**
```
temp_c_flu_lag4w       = temp_c shifted 4 weeks
humidity_pct_flu_lag8w = humidity_pct shifted 8 weeks
solar_wm2_flu_lag8w    = solar_wm2 shifted 8 weeks
dewpoint_c_flu_lag2w   = dewpoint_c shifted 2 weeks
```

**Cho Dengue:**
```
temp_c_dengue_lag0w        = temp_c (current week)
humidity_pct_dengue_lag2w  = humidity_pct shifted 2 weeks
dewpoint_c_dengue_lag0w    = dewpoint_c (current week)
precip_mm_dengue_lag0w     = precip_mm (current week)
```

Các features này sẽ được tạo ra trong Session 7 (Feature Engineering).

---

## Kết thúc Session 6

Bạn vừa thấy mình không chọn lag dựa trên "cảm giác" hay đọc paper rồi copy — mình **tính toán từ dữ liệu thực tế** của project này. CCF analysis là bằng chứng định lượng cho mỗi lag được chọn. Đây là điểm mạnh của pipeline: **data-driven lag selection**, không phải rule of thumb.

---

## Key Insights từ Session 6

**1. Flu lag 4 tuần, Dengue lag 0 tuần — hai cơ chế sinh học hoàn toàn khác nhau**
Cúm lây qua đường hô hấp: nhiệt độ thấp → virus sống lâu → ủ bệnh 1 tuần → lây lan 3 tuần → tổng 4 tuần. Dengue qua muỗi Aedes: mưa hiện tại tạo nước đọng ngay lập tức → muỗi sinh sản → lag gần 0. Sự khác biệt này justify tại sao hai model cần feature set hoàn toàn riêng.

**2. Humidity lag 8 tuần cho flu — tác động dài hạn qua nhiều thế hệ lây truyền**
Đây là insight không intuitive. Mình kỳ vọng lag 2–3 tuần như nhiệt độ, nhưng CCF cho thấy peak ở 8 tuần. Lý giải: độ ẩm tác động qua khả năng tồn tại của aerosol — ảnh hưởng tích lũy qua nhiều thế hệ lây, không phải tức thời.

**3. Dengue humidity lag 2 tuần — phản ánh chu kỳ sinh sản muỗi**
Mưa tạo nước đọng ngay → trứng muỗi sau ~2 tuần nở thành muỗi trưởng thành. Lag 2 tuần của humidity khớp chính xác với chu kỳ sinh học này — CCF và sinh học đồng thuận.

**4. Solar radiation lag 8 tuần cho flu — mechanism tia UV diệt khuẩn**
Ít nắng cuối thu → tia UV giảm → virus sống lâu trong môi trường → tích lũy dần → đỉnh dịch đầu đông. 8 tuần lag phản ánh thời gian từ "điều kiện tích lũy" đến "đỉnh dịch".

**5. Data-driven lag không phải lúc nào cũng khớp với literature**
Một số paper dùng lag cố định (ví dụ: tất cả biến lag 4 tuần). Cách của mình — tính CCF từng biến riêng — cho thấy mỗi biến có optimal lag khác nhau. Đây là điểm có thể nhấn mạnh khi báo cáo phương pháp.
