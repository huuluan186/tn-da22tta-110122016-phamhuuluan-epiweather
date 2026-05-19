# Session Summary 14/05/2026 — SESSION 9-10: Endemic Channel Labels + Multi-Model Training + Pipeline Fixes

## 🎯 Mục tiêu buổi

1. Hoàn thành SESSION 9 (Endemic Channel label generation per WHO EWARS spec)
2. Train + so sánh nhiều model với walk-forward CV (5 model: Majority, SWLY, LogReg, RF, XGB, LightGBM)
3. Identify champion model + save artifacts
4. Phát hiện & fix các vấn đề về feature set / data quality

## 📚 Bối cảnh

- Approach mới (chốt 13/05): **Ordinal Classification + Endemic Channel** (override Regression-then-Bucket cũ)
- Pipeline v3: notebook `KLTN_EpiWeather_ML_v3.ipynb`
- Đã có data sạch từ SESSION 1–8: `master_weekly_2010_2019.csv`, `features_flu_v3.csv`, `features_dengue_v3.csv`
- Walk-forward CV: val_year ∈ {2017, 2018, 2019}, min_hist=5 cho endemic channel

---

## 🔬 SESSION 9 — Endemic Channel Label Generation

### Quá trình
1. **[9.0]** Load features_flu_v3 + features_dengue_v3 (shape 57,739×13 + 58,448×13)
2. **[9.1]** Generate endemic channel labels:
   - Per (iso3, iso_week): baseline = mean(5 prev years), upper = baseline + 2σ
   - Low: cases < baseline; Medium: baseline ≤ cases < upper; High: cases ≥ upper
3. **[9.2]** Visualize class balance + save raw labeled CSV
4. **[9.3]** Filter year ≥ 2015 + filter dengue endemic countries (≥1 tuần cases > 0)

### Kết quả

| Disease | Rows | Countries | Low / Med / High |
|---|---|---|---|
| Flu | 20,552 | 116 | 57% / 26% / 17% |
| Dengue | 7,227 | **31** | 61% / 19% / 20% |

### Phát hiện quan trọng
- **Dengue countries 116 → 31** (sau filter endemic > 0 trong 2015-2019)
- 11 nước bị loại có cases ở 2010-2014 nhưng zero 2015-2019 → loại vì:
  - 2010-2014 là warm-up không train
  - Nếu giữ → toàn Low label inflate distribution
- Min_hist=5 (theo WHO EWARS spec) → label hợp lệ từ 2015 → train 2015-2019

### Quyết định cứng (cite được)
- **Bortman 1999** + **WHO EWARS Technical Guide 2012** đều specify 5 năm minimum
- KHÔNG dùng 3 năm: `std` của 3 mẫu không reliable → ngưỡng `mean + 2σ` dao động mạnh

---

## 🤖 SESSION 10 — Multi-Model Comparison (Walk-forward CV)

### Cells inserted
- **[10.1]** Feature check + NaN scan
- **[10.2]** Setup walk-forward CV + helper functions (`run_cv`, `compute_metrics`, `walk_forward_splits`)
- **[10.2b]** Sanity checks pre-train (class balance, country overlap, feature scale, leakage)
- **[10.3]** Naive baselines: Majority + SameWeekLastYear
- **[10.4]** Logistic Regression (StandardScaler + class_weight='balanced')
- **[10.5]** Random Forest (n=300, depth=12)
- **[10.6]** XGBClassifier (multi:softprob, n=500, depth=6)
- **[10.7]** LightGBM (multiclass, n=500, depth=6)
- **[10.8]** Comparison table + champion selection + re-train on full data + save

### Kết quả (baseline — 9 features, KHÔNG có who_region_enc + quarter)

| Model | Flu macroF1 | Dengue macroF1 | Dengue AUC |
|---|---|---|---|
| Majority | 0.240 | 0.275 | 0.50 |
| SameWeekLastYear | 0.355 | 0.413 | – |
| LogReg | 0.395 | 0.454 | 0.675 |
| **RandomForest 🥇** | **0.492** | **0.516** | **0.812** |
| XGBoost | 0.479 | 0.503 | 0.795 |
| LightGBM | 0.473 | 0.506 | 0.791 |

### Phát hiện quan trọng

1. **RandomForest thắng cả 2 diseases out-of-the-box** — không tune, vẫn vượt XGB/LGBM
2. **Tree models cluster** ~0.47–0.52 macroF1 → confirm signal ceiling với feature set hiện tại
3. **F1(High) dengue chỉ 0.30** → minority class struggle
4. **Insight cho thesis Chapter 4:** "Không phải model phức tạp nhất luôn tốt nhất — tuning matters, và data size matters"

### Bug đã fix

- **Target leakage `inf_cases` trong flu features** — phải bỏ vì là biến tính label
- **Dengue NaN labels** — drop rows where baseline=NaN (insufficient history)
- **Pipeline.fit sample_weight error** — chuyển sang `class_weight='balanced'` trong LogReg estimator
- **Dengue 116 → 31 countries** — filter year-first then endemic-second

---

## 🔧 Cải thiện đang triển khai (chưa re-run)

### [8.4] — Thêm who_region_enc + quarter (proven improvements từ approach cũ)

Phát hiện feature set v3 đang **MISSING** 2 features đã proven từ approach cũ (roadmap #5):
- `who_region_enc` (6 WHO regions: AFR=0, AMR=1, EMR=2, EUR=3, SEAR=4, WPR=5)
- `quarter` (1-4 từ iso_week)

→ Insert cell [8.4] thêm 2 features vào features_v3.csv
- WHO mapping: 194 countries (hardcoded chuẩn WHO list + patch 4 territories: ABW, AIA, CYM → AMR; NCL → WPR)
- Region distribution flu: AFR=10,928 / AMR=11,901 / EMR=5,672 / EUR=18,493 / SEAR=3,756 / WPR=6,989

### [8.5] — log1p AR features (fix extreme skewness — phát hiện qua [10.2b])

Sanity checks phát hiện **AR lag skewness cực đoan**:
- `inf_cases_lag*`: median=5, max=**13,193** (ratio ~2,600)
- `dengue_total_lag*`: median=11, max=**146,906** (Brazil 2016 outbreak, ratio ~13,000)

→ Insert cell [8.5] log1p transform AR features
- Tree-based: không hại (split theo rank)
- LogReg: boost mạnh nhờ gradient ổn định
- Kỳ vọng LogReg +0.05 macroF1, tree-based +0.01–0.02

### Phát hiện class shift dengue (KHÔNG fix — document only)

Sanity check [10.2b] phát hiện:
```
val=2017 | train High=0.32, val High=0.10  ← 3× chênh
val=2018 | train High=0.25, val High=0.05  ← 5× chênh!
val=2019 | train High=0.20, val High=0.22  ← OK
```

**Đây không phải bug** — là realistic limitation của endemic channel:
- baseline = mean(5 prev years) → 2016 Brazil outbreak làm baseline 2017+2018 bị inflate → ít cases vượt baseline → ít High label
- Giải thích F1(High) val=2018 = 0.08 ở session trước
- **Document trong Chapter 4** như "realistic difficulty of forecasting epidemic spikes, captured by walk-forward CV"

---

## 📂 Files đã thay đổi

| File | Thay đổi |
|---|---|
| `KLTN_EpiWeather_ML_v3.ipynb` | Thêm cells: [8.4], [8.5], SESSION 10 (8 cells), SESSION 11 header + [11.1] (chưa chạy) |
| `dataset/processed/features_flu_v3.csv` | Thêm cols `who_region_enc`, `quarter` (15 cols total) |
| `dataset/processed/features_dengue_v3.csv` | Thêm cols `who_region_enc`, `quarter` (15 cols total) |
| `dataset/processed/features_flu_labeled.csv` | 20,552 rows × 18 cols (label + ec_baseline + ec_upper) |
| `dataset/processed/features_dengue_labeled.csv` | 7,227 rows × 18 cols, 31 endemic countries |
| `dataset/processed/session10_metrics.csv` | Bảng so sánh 6 model × 2 disease |
| `dataset/processed/champion_flu_randomforest.pkl` | RF flu champion (re-trained on full 2015-2019) |
| `dataset/processed/champion_dengue_randomforest.pkl` | RF dengue champion |

---

## ✅ Đã hoàn thành

- [x] SESSION 9 — Endemic Channel labels (Bortman 1999 / WHO EWARS spec)
- [x] SESSION 10 — 6 model comparison với walk-forward CV
- [x] Champion selection: RandomForest cho cả 2 disease
- [x] Save artifacts (metrics CSV + 2 champion .pkl)
- [x] [8.4] Thêm who_region_enc + quarter vào features_v3 (đã chạy)
- [x] [10.2b] Sanity checks pre-train (đã chạy, phát hiện 2 vấn đề thực)

---

## ⏳ Pending cho buổi mai

1. **Chạy [8.5]** log1p AR features
2. **Re-run [9.0] → [9.3]** với features mới (~2 phút)
3. **Re-run [10.1] → [10.8]** so sánh model với 11 features (log1p + region + quarter)
4. **Quyết định Optuna XGB/LGBM** dựa trên kết quả mới
5. **SESSION 11 — Evaluation on 2022** test set (post-COVID generalization)
6. **SESSION 12 — Inference pipeline** (load .pkl, predict given country+week+disease)

---

## 🎓 Insights cho thesis report

### Chapter 4 — Kết quả thực nghiệm

1. **Methodology validation:** Walk-forward CV expose realistic limitations (class shift năm dengue) — đó là **giá trị** của CV scheme này, không phải weakness.

2. **Model selection insight:** RandomForest beat XGBoost on this dataset → quan trọng vì:
   - Demonstrate critical thinking (không chỉ "XGBoost là chuẩn → dùng XGBoost")
   - Highlight rằng tuning matters, data size matters
   - RF robust hơn cho small-to-medium dataset (~7-16k rows)

3. **Feature importance discovery:** Phát hiện missing features (who_region_enc + quarter) qua review roadmap cũ — show systematic approach trong development.

4. **Class imbalance reality:** Endemic channel labels phản ánh đúng tỷ lệ Low ~60% / Med ~20% / High ~20%. WHO EWARS thiết kế `mean + 2σ` để High là rare event — model phải dùng `class_weight='balanced'` + macro-F1.

### Chapter 2 — Literature

References đã cite:
- Bortman 1999 (PAHO endemic channel original)
- WHO EWARS Technical Guidelines 2012 (5-year minimum)
- Hussain-Alkhateeb et al. 2018 (EWARS Mexico/Brazil)
- Wellcome OR 2024 (ordinal influenza classification)

### Chapter 3 — System Design

Champion artifacts ready cho deployment:
- `champion_flu_randomforest.pkl` (RF, macroF1=0.492)
- `champion_dengue_randomforest.pkl` (RF, macroF1=0.516)
- Schema: `{'model': fitted_estimator, 'features': list[str], 'label_map': dict}`

---

## 🧠 Note quan trọng cho session mai

1. **Đừng quên chạy [8.5] TRƯỚC khi re-run [9.x]** — log1p phải áp dụng trên features_v3 trước, label gen dùng cases gốc (KHÔNG log)
2. **AR features sau log1p sẽ có giá trị nhỏ** — verify median ~2.5 thay vì 5 (log1p(5)=1.79)
3. **Endemic channel KHÔNG đổi** sau log1p — vì label gen dùng `dengue_total` raw, không phải lag
4. **Optuna decision** — nếu RF tuned vẫn thắng XGB/LGBM tuned → conclude RF cho production. Nếu XGB tuned vượt → có thể switch.
5. **Tránh re-run SESSION 8 cells trước [8.4]** — sẽ overwrite features_v3 và mất who_region_enc + quarter + log1p. Chỉ chạy từ [8.4] trở đi.
