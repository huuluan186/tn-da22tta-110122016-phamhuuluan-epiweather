# Thuyết trình báo cáo KLTN — EpiWeather Global Epidemic Warning System

> **Sinh viên:** Phạm Hữu Luân — MSSV 110122016 — DA22TTA
> **GVHD:** Cô Phạm Thị Trúc Mai — Bộ môn CNTT, Trường ĐH Trà Vinh
> **Đề tài:** Hệ thống cảnh báo nguy cơ dịch bệnh theo mùa dựa trên dữ liệu y tế và thời tiết toàn cầu
> **Mốc:** 23/05/2026 — sau khi hoàn thành Phase A (realtime) + Phase C (multi-horizon) + Dengue Nowcast
>
> **Giọng văn:** Đây là kịch bản nói trực tiếp với GVHD/hội đồng. Đọc như nghe thuyết trình thật, không phải tài liệu kỹ thuật tự đọc.
>
> **Thời lượng:** ~25 phút thuyết trình + 5-10 phút Q&A.

---

## Hướng dẫn sử dụng file này

- Câu trong khung `>` là **câu mẫu nói trực tiếp** — luyện thuộc, không đọc slide
- `[CHUYỂN SLIDE]` = cue chuyển slide
- `[NHẤN MẠNH]` = chỗ lên giọng / chậm lại
- `[NẾU HỎI]` = chuẩn bị trước cho câu hỏi GVHD có thể hỏi

**Quy tắc vàng khi đứng thuyết trình:**
1. Đừng đọc slide — slide là **bằng chứng**, miệng phải kể **câu chuyện**
2. Mỗi 2-3 phút phải có **con số** hoặc **phát hiện** để giữ attention
3. Khi thầy hỏi khó, không nói "em không biết" — nói **"em document làm limitation, hướng xử lý là..."**
4. Tự tin nhưng khiêm tốn — sai một chỗ vẫn được, đừng cãi

---

# PHẦN 1 — MỞ ĐẦU (2 phút)

## Slide 1 — Tiêu đề + sinh viên

> "Chào thầy cô. Em là Phạm Hữu Luân, MSSV 110122016, lớp DA22TTA. Hôm nay em xin trình bày đồ án tốt nghiệp với đề tài **Hệ thống cảnh báo nguy cơ dịch bệnh theo mùa dựa trên dữ liệu y tế và thời tiết toàn cầu**. GVHD của em là cô Phạm Thị Trúc Mai, bộ môn Công nghệ thông tin."

[Chờ 2 giây, nhìn xuống thầy cô]

## Slide 2 — Bài toán & motivation

> "Câu hỏi mà đề tài này giải là: **giả sử ta có dữ liệu thời tiết tuần này — nhiệt độ, độ ẩm, mưa, bức xạ mặt trời — của một quốc gia bất kỳ trên thế giới, có thể dự báo nguy cơ bùng phát dịch cúm và sốt xuất huyết 1 đến 4 tuần tới không?**"
>
> "Đây là bài toán có ý nghĩa thực tế. WHO ước tính cúm mùa gây 3-5 triệu ca nặng và 290-650 nghìn tử vong mỗi năm. Sốt xuất huyết ảnh hưởng 129 quốc gia, gần một nửa dân số thế giới có nguy cơ. Nếu cảnh báo sớm 2-3 tuần, ngành y tế có thể chuẩn bị vaccine, giường bệnh, hoặc chiến dịch diệt muỗi."
>
> [NHẤN MẠNH] "Đây không phải bài toán dễ — em sẽ giải thích vì sao trong vài phút tới."

## Slide 3 — 5 thử thách của bài toán

> "Có 5 thử thách chính khi em làm đề tài này."
>
> "**Thứ nhất**, dữ liệu đến từ **4 nguồn khác nhau**, mỗi nguồn định dạng khác, độ phủ khác. WHO FluNet cho cúm — 189 quốc gia, OpenDengue cho sốt xuất huyết — 82 quốc gia, ERA5 cho khí hậu lịch sử, Open-Meteo cho khí hậu realtime."
>
> "**Thứ hai**, em phải làm việc với **163 quốc gia**, mỗi nước có mùa bệnh khác. Bán cầu Bắc đỉnh cúm tuần 6, bán cầu Nam đỉnh tuần 28, lệch nhau 22 tuần. Mô hình phải học được pattern này."
>
> "**Thứ ba**, dữ liệu thời tiết ERA5 ở dạng **lưới địa lý 721×1440 điểm** — hơn 1 triệu điểm trên toàn cầu. Em cần data theo quốc gia × tuần, không theo lưới. Em phải dùng kỹ thuật KD-tree map từ lưới về quốc gia."
>
> "**Thứ tư**, đề tài yêu cầu **cả hai bài toán**: dự báo số ca (regression) và phân loại mức nguy cơ Low/Medium/High (classification). Em làm cả hai và so sánh — đây là đóng góp khoa học."
>
> "**Thứ năm**, kết quả phải chạy được trên **server thật** phục vụ dashboard React, không phải chỉ trong Jupyter notebook. Em phải build cả pipeline MLOps tự động sync data hàng tuần."

---

# PHẦN 2 — KIẾN TRÚC HỆ THỐNG (3 phút)

## Slide 4 — Sơ đồ tổng thể 4 tầng

> "Đây là kiến trúc hệ thống em xây dựng. Em chia thành **4 tầng riêng biệt**, mỗi tầng làm 1 việc và không phụ thuộc state của tầng cao hơn."

[Chỉ vào sơ đồ]

> "**Tầng 1: Nguồn dữ liệu** — 4 nguồn em đã kể."
>
> "**Tầng 2: ETL pipeline** — 4 script Python: `sync_flunet.py` pull WHO, `sync_weather.py` pull Open-Meteo, `feature_builder.py` tính lag features, `batch_predict.py` chạy model. Tất cả idempotent — chạy lại không lỗi."
>
> "**Tầng 3: Database PostgreSQL** — 16 bảng logic với 31 partition theo năm. Có disease_cases 87 nghìn dòng, weather_observations 24 nghìn dòng, feature_snapshots 75 nghìn dòng, predictions 75 nghìn dòng."
>
> "**Tầng 4: Backend FastAPI** — load 10 model `.pkl` vào memory, serve 15+ REST endpoints. APScheduler chạy 4 cron job tự động hàng tuần."
>
> "**Tầng cuối: Frontend React** — 3 trang chính: HomePage với bản đồ thế giới, DiseaseDetailPage với forecast 4 tuần, AnalyticsPage so sánh model."

## Slide 5 — Approach v5 + v6: Hybrid + Multi-horizon

> "Em xin nhấn mạnh approach của em — đây là phần khác biệt với baseline."
>
> "**Approach v5** (chốt 16/05/2026): em làm **hybrid Regression + Classification** chứ không chọn 1. Đề tài yêu cầu cả 'dự báo dịch bệnh có thể diễn ra' (số ca cụ thể) và 'cảnh báo mức độ' (Low/Med/High). Em làm cả hai và so sánh."
>
> "**Approach v6** (chốt 21/05/2026): em mở rộng thành **multi-horizon** — train **4 model riêng cho h=1, h=2, h=3, h=4 tuần**, mỗi model dùng feature actual (không recursive). Lý do: tránh error propagation — nếu predict h=1 rồi feed làm input cho h=2, error h=1 sẽ amplify."
>
> "**Phase A + nowcast extension** (chốt 23/05/2026): em thêm **latest-data/nowcast ingestion** — flu được sync hàng tuần từ WHO FluNet pipeline (2026-W21), dengue lấy từ OpenDengue v1.3 batch (2023-W36). Đây là điểm khác biệt: không chỉ predict historical training data."

---

# PHẦN 3 — DEEP DIVE TỪNG SESSION (10 phút)

## Slide 6 — Session 0-1: Lấy data ở đâu

> "Em không thể nói 'em load data về' rồi skip. Mỗi nguồn em chọn có lý do rõ ràng."
>
> "**WHO FluNet** — database cúm toàn cầu chính thức duy nhất của WHO, cập nhật hàng tuần từ 1995. Cột target em dùng là `INF_A + INF_B` (subtype A + B), KHÔNG dùng `INF_ALL` vì missing 44%."
>
> "**OpenDengue v1.3** — dataset học thuật, paper publish trên Scientific Data 2024 (Clarke et al). 82 quốc gia, Brazil chiếm 71% tổng ca dengue toàn cầu — em phải xử lý đặc biệt với log1p transform."
>
> "**ERA5** — em chọn vì là **reanalysis dataset chuẩn quốc tế** của ECMWF, độ chính xác cao hơn OpenWeatherMap historical, free cho research. Lưới 0.25°, 17 biến khí hậu, 6.2 GB cho 2010-2019."
>
> "**Open-Meteo Archive** — cho realtime weather. Free, dùng cùng ERA5 underneath → consistent với training data."
>
> [NẾU HỎI: "Sao không dùng Bộ Y tế VN hay WHO ICD-10?"]
> > "Em có khảo sát. Bộ Y tế VN không có API public, phải lấy data thủ công từ báo cáo PDF. ICD-10 là chuẩn coding bệnh, không phải dataset cases. FluNet và OpenDengue đã cover 92% dân số thế giới, đủ scope KLTN."

## Slide 7 — Session 2-3: EDA — phát hiện quan trọng nhất

> "Phần EDA em làm rất kỹ — đây là 50% giá trị của project."
>
> "Em đi qua **8 bước EDA bắt buộc** với mỗi dataset: schema check, missing analysis, distribution, outlier, time coverage, cross-validation logic, sanity check, label quality check."
>
> "**3 phát hiện quan trọng nhất:**"
>
> "**Phát hiện 1: log1p transform là bắt buộc.** Phân phối ca bệnh long-tail cực mạnh — Brazil dominate dengue 71%. Nếu không log1p, model sẽ chỉ học Brazil, ignore các nước khác. Sau log1p, R² dengue tăng từ ~0.5 lên 0.93."
>
> "**Phát hiện 2: loại 2020-2021 khỏi training flu.** Em phát hiện flu giảm ~99% năm 2020-2021 — không phải do data missing (số nước báo cáo vẫn 166-167 nước, ngang 2019), mà do NPI giãn cách + đeo khẩu trang. Train trên data này sẽ làm model học sai pattern bình thường."
>
> "**Phát hiện 3: hemisphere matters.** Bán cầu Bắc đỉnh flu tuần 6, bán cầu Nam đỉnh tuần 28. Em encode hemisphere làm feature → model học được pattern theo nửa cầu."

## Slide 8 — Session 4: ERA5 KD-tree mapping

> "Đây là phần kỹ thuật khó nhất của ETL."
>
> "ERA5 trả về dữ liệu khí hậu **theo lưới 721×1440 điểm** — hơn 1 triệu điểm trên toàn cầu, mỗi điểm cách nhau 0.25°. Nhưng em cần data **theo quốc gia × tuần**, không theo lưới."
>
> "Giải pháp: dùng **KD-tree** trên (latitude, longitude) của 197 country centroid. Với mỗi country, tìm **k=4 grid point gần nhất**, lấy trung bình. Đơn giản hơn point-in-polygon, đủ chính xác cho country-level grain."
>
> "Tại sao k=4? Vì 1 centroid có thể nằm gần biên giới → trung bình 4 điểm để smooth. Quốc gia nhỏ (Singapore) hay lớn (Russia) đều dùng cùng method → consistent."
>
> "Sau khi process, em được file `era5_weekly_2010_2019_final.csv` — 197 nước × 522 tuần × 17 biến."

## Slide 9 — Session 5: Merge 3 nguồn

> "Sau khi có 3 file (flu, dengue, weather), em merge theo key `(iso3, iso_year, iso_week)`."
>
> "Kết quả: `master_weekly_v1.csv` — **61,112 dòng × 27 cột, 163 quốc gia, 2010-2019**. Sau đó em filter riêng cho từng bệnh:
> - Flu: 143 nước có data flu + weather → features_flu_v1.csv
> - Dengue: 35 nước (loại các nước có < 26 weeks/year) → features_dengue_v1.csv"

## Slide 10 — Session 6: CCF Lag Analysis (CỐT LÕI khoa học)

> "Đây là phần em tự hào nhất — **đóng góp khoa học của project**."
>
> "Câu hỏi: thời tiết tuần này ảnh hưởng đến số ca bệnh tuần nào? Cùng tuần, hay 2 tuần sau, hay 8 tuần sau?"
>
> "Em dùng **Cross-Correlation Function (CCF)** giữa từng cặp (biến thời tiết, ca bệnh) qua lag 0 đến 24 tuần. Tìm **peak correlation** = lag tối ưu."
>
> [Chỉ vào biểu đồ CCF]
>
> "**Kết quả lag tối ưu cho Flu:**
> - Temperature: lag **4 tuần** (lạnh trước 4 tuần → flu peak)
> - Humidity: lag **8 tuần** (khô trước 8 tuần)
> - Solar radiation: lag **8 tuần**
> - Dewpoint: lag **2 tuần**"
>
> "**Kết quả lag tối ưu cho Dengue:**
> - Temperature: lag **11 tuần** (ấm trước 11 tuần → muỗi sinh sản)
> - Humidity: lag **1 tuần**
> - Solar radiation: lag **16 tuần** (UV ảnh hưởng dài hạn)
> - Precipitation: lag **6 tuần** (mưa tạo breeding sites)"
>
> [NHẤN MẠNH] "Điểm quan trọng: **lag dengue dài hơn flu rất nhiều** — vì vòng đời muỗi Aedes phức tạp (trứng → ấu trùng → trưởng thành → cắn người → ủ bệnh) tốn 2-3 tháng. Còn flu trực tiếp lây qua giọt bắn, chỉ 1-2 tuần."
>
> "Phát hiện này validate đúng với epidemiology literature (Lowe et al 2014 Lancet ID, Reich et al 2019 CDC FluSight)."

## Slide 11 — Session 7: Feature engineering + Endemic Channel

> "Dựa vào lag tối ưu, em build feature set:"
>
> "**Flu: 16 features**, max lag 7 tuần
> - AR features: `flu_log_lag1, lag2, lag3` (autoregressive trên cases)
> - Rolling mean: `rollmean4, rollmean8`
> - Weather lag: theo CCF — temp_lag3/7, humidity_lag1/7, solar_lag7, dewpoint_lag1
> - Seasonality: `iso_week_sin, iso_week_cos` (cyclical encoding)
> - Hemisphere: `HEMISPHERE_NH, HEMISPHERE_SH`"
>
> "**Dengue: 15 features**, max lag 16 tuần
> - AR features: `deng_log_lag6, lag8, lag10, lag12, lag14` (lag dài hơn flu)
> - Rolling mean: rollmean4, rollmean8
> - Weather lag: temp_lag11, dewpoint_lag8, precip_lag6, humidity_lag1, solar_lag16
> - Seasonality: iso_week_sin/cos
> - Year encoding: iso_year"
>
> "Tại sao dengue cần warmup 18 tuần? Vì max lag = 16 + buffer 2 tuần để tính rolling mean."
>
> "**Phần Endemic Channel** — đây là chuẩn quốc tế của WHO EWARS để phân Low/Med/High (Bortman 1999):
> - Baseline = trung bình lịch sử 5 năm gần của cùng quốc gia, cùng tuần ISO
> - Low: `cases < baseline`
> - Medium: `baseline ≤ cases < baseline + 2σ`
> - High: `cases ≥ baseline + 2σ`"
>
> "Mỗi (country, week_of_year) có baseline riêng → 163 × 52 = 8,476 baseline values."

## Slide 12 — Session 8: Train 5 model + walk-forward CV

> "Đây là core ML."
>
> "**Walk-forward CV 6 folds** — chuẩn time-series, không random:
> - Fold 1: train 2010-2013 → val 2014
> - Fold 2: train 2010-2014 → val 2015
> - ...
> - Fold 6: train 2010-2018 → val 2019"
>
> "Train luôn TRƯỚC validation → mô phỏng đúng cách deploy thực tế: tại thời điểm T, chỉ biết data đến T-1. **KHÔNG có data leakage.**"
>
> "Tại sao em train 5 models, không chỉ XGBoost?"
>
> "**Baselines (2):**
> 1. **Naive same-week-last-year** — đại diện 'không cần ML'. Nếu ML không vượt → không đáng dùng ML.
> 2. **Prophet** — statistical baseline của Facebook, không cần feature engineering nhiều.
>
> **Tree-based (3):**
> 3. **XGBoost** — gradient boosting, industry standard.
> 4. **LightGBM** — faster boosting, leaf-wise growth.
> 5. **Random Forest** — bagging, robust với noise."
>
> "Tại sao 3 tree models mà không chỉ XGBoost? **Critical thinking** — không default 'XGBoost vì XGBoost'. Tree models khác nhau bias-variance: RF bagging variance thấp, XGB/LGBM boosting bias thấp → kết quả khác nhau trên data nhỏ."

## Slide 13 — Kết quả Session 8 (v5)

> "Bảng so sánh **Regression** (mean R² qua 6 folds CV) — đây là kết quả v5:"

| Model | Flu R² | Dengue R² |
|---|---|---|
| Naive baseline | 0.560 | 0.487 |
| Prophet | 0.429 | -0.282 |
| XGBoost | 0.901 | 0.931 |
| **LightGBM** (champion flu) | **0.902** | 0.931 |
| **Random Forest** (champion dengue) | 0.899 | **0.936** |
| Best tuned (Optuna 60 trials) | **0.9019** | **0.9366** |

> "**3 phát hiện quan trọng:**"
>
> "**Phát hiện 1: Random Forest THẮNG dengue thay vì XGBoost.** Bagging robust hơn boosting với data nhỏ (5,926 rows). Đây là **critical thinking** — em không mặc định dùng XGBoost, em test và chọn theo bằng chứng."
>
> "**Phát hiện 2: Prophet R² âm với dengue** (-0.282) — statistical baseline không xử lý được data nhiều quốc gia + outliers. Tree-based vượt rõ rệt."
>
> "**Phát hiện 3: ML vượt Naive baseline rõ ràng** — flu Naive 0.560 → LGBM 0.902, dengue Naive 0.487 → RF 0.936. Chứng minh ML đáng giá."

## Slide 14 — Session 8 Multi-horizon (v6) — Extension 21/05

> "Sau khi v5 hoàn tất, em mở rộng thành **multi-horizon** — train 4 model riêng cho h=1, h=2, h=3, h=4 tuần."
>
> "Tại sao không recursive (dùng predict h=1 làm input cho h=2)?"
> "→ Error propagation. Nếu h=1 sai 10%, feed vào h=2 thì error compound thành 15-20%. Train riêng từng h dùng feature actual → error không cộng dồn."

| h | Flu R² (LGBM) | Dengue R² (RF) | So với Lowe 2014 |
|---|---|---|---|
| 1 | 0.866 | 0.929 | VƯỢT (Lowe 0.78-0.85) |
| 2 | 0.829 | 0.919 | VƯỢT (Lowe 0.70-0.78) |
| 3 | 0.793 | 0.909 | VƯỢT (Lowe 0.62-0.72) |
| 4 | 0.757 | 0.898 | **VƯỢT mạnh** (Lowe 0.55-0.68) |

> [NHẤN MẠNH] "**8/8 horizon đều vượt benchmark Lowe et al 2014 Lancet ID** — đây là paper reference cho dengue forecasting Brazil."
>
> "Phát hiện bất ngờ: **dengue degradation gentler hơn flu.**
> - Dengue mất ~0.010 R²/horizon
> - Flu mất ~0.036 R²/horizon"
>
> "Lý do: dengue có lag dài 6-14 tuần → AR signal phủ xa hơn flu (1-7 tuần). Plus, pattern endemic năm cả 12 tháng ở vùng nhiệt đới → ít volatile hơn flu mùa đông Bắc bán cầu."

## Slide 15 — Classification (v5)

> "Bảng Classification — XGBClassifier 3 lớp:"

| Disease | macro-F1 | Đạt mục tiêu? |
|---|---|---|
| Flu | 0.542 ± 0.027 | ✅ Đạt (>0.50) |
| Dengue | 0.475 ± 0.035 | ⚠️ Gần đạt — High recall thấp (14%) |

> "Flu đạt mục tiêu. Dengue chưa hoàn toàn đạt — **High recall thấp 14%**."
>
> "Tại sao? Em phân tích kỹ: do **class shift dengue 2017-2018** — outbreak Brazil 2016 làm inflate baseline → các năm sau ít cases vượt baseline → ít label High → model học khó."
>
> [NHẤN MẠNH] "Đây là **realistic limitation của endemic channel**, không phải bug của model. Walk-forward CV expose được điều này — đó là sức mạnh của CV chuẩn."
>
> "**Em document làm limitation trong báo cáo Chương 5**, hướng xử lý là dùng quantile threshold thay vì baseline+2σ, hoặc per-country threshold thay vì global."

## Slide 16 — Feature Importance (Session 9)

> "Em phân tích feature importance bằng `model.feature_importances_` (gain-based)."
>
> "**Phát hiện ‹$50,000 question›: AR features (lag số ca bệnh) dominate ~90% importance**, weather chỉ ~5%."
>
> "Có phải weather không quan trọng?"
>
> "**KHÔNG** — em document rõ trong báo cáo:
> 1. Weather **xuất hiện đúng theo CCF lag tối ưu** đã tìm trong Session 6 → validate insight epidemiological
> 2. AR dominate vì **disease có inertia** — số ca tuần này gần số ca tuần trước
> 3. Weather có signal nhưng AR đã 'hấp thụ' trực tiếp signal đó (lag đúng)
> 4. Nếu xóa weather features: R² giảm 0.04-0.07 → vẫn quan trọng, không phải irrelevant"

---

# PHẦN 4 — TRIỂN KHAI PRODUCTION (5 phút)

## Slide 17 — Backend FastAPI + ML Engine

> "Em không chỉ làm notebook, em build **full production system**."
>
> "**Backend FastAPI**:
> - 15+ REST endpoints
> - Load 10 model `.pkl` vào memory khi startup (load 1 lần, dùng nhiều)
> - Service layer tách: ml_engine, feature_lookup, risk_service, forecast_service, analytics_service
> - SQLAlchemy ORM, Pydantic validation, Loguru logging"
>
> "**Điểm em cần nói rõ:** hệ thống không bịa dữ liệu realtime. Với mỗi bệnh, backend luôn lấy **tuần mới nhất thật sự có dữ liệu**:
> - Flu: tuần mới nhất từ WHO FluNet sau khi pipeline sync, ví dụ 2026-W21.
> - Dengue: tuần mới nhất từ OpenDengue v1.3 batch, ví dụ 2023-W36.
> - Nếu user chọn ngoài phạm vi dữ liệu, API trả `data_coverage.warning` để FE hiện cảnh báo."
>
> "**Flow dự đoán khi user click một quốc gia:**
> ```
> User clicks Brazil dengue trên dashboard
>   ↓
> Frontend gọi API: GET /forecast/dengue/BRA/nowcast
>   ↓
> Backend forecast_service:
>   1. Xác định latest available week theo disease/country
>      - dengue/BRA → 2023-W36
>      - flu/THA → tuần mới nhất có trong FluNet
>   2. Query feature_snapshots theo (disease, iso3, year, week)
>   3. Lấy cột features JSONB → dict feature vector
>   4. ml_engine chọn model đúng bệnh + horizon h=1..4
>   5. Model predict trên log scale
>   6. expm1() đổi ngược về số ca dự đoán
>   7. Classifier/risk_service trả Low/Medium/High + risk_probability
>   8. Build DataCoverage warning nếu là nowcast/historical/out-of-range
>   9. Trả ForecastResponse JSON
>   ↓
> Frontend render ECharts line chart + badge cảnh báo dữ liệu
> ```"
>
> "**Giải thích thuật ngữ:** FastAPI là web framework Python để tạo REST API. `REST endpoint` là URL backend cho FE gọi. `Pydantic` validate dữ liệu request/response. `Service layer` là lớp tách business logic khỏi router. `JSONB` là kiểu JSON trong PostgreSQL, dùng để lưu feature vector linh hoạt."

## Slide 18 — Database PostgreSQL — 16 bảng

> "Database **16 bảng logic, 31 partition** theo năm cho 3 bảng lớn (`disease_cases`, `weather_observations`, `predictions`)."
>
> "**Partition không phải chia theo quốc gia.** Ở DB, partition là chia bảng lớn theo `iso_year`. Ví dụ query năm 2023 thì PostgreSQL chỉ đọc partition 2023 thay vì scan toàn bộ dữ liệu nhiều năm. Quốc gia vẫn là cột `iso3`, có khóa ngoại tới bảng `countries` và được dùng trong index/query/filter."
>
> "Tại sao partition theo năm? Dữ liệu là time-series theo tuần, các query thường lọc theo year/week → partition pruning giảm scan từ 87K rows xuống khoảng vài nghìn dòng/năm."
>
> "**Nhóm bảng quan trọng nhất:**
> - `countries` — danh mục quốc gia, mã ISO3, vùng WHO, tọa độ centroid.
> - `disease_cases` — số ca bệnh theo disease/country/year/week, gồm raw count và log1p.
> - `weather_observations` — thời tiết theo country/year/week, lưu JSONB như temp, humidity, precip, solar.
> - `feature_snapshots` — feature vector đã tính sẵn cho từng disease/country/week.
> - `predictions` — kết quả model đã dự đoán, dùng cho map và historical view.
> - `model_versions` / `model_evaluations` — metadata, artifact path và metric của model đang deploy."
>
> "**DB nhận dữ liệu mới như thế nào:**
> ```
> sync_flunet.py / sync_weather.py / OpenDengue batch
>   ↓
> disease_cases + weather_observations
>   ↓
> feature_builder.py tính lag/rolling/seasonality
>   ↓
> feature_snapshots
>   ↓
> batch_predict.py chạy model h=1..4
>   ↓
> predictions + pipeline_runs audit log
> ```"
>
> "Tại sao dùng JSONB cho features? Flu có 16 feature, dengue có 15 feature, schema khác nhau. JSONB cho phép dùng 1 bảng `feature_snapshots` chung, backend load thẳng thành dict rồi feed vào `model.predict()`."
>
> "**Phân theo quốc gia làm ở bước nào?** Không partition DB theo quốc gia. Việc tách theo quốc gia xảy ra ở bước feature engineering: khi tạo lag dùng `groupby('iso3').shift()`, nên Brazil chỉ nhìn lịch sử Brazil, Thái Lan chỉ nhìn lịch sử Thái Lan. Trong DB, `iso3` là khóa để query/filter từng quốc gia."

## Slide 19 — MLOps Pipeline — APScheduler

> "Em build pipeline tự động hoàn chỉnh — đây là **MLOps part** thầy cô có thể quan tâm."
>
> "**4 cron jobs trong scheduler:**
>
> | Job | Schedule (ICT) | Mục đích |
> |---|---|---|
> | sync_flunet | Mon 10:00 | Lấy ca cúm mới nhất từ WHO FluNet |
> | sync_weather | Daily 6:00 | Lấy thời tiết Open-Meteo/ERA5 archive cho các tuần gần nhất |
> | build_features | Mon 11:00 | Tính lại feature snapshots cho flu + dengue |
> | batch_predict | Mon 11:30 | Dự đoán tuần mới nhất có data → ghi vào predictions |"
>
> "**Manual triggers** qua admin endpoint:
> - `POST /admin/sync/build_features_dengue_nowcast` — đặc biệt cho OpenDengue batch release mới (không có realtime API)"
>
> "MLOps ở đây nghĩa là vận hành model sau khi train: tự động lấy data mới, build features, chạy inference, ghi log pipeline vào DB và có endpoint admin để kiểm tra."
>
> "Pipeline error handling: subprocess timeout 30 phút, log stdout/stderr tail vào Loguru, ghi `pipeline_runs` vào DB, admin endpoint trả 500 nếu fail → user gọi `/admin/scheduler/status` xem job lần cuối thành công khi nào."

## Slide 20 — Frontend React Dashboard — 3 trang

> "Frontend React + TypeScript + Vite, dùng ECharts cho cả map và charts (cùng lib → bundle nhỏ)."
>
> "**Page 1: HomePage** — world risk map
> - Sidebar trái: tab Flu/Dengue, WeekPicker, RegionFilter, SummaryStats
> - Map giữa: choropleth toàn cầu, hover hiện tooltip, click vào country → DetailPage
> - Sidebar phải: Top 10 Alerts (High risk countries) với sparkline 12 tuần"
>
> "**Page 2: DiseaseDetailPage** — chi tiết quốc gia
> - 4-week Forecast chart (ECharts line với confidence interval)
> - Historical picker: year + week để xem prediction quá khứ
> - DataCoverage warning badge: latest/nowcast/historical/out-of-range
> - 52-week Trend chart (area chart)
> - Summary cards: Predicted, Risk Level, Disease info"
>
> "**Page 3: AnalyticsPage** — model performance
> - Multi-horizon R² bar chart h=1..4
> - Feature importance top 10
> - Confusion matrix classifier"
>
> "**Flow FE gọi BE:**
> ```
> User chọn disease + week + country
>   ↓
> Zustand store lưu state UI
>   ↓
> React hook gọi /api/v1/risk-map hoặc /api/v1/forecast
>   ↓
> Backend trả JSON gồm prediction, risk, data_coverage
>   ↓
> FE vẽ map/chart bằng ECharts và hiện warning nếu dữ liệu không phải latest thật
> ```"
>
> "**Giải thích thuật ngữ:** React là thư viện UI, TypeScript giúp kiểm tra kiểu dữ liệu, Vite là dev/build tool, ECharts là thư viện vẽ map và biểu đồ, Zustand là state management để lưu disease/year/week/country đang chọn."

## Slide 21 — Disease-aware state management (chốt 23/05)

> "Một detail tinh tế em vừa fix tuần này: **state isolation khi switch disease.**"
>
> "Trước fix: zustand store giữ year/week khi switch tab. Nếu flu xem 2026-W21, switch sang dengue thì year=2026 không hợp lệ với dengue (max 2023) → UI lỗi silent."
>
> "Fix: trong action `setDisease()`, **reset year/week/selectedIso3 về DISEASE_DEFAULTS** per-disease. Flu default 2026-W21, dengue default 2023-W36."
>
> "Trade-off em đã cân nhắc: user mất context tuần đang xem, nhưng tránh confusion lớn hơn (year ngoài range → empty map, user không hiểu vì sao)."

---

# PHẦN 5 — REALTIME / NOWCAST (3 phút)

## Slide 22 — Latest-data flu 2026

> "**Đột phá nowcast** em làm trong Phase A (12-23/05):"
>
> "**Flu**: sync dữ liệu mới nhất từ WHO FluNet pipeline, hiện có đến 2026-W21.
> - Coverage: **163 quốc gia × 20 tuần (W02-W21/2026)**
> - Build features → predict h=1..4 cho mỗi tuần
> - User mở dashboard thấy ngay map 2026-W21 thật, không phải data 2019 cũ"
>
> [Demo nếu có thời gian]
>
> "[Mở localhost:5173 → click Flu → map render China 1,081 cases High, Canada 572 High, Brazil 203 High] — đây là dữ liệu **THẬT** tuần này từ WHO."

## Slide 23 — Dengue nowcast 2021-2023

> "**Dengue khó hơn vì OpenDengue không có realtime API** — chỉ có batch release."
>
> "OpenDengue v1.3 release dữ liệu đến **2023-W36**. Em phân tích kỹ:
> - 2020 dropping: COVID disruption làm thiếu báo cáo nhiều nước → loại
> - 2021-W01 đến 2023-W36: có ground truth → **dùng làm nowcast**
> - 2024+: chỉ 23 đảo Pacific (sparse), 2025 zero rows → không dùng được"
>
> "Quyết định: extend dengue coverage từ training-only (2010-2019) thành **training + nowcast (2021-W01 đến 2023-W36)**."
>
> "Coverage: **56 quốc gia × 140 tuần** (52 + 52 + 36) → 7,840 predictions mới"
>
> [NHẤN MẠNH] "Điểm quan trọng cho thầy cô: **đây không phải extrapolation mù** — có ground truth, em có thể compare predicted vs actual để validate. Báo cáo Chương 4 em sẽ document residual analysis trên giai đoạn nowcast."

## Slide 24 — Honesty với GVHD: DataCoverage warning

> "Em làm điểm này rất nghiêm túc: **không bao giờ fake data, luôn báo trung thực cho user.**"
>
> "Mỗi ForecastResponse có field `data_coverage` với 3 trạng thái:
>
> 1. **in_training_period = true**: Năm này có trong training (2010-2019). Đáng tin cậy.
>
> 2. **is_nowcast = true** (dengue 2021-2023): Có ground truth từ OpenDengue, nhưng release batch chứ không realtime. Em hiển thị warning vàng trên UI: '⚠ Năm 2023 là giai đoạn nowcast dengue, OpenDengue v1.3 đến 2023-W36.'
>
> 3. **Neither true** (flu 2026): Extrapolation thật, không có ground truth. Warning đỏ: 'Năm 2026 nằm ngoài training window. Dự báo là extrapolation — không có ground truth để validate độ chính xác.'"
>
> "Đây là điểm em muốn nhấn mạnh: **transparency với user/GVHD quan trọng hơn metric đẹp**. Em không che dấu limitation."

---

# PHẦN 6 — KẾT QUẢ & ĐÓNG GÓP (2 phút)

## Slide 25 — Tổng kết kết quả

> "**Số liệu quan trọng:**"

| Metric | Flu | Dengue |
|---|---|---|
| Countries (training) | 143 | 35 |
| Countries (realtime/nowcast) | 163 | 56 |
| R² h=1 (CV) | **0.866** | **0.929** |
| R² h=4 (CV) | 0.757 | 0.898 |
| Classifier macro-F1 | 0.542 ✅ | 0.475 ⚠️ |
| Latest data tuần | 2026-W21 (realtime) | 2023-W36 (nowcast) |

> "**So với baseline literature:**
> - Lowe 2014 Lancet ID (dengue Brazil): R² 0.55-0.85 → **mình vượt 8/8 horizons**
> - Naive SWLY (same-week-last-year): R² 0.5-0.56 → **mình gấp 1.6×**"

## Slide 26 — Đóng góp khoa học

> "**3 đóng góp chính của KLTN em:**"
>
> "**1. Multi-disease hybrid pipeline** — đa số paper chỉ làm 1 bệnh (flu HOẶC dengue). Em làm cả 2, cùng kiến trúc, kết quả vượt baseline cho cả 2."
>
> "**2. Multi-horizon (h=1..4) với feature actual** thay vì recursive — tránh error propagation. Documented kỹ trong Chương 4."
>
> "**3. End-to-end production system** — không chỉ notebook, mà cả: PostgreSQL với partition + JSONB, FastAPI với 15 endpoints, React dashboard 3 trang, APScheduler 4 cron jobs tự động. **Có thể deploy lên server thật ngay.**"

## Slide 27 — Limitation thẳng thắn

> "Em không che dấu hạn chế:"
>
> "**1. Dengue classifier macro-F1 chỉ 0.475** — High recall thấp 14% do class shift 2017-2018. Đã document làm limitation, đề xuất hướng giải quyết: per-country quantile threshold."
>
> "**2. Dengue nowcast giới hạn 2023-W36** — do OpenDengue không có realtime API. Đề xuất tương lai: scrape MOH các nước, hoặc đợi OpenDengue v1.4 release."
>
> "**3. Flu 2020-2021 bị loại** khỏi training do NPI distortion → model có thể không robust với pandemic mới. Đã document làm assumption."
>
> "**4. Weather features chỉ 5% importance** vs AR 90% — không phải weather không quan trọng, mà AR đã hấp thụ signal qua lag đúng. R² giảm 0.04-0.07 nếu xóa weather."

## Slide 28 — Hướng phát triển

> "**Sau khi báo cáo, em đã có plan tiếp theo:**"
>
> "**Phase D-1 (đang làm):**
> - Báo cáo Chương 4 + 5
> - Notion + Slide presentation hoàn thiện"
>
> "**Phase D-2 (sau demo):**
> - CI/CD GitHub Actions: `npx tsc --noEmit` + pytest mỗi PR
> - Model registry auto-register vào bảng `model_versions` khi train xong
> - pipeline_runs tracking persist vào DB (schema ready)"
>
> "**Phase D-3 (research extension):**
> - Per-country quantile threshold cho classifier
> - Add COVID-era data với COVID indicator feature
> - Multi-pathogen: thêm Zika, Chikungunya (cùng vector Aedes)"

---

# PHẦN 7 — Q&A CHUẨN BỊ (5-10 phút)

## Câu hỏi có thể gặp và cách trả lời

**Q1: Tại sao không dùng deep learning (LSTM, Transformer)?**

> "Em có cân nhắc. Nhưng:
> 1. Data tương đối nhỏ: flu 55K rows, dengue 5,900 rows → tree-based đủ, deep learning overfit
> 2. Tabular data đã có lag features → AR signal extract sẵn, không cần LSTM học temporal
> 3. Tree-based interpretable (feature importance) — quan trọng cho thuyết trình + debug
> 4. Inference nhanh hơn (<10ms vs >100ms LSTM)
> Nếu có thêm thời gian, em sẽ thử ensemble (LightGBM + LSTM) → đây là plan D-3."

**Q2: Tại sao Random Forest thắng XGBoost ở dengue?**

> "Bagging robust hơn boosting trên data nhỏ (5,926 rows). XGBoost overfit khi data limited — variance cao. RF average qua nhiều tree → variance thấp. Đây là pattern thường thấy: data > 100K rows thì XGBoost thắng, data < 10K thì RF thường tốt hơn."

**Q3: Walk-forward CV có bias không khi val_year 2014 chỉ có 4 năm training?**

> "Em có document. Fold 1 (val 2014, train 2010-2013) chỉ có 4 năm → R² thấp hơn fold 6 (val 2019, train 2010-2018, 9 năm). Em report **mean** qua 6 folds → đại diện performance tổng quát. Plus em report std deviation → confidence của metric."

**Q4: Em có handle missing data thế nào?**

> "3 chiến lược tùy nguồn:
> 1. **FluNet INF_ALL missing 44%** → bỏ luôn cột này, dùng `INF_A + INF_B`
> 2. **Disease cases missing tuần lẻ** → fillna(0) — vì missing = không báo cáo, không phải = 0 ca
> 3. **Weather lag missing đầu năm** → walk-forward CV bỏ qua các fold không đủ warmup (18 tuần dengue, 8 tuần flu)"

**Q5: Tại sao không dùng API real-time của WHO?**

> "WHO có dataset realtime nhưng chỉ qua Power BI public dashboard, không có REST API. Em phải pull qua URL Power BI → CSV download. `sync_flunet.py` em đã code để pull tuần mới mỗi Monday 10:00 ICT (sau WHO publish lúc 8:00 UTC)."

**Q6: Em test/validate hệ thống thế nào?**

> "3 cấp:
> 1. **Notebook level**: walk-forward CV 6 folds, RMSE/MAE/R² per fold
> 2. **API level**: pytest cho mỗi endpoint, mock DB. Đã có 47% coverage.
> 3. **Integration**: manual smoke test flow user — click country → forecast load → check DB. Em đã test với flu/dengue/multiple countries.
> Em document chi tiết trong Chương 4."

**Q7: Hệ thống deploy ra production được không?**

> "Có. Em đã build với mindset production:
> - PostgreSQL partition → scale tốt
> - FastAPI async → xử lý concurrent requests
> - Models load 1 lần vào memory → inference fast
> - APScheduler auto-sync → không cần cron Linux external
> Em chưa deploy lên cloud, nhưng có Dockerfile + docker-compose.yml ready. Sau demo em sẽ deploy thử Render/Railway free tier."

**Q8: Em có so sánh với commercial system (Google Flu Trends, BlueDot...) không?**

> "Em có khảo sát:
> - Google Flu Trends đã shut down 2015 vì overfit search query
> - BlueDot là commercial, không public benchmark
> - HealthMap mỗi nước khác → khó so sánh
> Em chọn so với **academic benchmark Lowe et al 2014 Lancet ID** vì có metric công khai. Kết quả vượt 8/8 horizons."

**Q9: Đề tài này giúp ích thực tế thế nào?**

> "3 ứng dụng thật:
> 1. **Bộ Y tế VN**: dashboard cảnh báo dengue Vietnam tuần này, lập kế hoạch diệt muỗi
> 2. **Hành khách quốc tế**: trước đi du lịch, check map risk
> 3. **Nghiên cứu**: feature importance giúp epidemiologist hiểu yếu tố thời tiết nào driver mạnh nhất"

**Q10 (catch-all): Nếu được làm lại, em sẽ làm gì khác?**

> "3 thứ:
> 1. **Spend thêm thời gian EDA dengue** — em phát hiện class shift 2017-2018 trễ → mất nhiều thời gian tune classifier dengue
> 2. **Setup CI/CD ngay từ đầu** — em làm khi gần cuối → một số commit không pass type check
> 3. **Thêm experiment tracking (MLflow)** — em manage version bằng tay (v1, v2, v3) → khó so sánh chi tiết"

---

## KẾT THÚC

> "Em xin cảm ơn thầy cô đã lắng nghe. Em xin nhận mọi câu hỏi và góp ý ạ."

[Đứng thẳng, hơi nghiêng người về phía hội đồng, mỉm cười]

---

## Phụ lục — Tài liệu liên quan

| File | Vai trò |
|---|---|
| `docs/chi_tiet_he_thong.md` | Chi tiết toàn bộ hệ thống (dataset, DB, BE, FE) — đọc khi GVHD đào sâu |
| `docs/presentation/README.md` | Index 9 session — slide truyền thống |
| `docs/presentation/session_*.md` | Thuyết trình từng session — phụ lục slide |
| `docs/presentation/hanh_trinh_cai_thien.md` | Lý do nâng cấp v3 → v5 → v6 |
| `docs/session_summaries/2026-05-23_session_summary.md` | Session gần nhất — nowcast extension |
| `docs/bao_cao_tong_quan_he_thong.md` | Tổng quan version trước (22/05) |
| `KLTN_EpiWeather_ML_v6.ipynb` | Notebook full — Session 0-9 |

---

**Sinh viên Phạm Hữu Luân — 110122016 — DA22TTA**
**EpiWeather Global Epidemic Warning System — Trường Đại học Trà Vinh — 2026**
