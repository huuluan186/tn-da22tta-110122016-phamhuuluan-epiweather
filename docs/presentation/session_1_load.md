# Session 1: Đọc dữ liệu thô và kiểm tra nhanh (Notebook v5/v6)

> **Dùng khi demo lần 1:** Không cần đọc hết file này. Chỉ cần nói ngắn rằng hệ thống lấy dữ liệu bệnh từ WHO FluNet (`VIW_FNT.csv`) và OpenDengue (`National_extract_V1_3.csv`), dữ liệu thời tiết từ ERA5, sau đó chuẩn hóa theo quốc gia và tuần để phục vụ mô hình.
>
> **Mục tiêu thuyết trình:** Người chấm hiểu dữ liệu đến từ đâu, 4 nguồn khác nhau ra sao, đã lọc và kiểm tra nhanh như thế nào trước khi đưa vào mô hình.

---

## Bản đọc khi thuyết trình

Ở session đầu tiên, em tập trung vào việc thu thập và kiểm tra dữ liệu nguồn. Vì đề tài của em dự báo nguy cơ dịch bệnh theo tuần, nên dữ liệu phải có ít nhất hai nhóm: số ca bệnh và các yếu tố thời tiết. Không có một nguồn duy nhất nào cung cấp đầy đủ cả hai nhóm dữ liệu cho toàn cầu, nên em phải kết hợp nhiều nguồn khác nhau.

Với bệnh cúm, em dùng WHO FluNet. Đây là nguồn dữ liệu giám sát cúm có độ phủ rộng, gồm nhiều quốc gia và được ghi nhận theo tuần. Trong dữ liệu này, em không dùng trực tiếp tất cả cột, mà kiểm tra mức thiếu dữ liệu trước. Một số cột thiếu quá nhiều nên bị loại bỏ. Cuối cùng, em tạo biến số ca cúm bằng cách cộng số ca cúm A và cúm B.

Với sốt xuất huyết, em dùng OpenDengue. Nguồn này phù hợp hơn cho các nước nhiệt đới, nhưng độ phủ giữa các năm không đều. Giai đoạn 2010-2014 có quá ít nước báo cáo nên không phù hợp để huấn luyện chính. Vì vậy, phần huấn luyện dengue được thu hẹp về 2015-2019 để dữ liệu ổn định hơn.

Một phát hiện quan trọng là giai đoạn 2020-2021 bị ảnh hưởng mạnh bởi COVID. Với cúm, số ca giảm rất sâu không phải vì mất dữ liệu, mà vì các biện pháp như khẩu trang, giãn cách và phong tỏa làm thay đổi hành vi lây truyền cũng như báo cáo bệnh. Nếu đưa giai đoạn này vào huấn luyện, mô hình có thể học sai mẫu bình thường của bệnh. Vì vậy em loại 2020-2021 khỏi giai đoạn huấn luyện chính.

Ngoài ra, em có đọc dữ liệu ECDC cho cúm châu Âu từ 2021 trở đi. Nguồn này không dùng để huấn luyện chính vì không trùng giai đoạn huấn luyện 2010-2019, nhưng có thể dùng làm nguồn tham khảo/kiểm chứng và phục vụ dashboard.

Ý chính của session này là: trước khi nói đến mô hình, phải hiểu dữ liệu. Quyết định dùng năm nào, bỏ cột nào, giữ nguồn nào đều ảnh hưởng trực tiếp đến kết quả dự báo sau này.

---

## 1. Vì sao có 4 nguồn dữ liệu

Đề tài yêu cầu kết hợp **y tế** (số ca bệnh) + **khí hậu** (thời tiết) theo (quốc gia × tuần). Không có **1 nguồn duy nhất** bao phủ toàn cầu cho cả hai nhóm dữ liệu, nên phải kết hợp 4 nguồn.

| Nguồn | Loại | Độ phủ | Giai đoạn | Vai trò |
|---|---|---|---|---|
| **WHO FluNet** | Cúm | 189 nước | 1995 đến nay, theo tuần | Dữ liệu ca bệnh để huấn luyện cúm |
| **OpenDengue v1.3** | Sốt xuất huyết | 82 nước, chủ yếu vùng nhiệt đới | 1990 đến 2023-W36 | Dữ liệu ca bệnh để huấn luyện dengue |
| **ERA5 ECMWF** | Khí hậu | Toàn cầu, lưới 0.25° | 1940 đến nay | Dữ liệu thời tiết để tạo đặc trưng |
| **ECDC Sentinel + ILI** | Cúm châu Âu | 30 nước EU | Từ 2021 | Dữ liệu tham khảo/kiểm chứng sau COVID, không dùng huấn luyện chính |

---

## 2. File đầu vào và cách lưu

Trong notebook, toàn bộ file thô được đặt trong thư mục `data/epidemic/raw/`. Session 1 chỉ đọc và kiểm tra dữ liệu thô, chưa train mô hình.

| Nguồn | Cách lấy | File lưu trong repo/workspace | Nội dung chính |
|---|---|---|---|
| WHO FluNet | Tải CSV export từ WHO FluNet/FluMart, sau này có script `scripts/sync_flunet.py` để đồng bộ dữ liệu mới | `data/epidemic/raw/VIW_FNT.csv` | Số ca cúm theo quốc gia, năm ISO, tuần ISO, subtype cúm |
| WHO FluNet metadata | Đi kèm bộ FluNet export | `data/epidemic/raw/VIW_FLU_METADATA.csv` | Metadata/country mapping phục vụ đọc hiểu dữ liệu cúm |
| OpenDengue v1.3 | Tải batch CSV từ OpenDengue global extract | `data/epidemic/raw/National_extract_V1_3.csv` | Số ca dengue theo quốc gia, ngày bắt đầu kỳ báo cáo, độ phân giải tuần/tháng/năm |
| ECDC Sentinel | Tải CSV từ ECDC surveillance data | `data/epidemic/raw/sentinelTestsDetectionsPositivity.csv` | Dữ liệu sentinel cúm châu Âu từ 2021 |
| ECDC ILI/SARI | Tải CSV từ ECDC surveillance data | `data/epidemic/raw/ILIARIRates.csv`, `data/epidemic/raw/SARIRates.csv`, `data/epidemic/raw/SARITestsDetectionsPositivity.csv` | Dữ liệu tham khảo hậu COVID, không dùng làm training chính |

Sau các session xử lý tiếp theo, dữ liệu trung gian được ghi ra:

| Bước | File output | Vai trò |
|---|---|---|
| Session 2 ERA5 | `data/weather/processed/era5_weekly_2010_2019_final.csv` | Thời tiết đã tổng hợp theo quốc gia-tuần |
| Session 3 merge | `data/processed/master_weekly_v1.csv` | File trung tâm gộp bệnh + thời tiết theo `(iso3, iso_year, iso_week)` |
| Session 5 features | `data/processed/features_flu_v1.csv`, `data/processed/features_dengue_v1.csv` | File đặc trưng đưa vào huấn luyện mô hình |

Đường dẫn trong notebook được gom vào biến `FILES` để các cell không hardcode rải rác:

```python
RAW = BASE / "data" / "epidemic" / "raw"
PROCESSED = BASE / "data" / "processed"
WEATHER_PROCESSED = BASE / "data" / "weather" / "processed"

FILES = {
    "flunet": RAW / "VIW_FNT.csv",
    "flu_meta": RAW / "VIW_FLU_METADATA.csv",
    "dengue": RAW / "National_extract_V1_3.csv",
    "ecdc_sen": RAW / "sentinelTestsDetectionsPositivity.csv",
    "ecdc_ili": RAW / "ILIARIRates.csv",
}
```

---

## 3. Load FluNet (Cell 1.1, 1.2)

```python
flu = pd.read_csv(FILES['flunet'], low_memory=False)
# Shape ban đầu: (183K rows, 53 cols)
```

**Nguồn bệnh:** cúm mùa từ WHO FluNet. Mỗi dòng tương ứng báo cáo của một quốc gia trong một tuần ISO, có các cột như `COUNTRY_CODE`, `ISO_YEAR`, `ISO_WEEK`, `INF_A`, `INF_B` và nhiều subtype cúm.

**File đọc:** `data/epidemic/raw/VIW_FNT.csv`.

**File metadata đọc kèm:** `data/epidemic/raw/VIW_FLU_METADATA.csv`.

**Quyết định + lý do:**

| Cột | Hành động | Lý do |
|---|---|---|
| `INF_ALL` | Bỏ | Missing 44% |
| `PARAINFLUENZA` | Bỏ | Missing 85.5% |
| `RSV_PROCESSED` | Bỏ | Khác đơn vị với `RSV`, correlation 0.729 (không 1.0) |
| `INF_A`, `INF_B` | **Giữ** | Build target `influenza_total = INF_A + INF_B` |
| UK X09-X12 | Gộp thành GBR | WHO không có mã GBR tổng hợp |
| `fillna(0)` cho INF_A, INF_B | Áp dụng | Missing = không báo cáo, không phải = 0 ca |

**Kết quả Session 1.1:** FluNet sau khi lọc 2010-2022 còn khoảng 113 nghìn dòng, 189 nước báo cáo.

**Phát hiện về độ phủ:**
- 2020-2021: vẫn 166-167 nước báo cáo, gần như ngang 2019, nên không phải thiếu dữ liệu hàng loạt.
- Số ca cúm năm 2020 giảm 99% do các biện pháp COVID như khẩu trang, giãn cách, phong tỏa; vì vậy loại 2020-2021 khỏi giai đoạn huấn luyện chính.

---

## 4. Load OpenDengue v1.3 (Cell 1.3, 1.4)

```python
dengue = pd.read_csv(FILES['dengue'], low_memory=False)
# Shape: (18K weekly rows, 15 cols) → 82 quốc gia
```

**Nguồn bệnh:** sốt xuất huyết từ OpenDengue v1.3 global extract. Đây là batch dataset tổng hợp từ nhiều nguồn giám sát quốc gia/khu vực, phù hợp cho dengue vì không có API WHO dengue toàn cầu chuẩn hóa như FluNet.

**File đọc:** `data/epidemic/raw/National_extract_V1_3.csv`.

**Cột quan trọng khi xử lý:** `adm_0_iso` để lấy mã quốc gia, `calendar_start_date` để quy đổi sang năm-tuần ISO, `T_res` để biết độ phân giải báo cáo, và cột giá trị ca bệnh dùng làm target sau khi chuẩn hóa.

**Quyết định + lý do:**

| Khía cạnh | Hành động | Lý do |
|---|---|---|
| `T_res` (resolution) | Chỉ giữ `Week` + `Month` | 77.8% Week, 10.5% Month, 11.7% Year (Year quá thô) |
| Giai đoạn | Huấn luyện **2015-2019** thay vì 2010-2019 | 2010-2014 chỉ 5-12 nước báo cáo, độ phủ quá thấp |
| Brazil | Dùng biến đổi log1p ở bước sau | **71% tổng ca toàn cầu** nên dễ làm mô hình bị lệch nếu dùng số ca thô |
| Giai đoạn mới nhất của dữ liệu | 2021-2023-W36 | OpenDengue v1.3 có dữ liệu đến 2023-W36 |

**Phát hiện:** Dengue năm 2020 cũng bị nhiễu bởi COVID, nên không dùng năm này như dữ liệu vận hành ổn định.

---

## 5. Load ECDC (Cell 1.5)

```python
ecdc_sen = pd.read_csv(FILES['ecdc_sen'])  # Sentinel surveillance
ecdc_ili = pd.read_csv(FILES['ecdc_ili'])  # ILI rates age-stratified
# Cover: 30 nước EU, từ 2021
```

**Nguồn bệnh:** giám sát cúm/ILI/SARI khu vực châu Âu từ ECDC.

**File đọc:** `data/epidemic/raw/sentinelTestsDetectionsPositivity.csv`, `data/epidemic/raw/ILIARIRates.csv`, và các file SARI nếu cần đối chiếu.

**Vai trò:** Kiểm chứng tham khảo sau COVID và phục vụ một phần hiển thị dashboard. **Không dùng để huấn luyện chính** vì giai đoạn 2021+ không trùng với giai đoạn huấn luyện 2010-2019.

---

## 6. Bảng tổng kết Session 1

| Dataset | File raw | Shape sau load | Cover | Quyết định period |
|---------|----------|----------------|-------|-------------------|
| FluNet | `data/epidemic/raw/VIW_FNT.csv` | Khoảng 113K dòng sau lọc 2010-2022, 53 cột | 189 nước | Huấn luyện 2010-2019, bỏ 2020-2021 do nhiễu COVID |
| OpenDengue | `data/epidemic/raw/National_extract_V1_3.csv` | Khoảng 18K dòng weekly, 15 cột | 82 nước | Huấn luyện 2015-2019, dữ liệu hiện có đến 2023-W36 |
| ECDC Sentinel | `data/epidemic/raw/sentinelTestsDetectionsPositivity.csv` | Khoảng 50K dòng | 30 nước EU, từ 2021 | Chỉ dùng tham khảo/kiểm chứng |
| ECDC ILI | `data/epidemic/raw/ILIARIRates.csv` | Khoảng 30K dòng | Theo nhóm tuổi, từ 2021 | Chỉ dùng tham khảo/kiểm chứng |

---

## Ý chính Session 1 (slide thuyết trình)

1. **Nguồn bệnh chính**: cúm từ WHO FluNet (`VIW_FNT.csv`), dengue từ OpenDengue (`National_extract_V1_3.csv`).
2. **`INF_ALL` missing 44% → bỏ, dùng `INF_A + INF_B`** = lý do EDA quan trọng hơn chọn model.
3. **2010-2014 dengue quá thưa → thu hẹp về 2015-2019** = không phải cứ nhiều năm hơn là tốt hơn.
4. **2020-2021 vẫn 166 nước báo cáo nhưng số ca giảm 99% do COVID** → loại khỏi huấn luyện để mô hình không học sai mẫu bình thường.
5. **File trung gian sau xử lý**: `master_weekly_v1.csv` là file gộp trung tâm; `features_flu_v1.csv` và `features_dengue_v1.csv` là input train model.

---

## Câu nói thuyết trình cho Session 1

> "Đầu tiên em nói về data. Em dùng **4 nguồn** vì không có nguồn nào single-source cover được toàn cầu cho cả y tế lẫn khí hậu."
>
> "**Nguồn bệnh chính** của em là 2 file raw: `VIW_FNT.csv` từ **WHO FluNet** cho cúm và `National_extract_V1_3.csv` từ **OpenDengue v1.3** cho sốt xuất huyết. Hai file này được lưu trong `data/epidemic/raw/`. Sau các bước xử lý, em ghi ra `data/processed/master_weekly_v1.csv`, rồi tạo `features_flu_v1.csv` và `features_dengue_v1.csv` để train model."
>
> "**WHO FluNet** 113 nghìn rows cho cúm, 189 nước. Em bỏ cột `INF_ALL` vì missing 44%, dùng `INF_A + INF_B` làm target. **OpenDengue v1.3** 18 nghìn rows cho sốt xuất huyết, 82 nước — Brazil chiếm 71% tổng ca nên em phải log1p downstream."
>
> [NHẤN MẠNH] "**Phát hiện quan trọng nhất Session 1**: 2020-2021 vẫn có **166 nước báo cáo flu, ngang 2019**, nhưng số ca giảm **99% do NPI** — mask, lockdown. Không phải data missing. Em loại 2 năm này khỏi training để model không học sai pattern bình thường."
>
> "Dengue em thu hẹp training về 2015-2019 vì 2010-2014 chỉ có 5-12 nước báo cáo — sparse quá để học. ECDC chỉ có data từ 2021 nên không dùng training, chỉ validation hậu COVID. Đây là ví dụ **data constraint chi phối ML design**."
