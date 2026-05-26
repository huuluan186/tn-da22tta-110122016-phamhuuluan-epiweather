# Hành Trình Cải Thiện Model — Từ v1 đến v5

> **Mục tiêu:** Trình bày cho người chấm thấy mình **không chỉ chạy code 1 lần ra kết quả**. Mình đi qua 5 version với 6 phát hiện lớn — đây là quá trình **học bằng làm**, khắc phục sai lầm để có model production.

---

## Tổng quan các version

| Version | Approach | Flu R² | Dengue R² | Flu F1 | Dengue F1 | Note |
|---------|----------|--------|-----------|--------|-----------|------|
| **v1** | Single XGBoost, target raw cases | 0.488 | 0.602 | — | — | Baseline naive |
| **v2** | Single XGBoost + log1p target | 0.791 | 0.849 | — | — | **+30% R²** từ 1 dòng code |
| **v3** | Multi-model classification (Bortman labels) | — | — | 0.492 | 0.516 | RF beat XGB on classification |
| **v4** | + who_region_enc + quarter + log1p AR | — | — | 0.534 | 0.508 | Marginal improvement |
| **v5** | **Hybrid Regression + Classification, walk-forward CV 6 folds, CCF lag refined** | **0.9019** | **0.9366** | **0.542** | **0.475** | **Production-ready** |

---

## Cải thiện 1 — log1p Target Transform (v1 → v2, +30% R²)

### Vấn đề:
- v1 train trên raw `INF_A + INF_B`, R² flu = 0.488
- Distribution skew = 25.6 (Brazil dengue: skew = 12.6)
- Model bị chi phối bởi outlier — predict đúng Brazil = R² cao, sai 100 nước khác vẫn R² cao

### Fix:
```python
df['inf_log1p'] = np.log1p(df['INF_A'] + df['INF_B'])
```

### Kết quả:
- Skew flu: 25.6 → 1.04 (gần normal)
- R² flu: **0.488 → 0.791** (+30%)
- R² dengue: 0.602 → 0.849 (+25%)

**Bài học:** 1 dòng code. Lý do hoạt động: tree-based regressor optimize MSE = squared error → outlier dominate gradient. Log compress → MSE đều hơn.

---

## Cải thiện 2 — Loại 2020-2021 khỏi training (v2)

### Vấn đề:
- Lúc đầu mình tưởng 2020-2021 missing nhiều do COVID disrupt reporting
- Sau khi check: 2020-2021 vẫn **166-167 nước báo cáo** (ngang 2019, không drop)
- Nhưng số ca flu **giảm 99%** do NPI (mask, lockdown, social distance)

### Fix:
- Loại 2020-2021 khỏi training (không phải vì missing, mà vì **artificial drop**)
- Train 2010-2019, validate 2022 (post-COVID, NPI đã relax)

### Kết quả:
- Không có drop R², nhưng generalization tốt hơn trên 2022

**Bài học:** Đừng tin assumption (missing = ít data), phải check actual numbers.

---

## Cải thiện 3 — Bortman 1999 Endemic Channel Labels (v2 → v3)

### Vấn đề:
- v2 chỉ làm regression — không đáp ứng yêu cầu đề tài "cảnh báo mức độ Low/Med/High"
- Naive approach: chia tertile theo cases → **sai** vì cases mỗi nước khác nhau (Brazil 10K ca/tuần, Singapore 50 ca/tuần — không thể dùng cùng threshold)

### Fix:
- Endemic channel: baseline = mean(5 năm trước), upper = baseline + 2σ
- **Per (iso3, iso_week)** — mỗi nước có threshold riêng
- Cite Bortman 1999 + WHO EWARS Technical Guide 2012

### Kết quả:
- Class balance hợp lý: Flu 56/26/17, Dengue 47/30/23
- F1 dengue = 0.516, F1 flu = 0.492

**Bài học:** Phải cite literature, không tự nghĩ ra threshold.

---

## Cải thiện 4 — Multi-model so sánh, không default XGBoost (v3)

### Vấn đề:
- v2 chỉ dùng XGBoost — assumption "XGBoost là chuẩn"
- v3 mình thử 6 models: Majority, SWLY, LogReg, RF, XGB, LightGBM

### Phát hiện:
- **Random Forest thắng cả 2 disease** out-of-the-box (F1 0.492 flu, 0.516 dengue)
- XGBoost = LightGBM ≈ 0.47-0.51 (cluster gần nhau)
- LogReg = 0.39-0.45 (kém hơn tree)

### Quyết định:
- v3 champion: Random Forest cho cả 2
- (sau này v5 chốt LightGBM cho flu vì có thêm AR features)

**Bài học:** Demonstrate critical thinking. RF robust hơn với data nhỏ → bagging > boosting cho small dataset.

---

## Cải thiện 5 — log1p AR features + WHO region encoding (v3 → v4)

### Vấn đề:
- Sanity check phát hiện AR lag features có skewness extreme:
  - `inf_cases_lag*`: median=5, max=13,193 (ratio ~2,600)
  - `dengue_total_lag*`: median=11, max=146,906 (ratio ~13,000)
- Missing 2 features đã proven từ approach cũ: `who_region_enc`, `quarter`

### Fix:
```python
# Log1p AR features
df['flu_log_lag1'] = np.log1p(df.groupby('iso3')['inf_cases'].shift(1))
df['flu_log_lag2'] = np.log1p(df.groupby('iso3')['inf_cases'].shift(2))

# WHO region
df['who_region_enc'] = df['iso3'].map(WHO_REGION_MAP).fillna(-1)
df['quarter'] = ((df['iso_week'] - 1) // 13) + 1
```

### Kết quả:
- F1 flu: 0.492 → 0.534 (+0.042)
- F1 dengue: 0.516 → 0.508 (marginal, nhưng AUC tăng)

**Bài học:** Sanity check pre-train QUAN TRỌNG. Không log1p AR = model học scale Brazil áp lên 100 nước nhỏ.

---

## Cải thiện 6 — CCF Lag Refined + Hybrid Approach (v4 → v5, FINAL)

### Vấn đề:
- v3-v4 vẫn dùng weather lag `[1, 2, 3]` đồng loạt cho mọi biến — sai lý thuyết
- Không có **regression** trong v3-v4 → mất nhánh "dự báo số ca cho dashboard biểu đồ"
- Validation single-split → không rigorous

### Fix v5 (build lại notebook từ đầu):
1. **CCF lag analysis** trên 30 nước top → tìm lag tối ưu per (disease, weather):
   - Flu: solar lag 7, temp lag 3, humidity lag 7, dewpoint lag 2
   - Dengue: temp lag 11, dewpoint lag 8, precip lag 6, humidity lag 4
2. **Hybrid Regression + Classification**: làm cả 2 nhánh
3. **Walk-forward CV 6 folds** (val 2014-2019) — chuẩn time-series
4. **5 models regression** + **1 classifier** so sánh
5. **Optuna tuning** champion model
6. **Champion khác nhau per disease**: LightGBM flu, RF dengue

### Kết quả final:
- **Flu R² = 0.9019** (so với v2: 0.791, **+0.11**)
- **Dengue R² = 0.9366** (so với v2: 0.849, **+0.087**)
- **Flu F1 = 0.542** (vượt mục tiêu 0.50)
- **Dengue F1 = 0.475** (gần đạt, document làm limitation)

**Bài học:** Validation rigorous + multi-model so sánh + CCF từ data = production-grade pipeline.

---

## Version 6 — Multi-Horizon Extension (chốt 21/05/2026)

### Vấn đề v5

v5 chỉ predict **h=1** (tuần tới). Đề tài yêu cầu "dự báo theo giai đoạn/mùa/tháng" → cần forecast 2-4 tuần.

### Quyết định v6

Train **4 model riêng** cho h=1, h=2, h=3, h=4. Mỗi model dùng feature **actual** (không recursive) để tránh error propagation.

### Kết quả

| h | Flu (LGBM) | Dengue (RF) | Lowe 2014 |
|---|---|---|---|
| 1 | 0.866 | 0.929 | 0.78-0.85 |
| 2 | 0.829 | 0.919 | 0.70-0.78 |
| 3 | 0.793 | 0.909 | 0.62-0.72 |
| 4 | 0.757 | 0.898 | 0.55-0.68 |

**8/8 horizon vượt benchmark Lowe 2014 Lancet ID.**

**Phát hiện bất ngờ:** dengue degradation gentler (0.010 R²/horizon) hơn flu (0.036 R²/horizon) — vì lag dengue dài 6-14 tuần phủ xa hơn flu 1-7 tuần, plus pattern endemic năm cả 12 tháng.

**Bài học:** Không stop ở h=1 dù v5 đã đẹp — đề tài yêu cầu forecast multi-horizon, push thêm 1 vòng để có deliverable đầy đủ.

---

## Phase A — Realtime Production (chốt 22-23/05/2026)

### Vấn đề v6

Notebook v6 có 10 model .pkl với R² > 0.85, nhưng:
- Chỉ chạy trên Colab → user cuối không truy cập được
- Data train chỉ tới 2019 → predict 2026 cần data thật từ đâu?
- Mỗi tuần WHO/Open-Meteo cập nhật → ai pull, ai rebuild features, ai predict?

### Quyết định Phase A

Build **production system** 4 layers:
1. 4 sync scripts idempotent (sync_flunet, sync_weather, feature_builder, batch_predict)
2. PostgreSQL với partition (16 bảng, 31 partitions)
3. FastAPI + ML engine load 10 .pkl vào memory
4. APScheduler 4 cron jobs tự động hàng tuần

### Kết quả realtime/nowcast

| Disease | Latest tuần | Countries | Source |
|---|---|---|---|
| Flu | 2026-W21 | 163 | WHO FluNet API weekly |
| Dengue | 2023-W36 | 56 | OpenDengue v1.3 batch |

**Bài học:** ML model trong notebook ≠ ML system production. Phải tính đến scheduler, idempotent, schema migration, error handling.

---

## Tóm tắt timeline đầy đủ

| Tuần | Version | Milestone | R² flu | R² dengue |
|------|---------|-----------|--------|-----------|
| Tuần 1 (~28/04) | v1 | Setup pipeline, baseline | 0.488 | — |
| Tuần 2 (~05/05) | v2 | log1p transform | 0.791 | 0.849 |
| Tuần 3 (~13/05) | v3 | Multi-model + classification | — | — |
| Tuần 3 (~14/05) | v4 | WHO region + log1p AR | — | — |
| Tuần 4 (16-17/05) | v5 | Hybrid + walk-forward CV + CCF lag | **0.902** | **0.937** |
| Tuần 5 (21/05) | **v6** | **Multi-horizon h=1..4** | **0.866→0.757** | **0.929→0.898** |
| Tuần 5 (22-23/05) | **Phase A** | **Realtime + Nowcast Production** | 163 nước 2026-W21 | 56 nước 2023-W36 |

**Trong 4 tuần đi từ R² 0.488 → 0.9019 (v5) → multi-horizon 4 tuần → production realtime** — đây là quá trình ML + MLOps thực sự.

---

## Insights cho slide bảo vệ

1. **Không dừng ở baseline đầu tiên** — mỗi version đi qua phát hiện cụ thể, không random tuning.
2. **Mỗi cải thiện đều có rationale** — log1p (statistical reason), Bortman (literature), CCF (data + literature), walk-forward (time-series chuẩn), multi-horizon (đề tài yêu cầu forecast giai đoạn).
3. **Demonstrate critical thinking** — RF beat XGB là phát hiện đáng kể, không default trust framework.
4. **Honest limitation** — F1(High) dengue thấp = realistic limit của data, document rõ ràng, không cố hide.
5. **Production-ready không chỉ là từ ngữ** — 10 model .pkl + FastAPI + PostgreSQL + APScheduler **chạy thật** với data realtime, không phải mock.
6. **MLOps awareness** — sync scripts idempotent, schema partition, DataCoverage warning, scheduler error handling. Bài học vượt khỏi notebook ML.
