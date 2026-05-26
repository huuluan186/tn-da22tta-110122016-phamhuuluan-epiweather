# Hướng dẫn sử dụng EpiWeather — Dashboard cảnh báo dịch bệnh

> **Đối tượng:** Người dùng cuối (quan trắc viên y tế, GVHD, sinh viên xem demo) — **KHÔNG cần biết ML hay code**.
>
> File này giải thích **từng nút, từng con số trên màn hình**: nó là gì, lấy từ đâu, tính như thế nào, có chính xác cho mục đích sử dụng không.
>
> Dashboard chạy ở **http://localhost:5173** (frontend), gọi data từ **http://localhost:8000/api/v1/...** (backend).

---

## Tổng quan 3 trang

| Trang | URL | Mục đích |
|---|---|---|
| **Home** (Bản đồ thế giới) | `/` | Xem nguy cơ dịch bệnh trên bản đồ toàn cầu, click quốc gia để vào chi tiết |
| **Disease Detail** (Chi tiết quốc gia) | `/country/:iso3` | Forecast 4 tuần + Trend 52 tuần cho 1 quốc gia |
| **Analytics** (Hiệu suất model) | `/analytics` | Hiệu năng AI model, không phải dùng hàng ngày |

---

# TRANG 1 — HOME (Bản đồ thế giới)

```
┌────────────────────┬──────────────────────────────────┬──────────────────┐
│  SIDEBAR TRÁI      │   BẢN ĐỒ THẾ GIỚI                │  SIDEBAR PHẢI    │
│                    │                                  │                  │
│  ▼ Disease         │   [Choropleth map]               │  Selected        │
│  [Flu] [Dengue]    │                                  │  Country         │
│                    │   Nước High = đỏ                 │                  │
│  ▼ Historical/     │   Nước Medium = cam              │  4-week Forecast │
│    Realtime        │   Nước Low = xanh dương          │                  │
│  Year:  [Select]   │   Click → mở chi tiết            │                  │
│  Week:  [Select]   │                                  │  ───────────     │
│  [Dự báo]          │                                  │  Alerts          │
│                    │                                  │  (Top 10 High)   │
│  ▼ WHO Region      │                                  │                  │
│  [WPR][AFR][...]   │                                  │                  │
│                    │                                  │                  │
│  ▼ Summary         │                                  │                  │
│  Reporting / High  │                                  │                  │
│  / Avg Risk Index  │                                  │                  │
└────────────────────┴──────────────────────────────────┴──────────────────┘
```

## A. Sidebar trái

### A.1. Disease (chọn bệnh)
- **2 lựa chọn**: Flu (cúm mùa) hoặc Dengue (sốt xuất huyết)
- Khi click → reset toàn bộ trang về tuần mới nhất của bệnh đó
  - Flu: 2026 tuần 21 (data realtime từ WHO FluNet)
  - Dengue: 2023 tuần 36 (nowcast từ OpenDengue v1.3 — không có data mới hơn)
- API tự gọi: `GET /api/v1/risk-map/{disease}/latest`

### A.2. Historical / Realtime (chọn tuần xem)
- **Năm + Tuần**: chọn tuần muốn xem
  - Flu hợp lệ: 2010-2019 (historical) + 2026 W02-W21 (realtime)
  - Dengue hợp lệ: 2010-2019 (historical) + 2021, 2022, 2023 W01-W36 (nowcast)
- **Nút "Dự báo"**:
  - **Xám / không bấm được**: khi picker = tuần đang hiển thị → không có gì để xem mới
  - Label `"Đang xem tuần hiện tại"` = bạn đang xem latest, không cần predict
  - **Bấm được khi**: đổi Năm hoặc Tuần khác với tuần đang hiển thị
  - Khi bấm → fetch lại map với tuần đã chọn
- **Nút "⟲ Latest"**: chỉ xuất hiện ở historical mode → quay về tuần mới nhất

### A.3. WHO Region (lọc theo vùng WHO)
- 6 vùng: **AFR** (Châu Phi), **AMR** (Châu Mỹ), **EMR** (Đông Địa Trung Hải), **EUR** (Châu Âu), **SEAR** (Đông Nam Á), **WPR** (Tây Thái Bình Dương)
- Click 1 hoặc nhiều vùng → bản đồ + sidebar phải + Summary **chỉ tính các nước thuộc vùng đó**
- Click lại để bỏ chọn (toggle)

### A.4. Summary (3 ô số liệu thống kê)

> **CÓ** tính theo filter WHO Region. Nguồn data: từ `entries` đã filter (= response `/risk-map/{disease}/latest`).

| Ô | Ý nghĩa | Cách tính | Ví dụ Flu W21/2026 (không filter) |
|---|---|---|---|
| **Reporting** | Số quốc gia có prediction (risk ≠ "none") | Đếm `entries` có risk in {high, medium, low} | 163 / 163 countries |
| **High** | Số quốc gia có risk = "high" | Đếm `entries.risk === 'high'` | ~23 (tuỳ tuần) |
| **Avg Risk Index** | Điểm trung bình **/ 100** | `tổng score reporting / số reporting` | ~38-45 |

**Risk Index là gì?**
- **KHÔNG phải predicted_cases**, KHÔNG phải từ ML model trực tiếp
- Là **mapping arbitrary** 4 mức rủi ro thành số 5-68:
  - `high` → 68
  - `medium` → 42
  - `low` → 18
  - `none` → 5
- Mục đích: cho phép tính "trung bình rủi ro" của 1 nhóm nước (vì không thể trung bình "High/Med/Low" trực tiếp)
- **Cảnh báo cho user**: con số này là **UX indicator**, không phải metric khoa học. Nếu muốn so sánh quốc gia với quốc gia, nên xem `Predicted Cases` trực tiếp.

## B. Bản đồ thế giới (giữa)

### B.1. Header bản đồ
- `Global Risk Map · Influenza` — tên bệnh đang xem
- Badge **LATEST** (xanh) hoặc **HISTORICAL** (vàng): trạng thái
- `W21 · 2026` — tuần đang hiển thị
- `163 country` — số nước sau khi filter

### B.2. Choropleth map
- Mỗi nước **tô màu theo risk level** của tuần đã chọn:
  - Đỏ (High) — predicted cases cao > q67 percentile của country đó
  - Cam (Medium) — predicted cases nằm giữa q33-q67
  - Xanh dương (Low) — predicted cases < q33
  - Xám (none) — không có data tuần này
- **Hover**: tooltip hiện tên + risk level
- **Click**: chọn country → hiện chi tiết ở sidebar phải

### B.3. Source API của map
```
GET http://localhost:8000/api/v1/risk-map/flu/latest
→ trả về {disease, iso_year, iso_week, count, items: [...]}
items: array các {iso3, country_name, predicted_cases, risk_level, who_region, ...}
```
- Backend đọc từ bảng `predictions` PostgreSQL
- Risk level được tính dựa trên `risk_thresholds` table (q33/q67 percentile per country)

## C. Sidebar phải — Selected Country

> Đây là phần user hỏi: "Russia RUS · Influenza HIGH ... Predicted 14 ..."

```
Selected Country
─────────────────
Russia                    [HIGH]   ← risk badge (đỏ)
RUS · Influenza

┌───────────────┬───────────────┐
│ Predicted     │ Week          │
│ 14            │ W21/2026      │
└───────────────┴───────────────┘

4-week Forecast (realtime)
W22/2026     14
W23/2026     9
W24/2026     7
W25/2026     5
                          [Xem chi tiết →]
```

### C.1. Header — tên quốc gia + risk badge
- `Russia` — tên quốc gia (từ `country_name` API)
- `RUS · Influenza` — ISO3 + bệnh đang xem
- **HIGH** (badge màu): risk level của tuần đang hiển thị (W21/2026)
- API: `GET /predictions/flu/RUS?year=2026&week=21` → trả `risk_level: "High"`

### C.2. Ô "Predicted 14"
- **Predicted cases** = số ca cúm dự báo cho Nga **tuần W21/2026**
- Đây là **output ML model** thật (LightGBM `lgbm_flu_regressor_h1_v1.pkl`)
- Đã chuyển từ log scale về scale gốc: `predicted_cases = expm1(predicted_log)`
- API: `GET /predictions/flu/RUS?year=2026&week=21` → field `predicted_cases`
- **Có ý nghĩa khoa học**: con số 14 là model nói "tuần này Nga dự kiến 14 ca cúm A/B"

### C.3. Ô "Week W21/2026"
- Tuần đang hiển thị trên map (= `activeWeek/activeYear` ở HomePage)

### C.4. "4-week Forecast (realtime)"
- 4 dòng = predict cho 4 tuần kế tiếp (h=1, h=2, h=3, h=4)
- Dùng **4 model multi-horizon riêng**:
  - h=1 dùng `lgbm_flu_regressor_h1_v1.pkl` → predict tuần kế tiếp (W22)
  - h=2 dùng `lgbm_flu_regressor_h2_v1.pkl` → W23
  - h=3, h=4 tương tự
- API: `GET /forecast/flu/RUS/nowcast` → trả 4 ForecastPoint
- **Badge** "(realtime)" hoặc "(nowcast)" hoặc "(historical)":
  - **realtime**: tuần hiện tại có data thật từ API (flu W21/2026)
  - **nowcast**: dengue 2021-2023 (có ground truth từ OpenDengue, batch không realtime)
  - **historical**: tuần trong training period 2010-2019

**Ví dụ con số "Pred 14 → 9 → 7 → 5":**
- Tuần W22: 14 ca dự báo
- Tuần W23: 9 ca → giảm 36%
- Tuần W24: 7 ca → tiếp tục giảm
- Tuần W25: 5 ca → end-of-season pattern (flu mùa đông Bắc bán cầu giảm vào mùa hè)

### C.5. Nút "Xem chi tiết →"
- Mở trang **Disease Detail** cho quốc gia này

## D. Sidebar phải — Alerts (Top 10 High Risk)

```
ALERTS · Top 10 High
┌────────────────────────────────┐
│ [BR]  Brazil                   │
│       AMR · DENV               │
│       ●HIGH                    │
│       Score 68/100  Pred 8,820 │ ← Score = 68 (mapping HIGH→68)
└────────────────────────────────┘
```

### D.1. Score 68/100
- Đây cũng là **Risk Score** mapping ở mục A.4:
  - high → **68**
  - medium → **42**
  - low → **18**
  - none → 5
- Mục đích: hiển thị "intensity bar" để user scan nhanh
- **Không phải xác suất**, **không phải probability output của classifier**
- Chỉ là UX representation

### D.2. Pred 8,820
- `predicted_cases` = số ca dự báo (cùng giá trị API trả về)
- Đây là **số đáng tin cậy nhất** cho user — output thực của model
- Format: `Pred {Math.round(predictedCases).toLocaleString()}`

## E. Bug & Tooltip mới (sau fix 23/05)

- **Nút "Dự báo" không bấm được**: là intentional. Đã thêm tooltip `"Đổi Năm hoặc Tuần ở trên rồi nhấn để xem dự báo tuần khác"` để user hiểu. Label cũng đổi `"Đang xem tuần hiện tại"` / `"Dự báo tuần đã chọn"` để rõ trạng thái.

---

# TRANG 2 — Disease Detail (Chi tiết quốc gia)

URL: `/country/:iso3` (ví dụ `/country/BRA`)

```
[← Back to map]    Brazil    [Risk: High]
                   Dengue · W36 · 2023

┌──────────────────────────────────────────────────────┐
│ 4-week Forecast · Dengue       ● nowcast / historical│
│ As of W36/2023 → W37-W40/2023                        │
│                                                      │
│ ⚠ Năm 2023 là nowcast dengue (OpenDengue v1.3...)    │
│                                                      │
│ [Line chart 4 horizons với confidence band]          │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│ 52-week Trend · Dengue                               │
│ [Area chart cases over time, smooth]                 │
└──────────────────────────────────────────────────────┘

┌─────────────────┬─────────────────┬─────────────────┐
│ Predicted Cases │ Risk Level      │ Disease         │
│ 8,820           │ High            │ DENV            │
└─────────────────┴─────────────────┴─────────────────┘
```

## F.1. Forecast Chart (4 tuần kế tiếp)
- **Đường line** = predicted_cases cho 4 horizon h=1..4
- API: `GET /forecast/dengue/BRA/nowcast`
- Có Year/Week picker để xem historical (vd 2018-W30)

## F.2. Trend Chart (52 tuần)
- API: `GET /predictions/dengue/BRA/history?start_year=2010&end_year=2019`
- Hiển thị 52 tuần gần nhất của 10 năm training
- **Predicted_cases** (đường) + actual_cases (nếu có)

## F.3. Summary Cards (3 ô)
- **Predicted Cases**: cùng con số `predicted_cases` từ `/predictions/...` (tuần đang xem)
- **Risk Level**: cùng `risk_level` từ API
- **Disease**: tên ngắn (DENV/INFL)

## F.4. DataCoverage Warning Badge

3 màu:
- 🟢 **realtime** — flu 2026 (data thật vừa pull từ WHO)
- 🟡 **nowcast** — dengue 2021-2023 (OpenDengue v1.3 batch, có ground truth nhưng không realtime)
- 🟠 **historical** — 2010-2019 (training period, có actual để compare)
- 🔴 **extrapolation warning** — năm ngoài cả 3 phạm vi → "Không có ground truth để validate độ chính xác"

---

# TRANG 3 — Analytics

URL: `/analytics`

Hiển thị hiệu năng AI model cho cả flu + dengue:
- **R² Cross-Validation** cho h=1..4 (bar chart)
- **Feature Importance** top 10 (horizontal bar)

API: `GET /analytics/model-performance/{disease}` + `/analytics/feature-importance/{disease}`

→ Phần này dành cho người **muốn xem độ tin cậy của model**, không phải dùng hàng ngày.

---

# BẢNG TÓM TẮT: TỪNG CON SỐ DÙNG CHO MỤC ĐÍCH GÌ

| Con số trên UI | Nguồn | Có dùng cho người dùng cuối không? |
|---|---|---|
| **Predicted Cases** (Brazil: 8,820) | ML model output thực, `expm1(predicted_log)` | ✅ **Có** — đây là con số cốt lõi |
| **Risk Level** (High/Med/Low) | Phân loại từ `risk_thresholds` q33/q67 | ✅ **Có** — cảnh báo chính |
| **4-week Forecast** | Multi-horizon h=1..4 từ 4 model riêng | ✅ **Có** — xu hướng tuần kế tiếp |
| **Score 68/100** | Mapping arbitrary high→68, med→42, low→18 | ⚠️ **Chỉ UX** — không phải metric |
| **Avg Risk Index 42/100** | Trung bình Score của các country reporting | ⚠️ **Chỉ UX** — để so sánh nhóm |
| **Reporting count** (163) | Số country có prediction tuần đó | ✅ **Có** — coverage indicator |
| **High count** (23) | Số country risk=high | ✅ **Có** — số cảnh báo |
| **Filter WHO Region** | Frontend filter, có ảnh hưởng Summary | ✅ **Có** — focus theo vùng |

---

# CÁCH DÙNG ĐÚNG cho USER

**Use case 1: "Tuần này nước nào nguy hiểm?"**
1. Mở Home → chọn Flu hoặc Dengue
2. Xem bản đồ + sidebar phải "Alerts" → top 10 High risk
3. Hoặc xem Summary "High count"

**Use case 2: "Tuần tới Việt Nam ra sao?"**
1. Mở Home → click vào Vietnam trên bản đồ
2. Sidebar phải hiện "4-week Forecast" → đọc 4 dòng W22, W23, W24, W25
3. Hoặc click "Xem chi tiết →" để vào Disease Detail

**Use case 3: "Nước này năm 2018 có dịch không?"**
1. Mở Home → chọn Year=2018, Week=30 → bấm "Dự báo tuần đã chọn"
2. Bản đồ hiện trạng thái 2018-W30
3. Hoặc vào Disease Detail → dùng historical picker

**Use case 4: "Vùng Tây Thái Bình Dương nguy cơ ra sao?"**
1. Mở Home → chọn WHO Region = WPR
2. Bản đồ + Summary + Alerts đều filter theo WPR

---

**Tóm tắt 1 câu cho GVHD:**

> Dashboard có 2 loại số: **số ML model thực** (Predicted Cases, Risk Level, 4-week Forecast) — dùng cho ra quyết định; **số UX** (Score 0-100, Avg Risk Index) — chỉ để so sánh nhanh, không phải metric khoa học.
