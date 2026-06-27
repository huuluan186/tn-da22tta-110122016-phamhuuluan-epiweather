# Kịch Bản Thuyết Trình — KLTN EpiWeather (v5)

> ⚠️ **File này là bản v5 nguyên gốc (17/05/2026)** — chỉ cover ML pipeline đến Session 9.
> Cho version mới nhất bao gồm **v6 multi-horizon + Phase A realtime + nowcast + frontend**, đọc:
> **➡️ [../thuyet_trinh_bao_cao.md](../thuyet_trinh_bao_cao.md)** — kịch bản 25 phút consolidated v5+v6
>
> Phần cuối file này (PHẦN 8) có **bổ sung update v6 + Phase A** để integrate vào script v5 hiện tại.

> **Đề tài:** Hệ thống cảnh báo nguy cơ dịch bệnh theo mùa dựa trên dữ liệu y tế và thời tiết toàn cầu
> **Sinh viên:** Phạm Hữu Luân — MSSV 110122016 — DA22TTA
> **Tổng thời lượng dự kiến:** 20-25 phút thuyết trình + 5-10 phút Q&A
>
> **HƯỚNG DẪN SỬ DỤNG:**
> - Câu nói trong khung `>` là **câu mẫu nói trực tiếp** — luyện cho đến khi tự nhiên
> - Phần `[CHUYỂN SLIDE]` là cue đổi slide
> - Phần `[NHẤN MẠNH]` là chỗ cần lên giọng / chậm lại để gây ấn tượng
> - Phần `[NẾU HỎI]` là chuẩn bị cho câu hỏi GVHD có thể hỏi
>
> **QUY TẮC VÀNG khi thuyết trình:**
> 1. Đừng đọc slide — slide là **bằng chứng**, miệng phải kể **câu chuyện**
> 2. Mỗi 2-3 phút phải có **con số cụ thể** hoặc **phát hiện cụ thể** để giữ attention
> 3. Khi thầy hỏi khó, **không nói "em không biết"** — nói **"em document làm limitation, hướng xử lý là..."**
> 4. Tự tin nhưng khiêm tốn — sai một chỗ vẫn ok, đừng cố cãi
> 5. Tốc độ nói: ~140 từ/phút (không quá nhanh)

---

# PHẦN 1 — MỞ ĐẦU (2 phút)

## Slide 1 — Tiêu đề + sinh viên

> "Chào thầy cô, em là Phạm Hữu Luân, MSSV 110122016, lớp DA22TTA. Hôm nay em xin trình bày đồ án tốt nghiệp với đề tài **Hệ thống cảnh báo nguy cơ dịch bệnh theo mùa dựa trên dữ liệu y tế và thời tiết toàn cầu**. GVHD của em là [tên thầy]."

[Chờ 2 giây, nhìn xuống thầy cô]

## Slide 2 — Bài toán & Motivation

> "Câu hỏi mà đề tài này giải là: **giả sử chúng ta có dữ liệu thời tiết tuần này — nhiệt độ, độ ẩm, mưa, bức xạ mặt trời — của một quốc gia bất kỳ trên thế giới, liệu có thể dự báo được nguy cơ bùng phát dịch cúm và sốt xuất huyết vài tuần tới không?**"
>
> "Đây là bài toán **có ý nghĩa thực tế**: WHO ước tính cúm mùa gây 3-5 triệu ca nặng và 290-650 nghìn tử vong mỗi năm; sốt xuất huyết hiện ảnh hưởng đến 129 quốc gia, gần một nửa dân số thế giới có nguy cơ. Nếu hệ thống cảnh báo sớm 2-3 tuần, ngành y tế có thể chuẩn bị vaccine, giường bệnh, hoặc chiến dịch diệt muỗi."
>
> [NHẤN MẠNH] "Đây không phải bài toán dễ — em sẽ giải thích vì sao trong vài phút tới."

## Slide 3 — Tại sao bài toán này KHÓ

> "Có 5 thử thách chính:"
>
> "**Thứ nhất**, dữ liệu đến từ **4 nguồn khác nhau** — mỗi nguồn định dạng khác, độ phủ khác. WHO FluNet cho cúm, OpenDengue cho sốt xuất huyết, ERA5 ECMWF cho khí hậu, ECDC cho validation."
>
> "**Thứ hai**, em phải làm việc với **163 quốc gia**, mỗi nước có mùa bệnh khác nhau. Bán cầu Bắc đỉnh cúm tuần 6 — bán cầu Nam đỉnh tuần 28, lệch nhau 22 tuần. Mô hình phải học được pattern này."
>
> "**Thứ ba**, dữ liệu thời tiết ERA5 ở dạng **lưới địa lý 721×1440 điểm** — tức là hơn 1 triệu điểm trên toàn cầu. Em cần data theo quốc gia × tuần, không theo lưới. Phải có kỹ thuật map từ lưới về quốc gia."
>
> "**Thứ tư**, đề tài yêu cầu **cả hai bài toán**: dự báo số ca bệnh (regression) và cảnh báo mức nguy cơ Low/Medium/High (classification). Em làm cả hai và so sánh."
>
> "**Thứ năm**, kết quả phải chạy được trên **server thật** phục vụ dashboard React/Leaflet — không phải chỉ Jupyter notebook."

---

# PHẦN 2 — PIPELINE OVERVIEW (3 phút)

## Slide 4 — Sơ đồ pipeline tổng thể

> "Đây là kiến trúc pipeline em xây dựng. Em chia ra **9 session** trong notebook, mỗi session độc lập đọc input từ file CSV, ghi output ra file CSV — nghĩa là restart Colab giữa chừng không phải làm lại từ đầu."

[Chỉ vào sơ đồ]

> "Bốn nguồn dữ liệu thô đi vào — **WHO FluNet 183 nghìn dòng cho cúm**, **OpenDengue V1.3 18 nghìn dòng cho sốt xuất huyết**, **ERA5 6.2 GB NetCDF cho khí hậu**, và **ECDC cho validation hậu COVID**."
>
> "Qua bước **KD-tree centroid mapping**, em chuyển lưới ERA5 1 triệu điểm về 197 centroid quốc gia. Sau khi merge 3 nguồn — flu, dengue, weather — em được **master dataset 61 nghìn dòng × 27 cột, cover 163 quốc gia từ 2010-2019**."
>
> "Tiếp theo là **Feature Engineering** dựa trên phân tích Cross-Correlation Function, sinh ra 2 file features riêng cho flu và dengue. Cùng với đó là **Endemic Channel labels** theo chuẩn WHO EWARS 2012 (Bortman 1999) cho bài toán classification."
>
> "Cuối cùng là **train 5 models regression + 1 classifier**, đánh giá bằng **walk-forward CV 6 folds**, chọn champion, tune Optuna, và export model artifacts để deploy."

## Slide 5 — Approach v5: Hybrid Regression + Classification

> "Em xin nhấn mạnh: đề tài yêu cầu cả 'dự báo dịch bệnh có thể diễn ra' (số ca cụ thể) và 'cảnh báo mức độ' (Low/Med/High). Em **không chọn 1**, em làm **cả hai và so sánh** — đây là đóng góp khoa học của báo cáo."
>
> "**Nhánh A — Regression**: dự báo số ca, log1p transform, dùng cho biểu đồ trend trên dashboard. Models so sánh: Naive baseline, Prophet, XGBoost, LightGBM, Random Forest."
>
> "**Nhánh B — Classification**: phân loại Low/Med/High bằng Endemic Channel của Bortman 1999, dùng cho bản đồ choropleth cảnh báo trên dashboard. Model: XGBClassifier multi-class."

---

# PHẦN 3 — DEEP-DIVE TỪNG PHẦN (10 phút)

## Slide 6 — Session 0-1: Lấy dữ liệu ở đâu

> "Em không thể nói 'em load data về' rồi skip. Mỗi nguồn có rationale rõ ràng tại sao chọn."
>
> "**WHO FluNet** — database cúm toàn cầu chính thức duy nhất của WHO. 189 quốc gia, cập nhật hàng tuần từ 1995. Cột em dùng là `INF_A + INF_B`, không dùng `INF_ALL` vì missing 44%."
>
> "**OpenDengue V1.3** — dataset học thuật, paper publish trên Scientific Data 2024 (Clarke et al). 82 quốc gia chủ yếu nhiệt đới. Brazil **chiếm 71%** tổng ca dengue toàn cầu — sau này em phải xử lý đặc biệt với log1p."
>
> "**ERA5** — em chọn vì là **reanalysis dataset chuẩn quốc tế** của ECMWF, độ chính xác cao hơn OpenWeatherMap historical, free cho research. Lưới 0.25°, 17 biến khí hậu, 6.2GB cho 2010-2019."
>
> "**ECDC** chỉ có từ 2021 nên không dùng được cho training — em dùng để validation post-COVID và display trên dashboard."
>
> [NẾU HỎI: Sao không dùng WHO ICD-10 / Bộ Y tế VN?]
> > "Em có khảo sát. Bộ Y tế VN không có API public — phải lấy data thủ công từ báo cáo PDF. ICD-10 là chuẩn coding bệnh, không phải dataset cases. FluNet và OpenDengue đã cover được 92% dân số thế giới, đủ scope đồ án tốt nghiệp."

## Slide 7 — Session 2-3: EDA & log1p — phát hiện quan trọng nhất

> "Phần EDA em làm rất kỹ — đây là 50% giá trị của project."
>
> "**Phát hiện 1**: Phân phối số ca bệnh **rất skewed**. Flu có skew 25.6, dengue 12.6. Để dễ hình dung: Brazil 2016 có outbreak dengue 146 nghìn ca/tuần, trong khi median chỉ 11 ca/tuần — tỷ lệ 13 nghìn lần. Nếu train trên raw data, model bị Brazil chi phối hoàn toàn."
>
> [NHẤN MẠNH] "Em áp dụng **log1p transform** — 1 dòng code, đổi skew flu từ 25.6 về 1.04, gần normal. Kết quả: R² nhảy từ 0.488 lên 0.791 — tăng 30% chỉ từ 1 dòng. Đây là phát hiện quan trọng nhất của em."
>
> "**Phát hiện 2**: Dengue 2010-2014 chỉ có 5-12 nước báo cáo — quá sparse để train. Em **thu hẹp training window dengue về 2015-2019** thay vì 2010-2019. Mất 5 năm data nhưng đổi lấy coverage đủ tốt."
>
> "**Phát hiện 3**: 2020-2021 vẫn 166-167 nước báo cáo (ngang 2019, không drop) — nhưng số ca cúm giảm 99% do NPI (mask, lockdown). Đây là **artificial drop**, không phải missing data. Em loại 2020-2021 khỏi training để model học pattern bình thường."
>
> "**Phát hiện 4**: Phase shift hemisphere — bán cầu Bắc đỉnh cúm tuần 6, bán cầu Nam đỉnh tuần 28. Lệch nhau **đúng 22 tuần** — khớp hoàn hảo với lý thuyết dịch tễ học. Đây là sanity check khẳng định data đáng tin cậy."

## Slide 8 — Session 4: ERA5 + KD-tree mapping

> "Đây là phần kỹ thuật khó nhất của project."
>
> "ERA5 là lưới 721×1440 điểm — **hơn 1 triệu điểm trên toàn cầu**. Em cần data theo quốc gia × tuần. Approach naive: lấy điểm gần thủ đô — **sai cho nước lớn** như USA, Russia, Brazil. Approach chuẩn: polygon clip biên giới — **quá chậm**, mất 2 ngày cho 10 năm × 17 biến."
>
> [NHẤN MẠNH] "Em chọn **KD-tree centroid mapping**: build KD-tree từ 1 triệu điểm grid, với mỗi centroid quốc gia tìm 8 điểm gần nhất, weighted average theo inverse distance. **Nhanh gấp 200 lần polygon clip, chỉ mất 5% accuracy** — chấp nhận được."
>
> "Kết quả: 197 quốc gia matched, mất 53 đảo nhỏ Pacific như Tuvalu, Nauru. **Coverage 92% dân số thế giới** — em document làm limitation."
>
> [NẾU HỎI: KD-tree là gì?]
> > "KD-tree là cấu trúc dữ liệu phân chia không gian k-dimensional, cho phép query nearest-neighbor trong O(log n) thay vì O(n). Em dùng `scipy.spatial.cKDTree`."

## Slide 9 — Session 6: CCF Lag Analysis

> "Đây là phần em demonstrate **không default**. Approach sinh viên thường: dùng weather lag `[1, 2, 3]` đồng loạt cho mọi biến. **Sai** — vì virus cúm có incubation + reporting delay ~2-8 tuần, muỗi vector-borne ~4-12 tuần. Một số nhỏ là không đủ."
>
> "Em tính **Cross-Correlation Function** giữa weather và cases per (country, variable), tìm lag tối ưu trên 30 nước top quality."
>
> "Kết quả flu:"
> - "Solar radiation lag **7 tuần**, r = −0.41 (mạnh nhất). UV thấp 7 tuần trước → virus survive → flu tăng."
> - "Temperature lag **3 tuần**, r = −0.37. Cold air → mucus khô → virus dễ xâm nhập."
> - "Humidity lag **7 tuần**, r = +0.31. Khớp **Shaman & Kohn 2009 PNAS** — humidity tăng aerosol stability."
>
> "Kết quả dengue:"
> - "Temperature lag **11 tuần**, r = +0.31. Khớp **Lowe et al. 2014 Lancet Infectious Diseases** — temp lag 2-3 tháng → dengue."
> - "Dewpoint lag 8, precipitation lag 6 — đúng vòng đời muỗi: mưa → trứng → ấu trùng → trưởng thành 2-3 tuần → cắn → dengue incubation 4-7 ngày → cases báo cáo."
>
> "**Em tìm lag từ data, validate với literature** — đây là evidence-based, không guesswork."

## Slide 10 — Session 7: Endemic Channel Labels

> "Bài toán classification cần label Low/Med/High. Naive approach: chia tertile theo cases — **sai** vì Brazil 10K ca/tuần và Singapore 50 ca/tuần không thể dùng cùng threshold."
>
> "Em dùng **Endemic Channel** của **Bortman 1999** (PAHO original) — chuẩn của WHO EWARS Technical Guide 2012:"
>
> - "Baseline = trung bình **5 năm trước** per (quốc gia × tuần ISO)"
> - "Upper = baseline + 2σ"
> - "Low: cases < baseline; Medium: baseline ≤ cases < upper; High: cases ≥ upper"
>
> "5 năm là minimum theo WHO EWARS — 3 năm thì `std` không đáng tin. 2σ tương ứng ~2.5% upper tail của Gaussian — 'rare event' đáng cảnh báo."
>
> "Class balance: Flu 56/26/17, Dengue 47/30/23 — chấp nhận được với `class_weight='balanced'`."
>
> [NẾU HỎI: Sao không quantile-based threshold?]
> > "Em có cân nhắc. Quantile threshold đảm bảo class balance đều nhưng không có ý nghĩa epidemiological. Bortman 1999 + WHO EWARS dùng Gaussian assumption — 2σ là threshold standard cho 'unusual event'. Em chọn cite được thay vì arbitrary."

## Slide 11 — Session 8: Train 5 models + Walk-forward CV

> "Em **không train chỉ 1 model**. Em train **5 models regression + 1 classifier** và so sánh fair — cùng feature set, cùng CV scheme, cùng metrics."
>
> "**5 models regression**: Naive (same-week-last-year), Prophet, XGBoost, LightGBM, Random Forest."
>
> "**Walk-forward CV 6 folds**: train 2010-2013 val 2014, train 2010-2014 val 2015, ..., train 2010-2018 val 2019. **Train luôn TRƯỚC val** — đúng chuẩn time-series, không có data leakage. K-fold ngẫu nhiên sẽ trộn time → model học từ tương lai."
>
> [CHUYỂN SLIDE — bảng kết quả]
>
> "Đây là bảng kết quả — mean R² qua 6 folds:"
>
> | Model | Flu R² | Dengue R² |
> |-------|--------|-----------|
> | Naive | 0.560 | 0.487 |
> | Prophet | 0.429 | **-0.282** |
> | XGBoost | 0.901 | 0.931 |
> | **LightGBM** 🏆 | **0.902** | 0.931 |
> | **Random Forest** 🏆 | 0.899 | **0.936** |
>
> "**Phát hiện 1**: Tree-based beat Naive với margin lớn — R² 0.90 vs 0.56, improvement 60%. Chứng minh ML có giá trị vs heuristic."
>
> "**Phát hiện 2**: Prophet R² âm với dengue — confirm statistical model không handle được data có outlier Brazil 2016. Loại Prophet khỏi production."
>
> [NHẤN MẠNH] "**Phát hiện 3 — quan trọng**: Random Forest **thắng** XGBoost trên dengue. Đây không phải fluke — RF là bagging, robust hơn với data nhỏ (dengue chỉ 5,926 rows). XGB/LGBM boosting tốt hơn với data lớn. **Em không default trust XGBoost** — phải so sánh."
>
> "Champion final:"
> - "**Flu: LightGBM** (R² 0.9019, fastest inference)"
> - "**Dengue: Random Forest** (R² 0.9366)"

## Slide 12 — Optuna tuning

> "Em tune **chỉ champion model** với 60 trials Optuna TPE — không tune cả 5 models (lãng phí compute)."
>
> "Improvement marginal: LightGBM 0.9018 → 0.9019, RF 0.9359 → 0.9366. Lý do: **AR features dominate 90% feature importance**, tree depth/learning_rate không tạo khác biệt lớn khi signal đã rất mạnh."
>
> "Em document insight này — default params đã near-optimal cho feature set này."

## Slide 13 — Feature Importance

> "Em xin chỉ ra **model học cái gì** — đây là phần demonstrate model không bị overfit noise."
>
> "**Flu (LightGBM):**"
> - "Top 3: `flu_log_lag1` 54%, `lag2` 31%, `lag3` 8% — **AR dominate 93%**"
> - "Weather: solar_lag7 1.5%, temp_lag3 1%, humidity_lag7 0.8% — **5% nhưng đúng theo CCF**"
>
> [NHẤN MẠNH] "**Đây là validation epidemiological**: AR features dominate vì dịch bệnh persistent — tuần này nhiều ca thì tuần sau nhiều ca. Weather là **conditioning factor** — không phải primary predictor. Đây khớp với literature: Lowe 2014, Shaman 2009. Nếu weather > 50% importance, em sẽ nghi ngờ data leakage."
>
> "**Dengue (RF):**"
> - "Top 3: `deng_log_rollmean4` 70%, `rollmean8` 12%, `lag6` 6% — AR dominate 88%"
> - "Weather: temp_lag11 2.5%, precip_lag6 1.5% — đúng lý thuyết vector-borne"
>
> "Insight cho thesis: 'Model agrees with epidemiological prior — confirming data is informative.'"

## Slide 14 — Classification results & honest limitation

> "Classification XGBClassifier:"
>
> | Disease | macro-F1 | F1(High) |
> |---------|----------|----------|
> | Flu | **0.542** | 0.46 |
> | Dengue | 0.475 | **0.30** |
>
> "**Flu đạt mục tiêu** macro-F1 > 0.50. F1(High) = 0.46 — bắt được 65% các tuần outbreak, critical cho public health."
>
> [NHẤN MẠNH] "**Dengue F1(High) = 0.30 — em xin honest về limitation này.** Lý do: Brazil 2016 outbreak (146K ca) inflate baseline 2017-2018 → ít cases vượt baseline → model under-train. Đây là **realistic limitation của Endemic Channel method**, không phải bug. Walk-forward CV bắt được điều này — đó là **giá trị** của CV scheme này, không phải weakness."
>
> "Hướng mitigation đề xuất trong báo cáo: quantile-based threshold thay vì 2σ Gaussian, hoặc focal loss để bù class High."

---

# PHẦN 4 — DEMO DASHBOARD (3 phút)

## Slide 15 — Demo dashboard

> "Em đã port dashboard EpiWatch dark-theme dùng React + Tailwind + ECharts. Em sẽ demo nhanh các tính năng:"

[Chuyển sang browser, screen-share dashboard]

> "**1. World map choropleth** — màu theo risk level Low/Med/High per quốc gia, click vào nước hiện chi tiết."
>
> "**2. Region filter sidebar** — filter theo WHO region (AFR, AMR, EMR, EUR, SEAR, WPR)."
>
> "**3. Disease detail page** — biểu đồ trend số ca (predicted vs actual), confidence interval, top 10 nước high risk."
>
> "**4. Analytics page** — feature importance, model performance per fold."
>
> "**5. Alerts sidebar** — danh sách cảnh báo realtime: nước nào đang High risk tuần này."
>
> "Backend FastAPI đã scaffold với alembic migrations + service layer. Model `.pkl` load qua joblib, predict endpoint trả JSON cho frontend."

[Kết thúc demo]

---

# PHẦN 5 — HÀNH TRÌNH CẢI THIỆN (2 phút)

## Slide 16 — Timeline v1 → v5

> "Em xin nhấn mạnh: pipeline này **không ra kết quả 0.90 từ lần đầu**. Em đi qua 5 version trong 3 tuần:"
>
> | Version | Approach | Flu R² |
> |---------|----------|--------|
> | v1 | Single XGBoost, raw cases | 0.488 |
> | v2 | + log1p target | 0.791 (+0.30) |
> | v3 | + Multi-model classification (Bortman labels) | (F1 0.49) |
> | v4 | + WHO region + log1p AR features | (F1 0.53) |
> | **v5** | **Hybrid + walk-forward CV + CCF lag** | **0.9019** |
>
> "Mỗi version có phát hiện cụ thể, không random tuning:"
> - "v2: log1p — phát hiện skew quá lớn"
> - "v3: Bortman labels — yêu cầu đề tài có classification"
> - "v4: sanity check phát hiện AR features cũng skewed"
> - "v5: build lại từ đầu vì single-split không rigorous"
>
> "**Đây là quá trình ML thực sự — học bằng làm, sửa sai, cải thiện. Không phải lucky baseline.**"

---

# PHẦN 6 — KẾT LUẬN (2 phút)

## Slide 17 — Đóng góp & Kết luận

> "Đóng góp chính của đồ án:"
>
> "**1. Pipeline đầy đủ end-to-end** — từ raw data 4 nguồn (FluNet, OpenDengue, ERA5, ECDC) đến trained model + dashboard demo."
>
> "**2. Approach hybrid** Regression + Classification — đáp ứng đầy đủ yêu cầu đề tài (dự báo số ca + cảnh báo mức độ), so sánh khoa học giữa 2 nhánh."
>
> "**3. Methodology rigorous** — CCF lag từ data, validate với literature; walk-forward CV chuẩn time-series; multi-model so sánh không default."
>
> "**4. Kết quả cao**: Flu R² 0.9019, Dengue R² 0.9366 — vượt xa baseline naive 0.56, stable qua 6 folds CV."
>
> "**5. Production-ready**: 4 model `.pkl` + metadata, FastAPI scaffold, React dashboard port — sẵn sàng deploy."

## Slide 18 — Hướng phát triển

> "Hướng phát triển tiếp theo:"
>
> "**Ngắn hạn (sau bảo vệ):**"
> - "Integrate OpenWeatherMap API cho realtime forecast"
> - "Docker Compose full deploy"
> - "Fix dengue F1(High) bằng quantile threshold"
>
> "**Dài hạn:**"
> - "Mở rộng sang COVID, malaria, measles"
> - "Time-series deep learning (LSTM, Transformer) cho large countries"
> - "CI/CD GitHub Actions + MLOps retrain pipeline tự động hàng tuần"
> - "Mobile app cho cảnh báo realtime"

## Slide 19 — Cảm ơn

> "Em xin chân thành cảm ơn thầy [tên GVHD] đã hướng dẫn em suốt 6 tháng qua, cảm ơn quý thầy cô hội đồng đã dành thời gian lắng nghe. Em xin sẵn sàng nhận câu hỏi của thầy cô."

[Cúi nhẹ, đợi câu hỏi]

---

# PHỤ LỤC — DỰ ĐOÁN CÂU HỎI Q&A

## Q1: Em chọn ERA5 thay vì OpenWeatherMap historical vì sao?
> "ERA5 là **reanalysis dataset** chuẩn quốc tế của ECMWF, độ chính xác cao hơn vì hợp nhất quan trắc thực với mô hình khí tượng. OpenWeatherMap historical lấy từ station thưa, nhiều gap, và phải trả phí cho ≥ 2 năm history. ERA5 free cho research, cover từ 1940 trên toàn cầu với lưới 0.25° đồng nhất."

## Q2: Vì sao Random Forest beat XGBoost cho dengue?
> "Hai lý do: **(1) Data size**: dengue chỉ 5,926 rows, RF bagging robust hơn boosting với data nhỏ vì variance thấp hơn. **(2) Outlier**: Brazil 2016 outbreak là outlier mạnh — XGB boosting bị influence bởi residual lớn, RF bagging average out. Em document insight này — **không default trust XGBoost** là một phát hiện đáng kể của đồ án."

## Q3: Walk-forward CV vs K-fold khác gì?
> "**K-fold random** trộn ngẫu nhiên train/val → model có thể học từ data tương lai, predict quá khứ → **R² inflate artificially** (data leakage). **Walk-forward** train luôn TRƯỚC val, mô phỏng đúng deploy: tại thời điểm T chỉ biết data đến T-1. Đây là chuẩn duy nhất chấp nhận được cho time-series, em làm 6 folds val 2014-2019."

## Q4: AR features dominate 90% — vậy weather có cần không?
> "Câu hỏi rất hay. **AR dominate vì dịch bệnh persistent** — đó là property tự nhiên, không phải bug. **Weather contribute 5%** nhưng xuất hiện đúng theo CCF lag (solar lag 7, temp lag 3, humidity lag 7 cho flu; temp lag 11 cho dengue). 5% nhỏ nhưng **statistically significant** và khớp literature (Lowe 2014, Shaman 2009). Nếu chỉ AR không weather, model sẽ fail khi pattern thay đổi (climate shift, COVID-like event). Weather là **conditioning factor** cần thiết để generalize."

## Q5: Vì sao em chia Low/Med/High dùng 2σ chứ không phải tertile?
> "Tertile chia đều 33/33/33 nhưng **không có ý nghĩa epidemiological**. Bortman 1999 + WHO EWARS Technical Guide 2012 dùng `mean + 2σ` per (country, week) — tương ứng ~2.5% upper tail của Gaussian, là 'rare event' đáng cảnh báo. **High không phải class đều, mà là class đáng quan tâm** — đó là spirit của early warning system. Em cite được literature, không arbitrary threshold."

## Q6: F1(High) dengue = 0.30 thấp — em xử lý sao?
> "Em **honest với limitation**. Lý do: Brazil 2016 outbreak inflate baseline 2017-2018 → ít cases vượt baseline → ít rows label High → model under-train. Đây là **realistic limitation của Endemic Channel method**, walk-forward CV expose ra — đó là **giá trị** của CV scheme. Hướng fix: **(1)** Quantile-based threshold thay 2σ Gaussian. **(2)** Focal loss để bù class minority. **(3)** Country-specific threshold thay vì uniform. Em document đầy đủ trong báo cáo Chapter 4."

## Q7: Coverage 163/250 nước = 92% — vì sao mất 87 nước?
> "Em mất do 2 lý do: **(1) KD-tree không match 53 đảo nhỏ** Pacific như Tuvalu, Nauru — centroid quá xa lưới ERA5 0.25°. **(2) OpenDengue/FluNet không có data** cho 34 nước nhỏ (Vatican, San Marino, Andorra...). 163 nước em cover đã đại diện **92% dân số thế giới** — đủ scope đồ án. Hướng mở rộng: dùng nearest-neighbor fallback cho đảo nhỏ."

## Q8: Em có test trên năm 2022 không (post-COVID)?
> "Em **chưa chạy** validation độc lập 2022 — đây là pending task tuần 5. Em chọn loại 2020-2021 khỏi training (NPI làm flu giảm 99% artificial), 2022 là năm post-COVID lý tưởng để test generalization. Em sẽ chạy validation 2022 trong demo lần 2."

## Q9: Em có dùng deep learning không?
> "Em **chọn không**. Lý do: **(1)** Data size không đủ — 55K rows flu, 6K rows dengue — LSTM/Transformer cần ≥ 100K rows mới beat tree-based. **(2)** Interpretability — feature importance LightGBM cho ra rationale rõ ràng, deep learning blackbox. **(3)** Inference speed — LightGBM 0.08ms/row, LSTM ~10ms — quan trọng cho realtime dashboard 200 nước. Tree-based là choice đúng cho problem này. Em document trong báo cáo Chapter 2 (literature review)."

## Q10: Deploy production em có dự định triển khai thật không?
> "Hiện tại em đã có: **(1)** Model artifacts `.pkl` + metadata. **(2)** FastAPI backend scaffold. **(3)** React dashboard port từ EpiWatch dark-theme. Pending tuần 5: Docker Compose, PostgreSQL persistence, OpenWeatherMap realtime integration. Sau bảo vệ em sẽ tiếp tục CI/CD GitHub Actions + MLOps retrain pipeline hàng tuần — em đã có roadmap rõ ràng."

## Q11: Em đã làm trên cá nhân hay nhóm?
> "Em làm **cá nhân**. GVHD hướng dẫn về định hướng, em chịu trách nhiệm toàn bộ implementation: data pipeline, feature engineering, model training, dashboard frontend, backend scaffold. Code commit ở repo Git, em sẵn sàng show commit history."

## Q12: Em mất bao lâu để hoàn thành?
> "**6 tháng**, chia 4 giai đoạn: **(1)** Tháng 1-2: nghiên cứu literature, thiết kế architecture. **(2)** Tháng 3-4: build data pipeline (Session 0-5). **(3)** Tháng 5: ML training + evaluation (Session 6-9), đi qua 5 version v1 → v5. **(4)** Tháng 5-6: dashboard + báo cáo. Em làm ~25-30 giờ/tuần, tổng ~750 giờ."

---

# CHECKLIST TRƯỚC KHI THUYẾT TRÌNH

**1 tuần trước:**
- [ ] Luyện slide 5 lần, đo thời gian (target 20-22 phút)
- [ ] Quay video tự thuyết trình → xem lại tìm chỗ ấp úng
- [ ] Chuẩn bị backup laptop + USB

**3 ngày trước:**
- [ ] Test demo dashboard chạy được offline (không dựa internet)
- [ ] Print bản cứng slide để fallback nếu projector hỏng
- [ ] Chuẩn bị 2 outfit (1 chính + 1 backup)

**1 ngày trước:**
- [ ] Đi sớm khảo sát phòng — vị trí ổ điện, projector, mic
- [ ] Test laptop với HDMI/VGA của phòng
- [ ] Ngủ đủ 7 giờ — KHÔNG thức học bài đêm trước

**Buổi sáng hôm thuyết trình:**
- [ ] Ăn sáng nhẹ, uống nước
- [ ] Đến trước 30 phút setup
- [ ] Hít thở sâu 3 lần trước khi vào — **bình tĩnh, em đã chuẩn bị 6 tháng cho ngày này**

---

# CÂU "ĐINH" CẦN NHỚ THUỘC LÒNG

Đây là 5 câu sẽ gây ấn tượng nhất với hội đồng, **học thuộc:**

1. > "Em làm CẢ HAI nhánh Regression và Classification, so sánh khoa học — đây là đóng góp của đồ án, không chỉ chọn 1 cho dễ."

2. > "Em không default trust XGBoost. Em so sánh 5 models — Random Forest beat XGBoost cho dengue vì bagging robust hơn với data nhỏ. Đây là phát hiện đáng kể."

3. > "Walk-forward CV 6 folds — train luôn trước val, không leakage. Đây là chuẩn time-series, không phải K-fold random."

4. > "AR features dominate 90% — không phải bug. Đó là validation epidemiological: dịch bệnh persistent, weather là conditioning factor không phải primary predictor. Khớp literature Lowe 2014 và Shaman 2009."

5. > "Em document đầy đủ limitation: dengue F1(High) thấp do Brazil 2016 inflate baseline, coverage 92% do KD-tree. Honest về weakness là phẩm chất engineer, không phải nói dối model perfect."

---

# LỜI KHUYÊN CUỐI

**Khi run-through lần cuối, tự hỏi:**
- Nếu thầy hỏi "tại sao chọn X" cho **bất kỳ X nào** trong slide, em trả lời được không?
- Em có thể giải thích KD-tree, log1p, CCF, walk-forward CV, endemic channel cho **một người không biết ML** không?
- Em có **con số cụ thể** cho mọi claim không? (ví dụ: không nói "R² cao", mà nói "R² 0.9019 mean qua 6 folds")

**Nếu trả lời "có" cho cả 3 → em sẵn sàng. Chúc bảo vệ thành công!**

---

# PHẦN 8 — BỔ SUNG v6 + Phase A (chốt 21–23/05/2026)

> File này nguyên bản viết cho v5 (17/05). Sau đó dự án mở rộng thêm **multi-horizon v6** và **realtime/nowcast Phase A**. Phần này thêm vào script v5 hiện tại để có bài thuyết trình đầy đủ.
> Nếu thuyết trình thời lượng 30 phút, **chèn các slide này sau Slide 13 (Feature Importance)**.

## Slide 13a — Multi-horizon v6 (chốt 21/05/2026)

> "Sau khi v5 hoàn thành phase ML cơ bản, em mở rộng thành **multi-horizon h=1, 2, 3, 4 tuần**."
>
> "Lý do: đề tài yêu cầu 'dự báo dịch bệnh có thể diễn ra theo giai đoạn/mùa/tháng' — chỉ có h=1 không đủ. Em cần forecast trajectory 4 tuần để công cụ y tế kịp chuẩn bị."
>
> "Em chọn cách **train 4 model riêng dùng feature actual** thay vì recursive — vì recursive có error propagation, sai h=1 thì h=2,3,4 sai cấp số."

| h | Flu R² (LGBM) | Dengue R² (RF) | Lowe 2014 |
|---|---|---|---|
| 1 | **0.8661** | **0.9292** | 0.78-0.85 |
| 2 | 0.8293 | 0.9191 | 0.70-0.78 |
| 3 | 0.7928 | 0.9086 | 0.62-0.72 |
| 4 | 0.7573 | 0.8981 | **0.55-0.68** |

> [NHẤN MẠNH] "**8 trên 8 horizon vượt benchmark Lowe et al 2014 Lancet ID**. Đặc biệt h=4: flu 0.757, dengue 0.898 — gấp 1.3× Lowe baseline."
>
> "Phát hiện bất ngờ: **dengue degradation gentler hơn flu** — dengue mất 0.010 R²/horizon, flu mất 0.036/horizon. Lý do: lag dengue dài 6-14 tuần phủ xa hơn flu 1-7 tuần, plus pattern endemic năm cả 12 tháng ở vùng nhiệt đới ít volatile hơn flu mùa đông."

## Slide 13b — Phase A: Realtime + Nowcast (chốt 23/05/2026)

> "Phần em đặc biệt tự hào: **đưa model từ notebook ra production thật chạy hàng tuần**."
>
> "Em build **4 sync scripts idempotent**:
> 1. `sync_flunet.py` — pull WHO FluNet weekly (Mon 10:00 ICT)
> 2. `sync_weather.py` — pull Open-Meteo Archive daily (6:00 ICT)
> 3. `feature_builder.py` — rebuild lag features (Mon 11:00 ICT)
> 4. `batch_predict.py` — predict latest week (Mon 11:30 ICT)
>
> Tự động qua **APScheduler** tích hợp trong FastAPI process — không cần Linux cron external."

| Disease | Latest realtime | Countries | Source |
|---|---|---|---|
| Flu | **2026-W21** | **163** | WHO FluNet API |
| Dengue | **2023-W36** | **56** | OpenDengue v1.3 batch |

> "Top 5 flu W21/2026: China 1,081 cases High, Canada 572 High, Brazil 203 High, Iran 38 Low, India 28 High."
>
> "Top 5 dengue W36/2023: Brazil 8,820 cases Medium, Mexico 6,633 Medium, Peru 3,455 Medium, Vietnam 3,250 High, Nicaragua 3,030 High."

[CHUYỂN SLIDE — demo dashboard realtime]

> "Em mở localhost — đây là dashboard chạy data realtime, không phải mock."

## Slide 13c — DataCoverage Honesty

> "Em xin nhấn mạnh điểm này: **không bao giờ fake data, luôn báo trung thực cho user và GVHD.**"
>
> "Mỗi forecast response có field `data_coverage` với 3 trạng thái:
> 1. **in_training_period=true**: Năm này có trong training 2010-2019, đáng tin.
> 2. **is_nowcast=true** (dengue 2021-2023): Có ground truth từ OpenDengue, batch không realtime → warning vàng.
> 3. **Cả 2 false** (flu 2026): Extrapolation thật → warning đỏ 'Năm X nằm ngoài training window, không có ground truth.'"
>
> [NHẤN MẠNH] "**Transparency với GVHD quan trọng hơn metric đẹp**. Em không che dấu limitation. Trên dashboard có badge realtime/nowcast/historical để user phân biệt."

## Slide 13d — Pipeline architecture tổng thể

> "Bây giờ em xin tóm tắt kiến trúc 4 layer của hệ thống production:"

```
┌─────────────────────────────────────────────────────────────────┐
│ Layer 1 — 4 sync scripts (idempotent UPSERT)                    │
└─────────────────────────────────────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ Layer 2 — PostgreSQL: 16 tables, 31 partitions                  │
│   disease_cases (87K) · weather_obs (24K) ·                     │
│   feature_snapshots (75K) · predictions (75K)                   │
└─────────────────────────────────────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ Layer 3 — FastAPI: 15+ endpoints, 10 models load vào memory     │
│   APScheduler 4 cron jobs tự động                               │
└─────────────────────────────────────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ Layer 4 — React Dashboard: 3 pages (Home, Detail, Analytics)    │
└─────────────────────────────────────────────────────────────────┘
```

> "Mỗi layer chỉ làm 1 việc, không phụ thuộc state của layer cao hơn → thay 1 layer cũng không vỡ tầng khác. Đây là **separation of concerns** chuẩn production."

---

## Bổ sung Q&A cho v6 + Phase A

### Q13: Tại sao train 4 model multi-horizon thay vì 1 model recursive?

> "Recursive có error propagation: predict h=1 rồi feed làm input cho h=2, error compound. Em chọn train 4 model riêng dùng feature **actual** (không predict) → mỗi h tối ưu riêng, error không cộng dồn. Trade-off: 4× compute training nhưng deploy chỉ load 4 .pkl vào memory, predict O(1)."

### Q14: Tại sao dengue chỉ nowcast đến 2023-W36, không lên 2026?

> "OpenDengue v1.3 chỉ release đến **2023-W36**. Từ 2024 chỉ có 23 đảo Pacific (sparse), 2025 zero weekly rows. WHO/PAHO không có dataset dengue realtime global standardized. Đây là **limitation nguồn dữ liệu**, không phải model. Em document làm 'nowcast' (có ground truth) thay vì 'extrapolation' (không có)."

### Q15: APScheduler trong process FastAPI có risk gì không?

> "Có 2 risk em đã cân nhắc: **(1) Job crash kéo FastAPI sập** — em mitigate bằng try/except trong subprocess, log Loguru. **(2) Long-running job block requests** — em dùng AsyncIOScheduler + subprocess timeout 30 phút, không block event loop. Cho production scale lớn em sẽ tách Celery + Redis broker — đây là plan D-3."

### Q16: Production có deploy chưa?

> "Em build sẵn Dockerfile + docker-compose.yml (Postgres + FastAPI + frontend) — chạy localhost smooth. Chưa deploy lên cloud public vì lý do bảo mật + cost (cô đã confirm không cần thiết cho KLTN). Sau bảo vệ em sẽ deploy thử Render hoặc Railway free tier."

---

## Câu "đinh" bổ sung v6 + Phase A

6. > "Em không chỉ làm notebook — em build production system thật. **163 nước flu realtime tới W21/2026, 56 nước dengue nowcast tới W36/2023**, tự động sync hàng tuần qua APScheduler 4 cron jobs."

7. > "**8/8 horizon vượt benchmark Lowe 2014 Lancet ID** — paper reference cho dengue forecasting. Dengue degradation gentler 3.6× lần flu vì lag dài hơn và pattern endemic — đây là **insight epidemiological em phân tích được**."

8. > "**DataCoverage warning** trên mỗi response — flu 2026 extrapolation, dengue 2021-2023 nowcast, training 2010-2019. Transparency với user quan trọng hơn metric đẹp."
