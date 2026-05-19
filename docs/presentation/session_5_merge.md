# Session 5: Ghép 3 Bộ Dữ Liệu Thành Một Bảng Duy Nhất

---

## Tại sao cần Session này?

Nhìn lại những gì đã có sau Session 1–4:

- **FluNet (WHO):** 172 quốc gia × 10 năm — mỗi hàng là 1 quốc gia, 1 tuần, số ca cúm
- **OpenDengue:** 41 quốc gia × 10 năm — mỗi hàng là 1 quốc gia, 1 tuần, số ca dengue
- **ERA5 (ECMWF):** 197 quốc gia × 10 năm — mỗi hàng là 1 quốc gia, 1 tuần, 17 biến thời tiết

Ba bảng riêng biệt. Model không thể học từ 3 bảng rời — nó cần **1 bảng duy nhất** mà mỗi hàng chứa đầy đủ: thông tin quốc gia, tuần, số ca bệnh, và điều kiện thời tiết tương ứng.

Session 5 làm đúng 1 việc: **ghép 3 bảng thành 1** theo khóa chung `(iso3, iso_year, iso_week)`.

Output: `master_weekly_2010_2019.csv` — file quan trọng nhất của toàn bộ dự án. Mọi session từ 6 trở đi đều đọc từ file này.

---

## Cell 5.0 — Kiểm tra xem đã có file chưa

```python
if MASTER_FILE.exists():
    master = pd.read_csv(MASTER_FILE)
    print(f'master_weekly da co: {MASTER_FILE.name}')
    print(f'Shape: {master.shape}')
    print(f'Countries: {master["iso3"].nunique()} | Years: {master["iso_year"].min()}-{master["iso_year"].max()}')
    print(f'Columns: {list(master.columns)}')
    print('SESSION 5 hoan thanh - chuyen sang SESSION 6')
else:
    print('master_weekly chua co - can chay tu [5.1]')
```

Giống như các session trước, bước đầu tiên luôn là kiểm tra file đã tồn tại chưa. Nếu rồi thì bỏ qua toàn bộ — không cần ghép lại. Nguyên tắc này áp dụng xuyên suốt pipeline để tránh tính toán thừa.

---

## Cell 5.1 — Ghép 3 nguồn thành 1 bảng

```python
flu    = pd.read_csv(FILES['flunet'], low_memory=False)
dengue = pd.read_csv(FILES['dengue'], low_memory=False)
era5   = pd.read_csv(ERA5_FILE)

# FluNet: lấy cột cần thiết, gộp INF_A + INF_B thành inf_cases
flu_proc = flu[flu['ISO_YEAR'].between(TRAIN_START, TRAIN_END)].copy()
flu_proc['inf_cases'] = flu_proc['INF_A'].fillna(0) + flu_proc['INF_B'].fillna(0)
flu_proc = flu_proc.rename(columns={'COUNTRY_CODE':'iso3','ISO_YEAR':'iso_year','ISO_WEEK':'iso_week'})
flu_proc = flu_proc[['iso3','iso_year','iso_week','inf_cases','rsv_cases']]

# ERA5: lọc 2010–2019
era5_proc = era5[era5['iso_year'].between(TRAIN_START, TRAIN_END)].copy()

# Dengue: tính iso_year, iso_week từ calendar_start_date; gộp nhiều hàng cùng quốc gia-tuần
dengue_proc = dengue_proc.groupby(['iso3','iso_year','iso_week'], as_index=False).agg(
    dengue_total=('dengue_total','sum'),
    dengue_log1p=('dengue_log1p','mean')
)

# Ghép: FluNet là bảng gốc (anchor), LEFT JOIN ERA5, LEFT JOIN Dengue
master = flu_proc.merge(era5_proc, on=['iso3','iso_year','iso_week'], how='left')
master = master.merge(dengue_proc, on=['iso3','iso_year','iso_week'], how='left')
master['dengue_total'] = master['dengue_total'].fillna(0)
master['dengue_log1p'] = master['dengue_log1p'].fillna(0)

master.to_csv(MASTER_FILE, index=False)
print(f'Saved {len(master):,} rows -> {MASTER_FILE.name}')
```

### Tại sao FluNet là bảng gốc (anchor)?

Khi ghép bảng, phải chọn 1 bảng làm "trục" — gọi là **anchor**. Các bảng khác ghép vào trục đó.

FluNet được chọn vì 3 lý do:

1. **Phủ rộng nhất:** 172 quốc gia báo cáo đều đặn hàng tuần — nhiều nhất trong 3 nguồn
2. **Là mục tiêu dự báo chính:** model Flu phải học từ chính dữ liệu FluNet — không thể mất bất kỳ hàng nào
3. **Cấu trúc rõ nhất:** mỗi hàng = 1 quốc gia × 1 tuần — không cần xử lý thêm

### LEFT JOIN nghĩa là gì trong thực tế?

Kiểu ghép "LEFT JOIN" giữ **toàn bộ hàng của bảng trái** (FluNet), dù bảng phải có dữ liệu hay không.

Ví dụ cụ thể:
- Malta không có dữ liệu ERA5 → hàng Malta trong FluNet **vẫn tồn tại** trong master, chỉ có các cột thời tiết bị trống (NaN)
- Quốc gia không có dengue → hàng trong FluNet **vẫn tồn tại**, dengue = 0

Nếu dùng INNER JOIN (chỉ giữ hàng có ở cả 2 bảng): mất 14 quốc gia đảo nhỏ không có ERA5, mất 131 quốc gia không có dengue — chỉ còn 41 quốc gia trong master. Đó là lý do không dùng INNER JOIN.

### Tại sao dengue thiếu thì điền 0, còn thời tiết thiếu thì để trống?

- **Dengue = 0:** Quốc gia không có báo cáo dengue nghĩa là thực sự không có ca bệnh (dengue chỉ tồn tại ở vùng nhiệt đới — Đan Mạch hay Na Uy không bao giờ có dengue). Điền 0 là đúng.
- **Thời tiết = NaN (để trống):** Thiếu thời tiết là do không tìm được dữ liệu ERA5 cho quốc gia đó — đây là **dữ liệu thực sự thiếu**, không phải "bằng 0". Để trống để model biết đây là missing, không phải nhiệt độ 0°C.

---

## Cell 5.2 — Kiểm tra tỷ lệ dữ liệu thiếu

```python
miss = master.isnull().mean().sort_values(ascending=False) * 100
print('=== NaN rate (%) ===')
print(miss[miss > 0].to_string())

has_weather = (master.groupby('iso3')['temp_c'].count() > 0).sum()
total_countries = master['iso3'].nunique()
print(f'\nNuoc co weather: {has_weather}/{total_countries}')
print(f'NaN weather tong the: {master["temp_c"].isnull().mean()*100:.1f}%')
```

**Output thực tế:**
```
temp_c        8.49603
dewpoint_c    8.49603
precip_mm     8.49603
... (tất cả 17 biến thời tiết đều = 8.49603%)

Nuoc co weather: 154/172
NaN weather tong the: 8.5%
```

### Đọc kết quả này như thế nào?

**8.5% dữ liệu thời tiết bị thiếu** — con số này có vẻ đáng lo, nhưng thực ra nằm trong kiểm soát hoàn toàn.

Nguyên nhân: 18 trong số 172 quốc gia FluNet không tìm được trong bản đồ ERA5 — đây đều là các lãnh thổ nhỏ hoặc đặc biệt như Malta, Singapore, Maldives, một số đảo Caribbean. Những quốc gia này không có đủ diện tích lãnh thổ để ERA5 mapping tìm được ô lưới nào trong biên giới.

**Tại sao 8.5% chứ không phải 10.5%?** (= 18/172 ≈ 10.5% nếu tính theo quốc gia)

Vì 18 quốc gia thiếu thời tiết (chủ yếu là đảo nhỏ) cũng **báo cáo ít tuần hơn** trong FluNet — trung bình ~369 tuần/nước. Trong khi 154 nước có thời tiết báo cáo nhiều hơn — ~464 tuần/nước. Khi tính theo số dòng (không phải số quốc gia), tỷ lệ thiếu thấp hơn.

**Tại sao tất cả 17 cột thời tiết có con số thiếu giống hệt nhau (8.49603%)?**

Đây là dấu hiệu ghép đúng. Dữ liệu ERA5 được ghép theo đơn vị quốc gia — một quốc gia hoặc có đủ cả 17 biến thời tiết, hoặc không có cái nào. Không có chuyện riêng cột nhiệt độ có nhưng cột độ ẩm lại thiếu. Nếu con số 17 cột này không giống nhau → có bug trong quá trình ghép.

**Ngưỡng chấp nhận:**
- 8.5% NaN thời tiết → bình thường, có giải thích rõ ràng
- `inf_cases` NaN = 0% → đúng (FluNet là bảng gốc, không mất hàng nào)
- `dengue_log1p` NaN = 0% → đúng (đã điền 0 sau ghép)

---

## Cell 5.3 — Kiểm tra giá trị thời tiết có hợp lý không

```python
weather_cols = ['temp_c', 'humidity_pct', 'precip_mm', 'solar_wm2', 'dewpoint_c']
print(master[weather_cols].describe().round(2).to_string())

flags = {
    'temp_c':       (master['temp_c'] < -60) | (master['temp_c'] > 60),
    'humidity_pct': (master['humidity_pct'] < 0) | (master['humidity_pct'] > 105),
    'precip_mm':    master['precip_mm'] < 0,
    'solar_wm2':    master['solar_wm2'] < 0,
}
for col, mask in flags.items():
    n = mask.sum()
    print(f'  {col}: {"OK" if n==0 else f"{n} rows ngoai nguong"}')
```

Bước này kiểm tra xem dữ liệu thời tiết có nằm trong khoảng vật lý hợp lý không:
- Nhiệt độ: -60°C đến +60°C (ngoài phạm vi này là lỗi chuyển đổi đơn vị ở Session 4)
- Độ ẩm: 0–105% (ERA5 đôi khi ra 100.x% do nội suy — chấp nhận được)
- Lượng mưa và bức xạ: không thể âm

Nếu `precip_mm < 0` → có nghĩa Session 4 quên nhân đơn vị đúng. Đây là lớp bảo vệ để phát hiện lỗi từ sớm, trước khi đưa vào training.

---

## Cell 5.4 — Kiểm tra coverage theo từng năm

```python
flu_cov     = master[master['inf_cases'] > 0].groupby('iso_year')['iso3'].nunique()
weather_cov = master.dropna(subset=['temp_c']).groupby('iso_year')['iso3'].nunique()

print('Nam   | Flu report | Co weather')
for yr in range(2010, 2020):
    print(f'{yr}  | {flu_cov[yr]:>10} | {weather_cov[yr]:>10}')
```

Mục đích: xem từng năm có bao nhiêu quốc gia thực sự có báo cáo bệnh và thời tiết.

Kỳ vọng:
- Flu report: ổn định >120 quốc gia/năm (WHO FluNet coverage tốt từ 2010–2019)
- Has weather: ổn định ~154 quốc gia/năm (ERA5 coverage đồng đều theo năm)

Nếu một năm đột ngột thấp hơn nhiều → có vấn đề ở bước lọc năm trong Session 4 hoặc Session 5.

---

## Cell 5.5 — Kiểm tra biến mục tiêu (target)

```python
# Influenza: tỷ lệ tuần không có ca bệnh
zero_flu = (master['inf_cases'] == 0).mean() * 100
print(f'Flu zero rows: {zero_flu:.1f}%  (kỳ vọng ~38-40%)')

# Dengue: bao nhiêu quốc gia thực sự có dengue
dengue_countries = master[master['dengue_log1p'] > 0]['iso3'].nunique()
print(f'Dengue endemic countries: {dengue_countries}  (kỳ vọng ~50)')

# Top 5 tuần có ca cúm cao nhất
print(master.nlargest(5, 'inf_cases')[['iso3','iso_year','iso_week','inf_cases']].to_string())
```

**Output thực tế:**
```
Flu zero rows: 38.8%
Dengue endemic countries: 51
```

### Đọc kết quả này như thế nào?

**38.8% tuần không có ca cúm — tại sao không phải 70–75%?**

Trong master dataset, mỗi hàng tương ứng với 1 tuần **mà quốc gia đó có gửi báo cáo lên WHO FluNet**. Những tuần quốc gia không báo cáo thì **không có hàng nào** trong master — không phải hàng với ca = 0.

Nên 38.8% zero rows có nghĩa: trong số những tuần đã báo cáo, 38.8% là tuần không phát hiện ca bệnh nào. Đây là tỷ lệ hợp lý — mùa cúm thường kéo dài khoảng 20–25 tuần/năm, còn lại là off-season.

**51 quốc gia có dengue — ý nghĩa gì?**

OpenDengue V1.3 thu thập được báo cáo từ 51 quốc gia có dengue lưu hành trong 2010–2019. Đây là phủ rộng hơn nhiều so với kỳ vọng ban đầu (15–25 quốc gia) — vì WHO ước tính dengue lưu hành tại hơn 100 quốc gia, và OpenDengue đã thu thập được báo cáo từ 51 trong số đó.

Con số này quan trọng: nó xác nhận model dengue sẽ được train trên 51 quốc gia nhiệt đới thực sự có bệnh — không phải 172 quốc gia với đa số = 0.

---

## Cell 5.6 — Kiểm tra thời tiết có đúng mùa không

```python
# USA: phải có mùa đông rõ rệt
usa = master[master['iso3'] == 'USA'].copy()
jan = usa[usa['iso_week'].between(1, 4)]['temp_c'].mean()
jul = usa[usa['iso_week'].between(27, 30)]['temp_c'].mean()
print(f'USA Jan avg: {jan:.1f}C  (kỳ vọng -5 đến 5C)')
print(f'USA Jul avg: {jul:.1f}C  (kỳ vọng 20-25C)')

# Việt Nam: nhiệt đới, ít dao động hơn nhưng vẫn có chênh lệch
vnm = master[master['iso3'] == 'VNM'].copy()
jan_v = vnm[vnm['iso_week'].between(1, 4)]['temp_c'].mean()
jul_v = vnm[vnm['iso_week'].between(27, 30)]['temp_c'].mean()
print(f'VNM Jan avg: {jan_v:.1f}C  (kỳ vọng 15-22C)')
print(f'VNM Jul avg: {jul_v:.1f}C  (kỳ vọng 27-32C)')
```

Đây là bước cuối cùng, và cũng là quan trọng nhất về mặt kiểm tra tính đúng đắn.

**Tại sao phải check USA và VNM?**

Nhớ lại Session 4: khi tải ERA5, nhiệt độ lưu dưới dạng **Kelvin** (khoảng 285–300K). Phải trừ đi 273.15 để ra Celsius. Nếu quên bước này, master sẽ chứa nhiệt độ ~285–300 thay vì 12–27°C.

Model XGBoost sẽ vẫn chạy được — nhưng nó sẽ học từ dữ liệu sai và cho kết quả vô nghĩa. Không có lỗi nào báo ra.

Bằng cách check nhiệt độ trung bình tháng 1 của USA (phải < 5°C) và tháng 7 (phải > 15°C), mình đảm bảo unit conversion đã đúng trước khi đi vào training.

Nếu check này FAIL → quay lại Session 4 kiểm tra `t2m - 273.15`.

---

## Kết quả Session 5

**File output:** `master_weekly_2010_2019.csv`

| Chỉ số | Giá trị | Giải thích |
|--------|---------|------------|
| Số hàng | 78,213 | FluNet anchor: 172 quốc gia × ~455 tuần trung bình |
| Số cột | ~25 | 3 id + inf_cases + dengue_total + 17 weather + seasonality |
| Quốc gia | 172 | Toàn bộ FluNet — không mất quốc gia nào |
| Có weather | 154/172 | 18 đảo nhỏ không map được ERA5 |
| Giai đoạn | 2010–2019 | 10 năm training data |
| Nguồn merge | FluNet + ERA5 + OpenDengue | 3 nguồn → 1 bảng |

**3 nguồn, 1 bảng. Từ đây, mọi session đều đọc từ file này.**

---

## Key Insights từ Session 5

**1. Bài toán merge không phải chỉ là nối bảng — đó là quyết định kiến trúc dữ liệu**

Chọn anchor là FluNet (LEFT JOIN) thay vì INNER JOIN bảo toàn 172 quốc gia. INNER JOIN với ERA5 sẽ mất 14 quốc gia; INNER JOIN với Dengue sẽ chỉ còn 41 quốc gia. Một quyết định ghép bảng ảnh hưởng trực tiếp đến số lượng quốc gia model có thể dự báo.

**2. NaN và 0 không phải như nhau — và phải xử lý khác nhau**

Dengue thiếu = "quốc gia này không có dengue" → điền 0 là đúng. Thời tiết thiếu = "không tìm được dữ liệu" → để NaN để model biết đây là missing thật. Lẫn lộn 2 loại này sẽ tạo ra model học sai.

**3. 38.8% zero rows không phải imbalanced — đó là đặc tính surveillance**

FluNet chỉ có hàng cho các tuần quốc gia gửi báo cáo. Off-season (không báo cáo) không có trong master. 38.8% zero trong số các tuần đã báo cáo là bình thường — mùa cúm chiếm ~60% số tuần báo cáo.

**4. Sanity check nhiệt độ USA/VNM là lớp bảo vệ cuối cùng**

Lỗi unit conversion (quên `- 273.15`) không tạo ra error message — model vẫn chạy nhưng kết quả vô nghĩa. Hai dòng check đơn giản này phát hiện được lỗi nghiêm trọng nhất trước khi bước vào training.

**5. Master dataset là checkpoint quan trọng nhất của pipeline**

Từ Session 6 trở đi, không cần chạm vào Session 1–4. Nếu sau này muốn thêm feature mới (dân số, độ cao, mật độ đô thị), chỉ cần cập nhật Session 5 và chạy lại từ đó. Đây là lý do mỗi session đọc input từ CSV và ghi output ra CSV — tách biệt hoàn toàn giữa các bước.
