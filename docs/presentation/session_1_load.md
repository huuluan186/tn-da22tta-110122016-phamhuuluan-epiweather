# Session 1: Load Raw Data & Sanity Check (Notebook v5/v6)

> **Mục tiêu thuyết trình:** Người chấm hiểu mình lấy dữ liệu ở đâu, 4 nguồn khác nhau ra sao, đã filter và sanity check như thế nào trước khi đụng vào model.

---

## 1. Vì sao có 4 nguồn dữ liệu

Đề tài yêu cầu kết hợp **y tế** (số ca bệnh) + **khí hậu** (thời tiết) theo (quốc gia × tuần). Không có **1 nguồn duy nhất** cover toàn cầu cả 2 loại → phải kết hợp 4 nguồn.

| Nguồn | Loại | Cover | Period | Vai trò |
|---|---|---|---|---|
| **WHO FluNet** | Cúm | 189 nước | 1995–nay (weekly) | Train flu target |
| **OpenDengue v1.3** | Sốt xuất huyết | 82 nước (chủ yếu nhiệt đới) | 1990–2023-W36 | Train dengue target |
| **ERA5 ECMWF** | Khí hậu | Toàn cầu (lưới 0.25°) | 1940–nay | Train weather features (Session 2) |
| **ECDC Sentinel + ILI** | Cúm châu Âu | 30 nước EU | 2021+ | Validation hậu COVID (không train) |

---

## 2. Load FluNet (Cell 1.1, 1.2)

```python
flu = pd.read_csv(FILES['flunet'], low_memory=False)
# Shape ban đầu: (183K rows, 53 cols)
```

**Quyết định + lý do:**

| Cột | Hành động | Lý do |
|---|---|---|
| `INF_ALL` | Bỏ | Missing 44% |
| `PARAINFLUENZA` | Bỏ | Missing 85.5% |
| `RSV_PROCESSED` | Bỏ | Khác đơn vị với `RSV`, correlation 0.729 (không 1.0) |
| `INF_A`, `INF_B` | **Giữ** | Build target `influenza_total = INF_A + INF_B` |
| UK X09-X12 | Gộp thành GBR | WHO không có mã GBR tổng hợp |
| `fillna(0)` cho INF_A, INF_B | Áp dụng | Missing = không báo cáo, không phải = 0 ca |

**Output Session 1.1:** FluNet sau filter 2010-2022 → 113K rows, 189 nước báo cáo.

**Coverage finding:**
- 2020-2021: vẫn 166-167 nước báo cáo (ngang 2019, không drop) → confirm data không thiếu
- Số ca flu 2020 giảm 99% là **do NPI (mask, lockdown)**, không phải missing → loại 2020-2021 khỏi training

---

## 3. Load OpenDengue v1.3 (Cell 1.3, 1.4)

```python
dengue = pd.read_csv(FILES['dengue'], low_memory=False)
# Shape: (18K weekly rows, 15 cols) → 82 quốc gia
```

**Quyết định + lý do:**

| Aspect | Hành động | Lý do |
|---|---|---|
| `T_res` (resolution) | Chỉ giữ `Week` + `Month` | 77.8% Week, 10.5% Month, 11.7% Year (Year quá thô) |
| Period | Training **2015-2019** thay 2010-2019 | 2010-2014 chỉ 5-12 nước báo cáo (sparse) |
| Brazil | Apply log1p downstream | **71% tổng ca toàn cầu** → dominate nếu raw scale |
| Period nowcast | 2021-2023-W36 | OpenDengue v1.3 batch released đến 2023-W36 |

**Phát hiện:** Dengue 2020 dropping toàn cầu do COVID disruption → loại 2020 khỏi nowcast.

---

## 4. Load ECDC (Cell 1.5)

```python
ecdc_sen = pd.read_csv(FILES['ecdc_sen'])  # Sentinel surveillance
ecdc_ili = pd.read_csv(FILES['ecdc_ili'])  # ILI rates age-stratified
# Cover: 30 nước EU, từ 2021
```

**Vai trò:** Validation độc lập tuần hậu COVID + display dashboard. **KHÔNG dùng để training** vì period 2021+ không overlap với training window 2010-2019.

---

## 5. Bảng tổng kết Session 1

| Dataset | Shape sau load | Cover | Quyết định period |
|---------|----------------|-------|-------------------|
| FluNet | (113K rows, 53 cols) | 189 nước | Train 2010-2019, skip 2020-2021 (NPI) |
| OpenDengue | (18K rows, 15 cols) | 82 nước | Train 2015-2019, nowcast 2021-W01 → 2023-W36 |
| ECDC Sentinel | ~50K rows | 30 nước EU, 2021+ | Validation only |
| ECDC ILI | ~30K rows | Age-stratified, 2021+ | Validation only |

---

## Key Insights Session 1 (slide thuyết trình)

1. **4 nguồn = 4 ngôn ngữ khác** — chuẩn hóa là bước khó nhất, không phải training.
2. **`INF_ALL` missing 44% → bỏ, dùng `INF_A + INF_B`** = lý do EDA quan trọng hơn chọn model.
3. **2010-2014 dengue quá sparse → thu hẹp về 2015-2019** = không tin "có nhiều data hơn = tốt hơn".
4. **2020-2021 vẫn 166 nước báo cáo nhưng case giảm 99% do NPI** → loại khỏi training để model không học pattern bất thường.
5. **ECDC chỉ có 2021+** → không match training window → chỉ dùng validation. Bài học data constraint chi phối ML design.

---

## Câu nói thuyết trình cho Session 1

> "Đầu tiên em nói về data. Em dùng **4 nguồn** vì không có nguồn nào single-source cover được toàn cầu cho cả y tế lẫn khí hậu."
>
> "**WHO FluNet** 113 nghìn rows cho cúm, 189 nước. Em bỏ cột `INF_ALL` vì missing 44%, dùng `INF_A + INF_B` làm target. **OpenDengue v1.3** 18 nghìn rows cho sốt xuất huyết, 82 nước — Brazil chiếm 71% tổng ca nên em phải log1p downstream."
>
> [NHẤN MẠNH] "**Phát hiện quan trọng nhất Session 1**: 2020-2021 vẫn có **166 nước báo cáo flu, ngang 2019**, nhưng số ca giảm **99% do NPI** — mask, lockdown. Không phải data missing. Em loại 2 năm này khỏi training để model không học sai pattern bình thường."
>
> "Dengue em thu hẹp training về 2015-2019 vì 2010-2014 chỉ có 5-12 nước báo cáo — sparse quá để học. ECDC chỉ có data từ 2021 nên không dùng training, chỉ validation hậu COVID. Đây là ví dụ **data constraint chi phối ML design**."
