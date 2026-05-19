# Hướng phát triển — KLTN EpiWeather

**Sinh viên:** Phạm Hữu Luân — MSSV 110122016 — DA22TTA
**Cập nhật:** 17/05/2026

---

## 1. Trạng thái hiện tại (sau tuần 4)

### Đã hoàn thành
- Pipeline dữ liệu: WHO FluNet + OpenDengue + ECDC + ERA5 → master file 61.112 dòng
- EDA toàn diện: CCF lag analysis, seasonality, coverage heatmap, case studies
- Feature engineering: 2 file features (flu, dengue) áp dụng lag từ CCF
- ML pipeline: 5 models so sánh + walk-forward CV + Optuna tuning
- 4 models saved: LightGBM flu (R²=0.90), RF dengue (R²=0.94), XGBClassifier risk class

### Còn lại trong scope KLTN
- Backend FastAPI (đã scaffold sơ bộ ở tuần 3, cần hoàn thiện endpoints)
- Frontend React + Leaflet (chưa khởi động)
- Validation năm 2022 độc lập
- Realtime weather integration (OpenWeatherMap)
- Docker Compose deployment
- Báo cáo cuối kỳ Chương 4, 5

---

## 2. Lộ trình trong KLTN (tuần 5 → tuần 10)

### Tuần 5 (18/5 - 24/5) — Demo lần 1

**Ưu tiên 1 — Validation độc lập:**
- Build features 2022 từ ERA5 2022 + flu/dengue 2022 raw
- Predict với 4 models v1, đo RMSE/MAE/R² thực sự out-of-sample
- Phát hiện vấn đề generalization sau COVID nếu có

**Ưu tiên 2 — Fix classification:**
- Apply `class_weight='balanced'` (qua sample_weight) cho XGBClassifier dengue
- Hoặc thử SMOTE oversample High class
- Target: dengue macro-F1 vượt 0.50, High recall > 0.40

**Ưu tiên 3 — Backend MVP:**
- FastAPI endpoints: `/predict`, `/history`, `/alert-map`, `/health`
- Load 4 models .pkl tại startup
- PostgreSQL schema: tables `predictions`, `historical_cases`, `weather_history`
- ETL daily refresh weather từ OpenWeatherMap

**Ưu tiên 4 — Frontend sơ bộ:**
- React + Tailwind base layout
- Leaflet choropleth bản đồ thế giới với màu Low/Medium/High
- Polling API mỗi 5 phút

**Deliverable cuối tuần:** Demo lần 1 với GVHD, bản hệ thống có thể chạy được end-to-end mức tối thiểu

### Tuần 6 (25/5 - 31/5) — Hoàn thiện hệ thống

- Backend: thêm filter theo quốc gia, ngày, bệnh; pagination cho /history
- Frontend: dashboard Recharts (trend line, bar chart per country)
- Trang chi tiết theo từng quốc gia (drill-down view)
- Daily auto-refresh pipeline qua cron job hoặc APScheduler
- Demo lần 2 với GVHD

### Tuần 7 (1/6 - 7/6) — Polish và tích hợp realtime

- Realtime weather: OpenWeatherMap API → cache redis → predict
- Bộ lọc linh hoạt theo nhiều tiêu chí
- Loading states, error handling cho frontend
- Mobile responsive layout
- Hoàn thiện báo cáo Chương 4 (thực nghiệm + kết quả)

### Tuần 8 (8/6 - 14/6) — Test và đóng gói

- End-to-end test toàn hệ thống
- Docker Compose: backend + postgres + frontend
- Performance test: load testing với Locust hoặc k6
- Bug fix
- Demo lần cuối với GVHD

### Tuần 9 (15/6 - 21/6) — Nộp báo cáo nháp

- Hoàn thiện toàn bộ báo cáo (5 chương + tài liệu tham khảo)
- Tạo sơ đồ ERD, sequence diagram, deployment diagram
- Nộp bản nháp cho GVHD góp ý lần 1

### Tuần 10 (22/6 - 28/6) — Hoàn thiện

- Sửa theo góp ý GVHD
- Chuẩn bị slide thuyết trình (20-25 slides)
- Quay video demo backup (phòng khi demo trực tiếp gặp sự cố)

---

## 3. Hướng phát triển sau KLTN (post-thesis)

### 3.1. MLOps và Production hardening

- **CI/CD GitHub Actions:**
  - Lint + test trên mỗi push
  - Auto-build Docker image
  - Auto-deploy lên VPS hoặc cloud (Render, Railway, AWS)

- **Model registry:**
  - MLflow hoặc Weights & Biases để track experiments
  - Version control cho models (v1, v2, v3...)
  - A/B test giữa models trước khi promote production

- **Retrain pipeline:**
  - Auto-trigger khi data mới về (hằng tuần WHO FluNet update)
  - Walk-forward CV tự động trên data mới
  - Alert nếu performance drift > 5% R²

- **Monitoring:**
  - Prometheus + Grafana track API latency, error rate
  - Sentry cho exception tracking
  - Data drift detection (feature distribution thay đổi)

### 3.2. Mở rộng dữ liệu và bệnh

- **Việt Nam dengue data:**
  - Tích hợp data từ Bộ Y tế VN (Cục Y tế dự phòng) cho dengue VNM 2016+
  - Hiện OpenDengue chỉ có VNM năm 2015 → lỗ hổng lớn cho người dùng Việt
  - Có thể crawl từ HFCS reports hoặc liên hệ trực tiếp Viện Pasteur

- **Thêm bệnh:**
  - RSV: có data trong WHO FluNet (`RSV` column), CCF analysis có thể khác cúm
  - Malaria: WHO GHO API có data, nhưng monthly grain → cần adapt
  - COVID-19 (post-pandemic): WHO data 2020+, có thể model với hybrid same approach

- **Higher resolution:**
  - Subnational data (US states, EU NUTS3): cải thiện accuracy
  - ERA5 hourly thay vì monthly: capture intra-week dynamics
  - Trade-off: tăng dữ liệu storage 100x, cần parquet + chunked processing

### 3.3. Cải thiện model

- **Deep learning:**
  - LSTM hoặc Temporal Fusion Transformer (TFT) cho time-series
  - Có thể vượt tree-based ở data lớn (>100K samples)
  - Cần GPU, không phù hợp cho Colab free

- **Ensemble:**
  - Stack LightGBM + RF + XGBoost với meta-learner Linear Regression
  - Có thể cải thiện 0.5-2% R²

- **Bayesian approaches:**
  - Prophet với external regressors (weather)
  - PyMC hierarchical model per-country
  - Quantification of uncertainty (predictive intervals)

- **SHAP analysis:**
  - Explain từng prediction cho user (vì sao alert High?)
  - Quan trọng cho dashboard có credibility với epidemiologist

### 3.4. UX và sản phẩm

- **Mobile app:**
  - React Native hoặc PWA
  - Push notification khi quốc gia user đang theo dõi có alert High

- **Email/Telegram alerts:**
  - User subscribe theo quốc gia + bệnh
  - Webhook khi High class predicted

- **API public:**
  - OpenAPI docs đầy đủ
  - Rate limiting, API keys
  - Có thể monetize cho health agencies, NGO, researchers

- **Interactive notebook:**
  - Streamlit hoặc Gradio để cho phép user chạy ad-hoc analysis
  - "Predict for my country + my weather" mode

### 3.5. Hợp tác và publication

- **Khoa học:**
  - Viết paper IEEE Vietnam Conf hoặc IEEE BHI (Biomedical Health Informatics)
  - Đóng góp: hybrid R+C approach + CCF-driven feature engineering on global scale

- **Open source:**
  - Public GitHub repo với full pipeline reproducible
  - Documentation tốt → users tự fork và adapt cho region khác

- **Hợp tác local:**
  - Viện Pasteur HCMC: có lab surveillance, có thể là pilot user
  - Sở Y tế các tỉnh: thử nghiệm cảnh báo dengue mùa mưa miền Nam

---

## 4. Hạn chế cần ghi báo cáo

| Hạn chế | Ảnh hưởng | Hướng khắc phục |
|---|---|---|
| ERA5 monthly broadcast xuống weekly | Mất intra-month variation | Dùng ERA5 daily nếu compute đủ |
| KD-tree centroid mapping miss 8% nước (đảo nhỏ) | Mất Singapore, Caribbean islands | Natural Earth 10m + polygon buffer |
| AR features dominate >>> weather (5%) | "EpiWeather" name hơi misleading | Frame weather as conditioning, không primary |
| Dengue 2010-2014 sparse | Training window thu hẹp 2015-2019 | Tìm nguồn alternative (PAHO data) |
| OpenDengue VNM chỉ 2015 | VN dengue model kém với data Việt | Tích hợp data Bộ Y tế VN |
| Dengue High class recall 14% | Miss outbreak alerts | class_weight balanced, SMOTE |
| Walk-forward CV chỉ 3 fold dengue | Std cao, kết quả kém stable | Cần thêm năm data |
| Skip 2020-2021 (COVID) | Không generalize qua pandemic | Document limitation, không claim universal |

---

## 5. Mục tiêu R&D dài hạn

- **3 tháng sau bảo vệ**: Deploy production trên domain riêng, public access
- **6 tháng**: Có 100+ users (researchers, health officers) sử dụng định kỳ
- **12 tháng**: Publication paper + đóng góp 1 module cho WHO EWARS (theoretical pipeline contribution)
- **24 tháng**: Multi-region adoption (SE Asia, Africa) với data local + thêm 2-3 bệnh mới
