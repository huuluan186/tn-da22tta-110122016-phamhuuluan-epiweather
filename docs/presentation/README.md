# Thuyết trình Pipeline ML — EpiWeather KLTN (Notebook v5 + v6)

> **Giọng văn:** Mình đang nói chuyện trực tiếp với người chấm điểm — giả định họ chưa biết gì về dự án.
> Đọc như nghe thuyết trình. Không phải tài liệu kỹ thuật để tự đọc.
>
> **Notebook v5/v6 có đúng 8 session làm việc** (Session 0 là setup môi trường, không tính). Mỗi session độc lập, ghi output ra CSV → restart Colab không phải chạy lại từ đầu.

---

## Bức tranh toàn cảnh trước khi bắt đầu

**Câu hỏi mình giải:** Dựa vào dữ liệu thời tiết toàn cầu và lịch sử ca bệnh, **có thể dự báo nguy cơ bùng phát dịch cúm và sốt xuất huyết** vài tuần tới ở bất kỳ quốc gia nào không?

Nghe đơn giản, nhưng dưới bề mặt có nhiều thứ phức tạp:
- Dữ liệu đến từ **4 nguồn khác nhau**, định dạng khác nhau, độ phủ khác nhau
- **163 quốc gia** sau khi merge, mỗi nước có mùa bệnh khác nhau (bán cầu Bắc đỉnh tuần 6, bán cầu Nam đỉnh tuần 28)
- Dữ liệu thời tiết ở dạng **lưới địa lý 721×1440 điểm** (0.25°), không phải theo quốc gia
- Phải làm **CẢ HAI bài toán**: dự báo số ca (Regression) và phân loại mức nguy cơ (Classification Low/Medium/High)
- Phải forecast **multi-horizon h=1..4 tuần** (Session 8) cho ứng dụng thực tế

---

## Approach v5+v6 — Hybrid Regression + Classification + Multi-horizon

**v5 (chốt 16/05/2026):** Hybrid Regression + Classification cho h=1.
**v6 (chốt 21/05/2026):** Mở rộng multi-horizon h=1, 2, 3, 4 tuần.

**Nhánh A — Regression** (dự báo số ca, log1p):
- Models so sánh: Naive baseline, Prophet, XGBoost, LightGBM, Random Forest
- Metrics: RMSE, MAE, R²
- Champion: **LightGBM cho flu**, **Random Forest cho dengue**

**Nhánh B — Classification** (phân loại mức nguy cơ):
- Model: XGBClassifier (multi:softprob, 3 lớp)
- Label: Endemic Channel — `Low: < baseline`, `Medium: baseline → baseline+2σ`, `High: ≥ baseline+2σ` (Bortman 1999, WHO EWARS Technical Guide 2012)
- Metrics: macro-F1, AUC OvR, Precision/Recall per class

**Validation scheme:** Walk-forward Cross-Validation 6 folds (val_year 2014, 2015, ..., 2019) + **2022 hold-out** (post-COVID, Session 7).

---

## Sơ đồ pipeline tổng thể (8 sessions)

```
SESSION 1 — LOAD RAW DATA
  WHO FluNet      ──┐   (183K rows → 113K filter 2010-2022, 189 nước)
  OpenDengue V1.3 ──┤   (18K weekly, 82 nước, Brazil chiếm 71%)
  ECDC Sentinel   ──┘   (validation 2021+, không train)
        │
        ▼
SESSION 2 — ERA5 DOWNLOAD/PROCESS
  ERA5 ECMWF (6.2GB NetCDF, lưới 721×1440, 17 biến)
  → KD-tree k=4 weighted average → 197 nước centroids
  → era5_weekly_2010_2019_final.csv
        │
        ▼
SESSION 3 — MERGE
  flu + dengue + ERA5 → master_weekly_v1.csv
  61,112 rows × 27 cols, 163 nước
        │
        ▼
SESSION 4 — EDA + CCF LAG ANALYSIS
  - log1p (skew 25.6 → 1.04)
  - Hemisphere phase shift 22 tuần
  - CCF lag tối ưu: flu temp lag 3w/solar lag 7w; dengue temp lag 11w/solar lag 16w
        │
        ▼
SESSION 5 — FEATURE ENGINEERING + ENDEMIC CHANNEL
  - features_flu_v1.csv (54,636 rows × 16 features)
  - features_dengue_v1.csv (5,786 rows × 15 features)
  - Endemic Channel labels (Bortman 1999, 5-year baseline + 2σ)
        │
        ▼
SESSION 6 — MODEL TRAINING & COMPARISON
  - 5 regressors (Naive, Prophet, XGB, LGBM, RF) + 1 classifier
  - Walk-forward CV 6 folds → champion: LGBM flu (0.902), RF dengue (0.936)
  - Optuna 60 trials tune top model
        │
        ▼
SESSION 7 — VALIDATION 2022 HOLD-OUT
  - Test generalization năm post-COVID chưa thấy
  - R² flu CV 0.902 → 2022 ~0.80 (Δ -0.10): generalize được
        │
        ▼
SESSION 8 — MULTI-HORIZON v6
  - Train 4 model riêng h=1, 2, 3, 4 (không recursive)
  - 8/8 horizon vượt benchmark Lowe 2014 Lancet ID
  - Dengue degradation gentler 3.6× flu (insight epidemiological)
```

---

## Danh sách 8 session

| File | Session | Nội dung | Output chính |
|---|---|---|---|
| [session_1_load.md](session_1_load.md) | 1 | Load 4 nguồn raw + sanity check + filter 2020-2021 | FluNet 113K rows, OpenDengue 18K, ECDC validation |
| [session_2_era5.md](session_2_era5.md) | 2 | ERA5 download CDS API + KD-tree map lưới → 197 nước | `era5_weekly_2010_2019_final.csv` (102K rows × 21 cols) |
| [session_3_merge.md](session_3_merge.md) | 3 | Merge flu+dengue+ERA5 → master | `master_weekly_v1.csv` (61K rows × 27 cols, 163 nước) |
| [session_4_eda.md](session_4_eda.md) | 4 | EDA + CCF lag (đóng góp khoa học) | log1p decision, lag tối ưu flu/dengue, hemisphere phase shift |
| [session_5_features.md](session_5_features.md) | 5 | Feature engineering + Endemic Channel labels | `features_flu_v1.csv` (54K × 16), `features_dengue_v1.csv` (5.7K × 15) |
| [session_6_training.md](session_6_training.md) | 6 | Train 5 regressors + 1 classifier + walk-forward CV + Optuna | 4 .pkl models v1 + metrics JSON |
| [session_7_validation.md](session_7_validation.md) | 7 | Validation độc lập 2022 (post-COVID hold-out) | R² flu 0.80, dengue 0.87, generalize được |
| [session_8_multi_horizon.md](session_8_multi_horizon.md) | 8 | **v6 extension** — Multi-horizon h=1..4 tuần | 8 .pkl (4 flu + 4 dengue), 8/8 vượt Lowe 2014 |

**Tài liệu phụ:**

| File | Nội dung |
|---|---|
| [hanh_trinh_cai_thien.md](hanh_trinh_cai_thien.md) | Hành trình v1 → v2 → v3 → v4 → v5 → v6 với rationale mỗi bước |
| [kich_ban_thuyet_trinh.md](kich_ban_thuyet_trinh.md) | Kịch bản nói chi tiết khi thuyết trình GVHD (v5 + bổ sung v6) |
| [../thuyet_trinh_bao_cao.md](../thuyet_trinh_bao_cao.md) | Kịch bản thuyết trình tổng thể 25 phút (v5+v6 + production) |
| [../chi_tiet_he_thong.md](../chi_tiet_he_thong.md) | Chi tiết hệ thống đầy đủ: dataset, DB, BE, FE |
| [../huong_dan_su_dung.md](../huong_dan_su_dung.md) | Hướng dẫn dùng dashboard cho end-user |

---

## Kết quả cuối cùng

### Bảng so sánh Regression v5 (mean R² qua 6 folds walk-forward CV, h=1)

| Model | Flu R² | Dengue R² |
|-------|--------|-----------|
| Naive baseline (same-week-last-year) | 0.560 | 0.487 |
| Prophet (statistical baseline) | 0.429 | -0.282 |
| XGBoost | 0.901 | 0.931 |
| **LightGBM** (champion flu) | **0.902** | 0.931 |
| **Random Forest** (champion dengue) | 0.899 | **0.936** |
| Best tuned (Optuna 60 trials) | **0.9019** | **0.9366** |

### Bảng Multi-horizon v6 (chốt 21/05/2026)

| h | Flu (LightGBM) | Dengue (Random Forest) | Lowe 2014 benchmark |
|---|----------------|------------------------|---------------------|
| 1 | **0.8661** | **0.9292** | 0.78-0.85 |
| 2 | 0.8293 | 0.9191 | 0.70-0.78 |
| 3 | 0.7928 | 0.9086 | 0.62-0.72 |
| 4 | 0.7573 | 0.8981 | 0.55-0.68 |

**8/8 horizon vượt benchmark Lowe et al 2014 Lancet ID.**

### Validation 2022 hold-out (Session 7)

| Model | Metric | CV 2014-2019 | 2022 hold-out | Δ |
|---|---|---|---|---|
| LightGBM flu | R² | 0.902 | ~0.80 | -0.10 |
| RF dengue | R² | 0.936 | ~0.87 | -0.07 |

→ **Cả 2 model generalize được** cho năm post-COVID chưa thấy.

### Bảng Classification (XGBClassifier macro-F1)

| Disease | macro-F1 | Đạt mục tiêu? |
|---------|----------|---------------|
| Flu | 0.542 ± 0.027 | ✅ Đạt (>0.50) |
| Dengue | 0.475 ± 0.035 | ⚠️ Gần đạt — High recall thấp (14%), document làm limitation |

### Phát hiện khoa học quan trọng

1. **AR features dominate ~90%** feature importance — Weather chỉ ~5% nhưng xuất hiện đúng theo CCF lag → **validate insight epidemiological**, không phải primary predictor.
2. **Random Forest thắng dengue** thay XGBoost — bagging robust hơn boosting với data nhỏ (5,786 rows). **Demonstrate critical thinking**, không default trust framework.
3. **Prophet R² âm với dengue** (-0.282) — confirm tree-based vượt statistical baseline trên data có outliers.
4. **Dengue degradation gentler 3.6× flu** — lag dài 6-14 tuần phủ xa hơn flu 1-7 tuần + endemic pattern stable hơn seasonal.
5. **Class shift dengue 2017-2018**: Brazil 2016 outbreak inflate baseline → ít cases vượt baseline → F1(High) thấp. **Realistic limitation của endemic channel**, walk-forward CV expose được.
