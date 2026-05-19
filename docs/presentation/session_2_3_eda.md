# Session 2–3: Kiểm Tra Chất Lượng & Phân Tích Mùa Vụ

---

## Session 2 — Data Quality Check: "Dữ liệu này có đáng tin không?"

### Tại sao phải làm bước này?

Nhiều người hay bỏ qua bước kiểm tra chất lượng — load data xong rồi train luôn. Đó là sai lầm rất phổ biến. Mình đã từng làm vậy và phải quay lại fix vì model cho kết quả vô lý.

Ở bước này, mình trả lời 3 câu hỏi:
1. **Dữ liệu thiếu ở đâu?** (missing rates)
2. **Dữ liệu có bao phủ đủ quốc gia và năm không?** (coverage)
3. **Có giá trị bất thường nào không?** (outliers, anomalies)

---

### Cell 2.0 — RESTART CELL

```python
flu    = pd.read_csv(FILES['flunet'], low_memory=False)
dengue = pd.read_csv(FILES['dengue'], low_memory=False)
print(f'flu: {flu.shape}')
print(f'dengue: {dengue.shape}')
```

Chỉ load 2 file cần cho session này để tiết kiệm RAM. Nếu đã chạy SESSION 1 và biến còn tồn tại, cell này không bị lỗi — chỉ reload mới nhất từ disk.

---

### Cell 2.1 — FluNet: Missing Rate từng cột

```python
check_cols = ['INF_A', 'INF_B', 'INF_ALL', 'RSV', 'RSV_PROCESSED',
              'PARAINFLUENZA', 'ILI_ACTIVITY', 'SPEC_PROCESSED_NB']
check_cols = [c for c in check_cols if c in flu.columns]
missing_pct = flu[check_cols].isnull().mean().sort_values(ascending=False) * 100

missing_pct.plot(kind='barh', color='salmon', ...)
```

**Output:** Biểu đồ bar chart nằm ngang — cột nào missing nhiều nhất hiện ở trên cùng.

**Kết quả xác nhận các quyết định đã chốt:**

| Cột | Missing Rate | Quyết định |
|-----|-------------|-----------|
| `PARAINFLUENZA` | **~85.5%** | Bỏ hoàn toàn |
| `INF_ALL` | **~44.0%** | Bỏ, dùng `INF_A + INF_B` thay |
| `RSV_PROCESSED` | **~65%** | Bỏ, giữ `RSV` raw |
| `INF_A` | ~12% | Giữ, `fillna(0)` |
| `INF_B` | ~12% | Giữ, `fillna(0)` |

Tại sao `fillna(0)` cho INF_A và INF_B mà không phải interpolate hay median? Vì trong hệ thống giám sát WHO, **tuần không có dữ liệu = quốc gia không gửi báo cáo**. Điều đó thường có nghĩa là không có ca đáng kể — nên 0 là assumption hợp lý nhất trong ngữ cảnh này.

---

### Cell 2.2 — FluNet: Coverage theo năm

```python
coverage = flu.groupby('ISO_YEAR')['COUNTRY_CODE'].nunique().reset_index()

ax.bar(coverage['year'], coverage['n_countries'], color='steelblue', ...)
ax.axvline(TRAIN_START - 0.5, color='green', ls='--', label=f'Train start ({TRAIN_START})')
ax.axvline(TRAIN_END + 0.5, color='red', ls='--', label=f'Train end ({TRAIN_END})')
```

**Output:** Bar chart số quốc gia báo cáo mỗi năm, với 2 đường dọc xanh/đỏ đánh dấu giai đoạn training.

**Phát hiện quan trọng:** Coverage tăng đều từ 2010 (123 quốc gia) lên 167 năm 2019, đỉnh 180 năm 2023. **Đính chính:** Giai đoạn 2020–2021 coverage **KHÔNG GIẢM** (vẫn 166–167 nước, ngang bằng 2019) — quan sát ban đầu rằng "coverage giảm mạnh do COVID" là **sai**. Lý do thực sự để exclude 2020–2021 không phải data quality mà là **confounder dịch tễ**: NPI (giãn cách, khẩu trang) + reporting bias (ưu tiên test COVID hơn flu) khiến số ca cúm giảm ~99% toàn cầu không do thời tiết. Train period 2010–2019 đáng tin cậy vì coverage tốt và không bị COVID disturbance.

---

### Cell 2.3 — OpenDengue: Missing & T_res Distribution

```python
print('dengue_total missing rate:', round(dengue['dengue_total'].isnull().mean()*100, 1), '%')
print('Year range:', dengue['calendar_start_date'].dropna().iloc[0], '...',
      dengue['calendar_start_date'].dropna().iloc[-1])

tres_counts = dengue['T_res'].value_counts()
ax.pie(tres_counts, labels=tres_counts.index, autopct='%1.1f%%', startangle=90,
       colors=['#2ecc71','#3498db','#e74c3c'])
ax.set_title('OpenDengue — T_res Distribution')
```

**Output:**
```
dengue_total missing rate: 0.0 %
Year range: 9/5/2021 ... 7/21/2024
```

Kèm theo pie chart T_res: **Week 77.8% | Month 10.5% | Year 11.7%**

**Giải thích:**

**`missing rate: 0.0%`** trên raw OpenDengue file — không có hàng nào thiếu `dengue_total`. Tuy nhiên sau khi merge vào master_weekly (SESSION 5), missing rate sẽ tăng lên ~88.9% — vì dengue chỉ có ở 41 endemic countries, còn lại để trống.

**`Year range`** xuất ra `9/5/2021 ... 7/21/2024` là `iloc[0]` và `iloc[-1]` — **không phải min/max thời gian**, chỉ là hàng đầu và cuối theo vị trí. OpenDengue thực tế có dữ liệu từ những năm 1990 đến 2024 tùy quốc gia. Để biết range thật cần parse thành datetime và dùng `.min()` / `.max()`.

**T_res 77.8% Week:** Phần lớn dữ liệu đã ở mức tuần — tốt. Chiến lược ở SESSION 5: giữ Week + resample Month → Week, bỏ Year (quá thô).

---

### Cell 2.4 — ERA5: Coverage Check

```python
era5 = pd.read_csv(ERA5_FILE)
print(f'ERA5 shape: {era5.shape}')
print(f'Countries: {era5["iso3"].nunique()}')

missing_era5 = era5.drop(columns=['iso3','iso_year','iso_week']).isnull().mean() * 100
missing_era5 = missing_era5[missing_era5 > 0].sort_values(ascending=False)
```

**Output:** Shape + số quốc gia. Nếu có missing thì vẽ bar chart, nếu không có thì in `"ERA5: khong co missing values"`.

**Kết quả thực tế:**
```
ERA5 shape: (102440, 21)
Countries: 197
ERA5: khong co missing values
```

ERA5 cover đầy đủ **197 quốc gia**, 102,440 rows = 197 × 520 tuần (2010–2019), 21 columns (17 biến khí hậu + các cột định danh iso3/year/week/date). Không có missing values — KD-tree centroid mapping đã xử lý hoàn chỉnh, kể cả các đảo nhỏ. Shape này là base để merge với WHO epidemic data ở SESSION 5.

---

## Session 3 — EDA: Phân Tích Mùa Vụ

### Mục tiêu

Bây giờ mình biết dữ liệu tốt (hoặc biết dữ liệu xấu ở đâu). Bước tiếp theo: **nhìn vào pattern thực tế của dịch bệnh**. Đây là bước quan trọng để chọn features phù hợp sau này.

---

### Cell 3.0 — RESTART CELL + Setup Train Range

```python
flu    = pd.read_csv(FILES['flunet'], low_memory=False)
dengue = pd.read_csv(FILES['dengue'], low_memory=False)

flu_train = flu[flu['ISO_YEAR'].between(TRAIN_START, TRAIN_END)].copy()
flu_train['inf_total'] = flu_train['INF_A'].fillna(0) + flu_train['INF_B'].fillna(0)
print(f'flu_train: {flu_train.shape} | years: {TRAIN_START}-{TRAIN_END}')
```

`TRAIN_START=2010`, `TRAIN_END=2019` đã chốt ở SESSION 0. `flu_train` ở đây dùng riêng cho EDA, không phải feature matrix cuối cùng. `inf_total = INF_A + INF_B` — target chính, INF_ALL bị bỏ do missing 44%.

---

### Cell 3.1 — FluNet: Global Trend & Seasonality

```python
flu_weekly = flu_train.groupby(['ISO_YEAR','ISO_WEEK'])['inf_total'].sum().reset_index()
flu_weekly['time_idx'] = flu_weekly['ISO_YEAR'] + flu_weekly['ISO_WEEK'] / 53
flu_season = flu_train.groupby('ISO_WEEK')['inf_total'].mean().reset_index()

# 2 subplots: time series + by-week average
axes[0].plot(flu_weekly['time_idx'], flu_weekly['inf_total'], ...)
axes[1].bar(flu_season['ISO_WEEK'], flu_season['inf_total'], ...)
```

**Output:** 2 biểu đồ chồng nhau:
- **Trên:** Time series toàn bộ 2010–2019 (số ca theo tuần)
- **Dưới:** Trung bình mỗi tuần ISO trong năm (seasonality pattern)

**Nhìn vào biểu đồ bạn thấy:**
- Trend phẳng (không tăng mạnh) — tốt, data ổn định, không bị confound bởi reporting bias tăng theo năm
- Seasonality rõ: **đỉnh tuần 1–10** (mùa đông bắc bán cầu) — pattern chính model cần học
- Weather features cung cấp signal để predict timing và amplitude của đỉnh này

---

### Cell 3.2 — FluNet: Seasonality 5 Quốc Gia Đại Diện

```python
countries = ['VNM', 'USA', 'GBR', 'BRA', 'AUS']
fig, axes = plt.subplots(1, 5, figsize=(20, 4), sharey=False)

for ax, iso in zip(axes, countries):
    df_c = flu_train[flu_train['COUNTRY_CODE'] == iso]
    season_c = df_c.groupby('ISO_WEEK')['inf_total'].mean()
    ax.bar(season_c.index, season_c.values, ...)
```

**Output:** 5 bar chart ngang, mỗi chart = 1 quốc gia, trục x là ISO week 1–52.

**Pattern khác nhau rõ theo khí hậu:**
- **BRA, AUS** (nam bán cầu): đỉnh tuần 25–35 (tháng 6–8)
- **USA, GBR** (bắc bán cầu ôn đới): đỉnh tuần 1–10 và 45–52 (tháng 12–2)
- **VNM** (nhiệt đới): 2 đỉnh nhỏ, không rõ ràng

**Điều quan trọng:** Model train per-country tự học được sự khác biệt này qua `iso3` encoding và lag features — không cần hardcode hemisphere manually.

---

### Cell 3.3 — Dengue: Filter + Parse Date

```python
dengue_wm = dengue[dengue['T_res'].isin(['Week','Month'])].copy()
dengue_wm['date_parsed'] = pd.to_datetime(dengue_wm['calendar_start_date'], format='mixed', dayfirst=False)
iso_cal = dengue_wm['date_parsed'].dt.isocalendar()
dengue_wm['ISO_YEAR'] = iso_cal.year.astype(int)
dengue_wm['ISO_WEEK'] = iso_cal.week.astype(int)

dengue_train = dengue_wm[dengue_wm['ISO_YEAR'].between(TRAIN_START, TRAIN_END)].copy()
dengue_train['dengue_log'] = np.log1p(dengue_train['dengue_total'])
print(f'dengue_train: {dengue_train.shape}')
print(f'Countries: {dengue_train["ISO_A0"].nunique()}')
```

`format='mixed'` cần thiết vì OpenDengue date không nhất quán (có file dùng `MM/DD/YYYY`, có file dùng `DD/MM/YYYY`). `log1p` được tính ngay ở đây để visualization dùng log scale — `dengue_total` bị dominated bởi Brazil với ~7.15M ca, chiếm **51.4%** tổng global (2010–2019).

---

### Cell 3.4 — Dengue: Trend & Seasonality (Raw vs Log)

```python
# 2x2 subplot grid
axes[0,0].bar(by_year_raw.index, by_year_raw.values, color='coral')   # Raw by Year
axes[0,1].bar(by_week_raw.index, by_week_raw.values, color='coral')   # Raw by ISO Week
axes[1,0].bar(by_year_log.index, by_year_log.values, color='#27ae60') # Log1p by Year
axes[1,1].bar(by_week_log.index, by_week_log.values, color='#27ae60') # Log1p by ISO Week
```

**Output:** 4 biểu đồ trong grid 2×2.

**Đây là khoảnh khắc "aha":**

Hàng trên (raw) — Brazil là đường thẳng khổng lồ, tất cả các nước khác gần như bằng 0. Model chỉ học được Brazil.

Hàng dưới (log1p) — tất cả quốc gia hiện ra rõ ràng, pattern mùa vụ thấy được. By-week log plot thể hiện seasonality thực sự khi không bị Brazil che khuất. **Đây chính xác là lý do mình dùng log1p làm target.**

---

### Cell 3.5 — Dengue: Top 5 Quốc Gia (Loại Brazil)

```python
dengue_no_bra = dengue_train[dengue_train['ISO_A0'] != 'BRA']
top5 = dengue_no_bra.groupby('ISO_A0')['dengue_total'].sum().nlargest(5).index.tolist()

for ax, iso in zip(axes, top5):
    season_c = df_c.groupby('ISO_WEEK')['dengue_total'].mean()
    ax.bar(season_c.index, season_c.values, color='#27ae60', ...)
```

**Output:** 5 bar chart — top 5 quốc gia dengue (không tính Brazil).

**Phát hiện (output thực tế):** Top 5 ex-Brazil: IDN, MEX, THA, LKA, NIC. Peak khác nhau rõ rệt:
- THA tuần 27, LKA tuần 26 → tháng 7 (mùa mưa Đông Nam Á / Nam Á)
- NIC tuần 34 → tháng 8–9 (mùa mưa Trung Mỹ)
- MEX tuần 41 → tháng 10 (cuối mùa mưa Bắc Mỹ nhiệt đới)
- IDN tuần 53 → tháng 12–1 (mùa mưa Indonesia cuối năm — ngược với THA)

Sự đa dạng này xác nhận không thể dùng global model — mỗi quốc gia theo lịch mùa mưa địa phương riêng.

---

### Cell 3.6 — Heatmap Mùa Vụ Việt Nam (Influenza)

```python
vnm_flu = flu_train[flu_train['COUNTRY_CODE'] == 'VNM'][['ISO_YEAR','ISO_WEEK','inf_total']]
pivot = vnm_flu.pivot_table(index='ISO_YEAR', columns='ISO_WEEK',
                             values='inf_total', aggfunc='sum')

sns.heatmap(pivot, cmap='YlOrRd', linewidths=0.3, ...)
```

**Output:** Heatmap Năm × ISO Week — trục x là tuần (1–52), trục y là năm (2010–2019), màu đậm = nhiều ca.

Heatmap Tuần×Năm là cách visualize seasonality hiệu quả nhất. Nếu màu lặp lại theo cột (cùng tuần qua các năm) → pattern ổn định, model có thể học được. Việt Nam thường có **2 đợt nhỏ** trong năm, không rõ ràng như USA/GBR — thách thức hơn cho model so với các nước ôn đới.

---

### Kết thúc Session 2–3 — Bạn đã biết gì?

1. FluNet: cột nào bỏ (`PARAINFLUENZA`, `INF_ALL`, `RSV_PROCESSED`), cột nào giữ (`INF_A`, `INF_B`), fillna như thế nào
2. FluNet: coverage **không giảm** 2020–2021 (vẫn 166–167 nước) — lý do exclude là **NPI/COVID confounder làm pattern flu méo**, không phải data quality
3. ERA5: 158/172 quốc gia (92%), 14 đảo nhỏ bị miss do KD-tree mapping
4. Influenza có mùa vụ rõ ràng, ngược nhau giữa bắc và nam bán cầu
5. Dengue cần log transform vì Brazil dominated 51.4% tổng ca (7.15M / 13.9M ca)
6. Dengue có peak theo khu vực địa lý khác nhau — cần per-country model

Session 4 tiếp theo sẽ giải quyết câu hỏi: **dữ liệu thời tiết từ vệ tinh/mô hình khí quyển được xử lý như thế nào để ra được bảng theo quốc gia?**

---

## Key Insights từ Session 2–3

**1. 3 cột bị bỏ — mỗi cột một lý do khác nhau**
`PARAINFLUENZA` bỏ vì missing 85.5% (không có signal). `INF_ALL` bỏ vì missing 44% và là tổng của INF_A + INF_B — dùng tổng trực tiếp thay thế, không mất thông tin. `RSV_PROCESSED` bỏ vì khác đơn vị với `RSV`, correlation 0.729 cho thấy trùng lặp.

**2. ĐÍNH CHÍNH: Coverage 2020–2021 KHÔNG giảm — lý do exclude là confounder dịch tễ**
Biểu đồ SESSION 2 cho thấy 2020 = 166 nước, 2021 = 167 nước (ngang 2019 = 167). Quan sát cũ "coverage giảm mạnh do COVID" là **sai**. Lý do thực sự để exclude 2020–2021:
- **NPI effects** (giãn cách, khẩu trang, lockdown) → giảm transmission flu artificially
- **Reporting bias** — ca hô hấp ưu tiên test COVID, không test flu → underreporting
- **Pattern méo** — flu 2020 giảm ~99% toàn cầu, không phải do thời tiết (yếu tố confounder phá hỏng correlation giữa weather và cases)
Đây không phải vấn đề data quality (coverage đủ) mà là vấn đề **distribution shift bắt nguồn từ can thiệp y tế công cộng**.

**3. ERA5 cover đầy đủ 197 quốc gia, không missing**
Output thực tế: 102,440 rows = 197 × 520 tuần. Đây là kết quả tốt hơn ước tính ban đầu (154–158 quốc gia) — KD-tree đã xử lý được kể cả các đảo nhỏ.

**4. Brazil dominated 51.4% tổng ca Dengue toàn cầu (7.15M / 13.9M ca)**
Đây là insight quan trọng nhất của SESSION 3 về dengue. Nếu không có log1p, model chỉ học được Brazil và bỏ qua 40 quốc gia còn lại. `log1p` là transform bắt buộc, không phải tùy chọn.

**5. Flu và Dengue có cơ chế mùa vụ khác nhau hoàn toàn**
Flu: driven bởi nhiệt độ → peak mùa đông theo bán cầu (tuần 1–10 bắc, tuần 25–35 nam). Dengue: driven bởi mưa + nhiệt độ, nhưng peak **khác nhau theo từng quốc gia** — THA/LKA peak tuần 26–27 (tháng 7), IDN peak tuần 53 (tháng 12–1), MEX peak tuần 41 (tháng 10), NIC peak tuần 34 (tháng 8–9). Không có một "mùa dengue toàn cầu" thống nhất — mỗi quốc gia theo mùa mưa địa phương riêng. Đây là lý do cần per-country model với weather lag features, và tại sao lag analysis của dengue khác hoàn toàn với flu.
