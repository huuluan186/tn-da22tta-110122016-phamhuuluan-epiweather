# Session 5: Tạo đặc trưng và nhãn mức rủi ro (Notebook v5/v6)

> **Dùng khi demo lần 1:** Đây là file để giải thích "mô hình dựa vào cái gì". Khi demo giao diện, chỉ cần nói mô hình dùng lịch sử ca bệnh, mùa vụ theo tuần/năm và nhóm đặc trưng thời tiết có độ trễ.
>
> **Mục tiêu thuyết trình:** Biến `master_weekly_v1.csv` thành 2 file đặc trưng sẵn sàng huấn luyện: `features_flu_v1.csv` và `features_dengue_v1.csv`. Đồng thời tạo nhãn Low/Medium/High cho bài toán phân mức rủi ro.

---

## Bản đọc khi thuyết trình

Sau khi đã hiểu dữ liệu, em chuyển dữ liệu thô thành các đặc trưng để mô hình học. Nói đơn giản, đặc trưng là những thông tin đầu vào mà mô hình được phép nhìn thấy khi dự báo.

Nhóm đặc trưng quan trọng nhất là lịch sử ca bệnh. Ví dụ với cúm, mô hình nhìn số ca của 1, 2, 3 tuần trước và trung bình vài tuần gần nhất. Với sốt xuất huyết, độ trễ dài hơn vì bệnh liên quan đến muỗi truyền bệnh, nên tác động có thể kéo dài qua nhiều tuần. Đây là lý do hai bệnh không dùng cùng một bộ đặc trưng.

Nhóm thứ hai là đặc trưng mùa vụ. Dịch bệnh có thể thay đổi theo tuần trong năm, nên em mã hóa tuần theo dạng sin/cos để mô hình hiểu được tính chu kỳ. Với cúm, em còn thêm thông tin bán cầu vì mùa cúm ở Bắc bán cầu và Nam bán cầu lệch nhau.

Nhóm thứ ba là đặc trưng thời tiết có độ trễ. Các độ trễ này lấy từ phân tích ở Session 4, không chọn tùy tiện. Ví dụ dengue dùng độ trễ dài hơn cho nhiệt độ, mưa và bức xạ mặt trời vì vòng đời muỗi và thời gian báo cáo bệnh dài hơn cúm.

Một lỗi rất dễ mắc là lấy độ trễ mà không tách theo quốc gia. Nếu chỉ dùng `shift` trên toàn bộ bảng, tuần đầu của Brazil có thể lấy nhầm dữ liệu từ tuần cuối của Mỹ. Đây là rò rỉ dữ liệu nghiêm trọng. Vì vậy notebook luôn lấy độ trễ trong từng quốc gia riêng bằng `groupby('iso3').shift()`.

Nói đơn giản hơn: độ trễ của Brazil tuần này phải lấy từ Brazil tuần trước, không được lấy từ quốc gia khác. `groupby('iso3')` giống như chia bảng thành nhiều bảng nhỏ theo từng quốc gia trước, rồi `shift()` mới được thực hiện bên trong từng bảng nhỏ đó.

Ngoài dự báo số ca, dashboard còn cần mức rủi ro Low/Medium/High. Mức rủi ro không nên chỉ dựa vào một ngưỡng số ca tuyệt đối, vì một nước lớn và một nước nhỏ có quy mô báo cáo rất khác nhau. Vì vậy em tạo nhãn dựa trên mức nền lịch sử của từng quốc gia và từng tuần. Cách này giúp mức High thể hiện sự bất thường so với nền của chính quốc gia đó, chứ không chỉ là số ca lớn tuyệt đối.

Kết quả của session này là hai file đặc trưng: một cho cúm và một cho dengue. Đây là đầu vào trực tiếp cho bước huấn luyện mô hình.

---

## 1. Cell 5.1 - Hàm hỗ trợ tạo độ trễ

```python
def make_lag(df, col, lag, group='iso3'):
    """Chỉ lấy độ trễ trong cùng quốc gia để tránh rò rỉ dữ liệu."""
    return df.groupby(group)[col].shift(lag)

def make_rollmean(df, col, window, group='iso3'):
    """Trung bình trượt trong cùng quốc gia, dùng shift(1) để không nhìn trước tương lai."""
    return df.groupby(group)[col].apply(
        lambda x: x.shift(1).rolling(window, min_periods=1).mean()
    )
```

**Bug suýt mắc:**

```python
# SAI — shift toàn bộ DataFrame, không group
df['flu_log_lag1'] = df['inf_log1p'].shift(1)
# Brazil tuần 1 = USA tuần 52 → rò rỉ dữ liệu nghiêm trọng

# ĐÚNG — groupby + shift
df['flu_log_lag1'] = df.groupby('iso3')['inf_log1p'].shift(1)
# Độ trễ chỉ lấy trong cùng một quốc gia
```

→ `groupby + shift` là quy tắc bắt buộc khi tạo đặc trưng theo thời gian cho nhiều quốc gia.

### Giải thích dễ hiểu về `groupby().shift()`

Giả sử dữ liệu đã được sắp theo quốc gia và thời gian, nhưng ví dụ này chỉ đang cắt ra vài dòng để minh họa:

| Dòng | Quốc gia | Tuần | Số ca |
|---:|---|---:|---:|
| 1 | USA | 51 | 100 |
| 2 | USA | 52 | 120 |
| 3 | BRA | 1 | 30 |
| 4 | BRA | 2 | 40 |

Nếu dùng `shift(1)` trên toàn bộ bảng, dòng BRA tuần 1 sẽ lấy dòng ngay phía trên nó, tức là USA tuần 52:

| Quốc gia | Tuần | Số ca | Lag sai |
|---|---:|---:|---:|
| USA | 51 | 100 | trống |
| USA | 52 | 120 | 100 |
| BRA | 1 | 30 | 120 |
| BRA | 2 | 40 | 30 |

Chỗ sai là BRA tuần 1 bị gán lịch sử của USA. Như vậy mô hình tưởng rằng Brazil tuần trước có 120 ca, nhưng thật ra 120 là của Mỹ. Đây là rò rỉ dữ liệu giữa các quốc gia.

Nếu dùng `groupby('iso3').shift(1)`, bảng được tách theo từng quốc gia trước:

| Quốc gia | Tuần | Số ca | Lag đúng |
|---|---:|---:|---:|
| USA | 51 | 100 | trống |
| USA | 52 | 120 | 100 |
| BRA | 1 | 30 | trống |
| BRA | 2 | 40 | 30 |

Trong ví dụ cắt ngắn này, BRA tuần 1 để trống vì trước đó không có dòng BRA tuần 52 của năm trước. Nhưng trong dữ liệu thật, nếu có Brazil năm 2018 tuần 52 rồi Brazil năm 2019 tuần 1, thì `groupby('iso3').shift(1)` vẫn lấy đúng tuần 52 của Brazil năm trước.

Ví dụ đúng khi có đủ năm trước:

| Quốc gia | Năm | Tuần | Số ca | Lag đúng |
|---|---:|---:|---:|---:|
| BRA | 2018 | 52 | 25 | trống hoặc tuần 51 nếu có |
| BRA | 2019 | 1 | 30 | 25 |
| BRA | 2019 | 2 | 40 | 30 |

Vì vậy, tuần 1 không bắt buộc phải rỗng. Nó chỉ rỗng khi đó là tuần đầu tiên của quốc gia trong toàn bộ giai đoạn dữ liệu, hoặc khi dữ liệu năm trước bị thiếu. Khi thuyết trình có thể nói: “Em dùng `groupby` để đảm bảo mỗi nước chỉ nhìn lịch sử của chính nó, kể cả khi lịch sử đó nằm ở năm trước.”

### V5 có lấy được tuần 52 năm trước không?

Có, nếu tuần 52 năm trước còn nằm trong bảng đang tạo đặc trưng. Trong v5, hàm tạo lag có bước:

```python
df = df.sort_values([group_col, 'iso_year', 'iso_week']).copy()
df[f'{col}_lag{k}'] = df.groupby(group_col)[col].shift(k)
```

Vì dữ liệu được sắp theo `iso3`, `iso_year`, `iso_week`, nên trong cùng một quốc gia, dòng năm sau tuần 1 sẽ đứng ngay sau năm trước tuần 52. Khi đó `shift(1)` sẽ lấy đúng tuần 52 của cùng quốc gia.

Nhưng có một giới hạn cần nói rõ:

| Trường hợp | V5 xử lý thế nào |
|---|---|
| Brazil 2019-W01, trong bảng có Brazil 2018-W52 | Lấy được lag từ 2018-W52 |
| Brazil 2010-W01 trong bộ flu 2010-2019 | Không lấy từ 2009-W52 vì v5 đã lọc từ 2010 trở đi |
| Brazil 2015-W01 trong bộ dengue 2015-2019 | Không lấy từ 2014-W52 vì grid dengue v5 bắt đầu từ 2015 |
| Một quốc gia bị thiếu tuần giữa chừng | `shift(1)` lấy dòng báo cáo trước đó của cùng quốc gia; với dengue v5 đã tạo grid đầy đủ nên ít gặp hơn |

Cách nói gọn: “V5 có nối lag qua năm trước trong cùng quốc gia, ví dụ 2019 tuần 1 lấy được 2018 tuần 52. Nhưng nó không lấy được dữ liệu nằm ngoài giai đoạn đã lọc, ví dụ đầu năm 2010 hoặc đầu năm 2015.”

---

## 2. Cell 5.2 — Build features FLU (2010-2019)

```python
# Pre-step: complete grid (iso3 × year × week) + fillna(0)
# → Giữ 89% data thay vì mất 93% (do shift bị NaN ở rows missing)
grid = expand_to_full_grid(master_flu, ['iso3', 'iso_year', 'iso_week'])
grid['inf_log1p'] = grid['inf_log1p'].fillna(0)

# Tạo 16 đặc trưng
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
    # Mùa vụ theo tuần trong năm
    'iso_week_sin':       np.sin(2*np.pi*grid['iso_week']/52),
    'iso_week_cos':       np.cos(2*np.pi*grid['iso_week']/52),
    # Đặc trưng cố định
    'iso_year':           grid['iso_year'],
    'HEMISPHERE_NH':      (grid['hemisphere'] == 'NH').astype(int),
    'HEMISPHERE_SH':      (grid['hemisphere'] == 'SH').astype(int),
}
```

### Vì sao dùng `sin/cos` cho tuần trong năm?

Tuần trong năm là dữ liệu có tính vòng lặp. Sau tuần 52 sẽ quay lại tuần 1. Nếu đưa trực tiếp `iso_week = 1, 2, 3, ..., 52` vào mô hình, mô hình có thể hiểu nhầm rằng tuần 52 rất xa tuần 1, vì số 52 và số 1 cách nhau nhiều. Nhưng trong thực tế, tuần 52 và tuần 1 nằm sát nhau trên lịch.

Dùng `sin/cos` là cách biến tuần trong năm thành một vòng tròn:

```python
iso_week_sin = np.sin(2*np.pi*iso_week/52)
iso_week_cos = np.cos(2*np.pi*iso_week/52)
```

Có thể giải thích đơn giản:

| Cách mã hóa | Vấn đề hoặc lợi ích |
|---|---|
| Dùng số tuần 1-52 | Tuần 52 và tuần 1 bị hiểu là rất xa nhau |
| Dùng `sin/cos` | Tuần 52 và tuần 1 nằm gần nhau trên vòng mùa vụ |

Vì bệnh có mùa vụ, mô hình cần biết hiện tại đang ở vị trí nào trong chu kỳ một năm. `sin/cos` giúp mô hình học được chu kỳ đó mượt hơn, đặc biệt với các bệnh có mùa rõ như cúm.

### Câu nói ngắn khi thuyết trình

“Em không đưa tuần trong năm dưới dạng số 1 đến 52 vì như vậy mô hình sẽ hiểu nhầm tuần 52 rất xa tuần 1. Trong thực tế hai tuần này liền nhau, nên em dùng `sin/cos` để biểu diễn tuần theo dạng vòng tròn của một năm.”

**Kết quả:** `features_flu_v1.csv` - **54,636 dòng × 17 cột** (16 đặc trưng + biến cần dự báo `inf_log1p`).

**Độ phủ:** 143 nước sau khi bỏ các dòng đầu chưa đủ dữ liệu độ trễ.

---

## 3. Cell 5.3 — Build features DENGUE (2015-2019)

```python
DENGUE_FEATURES = {
    # Lịch sử ca bệnh, dùng độ trễ dài hơn flu vì vòng đời muỗi
    'deng_log_lag6':      make_lag(grid, 'dengue_log1p', 6),
    'deng_log_lag8':      make_lag(grid, 'dengue_log1p', 8),
    'deng_log_lag10':     make_lag(grid, 'dengue_log1p', 10),
    'deng_log_lag12':     make_lag(grid, 'dengue_log1p', 12),
    'deng_log_lag14':     make_lag(grid, 'dengue_log1p', 14),
    'deng_log_rollmean4': make_rollmean(grid, 'dengue_log1p', 4),
    'deng_log_rollmean8': make_rollmean(grid, 'dengue_log1p', 8),
    # Thời tiết với độ trễ chọn từ Session 4.4
    'temp_c_lag11':       make_lag(grid, 'temp_c', 11),
    'dewpoint_c_lag8':    make_lag(grid, 'dewpoint_c', 8),
    'precip_mm_lag6':     make_lag(grid, 'precip_mm', 6),
    'humidity_pct_lag1':  make_lag(grid, 'humidity_pct', 1),
    'solar_wm2_lag16':    make_lag(grid, 'solar_wm2', 16),
    # Mùa vụ
    'iso_week_sin':       np.sin(2*np.pi*grid['iso_week']/52),
    'iso_week_cos':       np.cos(2*np.pi*grid['iso_week']/52),
    'iso_year':           grid['iso_year'],
}
```

**Kết quả:** `features_dengue_v1.csv` - **5,786 dòng × 16 cột** (15 đặc trưng + biến cần dự báo).

**Độ phủ:** 35 nước trong giai đoạn 2015-2019, sau khi bỏ các tuần đầu chưa đủ dữ liệu độ trễ.

**Lưu ý:** Dengue **không dùng đặc trưng bán cầu** vì dữ liệu chủ yếu ở vùng nhiệt đới, mùa vụ không rõ theo hai bán cầu như cúm.

---

## 4. Cell 5.4 - Nhãn mức rủi ro theo Endemic Channel (Bortman 1999)

**Bài toán phân mức rủi ro cần nhãn Low/Medium/High.**

**Cách đơn giản nhưng không phù hợp:** chia đều theo số ca. Cách này sai về ý nghĩa vì Brazil 10 nghìn ca/tuần và Singapore 50 ca/tuần không nên dùng cùng một ngưỡng tuyệt đối.

**Endemic Channel chuẩn WHO EWARS (Bortman 1999 PAHO):**

```python
def endemic_label(row, history):
    """Per (iso3, iso_week) — baseline + 2σ rule."""
    past = history[
        (history["iso3"] == row["iso3"]) &
        (history["iso_week"] == row["iso_week"]) &
        (history["iso_year"] < row["iso_year"]) &
        (history["iso_year"] >= row["iso_year"] - 5)
    ]
    baseline = past["cases"].mean()
    sigma = past["cases"].std()
    upper = baseline + 2 * sigma

    if row["cases"] < baseline:
        return "Low"
    if row["cases"] >= upper:
        return "High"
    return "Medium"
```

| Threshold | Label | Ý nghĩa |
|---|---|---|
| `cases < baseline` | **Low** | Dưới trung bình lịch sử 5 năm gần của cùng quốc gia, cùng tuần ISO |
| `baseline ≤ cases < baseline+2σ` | **Medium** | Normal range |
| `cases ≥ baseline+2σ` | **High** | Outbreak (rare event ~2.5% tail) |

### Baseline được tính như thế nào?

Baseline là mức ca bệnh “bình thường” của chính quốc gia đó ở đúng tuần đó trong năm. Không lấy trung bình toàn cầu, cũng không lấy trung bình cả năm, vì mỗi quốc gia có quy mô báo cáo khác nhau và mỗi tuần có mùa vụ khác nhau.

Cách tính:

1. Chọn dòng đang cần gán nhãn, ví dụ USA năm 2019 tuần 6.
2. Lấy các năm quá khứ gần nhất của cùng quốc gia và cùng tuần 6, ví dụ USA tuần 6 của các năm 2014-2018.
3. Tính trung bình các số ca đó, đây là `baseline`.
4. Tính độ dao động lịch sử, gọi là `sigma`.
5. So sánh số ca hiện tại với `baseline` và `baseline + 2*sigma`.

Ví dụ dễ hiểu:

| Quốc gia | Tuần | Năm quá khứ | Số ca |
|---|---:|---:|---:|
| USA | 6 | 2014 | 900 |
| USA | 6 | 2015 | 1,000 |
| USA | 6 | 2016 | 1,100 |
| USA | 6 | 2017 | 950 |
| USA | 6 | 2018 | 1,050 |

Baseline của USA tuần 6 sẽ xấp xỉ trung bình của các năm này, tức khoảng 1,000 ca. Nếu USA tuần 6 năm 2019 có 800 ca thì là thấp hơn nền, có thể gán Low. Nếu có khoảng 1,100 ca thì vẫn quanh mức bình thường, có thể là Medium. Nếu tăng rất cao vượt `baseline + 2*sigma`, thì mới gán High.

Điểm quan trọng là baseline được tính theo từng cặp `(quốc gia, tuần trong năm)`. Brazil tuần 10 có baseline riêng, USA tuần 10 có baseline riêng, và USA tuần 6 cũng khác USA tuần 30. Nhờ vậy mức rủi ro phản ánh “bất thường so với chính lịch sử của nơi đó”, không phải so với một ngưỡng chung cho mọi nước.

### Câu nói ngắn khi thuyết trình baseline

“Baseline là mức nền lịch sử của cùng quốc gia và cùng tuần trong năm. Ví dụ muốn biết USA tuần 6 năm 2019 có bất thường không, em so với USA tuần 6 của các năm trước, không so với Brazil hay không so với tuần khác. Nếu số ca vượt xa mức nền cộng thêm độ dao động lịch sử thì mới xem là High.”

**Tại sao 5 năm:** Theo WHO EWARS, 3 năm thường chưa đủ ổn định để tính mức nền, 5 năm là mốc tối thiểu hợp lý.

**Tại sao 2σ:** Tương ứng vùng bất thường phía trên của phân phối, có thể xem là tín hiệu đáng cảnh báo theo Bortman 1999.

**Class balance kết quả:**

| Disease | Low | Medium | High |
|---|---|---|---|
| Flu | 56% | 26% | 17% |
| Dengue | 47% | 30% | 23% |

→ Mất cân bằng lớp ở mức chấp nhận được, có thể xử lý bằng tham số cân bằng lớp trong XGBClassifier.

---

## 5. Cell 5.5 — Save 2 feature files + verify

```python
features_flu.to_csv(PROCESSED / 'features_flu_v1.csv', index=False)
features_dengue.to_csv(PROCESSED / 'features_dengue_v1.csv', index=False)
```

**Kiểm tra nhanh:**
- Không còn giá trị thiếu trong các cột đặc trưng.
- Tỷ lệ Low/Medium/High hợp lý.
- Dữ liệu đủ để kiểm chứng theo thời gian từ năm 2014 trở đi.

---

## 6. Cách kiểm chứng theo thời gian (xem trước Session 6)

```
Fold 1: train 2010-2013, val 2014
Fold 2: train 2010-2014, val 2015
Fold 3: train 2010-2015, val 2016
Fold 4: train 2010-2016, val 2017
Fold 5: train 2010-2017, val 2018
Fold 6: train 2010-2018, val 2019
```

→ Mỗi lần kiểm chứng chỉ huấn luyện trên dữ liệu **trước** năm kiểm chứng. Cách này tránh rò rỉ dữ liệu tương lai.

---

## Ý chính Session 5 (slide thuyết trình)

1. **Đặc trưng có lý do từ phân tích dữ liệu** - không chọn độ trễ tùy tiện.
2. **`groupby + shift` bắt buộc** - nếu quên, dữ liệu của quốc gia này có thể lẫn sang quốc gia khác.
3. **Tạo lưới đầy đủ trước khi lấy độ trễ** - giúp giữ lại nhiều dữ liệu hơn.
4. **Endemic Channel có cơ sở tham khảo** - không tự nghĩ ngưỡng Low/Medium/High tùy ý.
5. **Mức rủi ro không chỉ là số ca tuyệt đối** - còn phụ thuộc mức nền của từng quốc gia và từng tuần.

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
> [NẾU HỎI: Sao không chia theo quantile?]
> > "Quantile nghĩa là sắp xếp tất cả số ca rồi chia đều thành 3 nhóm, ví dụ 33% thấp nhất là Low, 33% giữa là Medium, 33% cao nhất là High. Cách này làm số lượng mỗi nhóm đẹp hơn, nhưng không trả lời đúng câu hỏi dịch tễ: số ca này có bất thường so với chính quốc gia đó, đúng tuần đó trong năm hay không?
> >
> > Ví dụ 100 ca ở một nước nhỏ có thể là bất thường, nhưng 100 ca ở một nước lớn có thể là bình thường. Nếu chia quantile chung, hai trường hợp này dễ bị đánh giá sai. Vì vậy em dùng Endemic Channel: so số ca hiện tại với mức nền lịch sử của cùng quốc gia và cùng tuần trong năm. Nếu vượt xa mức nền, cụ thể là vượt `baseline + 2*sigma`, thì mới gán High. Cách này có ý nghĩa cảnh báo dịch hơn và có tài liệu tham khảo, không phải tự đặt ngưỡng tùy ý."
