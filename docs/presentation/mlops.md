# Vận hành mô hình trong phạm vi KLTN

Tài liệu này trình bày phần vận hành mô hình một cách trung thực: hệ thống có các thành phần cơ bản để đưa mô hình từ notebook vào API và bảng điều khiển, nhưng chưa phải hệ thống vận hành mô hình hoàn chỉnh như trong doanh nghiệp.

## 1. Những gì hệ thống đã làm

**Tách huấn luyện và dự báo**

Notebook `KLTN_EpiWeather_ML_v5.ipynb` và `KLTN_EpiWeather_ML_v6.ipynb` chịu trách nhiệm phân tích dữ liệu, tạo đặc trưng, huấn luyện, đánh giá và xuất tệp mô hình. API không huấn luyện lại mô hình khi giao diện gọi.

**Lưu tệp mô hình**

Thư mục `ml_models/` chứa các file `.pkl`, danh sách đặc trưng JSON và chỉ số đánh giá JSON. Tên tệp thể hiện bệnh, nhiệm vụ và phiên bản:

- `lgbm_flu_regressor_v1.pkl`
- `rf_dengue_regressor_v1.pkl`
- `xgb_flu_classifier_v1.pkl`
- `xgb_dengue_classifier_v1.pkl`
- `lgbm_flu_regressor_h1_v1.pkl` đến `lgbm_flu_regressor_h4_v1.pkl`
- `rf_dengue_regressor_h1_v1.pkl` đến `rf_dengue_regressor_h4_v1.pkl`

**API nạp mô hình để dự báo**

`backend/app/services/ml_engine.py` nạp mô hình dự báo số ca, mô hình phân mức rủi ro và các mô hình dự báo 4 tuần. Khi dự đoán, API sắp xếp dữ liệu đầu vào theo đúng danh sách đặc trưng đã xuất ra, gọi mô hình, rồi trả về `predicted_log`, `predicted_cases`, `risk_level` và `risk_probability`.

**Lưu thông tin mô hình**

Schema có `model_versions` và `model_evaluations` để lưu thuật toán, giai đoạn huấn luyện, giai đoạn đánh giá, đường dẫn tệp mô hình, chỉ số và trạng thái đang dùng. Đây là nền tảng để truy vết mô hình sinh ra dự báo.

**Dự báo hàng loạt**

`scripts/batch_predict.py` đọc `feature_snapshots`, gọi bộ dự báo ML và ghi/cập nhật vào `predictions`. Cách này giúp bảng điều khiển đọc kết quả nhanh và ổn định, thay vì chạy mô hình lại cho mỗi request từ giao diện.

**Bộ đặc trưng đã tính sẵn**

`feature_snapshots` lưu bộ đặc trưng theo bệnh/quốc gia/năm/tuần/phiên bản. Đây là điểm nối giữa quy trình dữ liệu và phần dự báo trong API. Khi cần kiểm tra một dự báo, có thể xem bộ đặc trưng đã dùng.

**Lịch chạy và trang quản trị mức bản mẫu**

Repo có `scripts/run_daily_pipeline.py`, `scripts/setup_windows_task.ps1`, service lịch chạy và endpoint quản trị. Mục tiêu là mô phỏng quy trình định kỳ: đồng bộ dữ liệu, tạo đặc trưng, dự báo hàng loạt, ghi log.

**Ghi log và kiểm tra chất lượng dữ liệu**

Schema có `pipeline_runs`, `data_quality_checks` và `api_request_logs`. Đây là bước đầu để theo dõi quy trình, số dòng xử lý, lỗi và request.

## 2. Luồng chạy kỹ thuật

Phần này dùng khi giảng viên hỏi: "Cụ thể hệ thống chạy như thế nào, chạy khi nào, lưu vào đâu?"

### 2.1 Khi huấn luyện mô hình

Huấn luyện không chạy trong API. Huấn luyện chạy trong notebook:

```text
KLTN_EpiWeather_ML_v5.ipynb / KLTN_EpiWeather_ML_v6.ipynb
        |
        v
Xuất tệp mô hình, danh sách đặc trưng, chỉ số đánh giá
        |
        v
ml_models/
```

Kết quả được lưu ở thư mục `ml_models/`:

- File mô hình: `.pkl`
- Danh sách đặc trưng: `_features.json`
- Chỉ số đánh giá: `_metrics.json`

Ví dụ:

```text
ml_models/lgbm_flu_regressor_h1_v1.pkl
ml_models/lgbm_flu_regressor_h1_v1_features.json
ml_models/lgbm_flu_regressor_h1_v1_metrics.json
```

Thông tin phiên bản mô hình có thể lưu trong các bảng:

- `model_versions`: mô hình nào, thuật toán nào, huấn luyện năm nào, file nằm ở đâu.
- `model_evaluations`: chỉ số đánh giá của mô hình.

### 2.2 Khi API khởi động

Khi API chạy, `backend/app/services/ml_engine.py` nạp các file trong `ml_models/` vào bộ nhớ:

```text
FastAPI khởi động
        |
        v
ml_engine.load_models(ml_models/)
        |
        v
Nạp mô hình dự báo số ca, mô hình phân mức rủi ro, mô hình dự báo nhiều tuần
```

Sau bước này, API không cần mở notebook. API chỉ cần có sẵn file `.pkl` và danh sách đặc trưng đi kèm.

### 2.3 Khi có dữ liệu mới

Luồng dữ liệu vận hành trong repo gồm 4 bước chính:

```text
1. sync_flunet.py
   WHO FluNet -> disease_cases

2. sync_weather.py
   Open-Meteo -> weather_observations

3. feature_builder.py
   disease_cases + weather_observations -> feature_snapshots

4. batch_predict.py
   feature_snapshots + ml_models -> predictions
```

Ý nghĩa từng bảng:

| Bảng | Lưu gì |
|---|---|
| `disease_cases` | Số ca bệnh thực tế theo bệnh, quốc gia, năm, tuần |
| `weather_observations` | Dữ liệu thời tiết theo quốc gia, năm, tuần |
| `feature_snapshots` | Bộ đặc trưng đã tính sẵn để đưa vào mô hình |
| `predictions` | Kết quả dự báo: số ca, mức rủi ro, xác suất rủi ro cao |
| `pipeline_runs` | Lịch sử mỗi lần chạy quy trình: chạy tay hay chạy lịch, thành công/thất bại, số dòng xử lý |

### 2.4 Chạy bằng lệnh tay

Khi demo hoặc cần chạy lại thủ công, có thể chạy từng bước:

```powershell
python scripts/sync_flunet.py --from-year 2024
python scripts/sync_weather.py --weeks-back 12
python scripts/feature_builder.py --disease flu --from-year 2026
python scripts/feature_builder.py --disease dengue --from-year 2020 --to-year 2023
python scripts/batch_predict.py
```

Một số chế độ hữu ích:

```powershell
python scripts/batch_predict.py --disease flu
python scripts/batch_predict.py --year 2026 --week 21
python scripts/batch_predict.py --year 2023 --from-week 24 --to-week 36
python scripts/batch_predict.py --all-snapshots
python scripts/batch_predict.py --dry-run
```

Giải thích:

- `--dry-run`: chạy thử, in kết quả nhưng không ghi vào cơ sở dữ liệu.
- `--year --week`: dự báo lại một tuần cụ thể.
- `--from-week --to-week`: dự báo lại một khoảng tuần trong cùng năm.
- `--all-snapshots`: chạy lại toàn bộ các tuần đã có bộ đặc trưng, dùng khi cần lấp dữ liệu cũ hoặc phục vụ BACKTEST.

### 2.5 Chạy theo lịch

Repo có hai cách mô phỏng chạy định kỳ.

Cách 1 là chạy qua script tổng:

```powershell
python scripts/run_daily_pipeline.py
```

Script này chạy tuần tự:

1. `sync_flunet.py --from-year 2024`
2. `sync_weather.py --weeks-back 12`
3. `feature_builder.py --disease flu --from-year <năm hiện tại>`
4. `feature_builder.py --disease dengue --from-year <năm hiện tại>`
5. `batch_predict.py`

Theo ghi chú trong code, script này dự kiến chạy hằng ngày lúc 00:00 ICT bằng Windows Task Scheduler. Mỗi job con tự ghi log vào `pipeline_runs`.

Cách 2 là chạy qua lịch chạy trong API:

| Công việc | Khi nào | Làm gì |
|---|---|---|
| `sync_flunet` | Thứ Hai 10:00 ICT | Kéo dữ liệu cúm mới từ WHO FluNet |
| `sync_weather` | Hằng ngày 06:00 ICT | Kéo thời tiết 12 tuần gần nhất từ Open-Meteo |
| `build_features` | Thứ Hai 11:00 ICT | Tạo lại đặc trưng cho flu và dengue năm hiện tại |
| `batch_predict` | Thứ Hai 11:30 ICT | Dự báo tuần mới nhất và ghi vào `predictions` |

Có thể xem trạng thái lịch chạy qua API:

```text
GET /api/v1/admin/scheduler/status
```

Có thể kích hoạt một job bằng tay qua API:

```text
POST /api/v1/admin/sync/sync_flunet
POST /api/v1/admin/sync/sync_weather
POST /api/v1/admin/sync/build_features
POST /api/v1/admin/sync/build_features_dengue_nowcast
POST /api/v1/admin/sync/batch_predict
```

### 2.6 Khi người dùng mở giao diện

Giao diện không trực tiếp chạy mô hình. Giao diện gọi API, API đọc kết quả đã có trong cơ sở dữ liệu:

```text
Giao diện
  -> API risk / predictions / forecast
  -> Cơ sở dữ liệu predictions + feature_snapshots
  -> Trả JSON về giao diện
```

Vì vậy bản đồ và biểu đồ phản hồi nhanh hơn, kết quả dễ kiểm tra lại hơn, và cùng một tuần/bệnh/quốc gia không bị thay đổi ngẫu nhiên giữa các lần mở trang.

### 2.7 Tóm tắt một câu để nói khi bảo vệ

> Mô hình được huấn luyện trong notebook và xuất ra file `.pkl`. API nạp các file đó khi khởi động. Khi có dữ liệu mới, các script đồng bộ dữ liệu bệnh và thời tiết, tạo bộ đặc trưng, chạy dự báo hàng loạt, rồi lưu kết quả vào bảng `predictions`. Giao diện chỉ đọc kết quả qua API, không chạy notebook và không huấn luyện lại mô hình khi người dùng mở trang.

## 3. Những gì không nên phóng đại

Không nên nói hệ thống đã là phần vận hành mô hình hoàn chỉnh. Trong phạm vi KLTN, hệ thống mới có các thành phần cần thiết để chứng minh việc tích hợp mô hình học máy từ đầu đến cuối.

Chưa nên cam kết:

- Kho quản lý phiên bản mô hình đầy đủ như MLflow.
- Tự động huấn luyện lại hoàn toàn.
- Theo dõi dữ liệu bị lệch theo thời gian một cách hoàn chỉnh.
- Triển khai tự động cho môi trường vận hành thật.
- Thử nghiệm song song nhiều mô hình kiểu A/B testing.
- SLA, tính sẵn sàng cao hoặc kiểm định y tế cấp sản phẩm thật.
- Khoảng tin cậy được hiệu chỉnh tốt cho từng bệnh/quốc gia.

## 4. Vì sao cần dự báo hàng loạt và cơ sở dữ liệu

Dự báo hàng loạt giúp tách thời điểm chạy mô hình khỏi thời điểm người dùng mở bảng điều khiển. Điều này có ba lợi ích:

- Bảng điều khiển nhanh hơn vì chỉ truy vấn cơ sở dữ liệu.
- Kết quả có thể kiểm tra lại vì đã gắn phiên bản mô hình và bộ đặc trưng.
- BACKTEST dễ hơn vì dự báo theo tuần quá khứ được lưu lại, không phụ thuộc trạng thái mô hình đang nạp tại thời điểm xem.

Trong demo vận hành, quy trình có thể chạy theo lịch định kỳ. Với mỗi lần chạy, hệ thống tạo đặc trưng cho tuần mới nhất đủ dữ liệu, sinh dự báo và cập nhật bảng điều khiển.

## 5. Quy trình thay phiên bản mô hình

Quy trình phù hợp để trình bày:

1. Huấn luyện hoặc huấn luyện lại mô hình trong notebook.
2. Đánh giá bằng kiểm chứng theo thời gian và năm giữ lại/BACKTEST.
3. Xuất `.pkl`, danh sách đặc trưng và file chỉ số JSON.
4. Ghi thông tin vào `model_versions` và `model_evaluations`.
5. Cập nhật API để nạp tệp mô hình mới.
6. Chạy dự báo hàng loạt cho giai đoạn cần hiển thị.
7. Kiểm tra bảng điều khiển và API.

## 6. Hướng phát triển tiếp

Các hướng nâng cấp sau KLTN:

- Kho quản lý phiên bản mô hình đầy đủ, có trạng thái thử nghiệm/chính thức.
- Theo dõi dữ liệu bị lệch theo thời gian theo bệnh/quốc gia/đặc trưng.
- Tự động huấn luyện lại khi có số ca thực tế mới.
- So sánh dự báo với số ca thực tế sau khi dữ liệu mới cập nhật.
- Khoảng dự báo tốt hơn.
- Triển khai tự động cho API, giao diện, migration và job chạy nền.
- Màn hình theo dõi lịch sử chạy quy trình và chất lượng dữ liệu.
- Chuẩn hóa nguồn dữ liệu dengue cập nhật hơn nếu có API chính thức.
