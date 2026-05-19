# Session Summary — 17/05/2026

**Sinh viên:** Phạm Hữu Luân — MSSV 110122016 — DA22TTA
**Chủ đề:** Tái cấu trúc toàn bộ ML pipeline — Notebook v5 hybrid approach
**Thời lượng:** Cả ngày (SESSION 0 → SESSION 6 của notebook v5)

---

## 1. Mục tiêu phiên làm việc

Rà soát lại toàn bộ ML pipeline tuần 3 vì phát hiện một số hạn chế phương pháp luận: chỉ dùng 1 model XGBoost, single validation split không rigorous, lag features cố định không dựa CCF. Quyết định nâng cấp approach từ single XGBoost lên **Hybrid Regression + Classification** với walk-forward CV chuẩn time-series.

## 2. Bối cảnh thay đổi

- Tham khảo lại 3 paper chính: Lowe et al. 2014 (Lancet ID), Shaman & Kohn 2009 (PNAS), Bortman 1999 (WHO EWARS)
- Tham chiếu CDC FluSight winners — đều dùng heavy AR features + walk-forward CV
- Phát hiện CLAUDE.md cũ vẫn dùng LAG_FLU=[1,2,3] cứng, không match CCF analysis

## 3. Kết quả từng SESSION

### SESSION 0 — Setup & paths (7 sub-steps)
- Mount Drive, install packages (xgboost 3.2, lightgbm 4.6, optuna 4.8)
- Define paths tập trung: BASE, RAW, PROCESSED, MODELS_DIR
- Fix path bug: `Dataset` → `dataset` (case sensitive Linux), `era5_weekly` → `weather/processed/`
- Verify 6/7 files OK trên Drive

### SESSION 1 — Load raw data (5 sub-steps)
- FluNet: 183K → 113K rows sau filter 2010-2022, 189 nước
- Dengue: 18K weekly rows, 82 nước, Brazil top 1 (10.5M cases)
- ECDC: chỉ 2021-2026, dùng cho dashboard validation
- Phát hiện: dengue 2010-2014 chỉ 5-12 nước báo cáo → cần thu hẹp training window

### SESSION 2 — ERA5 load & verify (5 sub-steps)
- File `era5_weekly_2010_2019_final.csv`: 102,440 rows × 21 cột, 197 nước × 10 năm × 52 tuần (lưới cân bằng)
- Confirm monthly broadcast: 100% rows có temp_range_c = 0
- USA seasonal sanity PASS: Jan -4.2°C, Jul 21.3°C
- Thêm cell [2.A] [2.B] [2.C] documentation CDS API (flag DOCUMENTATION_ONLY)

### SESSION 3 — Merge → master_weekly_v1.csv (7 sub-steps)
- Output: `dataset/processed/master_weekly_v1.csv` (61,112 × 27, 20.9MB)
- 163 nước (mất 21 flu + 30 dengue do KD-tree không match đảo nhỏ — known limitation 92%)
- 52,750 rows chỉ flu, 1,947 chỉ dengue, 6,415 cả hai
- Path bug đã fix: `dataset/epidemic/processed/` → `dataset/processed/` (top-level cross-domain)

### SESSION 4 — EDA (6 sub-steps)
- log1p transform: flu skew 25.64→1.04, dengue 12.65→-0.12 (gần normal)
- Coverage heatmap: flu 91%, dengue 40% (xác nhận thu hẹp dengue về 2015-2019)
- Seasonality: phase shift hemisphere W6 (NH) vs W28 (SH), đúng 22 tuần
- **CCF lag refined:**
  - Flu: solar_wm2 lag 7 (r=-0,41 strongest), temp_c lag 3 (r=-0,37), humidity lag 7 (r=+0,31), drop precip_mm
  - Dengue: temp_c lag 11 (r=+0,31, khớp Lowe 2014), dewpoint lag 8, precip lag 6
- Case studies: BRA (hybrid), USA (NH winter), VNM (tropical, no dengue gap)
- Phát hiện limitation: OpenDengue VNM chỉ có data 2015, không có 2017+

### SESSION 5 — Feature engineering (5 sub-steps)
- `features_flu_v1.csv`: 55,208 × 21, 146 nước, 2010-2019, 16 features
- `features_dengue_v1.csv`: 5,926 × 20, 37 nước, 2015-2019, 15 features
- Endemic channel labels (Bortman 1999):
  - Flu: Low 56%, Medium 26%, High 17%
  - Dengue: Low 47%, Medium 30%, High 23%
- Quan trọng: dengue build complete grid (37×5×52) + fillna(0) trước khi compute lag → giữ 89% data (vs 7% nếu filter dengue.notna() trước)

### SESSION 6 — Model training & comparison (10 sub-steps)

**Regression walk-forward CV (mean R²):**

| Model | Flu R² | Dengue R² |
|---|---|---|
| Naive baseline | 0.560 | 0.487 |
| Prophet | 0.429 | -0.282 |
| XGBoost | 0.901 | 0.931 |
| **LightGBM** | **0.902** | 0.931 |
| Random Forest | 0.899 | **0.936** |
| Best tuned (Optuna 60 trials) | **0.9019** | **0.9366** |

**Classification (XGBClassifier macro-F1):**
- Flu: 0.542 ± 0.027 (đạt mục tiêu >0.50)
- Dengue: 0.475 ± 0.035 (chưa đạt, High recall 14% — cần fix tuần 5)

**Feature importance top 3:**
- Flu: flu_log_lag1 (54%), lag2 (31%), lag3 (8%) → AR dominate 93%
- Dengue: deng_log_rollmean4 (70%), rollmean8 (12%), lag6 (6%) → AR dominate 88%
- Weather contribute ~5% nhưng xuất hiện đúng theo CCF (validate epidemiological insight)

**Models saved (4 file .pkl + metadata):**
- `lgbm_flu_regressor_v1.pkl` (1.8MB) — production flu regression
- `rf_dengue_regressor_v1.pkl` (34.6MB) — production dengue regression
- `xgb_flu_classifier_v1.pkl` (3.9MB) — flu risk classification
- `xgb_dengue_classifier_v1.pkl` (2.9MB) — dengue risk classification

## 4. Phát hiện và quyết định kỹ thuật chốt

| Phát hiện | Quyết định |
|---|---|
| Dengue 2010-2014 chỉ 5-12 nước báo cáo | Thu hẹp training window dengue về 2015-2019 |
| Prophet R² âm với dengue (-0.28) | Loại Prophet khỏi production cho dengue, giữ baseline so sánh |
| Random Forest thắng dengue (0.936) | Chọn RF cho dengue production thay XGBoost — bagging robust hơn boosting với data nhỏ |
| LightGBM thắng flu 6/6 folds | Chọn LightGBM cho flu production |
| Optuna improvement marginal (+0.04-0.07%) | Default params đã near-optimal vì AR features dominant |
| AR dominate 90%+ feature importance | Weather là conditioning feature, không phải primary predictor — phù hợp literature |
| Path Drive `Dataset` vs `dataset` | Linux case-sensitive, đã fix toàn bộ về lowercase |
| Master file lưu nhầm vào `dataset/epidemic/processed/` | Fix về `dataset/processed/` (top-level cross-domain merged data) |

## 5. Files tạo ra trong phiên này

### Notebook
- `KLTN_EpiWeather_ML_v5.ipynb` — notebook hoàn chỉnh SESSION 0-6 (~110 cells)

### Dataset trên Drive
- `dataset/processed/master_weekly_v1.csv` (20.9MB)
- `dataset/processed/features_flu_v1.csv` (14.8MB)
- `dataset/processed/features_dengue_v1.csv` (1.6MB)

### Models trên Drive
- `models/lgbm_flu_regressor_v1.pkl` + features.json + metrics.json
- `models/rf_dengue_regressor_v1.pkl` + features.json + metrics.json
- `models/xgb_flu_classifier_v1.pkl` + features.json + metrics.json
- `models/xgb_dengue_classifier_v1.pkl` + features.json + metrics.json

### Documentation local
- `docs/dataset_description_v1.md` — mô tả 3 file dataset, gửi kèm email cô

## 6. Báo cáo cô tuần 4

- Email báo cáo đã draft với 4 mục (đã làm, khó khăn, kế hoạch tuần 5, file đính kèm)
- Đề xuất sửa DCCT: 4 thay đổi chính (model compare 5 thay 2, walk-forward CV, dời demo lần 1 sang tuần 5, đảo nội dung tuần 5-6-7)
- Pipeline workflow diagram vẫn dùng được, không cần vẽ lại
- File đính kèm gửi cô: Colab v5, link 3 file dataset, pipeline_workflow_kltn_v3.png, dataset_description_v1.pdf

## 7. Best result hiện tại (cập nhật từ memory)

- **Flu**: LightGBM tuned, R² = 0.9019 ± 0.008, RMSE = 0.587 (log scale)
- **Dengue**: Random Forest tuned, R² = 0.9366 ± 0.015, RMSE = 0.739 (log scale)
- Cả 2 đều VƯỢT XA mục tiêu CLAUDE.md (>0.20 flu, >0.79 dengue)

## 8. Vấn đề còn lại / chưa làm

- Validation độc lập trên năm 2022 (post-COVID hold-out) — chưa chạy
- Dengue classifier High recall = 0.14 — cần fix bằng class_weight balanced
- FastAPI backend chưa scaffold endpoints predict/history/alert-map
- React frontend chưa khởi động
- Realtime weather integration (OpenWeatherMap) chưa làm
- Docker Compose deploy chưa làm

## 9. Cảm nhận làm việc

Phiên này cường độ cao (xây dựng lại từ đầu notebook v5 với approach mới). Phát hiện quan trọng: data dengue 2010-2014 quá sparse, AR features dominate >>> weather. Đây không phải lỗi mà là finding khoa học có giá trị cho báo cáo. Quyết định hybrid + walk-forward CV là đúng hướng — kết quả R² 0.90+ vượt expectation và stable qua nhiều folds.

Tuần 5 sẽ trọng tâm chuyển sang **deployment** (Backend + Frontend) thay vì tối ưu thêm model. Model hiện tại đã đủ tốt để demo.
