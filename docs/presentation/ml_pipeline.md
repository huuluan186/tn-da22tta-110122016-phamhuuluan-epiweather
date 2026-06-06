# Tóm tắt quy trình ML và dữ liệu

Tài liệu này là bản tóm tắt để đối chiếu khi viết báo cáo và trả lời câu hỏi. Phần trình bày chi tiết từng bước ML vẫn nằm ở các file session trong thư mục này:

| File | Vai trò khi trình bày |
|---|---|
| [session_1_load.md](session_1_load.md) | Đọc dữ liệu bệnh, kiểm tra nguồn và độ phủ |
| [session_2_era5.md](session_2_era5.md) | Xử lý dữ liệu thời tiết ERA5 |
| [session_3_merge.md](session_3_merge.md) | Ghép dữ liệu bệnh và thời tiết |
| [session_4_eda.md](session_4_eda.md) | Phân tích dữ liệu, mùa vụ, độ lệch, thiếu dữ liệu |
| [session_5_features.md](session_5_features.md) | Tạo đặc trưng cho mô hình |
| [session_6_training.md](session_6_training.md) | Huấn luyện và so sánh mô hình |
| [session_7_validation.md](session_7_validation.md) | Kiểm chứng mô hình bằng năm giữ lại |
| [session_8_multi_horizon.md](session_8_multi_horizon.md) | Dự báo 4 tuần tới |

Nội dung tóm tắt dưới đây dựa trên các file đã rà soát trong repo:

- `KLTN_EpiWeather_ML_v6.ipynb`: notebook mới hơn, mở rộng dự báo nhiều mốc h=1..4.
- `KLTN_EpiWeather_ML_v5.ipynb`: notebook nền cho dự báo h=1, kiểm chứng và xuất tệp mô hình.
- `docs/presentation/session_8_multi_horizon.md`: tổng kết kết quả multi-horizon v6.
- `backend/app/services/ml_engine.py`, `scripts/feature_builder.py`, `scripts/batch_predict.py`: phần tích hợp tệp mô hình vào API.
- `ml_models/`: mô hình `.pkl`, danh sách đặc trưng và chỉ số đánh giá đã xuất ra.

Lưu ý: trong notebook v6, phần tiêu đề markdown vẫn có chỗ ghi "v5", nhưng file `KLTN_EpiWeather_ML_v6.ipynb` là bản mới hơn và có Session 8 multi-horizon.

## 1. Tổng quan bài toán

Đây không phải là website nghiệp vụ thông thường như thương mại điện tử hay quản lý bán hàng. Bài toán của KLTN là xây dựng một hệ thống hỗ trợ phân tích và cảnh báo nguy cơ dịch bệnh truyền nhiễm theo tuần, cấp quốc gia.

Mục tiêu của đồ án là một bản mẫu hoàn chỉnh từ dữ liệu đến giao diện: có quy trình dữ liệu, mô hình học máy, API, cơ sở dữ liệu và bảng điều khiển. Hệ thống không cam kết là một nền tảng y tế vận hành thật. Kết quả dự báo cần được hiểu như tín hiệu hỗ trợ phân tích, không phải kết luận y tế tuyệt đối.

Hệ thống trả lời các câu hỏi chính:

- Quốc gia nào đang có nguy cơ cao?
- Tuần nào nguy cơ tăng?
- Dự đoán số ca là bao nhiêu?
- Mức rủi ro là Low, Medium hay High?
- Có thể chọn tuần quá khứ để kiểm thử lại dự báo không?

## 2. Phân tách giai đoạn dữ liệu

Ba khái niệm cần dùng nhất quán khi trình bày:

**Giai đoạn huấn luyện:** giai đoạn dùng để dạy mô hình học từ dữ liệu cũ. Trong notebook, giai đoạn chính được cấu hình là 2010-2019 đối với flu. Với dengue, notebook v6 ghi rõ dữ liệu 2010-2014 có độ phủ thấp và giai đoạn huấn luyện thực tế được thu hẹp về 2015-2019 trong các bước sau.

**Giai đoạn kiểm thử quá khứ / BACKTEST:** giai đoạn sau huấn luyện nhưng đã có số ca thực tế, dùng để kiểm chứng mô hình. Notebook dùng 2022 làm năm giữ lại để kiểm tra sau COVID. Bảng điều khiển cũng có thể cho phép chọn các tuần quá khứ đã có đặc trưng/dự báo để mô phỏng câu hỏi: "nếu đứng tại tuần đó thì mô hình dự báo gì?"

**Giai đoạn dự báo mới nhất trong hệ thống:** giai đoạn mới nhất mà hệ thống có đủ đặc trưng để sinh dự báo và hiển thị trên bảng điều khiển. Giai đoạn này không nhất thiết là ngày hiện tại ngoài đời. Với từng bệnh, tuần mới nhất có thể khác nhau do nguồn dữ liệu khác nhau. Ví dụ trong phạm vi dữ liệu hiện có, flu có thể tới 2026, còn dengue tới 2023-W36. Vì vậy không nên gọi tất cả là dữ liệu thời gian thực.

Thuật ngữ dùng trong UI và báo cáo:

- **MỚI NHẤT:** tuần mới nhất hệ thống có dự báo.
- **BACKTEST:** tuần/năm quá khứ được chọn để mô phỏng hoặc kiểm chứng dự báo.
- Tránh dùng "realtime" nếu dữ liệu bệnh không thật sự được cập nhật theo thời gian thực ngoài đời.

## 3. Quy trình thực tế trong notebook

### 3.1 Setup và cấu hình

Notebook cấu hình các mốc chính:

- `TRAIN_START = 2010`
- `TRAIN_END = 2019`
- `COVID_YEARS = [2020, 2021]`
- `VAL_YEAR = 2022`
- `TARGET_FLU = influenza_total`
- `TARGET_DENGUE = dengue_log`
- Lag flu chính: `LAG_FLU = [1, 2, 3]`
- Lag dengue chính: `LAG_DENGUE = [6, 8, 10, 12, 14]`

Các mô hình được so sánh trong notebook gồm Naive baseline, Prophet, XGBoost, LightGBM và Random Forest. Phân lớp rủi ro dùng XGBClassifier. Các tên tiếng Anh này là tên mô hình/thư viện nên giữ nguyên khi trình bày kỹ thuật.

### 3.2 Nguồn dữ liệu

**Flu:** notebook đọc WHO FluNet từ `VIW_FNT.csv` và thông tin mô tả từ `VIW_FLU_METADATA.csv`. Biến `influenza_total` được tạo bằng `INF_A.fillna(0) + INF_B.fillna(0)`. Dữ liệu được lọc theo giai đoạn 2010-2022 để phục vụ huấn luyện và kiểm chứng.

Theo ghi chú trong notebook, FluNet có khoảng 183.026 dòng thô, sau khi lọc còn 113.399 dòng và 189 quốc gia. Notebook cũng kiểm tra tỷ lệ dữ liệu thiếu, số quốc gia theo năm và ảnh hưởng COVID. Ví dụ 2019 có 788.175 ca làm mức nền, 2020 giảm còn 481.271 và 2021 còn 114.863; notebook quyết định loại 2020-2021 khỏi huấn luyện vì giai đoạn này bị nhiễu bởi can thiệp COVID và thay đổi hành vi giám sát.

**Dengue:** notebook đọc OpenDengue v1.3 từ `National_extract_V1_3.csv`, lọc các dòng weekly. Ghi chú notebook cho biết dữ liệu weekly có khoảng 18.125 dòng và 82 quốc gia. Coverage thay đổi mạnh theo năm: 2010-2014 thấp hơn, 2015-2016 tăng, 2017-2022 phủ rộng hơn. Notebook ghi nhận Brazil chiếm tỷ trọng ca rất lớn trong nhóm quốc gia đầu, nên cần biến đổi log.

Trong notebook, dengue được xử lý thận trọng hơn flu: bỏ giai đoạn độ phủ thấp 2010-2014 trong các bước huấn luyện sau, và xem 2021-2023-W36 là giai đoạn có dữ liệu hiện có để dự báo/kiểm thử trong phạm vi bộ dữ liệu, không phải API thời gian thực.

**ECDC:** notebook có đọc dữ liệu sentinel/ILI từ ECDC cho 2021-2026, nhưng vai trò chính là kiểm chứng/bảng điều khiển, không phải nguồn huấn luyện chính cho mô hình flu toàn cầu.

**Weather ERA5:** notebook dùng ERA5/ECMWF `reanalysis-era5-single-levels-monthly-means`. Ghi chú notebook mô tả 17 biến khí hậu, giai đoạn 2010-2019, raw khoảng 6.2 GB. Quy trình xử lý gồm ánh xạ grid khí hậu về quốc gia bằng centroid/Natural Earth/KD-tree, tổng hợp theo quốc gia-tháng, rồi broadcast sang tuần. Các biến dẫn xuất gồm `humidity_pct`, `wind_ms`, `temp_range_c`. Output chính là `era5_weekly_2010_2019_final.csv`.

### 3.3 EDA và hiểu dữ liệu

Notebook thực hiện các bước EDA có căn cứ:

- Kiểm tra shape, missing rate và coverage theo năm/quốc gia.
- Kiểm tra phân bố số ca và nhận thấy dữ liệu ca bệnh lệch mạnh, vì vậy bài toán dự báo số ca dùng dạng log.
- So sánh biến động trước, trong và sau COVID đối với flu.
- Kiểm tra coverage dengue theo năm và nhận diện sự mất cân bằng giữa các quốc gia.
- Phân tích mùa vụ theo tuần/năm và khác biệt giữa bệnh/quốc gia.
- Phân tích CCF để chọn lag thời tiết phù hợp hơn cho từng bệnh.

Các điểm cần trình bày trung thực:

- Số ca bệnh thường skew, nhiều tuần bằng 0 hoặc thấp, nhưng một số đỉnh dịch rất lớn.
- Có gap/missing data theo quốc gia và nguồn dữ liệu.
- Flu và dengue có đặc điểm khác nhau, nên không dùng chung độ trễ đặc trưng và mô hình.
- Quốc gia khác nhau có quy mô báo cáo khác nhau; số ca tuyệt đối không nên diễn giải tách khỏi bối cảnh quốc gia/bệnh.
- Dữ liệu thời tiết là nhóm yếu tố hỗ trợ, không phải nguyên nhân duy nhất.
- Không diễn giải mô hình như quan hệ nhân quả tuyệt đối.

TODO: khi làm slide, bổ sung hình/bảng trực tiếp từ notebook cho phân bố log1p, coverage theo năm, missing rate và seasonal plot. Không tự bịa số nếu chưa trích xuất được từ notebook.

### 3.4 Feature engineering

Bộ đặc trưng thực tế được xuất ra và API đang dùng gồm ba nhóm: đặc trưng từ lịch sử ca bệnh, đặc trưng mùa vụ/thời gian và đặc trưng thời tiết có độ trễ.

Flu dùng 16 đặc trưng:

- `flu_log_lag1`, `flu_log_lag2`, `flu_log_lag3`
- `flu_log_rollmean4`, `flu_log_rollmean8`
- `temp_c_lag3`, `temp_c_lag7`
- `humidity_pct_lag1`, `humidity_pct_lag7`
- `solar_wm2_lag7`
- `dewpoint_c_lag1`
- `iso_week_sin`, `iso_week_cos`, `iso_year`
- `HEMISPHERE_NH`, `HEMISPHERE_SH`

Dengue dùng 15 đặc trưng:

- `deng_log_lag6`, `deng_log_lag8`, `deng_log_lag10`, `deng_log_lag12`, `deng_log_lag14`
- `deng_log_rollmean4`, `deng_log_rollmean8`
- `temp_c_lag11`
- `dewpoint_c_lag8`
- `precip_mm_lag6`
- `humidity_pct_lag1`
- `solar_wm2_lag16`
- `iso_week_sin`, `iso_week_cos`, `iso_year`

Ý nghĩa: mô hình không chỉ nhìn thời tiết hiện tại, mà dùng lịch sử ca bệnh các tuần trước, trung bình trượt, mùa vụ theo tuần ISO và độ trễ thời tiết đã được chọn theo phân tích notebook.

### 3.5 Đầu ra dự báo số ca và phân mức rủi ro

Bài toán dự báo số ca dự đoán log số ca, sau đó API chuyển về số ca bằng `expm1`. Với flu, notebook tạo `influenza_total`; với dengue, notebook dùng `dengue_log`/log target. API hiện trả về:

- `predicted_log`
- `predicted_cases`

Bài toán phân mức rủi ro dự đoán Low/Medium/High bằng XGBClassifier. API hiện nạp `xgb_flu_classifier_v1.pkl` và `xgb_dengue_classifier_v1.pkl`, trả về:

- `risk_level`
- `risk_probability`, được hiểu là xác suất lớp High (`P(High)`) để giao diện dùng như điểm rủi ro liên tục.

Nhãn Low/Medium/High dùng để huấn luyện classifier được tạo bằng Endemic Channel theo từng quốc gia và từng tuần ISO:

- `baseline` = trung bình lịch sử 5 năm gần của cùng quốc gia, cùng tuần ISO.
- `upper` = `baseline + 2σ`.
- Low: `cases < baseline`.
- Medium: `baseline ≤ cases < upper`.
- High: `cases ≥ upper`.

API không tự chia ngưỡng lại khi người dùng mở dashboard; API chỉ nạp mô hình phân lớp đã xuất ra và trả `risk_level` cùng `risk_probability = P(High)`.

### 3.6 Chia dữ liệu huấn luyện, kiểm chứng và BACKTEST

Notebook dùng cách kiểm chứng theo thời gian trên giai đoạn huấn luyện và dùng năm giữ lại 2022 để kiểm tra khả năng áp dụng sau COVID. Giai đoạn 2020-2021 bị loại khỏi huấn luyện chính do nhiễu lớn từ COVID.

Các kết quả chính đã được ghi trong notebook/tài liệu session:

- Flu dự báo số ca h=1: LightGBM, R2 kiểm chứng khoảng 0.9019, R2 năm 2022 khoảng 0.9022 trong output notebook được trích xuất trước đó.
- Dengue dự báo số ca h=1: Random Forest, R2 kiểm chứng khoảng 0.9366, R2 năm 2022 khoảng 0.9136 trong output notebook được trích xuất trước đó.
- Flu phân mức rủi ro: XGBClassifier macro-F1 khoảng 0.4491 trên năm 2022, kiểm chứng khoảng 0.5422.
- Dengue phân mức rủi ro: XGBClassifier macro-F1 khoảng 0.4257 trên năm 2022, kiểm chứng khoảng 0.4749; khả năng bắt lớp High còn thấp.

Lưu ý về độ khớp tài liệu: một số tài liệu thuyết trình cũ trong repo ghi kết quả flu 2022 khoảng 0.80, trong khi output notebook được rà soát có chỗ ghi khoảng 0.9022. Khi đưa vào báo cáo chính thức, nên chụp lại đúng bảng chỉ số từ lần chạy cuối cùng của notebook v6/v5 và dùng một con số thống nhất. Nếu chưa chốt được, ghi TODO thay vì chọn số đẹp hơn.

### 3.7 Multi-horizon v6

Session 8 trong v6 mở rộng từ h=1 sang dự báo 4 tuần tới. Cách làm là huấn luyện mô hình riêng cho từng mốc h=1, h=2, h=3, h=4, không dự báo kiểu lặp lại tuần này sang tuần khác.

Các tệp mô hình dự báo nhiều mốc trong `ml_models/`:

- Flu: `lgbm_flu_regressor_h1_v1.pkl` đến `lgbm_flu_regressor_h4_v1.pkl`
- Dengue: `rf_dengue_regressor_h1_v1.pkl` đến `rf_dengue_regressor_h4_v1.pkl`

Theo `docs/presentation/session_8_multi_horizon.md`, kết quả CV R2:

| Horizon | Flu LightGBM | Dengue Random Forest |
|---|---:|---:|
| h=1 | 0.8661 | 0.9292 |
| h=2 | 0.8293 | 0.9191 |
| h=3 | 0.7928 | 0.9086 |
| h=4 | 0.7573 | 0.8981 |

Điểm cần trình bày: chỉ số h=1 trong bản dự báo nhiều mốc thấp hơn nhẹ so với bản dự báo một mốc v5 vì tập dữ liệu dự báo nhiều mốc phải loại thêm các dòng không đủ dữ liệu tương lai. Đây là đánh đổi hợp lý để bảng điều khiển có dự báo 4 tuần.

## 4. Quy trình tích hợp vào hệ thống

Sau khi notebook huấn luyện và xuất mô hình:

1. Tệp mô hình `.pkl`, danh sách đặc trưng JSON và chỉ số đánh giá JSON được lưu trong `ml_models/`.
2. API khởi động và `ml_engine.py` nạp các mô hình dự báo số ca/phân mức rủi ro tương ứng.
3. `feature_builder.py` tạo `feature_snapshots` theo khóa `(disease, iso3, iso_year, iso_week, feature_version)`.
4. `batch_predict.py` đọc bộ đặc trưng đã tính sẵn, gọi mô hình dự báo số ca để sinh `predicted_cases`, gọi mô hình phân mức rủi ro để sinh `risk_level` và `risk_probability`.
5. Kết quả được ghi/cập nhật vào bảng `predictions`, gắn `disease`, `iso3`, `iso_year`, `iso_week`, `horizon_weeks` và `model_version_id` nếu có.
6. Giao diện chỉ gọi API ổn định để hiển thị bản đồ rủi ro, chi tiết quốc gia, biểu đồ dự báo và thống kê.

Điểm khác biệt giữa notebook và API:

- Notebook là nơi huấn luyện, EDA, tuning và export.
- API không huấn luyện lại mô hình khi giao diện gọi; API nạp tệp mô hình có sẵn để dự báo trực tiếp hoặc dự báo hàng loạt.
- API dự báo nhiều mốc dùng các tệp mô hình h=1..4.
- API bản đồ rủi ro/dự báo đọc dữ liệu đã lưu trong cơ sở dữ liệu để phục vụ bảng điều khiển nhanh và ổn định.

## 5. Vì sao dùng hồi quy rồi phân lớp

Dashboard cần trả lời hai loại câu hỏi khác nhau.

Dự báo số ca trả lời: dự đoán khoảng bao nhiêu ca. Kết quả `predicted_cases` dùng cho biểu đồ dự báo, tổng số ca, xếp hạng quốc gia và phần chi tiết quốc gia.

Phân lớp trả lời: mức rủi ro là gì. Kết quả `risk_level` dùng cho màu bản đồ, danh sách cảnh báo, lọc High/Medium/Low và ưu tiên phân tích.

Hai kết quả này cùng tồn tại vì số ca tuyệt đối và mức rủi ro không luôn tuyến tính đơn giản. Một nước đông dân có số ca tuyệt đối cao nhưng có thể không bất thường so với nền lịch sử của nước đó; ngược lại một nước nhỏ có số ca không quá cao tuyệt đối nhưng tăng mạnh so với pattern thông thường có thể đáng chú ý. Risk level có thể phụ thuộc pattern, mùa vụ, quốc gia, bệnh và phân phối dữ liệu, không chỉ phụ thuộc một ngưỡng ca tuyệt đối.

## 6. Cách diễn giải một dự đoán cụ thể

Template dùng khi demo:

> Với quốc gia X, bệnh Y, tuần W năm Z, hệ thống dự đoán khoảng N ca và mức rủi ro R. Kết quả này được tạo từ các đặc trưng lịch sử dịch bệnh trước đó, đặc trưng mùa vụ theo tuần/năm và nhóm đặc trưng thời tiết tương ứng. Nếu đây là BACKTEST, ta có thể so sánh với số ca thực tế để đánh giá sai số. Nếu đây là MỚI NHẤT, kết quả nên hiểu là tín hiệu cảnh báo hỗ trợ phân tích, không phải kết luận y tế tuyệt đối.

Khi giải thích, cần nhấn mạnh:

- Model không khẳng định chắc chắn đúng.
- Đặc trưng thời tiết không chứng minh quan hệ nhân quả tuyệt đối.
- Dữ liệu có skew, gap/missing và khác biệt nguồn báo cáo theo quốc gia.
- `predicted_cases` dùng để hiểu quy mô dự báo, còn `risk_level` dùng để ưu tiên cảnh báo.
- Nếu rủi ro High nhưng số ca không cao tuyệt đối, có thể do mô hình/ngưỡng đang đánh giá mức tăng tương đối hoặc đặc điểm bất thường theo bệnh/quốc gia/tuần.
