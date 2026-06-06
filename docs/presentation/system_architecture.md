# Kiến trúc hệ thống và bảng điều khiển

Tài liệu này mô tả phần hệ thống của KLTN: cơ sở dữ liệu, API và giao diện bảng điều khiển. Cách trình bày phù hợp với phạm vi bản mẫu học thuật, không phóng đại thành hệ thống y tế vận hành thật.

## 1. Vai trò hệ thống

Đồ án xây dựng một hệ thống dự báo và trực quan hóa nguy cơ dịch bệnh truyền nhiễm theo tuần. Người dùng không thao tác nghiệp vụ mua bán hay quản lý đơn hàng; người dùng phân tích bản đồ rủi ro, chọn bệnh/quốc gia/tuần và đọc tín hiệu dự báo.

Quy trình tổng quát:

```text
Dữ liệu bệnh + dữ liệu thời tiết thô
        |
        v
Notebook ML: phân tích dữ liệu, tạo đặc trưng, huấn luyện, đánh giá, xuất tệp mô hình
        |
        v
API: nạp mô hình, tạo/đọc đặc trưng, dự báo hàng loạt, cung cấp đường dẫn truy cập
        |
        v
Cơ sở dữ liệu: quốc gia, bệnh, đặc trưng, dự báo, đánh giá
        |
        v
Giao diện: bản đồ, bộ lọc, dự báo, chi tiết quốc gia, thống kê
```

Hệ thống mặc định hiển thị tuần mới nhất có dự báo trong cơ sở dữ liệu. Tuần này được gọi là **MỚI NHẤT**, không gọi là dữ liệu thời gian thực nếu dữ liệu bệnh không thật sự cập nhật theo thời gian thực. Khi người dùng chọn một tuần/năm quá khứ, chế độ đó là **BACKTEST**.

## 2. Thiết kế cơ sở dữ liệu

Các bảng chính hiện có trong phần API:

| Bảng | Vai trò |
|---|---|
| `countries` | Thông tin quốc gia: ISO3, tên, vùng WHO, tọa độ, dân số |
| `diseases` | Danh mục bệnh, biến cần dự đoán, cách biến đổi dữ liệu |
| `data_sources` | Thông tin nguồn dữ liệu |
| `weather_variables` | Thông tin các biến thời tiết |
| `disease_cases` | Số ca thực tế theo bệnh, quốc gia, năm, tuần |
| `weather_observations` | Dữ liệu thời tiết theo quốc gia, năm, tuần |
| `feature_snapshots` | Bộ đặc trưng đã chuẩn hóa để dự báo |
| `predictions` | Kết quả dự báo đã lưu |
| `model_versions` | Thông tin phiên bản mô hình |
| `model_evaluations` | Chỉ số đánh giá mô hình |
| `risk_thresholds` | Bảng legacy/phụ trợ từ hướng threshold cũ; dashboard hiện dùng `risk_level` từ classifier |
| `pipeline_runs` | Lịch sử các lần chạy quy trình |
| `data_quality_checks` | Lịch sử kiểm tra chất lượng dữ liệu |
| `api_request_logs` | Lịch sử request API, phục vụ theo dõi hệ thống sau này |

### Vì sao dự báo cần lưu theo bệnh, quốc gia, năm, tuần

Dự báo là một kết quả phụ thuộc vào bệnh, quốc gia và thời điểm. Cùng một quốc gia nhưng flu và dengue có đặc điểm khác nhau, mô hình khác nhau và đặc trưng khác nhau. Cùng một bệnh/quốc gia nhưng tuần khác nhau có mùa vụ và lịch sử trước đó khác nhau. Vì vậy bảng `predictions` cần lưu theo:

- `disease_id`
- `iso3`
- `iso_year`
- `iso_week`
- `horizon_weeks`
- `model_version_id`

### Vì sao lưu số ca dự đoán và mức rủi ro

- `predicted_cases`: số ca dự đoán, phục vụ biểu đồ, xếp hạng, thống kê và diễn giải kết quả.
- `risk_level`: mức rủi ro Low/Medium/High, phục vụ màu bản đồ, bộ lọc và danh sách cảnh báo.
- `risk_probability`: trong hệ thống hiện hiểu là xác suất rủi ro High, giúp có điểm rủi ro liên tục thay vì chỉ 3 nhãn rời rạc.
- `model_version_id`: giúp truy vết kết quả được sinh bởi mô hình nào.
- `features_snapshot`: hỗ trợ kiểm tra lại bộ đặc trưng tại thời điểm dự báo.

### Vì sao lưu dự báo vào cơ sở dữ liệu thay vì chạy mô hình mỗi lần giao diện gọi

Lưu dự báo vào cơ sở dữ liệu giúp bảng điều khiển phản hồi nhanh, ổn định và dễ tái lập. Nếu mỗi lần giao diện gọi đều chạy mô hình trực tiếp, hệ thống khó kiểm soát phiên bản mô hình, khó kiểm tra lại kết quả, dễ chậm và khó so sánh BACKTEST. Với cơ sở dữ liệu, cùng một tuần/bệnh/quốc gia luôn trả về một kết quả đã được sinh bởi một lần chạy cụ thể.

Cơ sở dữ liệu hỗ trợ các màn hình:

- Bản đồ rủi ro: truy vấn dự báo theo bệnh/năm/tuần.
- Chi tiết quốc gia: truy vấn dự báo và số ca thực tế theo một quốc gia.
- BACKTEST: chọn tuần quá khứ để xem dự báo đã lưu.
- Thống kê: tổng hợp mức rủi ro, nhóm quốc gia đứng đầu, xu hướng.
- Dự báo mới nhất: tìm tuần mới nhất có dự báo hợp lệ.

## 3. API

API là lớp tích hợp giữa dữ liệu, tệp mô hình và giao diện. API không chỉ là CRUD.

Vai trò chính:

- Nạp các tệp mô hình `.pkl` khi ứng dụng khởi động.
- Chuẩn hóa dữ liệu đầu vào theo danh sách đặc trưng đã xuất ra.
- Chạy mô hình dự báo số ca và phân mức rủi ro.
- Chạy dự báo hàng loạt để sinh kết quả cho nhiều quốc gia/tuần.
- Lưu dự báo vào cơ sở dữ liệu.
- Cung cấp API ổn định cho giao diện.
- Ghi log quy trình và hỗ trợ trang quản trị/lịch chạy ở mức bản mẫu.

Các nhóm API hiện có trong `backend/app/api/v1/endpoints/`:

- `countries`: danh sách và thông tin quốc gia.
- `diseases`: danh sách bệnh.
- `risk`: bản đồ rủi ro mới nhất hoặc theo bệnh/năm/tuần.
- `predictions`: dự báo chi tiết và dữ liệu phục vụ BACKTEST.
- `forecast`: dự báo 4 tuần cho một quốc gia/bệnh.
- `analytics`: thống kê phục vụ bảng điều khiển.
- `infer`: dự báo trực tiếp nếu cần kiểm tra mô hình.
- `weather`: dữ liệu thời tiết.
- `admin`: kích hoạt job, xem lịch chạy và quản trị quy trình.

Dự báo hàng loạt và lịch chạy tồn tại để mô phỏng quy trình vận hành định kỳ: khi có dữ liệu mới, hệ thống tạo đặc trưng, chạy mô hình, lưu dự báo, sau đó bảng điều khiển chỉ đọc API.

## 4. Giao diện

Giao diện là bảng điều khiển phân tích rủi ro, không chỉ là màn hình minh họa. Nhiệm vụ của giao diện là giúp người dùng đọc nhanh tình hình theo không gian, thời gian và bệnh.

Các chức năng chính:

- Bản đồ rủi ro toàn cầu theo màu Low/Medium/High.
- Bộ lọc bệnh, năm, tuần, vùng WHO, mức rủi ro.
- Chế độ **MỚI NHẤT**: tuần mới nhất hệ thống có dự báo.
- Chế độ **BACKTEST**: chọn tuần/năm quá khứ để mô phỏng hoặc kiểm chứng dự báo.
- Trang chi tiết quốc gia: xem chi tiết một quốc gia.
- Biểu đồ dự báo: dự báo 4 tuần tới.
- Trang thống kê: thống kê tổng hợp và xếp hạng.
- Thanh cảnh báo: danh sách điểm cần chú ý.

Ngôn ngữ UI cần nhất quán:

- Không dùng "REALTIME" nếu ý nghĩa chỉ là tuần mới nhất có dữ liệu/dự báo trong cơ sở dữ liệu.
- Không dùng "LỊCH SỬ" nếu người dùng đang xem dự báo BACKTEST.
- Dùng "MỚI NHẤT" và "BACKTEST".
- Không gọi dữ liệu quá khứ là "training data" trên giao diện, vì người dùng đang xem dự báo/BACKTEST, không trực tiếp xem tập huấn luyện.

## 5. Cách đọc hai API hay gặp

Ví dụ:

```text
/api/v1/forecast/flu/USA?as_of_year=2019&as_of_week=2
/api/v1/predictions/flu/USA?year=2019&week=2
```

Ý nghĩa nên trình bày:

- `forecast`: đứng tại tuần được chọn, dùng bộ đặc trưng của tuần đó để dự báo các tuần tiếp theo, thường h=1..4.
- `predictions`: đọc dự báo đã lưu cho đúng bệnh/quốc gia/năm/tuần trong cơ sở dữ liệu, thường dùng cho chi tiết quốc gia và BACKTEST.

Giao diện có thể gọi cả hai API khi chọn một quốc gia vì hai phần màn hình cần dữ liệu khác nhau: phần chi tiết tuần đang xem và phần dự báo 4 tuần tới. Đây là hành vi bình thường nếu hai API phục vụ hai khối hiển thị khác nhau.

## 6. Mẫu câu giải thích kết quả trên bảng điều khiển

Ví dụ câu nói khi demo:

> Với Brazil, bệnh dengue, tuần W36 năm 2023, hệ thống dự đoán khoảng N ca và mức rủi ro R. Đây là tuần mới nhất mà bộ dữ liệu hiện có đủ đặc trưng/dự báo cho dengue, nên bảng điều khiển gọi là MỚI NHẤT trong phạm vi dữ liệu, không phải dữ liệu thời gian thực ngoài đời. Kết quả được tạo từ lịch sử ca bệnh, mùa vụ theo tuần/năm và nhóm đặc trưng thời tiết. Nếu chọn một tuần quá khứ, chế độ đó là BACKTEST và có thể so sánh với số ca thực tế để đánh giá sai số.

Nguyên tắc diễn giải:

- Không nói mô hình chắc chắn đúng.
- Không khẳng định thời tiết là nguyên nhân duy nhất.
- Nhắc đến dữ liệu thiếu, dữ liệu đứt quãng và khác biệt nguồn dữ liệu nếu kết quả bất thường.
- Giải thích cả `predicted_cases` và `risk_level`, vì bảng điều khiển cần cả số ca và mức cảnh báo.
