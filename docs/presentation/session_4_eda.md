# Session 4: EDA + CCF Lag Analysis trên Master File (Notebook v5/v6)

> **Mục tiêu thuyết trình:** EDA là 50% giá trị của project — đây là phần phân biệt "engineer hiểu data" và "engineer chỉ chạy code". Phát hiện EDA chi phối mọi quyết định downstream (target transform, period filter, lag config).

---

## 1. EDA Workflow — 6 bước trên master file

| Cell | Bước | Phát hiện chính |
|---|---|---|
| 4.1 | Distribution target (raw vs log1p) | log1p giảm skew 25.6 → 1.04 |
| 4.2 | Coverage heatmap nước × năm | 2020-2021 vẫn 166 nước nhưng case giảm 99% (NPI) |
| 4.3 | Seasonality peak week theo hemisphere | Bắc bán cầu peak W6, Nam bán cầu peak W28 — lệch đúng 22 tuần |
| 4.4 | **Cross-Correlation Function (CCF)** | Lag tối ưu weather → disease — **đóng góp khoa học** |
| 4.5 | Case studies Brazil, USA, Vietnam | Confirm pattern epidemiological đúng literature |
| 4.6 | Tổng kết quyết định EDA | Lock vào feature engineering Session 5 |

---

## 2. Cell 4.1 — Distribution + log1p transform

**Phân tích trước log:**

| Disease | Skew | Min | Max | Median |
|---|---|---|---|---|
| Flu raw | **25.6** | 0 | 152,341 (China 2009) | 14 |
| Dengue raw | **12.6** | 0 | 146,000 (Brazil 2016) | 11 |

→ **Cực skewed**. Brazil 2016 outbreak gấp **13,000×** median dengue → nếu train raw, model bị Brazil dominate hoàn toàn.

**Sau log1p:**

| Disease | Skew sau log1p |
|---|---|
| Flu | **1.04** (gần normal) |
| Dengue | **0.93** (gần normal) |

```python
master['inf_log1p']    = np.log1p(master['influenza_total'])
master['dengue_log1p'] = np.log1p(master['dengue_cases'])
```

**Đây là 1 dòng code nhưng đổi cả game** — chi tiết trong [`hanh_trinh_cai_thien.md`](hanh_trinh_cai_thien.md): R² flu nhảy từ 0.488 (v1, không log) lên 0.791 (v2, có log).

---

## 3. Cell 4.2 — Coverage heatmap

Heatmap (nước × năm) cho cả flu + dengue:

**Flu coverage:**
- 2010: 107 nước báo cáo
- 2018-2019: 144-147 nước (peak)
- 2020-2021: **166-167 nước** (ngang 2019, không drop)
- → 2020-2021 KHÔNG thiếu data, mà flu **giảm thật 99% do NPI**

**Dengue coverage:**
- 2010-2014: 5-12 nước (sparse)
- 2015-2019: 19-33 nước (đủ để training)
- 2020: drop nặng do COVID disruption
- 2021-2023-W36: 56 nước (OpenDengue v1.3 batch — nowcast era)

**Decision lock:**
- Flu training **2010-2019**, skip 2020-2021
- Dengue training **2015-2019**, nowcast 2021-2023-W36

---

## 4. Cell 4.3 — Seasonality: hemisphere phase shift

**Plot peak week (week-of-year of max cases) for each country.**

```python
peak_week = master.groupby(['iso3', 'hemisphere'])['influenza_total'].apply(
    lambda x: x.idxmax()[2]  # ISO week
)
```

**Kết quả:**
- Bắc bán cầu (USA, France, Russia, China): peak **W6** (tháng 2)
- Nam bán cầu (Australia, South Africa, Brazil South): peak **W28** (tháng 7)
- **Phase shift = 22 tuần** = đúng nửa năm

→ **Confirm hoàn hảo lý thuyết dịch tễ học:** flu peak vào mùa đông local. Data **đáng tin cậy**, không có bug merge.

Decision: encode `HEMISPHERE_NH` / `HEMISPHERE_SH` làm feature → model học pattern theo nửa cầu.

---

## 5. Cell 4.4 — Cross-Correlation Function (CCF) ⭐ **Đóng góp khoa học**

**Vấn đề:** Thời tiết tuần này ảnh hưởng ca bệnh tuần nào? Cùng tuần (lag 0), 2 tuần sau (lag 2), hay 8 tuần sau?

**Naive approach:** dùng weather lag `[1, 2, 3]` đồng loạt cho mọi biến.

**SAI** — vì virus cúm có incubation + reporting delay ~2-8 tuần, muỗi vector-borne ~4-12 tuần. Hard-code lag không đủ.

**CCF method:**

```python
def ccf(x, y, max_lag=24):
    return [np.corrcoef(x[:-lag] if lag > 0 else x, y[lag:] if lag > 0 else y)[0,1]
            for lag in range(max_lag + 1)]
```

Tính CCF giữa từng cặp (weather var, disease cases) qua lag 0-24 tuần, tìm **peak correlation** = lag tối ưu.

**Kết quả lag tối ưu:**

| Disease | Variable | Lag tối ưu | Correlation | Validate literature |
|---|---|---|---|---|
| Flu | Solar radiation | **7 tuần** | r = −0.41 | UV inactivation virus (Shaman 2009 PNAS) |
| Flu | Temperature | **3 tuần** | r = −0.37 | Cold air → mucus dry, virus xâm nhập |
| Flu | Humidity | **7 tuần** | r = +0.31 | Khớp Shaman & Kohn 2009 PNAS |
| Flu | Dewpoint | **2 tuần** | r = +0.25 | Aerosol stability |
| Dengue | Temperature | **11 tuần** | r = +0.31 | Khớp **Lowe et al 2014 Lancet ID** |
| Dengue | Dewpoint | **8 tuần** | — | Vòng đời muỗi |
| Dengue | Precipitation | **6 tuần** | — | Mưa tạo breeding sites |
| Dengue | Humidity | **1 tuần** | — | Mosquito activity short-term |
| Dengue | Solar | **16 tuần** | — | UV ảnh hưởng dài hạn |

**Phát hiện quan trọng:** **Lag dengue dài hơn flu RẤT NHIỀU** (6-16w vs 1-8w) — đúng với epidemiology:
- Flu lây trực tiếp qua giọt bắn → incubation 1-4 ngày → lag short
- Dengue qua muỗi Aedes: trứng → ấu trùng → trưởng thành 2-3 tuần → cắn người → ủ bệnh 4-7 ngày → cases báo cáo → **lag 2-3 tháng**

→ Decision: hardcode lag tối ưu vào feature engineering Session 5, không default `[1,2,3]`.

---

## 6. Cell 4.5 — Case studies

3 quốc gia tiêu biểu (Brazil, USA, Vietnam) — plot cases + weather theo thời gian.

**Brazil 2016 dengue outbreak:** 146K ca tuần peak → outlier mạnh nhất dataset → confirm cần log1p + sẽ inflate Endemic Channel baseline 2017-2018 (limitation document Session 6).

**USA flu:** Pattern annual peak W6 ổn định 2010-2019, dip sharp 2020-2021 (NPI) → confirm loại 2020-2021.

**Vietnam:** Có cả flu + dengue, peak khác nhau (flu W47-W3 dry season, dengue W30-W40 wet season) → tropical mixed pattern.

---

## 7. Cell 4.6 — Tổng kết quyết định EDA

| Quyết định | Lý do | Lock vào |
|---|---|---|
| `log1p` cho flu + dengue | Skew 25.6/12.6 → 1.04/0.93 | Session 5 target |
| Training flu 2010-2019, skip 2020-2021 | NPI làm flu giảm 99% giả tạo | Session 6 train period |
| Training dengue 2015-2019 | 2010-2014 chỉ 5-12 nước (sparse) | Session 6 train period |
| Encode hemisphere NH/SH | Phase shift 22 tuần | Session 5 features |
| Lag flu: temp=3w, hum=7w, solar=7w, dewpoint=2w | CCF + Shaman 2009 | Session 5 features |
| Lag dengue: temp=11w, hum=1w, solar=16w, precip=6w, dewpoint=8w | CCF + Lowe 2014 | Session 5 features |
| Dengue cần warmup 18w | Max lag 16 + buffer 2w | Session 5 build |
| Flu cần warmup 8w | Max lag 7 + buffer 1w | Session 5 build |

---

## Key Insights Session 4 (slide thuyết trình)

1. **log1p là quyết định quan trọng nhất** — 1 dòng code, đổi skew 25.6 → 1.04, R² nhảy 0.488 → 0.791.
2. **Phase shift hemisphere 22 tuần** = sanity check confirm data đáng tin cậy, không có bug merge.
3. **CCF lag analysis là đóng góp khoa học** — em tìm lag từ DATA, validate với LITERATURE (Lowe 2014, Shaman 2009). Không guesswork.
4. **Lag dengue dài hơn flu rất nhiều** (16w vs 7w) — đúng vòng đời muỗi Aedes 2-3 tháng vs flu lây trực tiếp 1-4 ngày.
5. **EDA = 50% công việc project**. Khi nói chuyện GVHD, đừng nhảy thẳng vào model — phải kể câu chuyện data trước.

---

## Câu nói thuyết trình cho Session 4

> "Session 4 là EDA + CCF lag analysis — em làm rất kỹ. **6 bước** trên master file: distribution, coverage, seasonality, CCF, case studies, summary."
>
> "**3 phát hiện quan trọng nhất:**"
>
> "**Phát hiện 1: log1p transform**. Phân phối skew **25.6 cho flu**, 12.6 cho dengue. Brazil 2016 outbreak gấp **13,000 lần** median dengue. Nếu train raw, model bị Brazil dominate. Em apply log1p — skew giảm về 1.04, gần normal. **1 dòng code, R² nhảy từ 0.488 lên 0.791.**"
>
> "**Phát hiện 2: phase shift hemisphere 22 tuần**. Bắc bán cầu peak flu tuần 6, Nam bán cầu tuần 28 — lệch đúng nửa năm. Confirm hoàn hảo lý thuyết dịch tễ → data đáng tin cậy, không bug merge."
>
> [NHẤN MẠNH] "**Phát hiện 3 — đóng góp khoa học**: **Cross-Correlation Function** tìm lag tối ưu weather → disease. Em **không default [1,2,3]** lag, mà tính CCF qua lag 0-24 tuần."
>
> "**Lag flu**: temperature lag 3w, solar radiation lag 7w (UV inactivation, khớp Shaman 2009 PNAS), humidity lag 7w. **Lag dengue**: temperature lag 11w (khớp Lowe 2014 Lancet ID), solar lag 16w, precipitation lag 6w."
>
> "Điểm quan trọng: **lag dengue dài hơn flu rất nhiều** — vì vòng đời muỗi Aedes phức tạp (trứng → ấu trùng → trưởng thành → cắn người → ủ bệnh) tốn 2-3 tháng. Còn flu lây trực tiếp qua giọt bắn, chỉ 1-2 tuần. Em tìm lag từ data, validate với literature — **evidence-based, không guesswork**."
