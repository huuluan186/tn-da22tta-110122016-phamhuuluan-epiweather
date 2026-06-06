# Q&A bảo vệ

Các câu trả lời dưới đây dùng cho phần hỏi đáp hội đồng. Mục tiêu là trả lời trung thực, đúng phạm vi bản mẫu KLTN và không phóng đại thành hệ thống vận hành thật.

## 1. Vì sao dữ liệu huấn luyện tới 2019 nhưng giao diện có 2023 hoặc 2026?

Giai đoạn huấn luyện là giai đoạn dùng để dạy mô hình học từ dữ liệu cũ, ví dụ 2010-2019. Sau khi huấn luyện xong, mô hình có thể được áp dụng cho các giai đoạn sau nếu hệ thống có đủ đặc trưng đầu vào.

Bảng điều khiển có 2023 hoặc 2026 vì đó là giai đoạn sau huấn luyện dùng để kiểm thử quá khứ hoặc demo vận hành. Với flu, hệ thống có thể có dữ liệu/dự báo tới 2026. Với dengue, nguồn hiện có chỉ tới 2023-W36, nên đó là tuần mới nhất của dengue trong phạm vi dữ liệu hiện có.

## 2. Dự đoán quá khứ có ý nghĩa gì?

Dự đoán quá khứ là BACKTEST, tức kiểm thử lại trên quá khứ. Ta giả lập rằng hệ thống đang đứng tại tuần đó, dùng các đặc trưng đã biết trước thời điểm dự báo, rồi so sánh dự báo với số ca thực tế nếu số ca thực tế đã có. Cách này giúp kiểm chứng mô hình, đo sai số và giải thích độ tin cậy trước khi dùng cho giai đoạn mới nhất.

## 3. Có phải dữ liệu thời gian thực không?

Không nên gọi chung là dữ liệu thời gian thực. Bảng điều khiển mặc định hiển thị tuần mới nhất có dự báo trong cơ sở dữ liệu. Giai đoạn này nên gọi là **MỚI NHẤT**.

Dữ liệu thời gian thực ngoài đời nghĩa là dữ liệu bệnh được cập nhật gần thời gian thực từ nguồn giám sát chính thức. Không phải bệnh nào cũng có nguồn như vậy. Ví dụ dengue trong dữ liệu hiện chỉ tới 2023-W36, nên 2023-W36 là tuần mới nhất của hệ thống cho dengue, không phải dữ liệu thời gian thực năm 2026.

## 4. Làm sao biết mô hình đúng?

Notebook đánh giá mô hình bằng kiểm chứng theo thời gian và một năm giữ lại là 2022. Bài toán dự báo số ca dùng các chỉ số R2, RMSE, MAE. Bài toán phân mức rủi ro dùng macro-F1 và các chỉ số theo từng lớp Low/Medium/High.

Ngoài các chỉ số đánh giá, bảng điều khiển hỗ trợ BACKTEST để chọn tuần quá khứ và so sánh dự báo với số ca thực tế. Tuy vậy, mô hình không được xem là chắc chắn đúng; nó là công cụ hỗ trợ phân tích rủi ro.

## 5. Vì sao mỗi bệnh có mô hình khác nhau?

Flu và dengue có mùa vụ, độ trễ thời tiết, nguồn dữ liệu và độ phủ khác nhau. Notebook cũng chọn độ trễ khác nhau: flu dùng độ trễ ngắn hơn, dengue dùng độ trễ dài hơn. Kết quả huấn luyện chọn LightGBM cho dự báo số ca flu và Random Forest cho dự báo số ca dengue. Dùng mô hình riêng giúp phản ánh đặc điểm riêng của từng bệnh.

## 6. Vì sao số quốc gia khác nhau?

Mỗi nguồn dữ liệu có độ phủ khác nhau. WHO FluNet, OpenDengue, ECDC và dữ liệu thời tiết không có cùng số quốc gia, cùng giai đoạn hay cùng mức đầy đủ. Một quốc gia chỉ có thể hiển thị dự báo nếu hệ thống có đủ dữ liệu để tạo bộ đặc trưng và mô hình tương ứng có thể dự đoán.

## 7. Vì sao dùng cả dự báo số ca và phân mức rủi ro?

Dự báo số ca trả lời "dự đoán bao nhiêu ca", còn phân mức rủi ro trả lời "mức rủi ro là gì". Bảng điều khiển cần cả hai. `predicted_cases` phục vụ biểu đồ, xếp hạng và diễn giải số ca. `risk_level` phục vụ bản đồ màu, cảnh báo và lọc ưu tiên.

Mức rủi ro không nhất thiết tăng tuyến tính theo số ca tuyệt đối, vì có thể phụ thuộc đặc điểm theo quốc gia, bệnh, tuần, mùa vụ hoặc phân phối dữ liệu.

## 8. Vì sao cần API/cơ sở dữ liệu, sao không chạy notebook là đủ?

Notebook phù hợp cho nghiên cứu, phân tích dữ liệu và huấn luyện. Nhưng bảng điều khiển cần API ổn định, truy vấn nhanh, lưu kết quả, truy vết phiên bản mô hình và phục vụ nhiều màn hình.

API và cơ sở dữ liệu giúp biến mô hình thành hệ thống:

- API nạp tệp mô hình và chuẩn hóa đầu vào dự báo.
- Cơ sở dữ liệu lưu bộ đặc trưng, kết quả dự báo, thông tin mô hình và chỉ số đánh giá.
- Giao diện chỉ gọi API, không phụ thuộc notebook.
- Chế độ BACKTEST và MỚI NHẤT hoạt động nhất quán.

## 9. Nếu dữ liệu bị thiếu hoặc đứt quãng thì xử lý thế nào?

Notebook có kiểm tra dữ liệu thiếu, độ phủ theo năm/quốc gia và các giai đoạn bất thường như COVID. Với flu, 2020-2021 bị loại khỏi huấn luyện chính vì bị nhiễu bởi thay đổi giám sát và can thiệp xã hội. Với dengue, giai đoạn độ phủ thấp 2010-2014 được xử lý thận trọng và huấn luyện thực tế tập trung hơn vào 2015-2019.

Trong hệ thống, nếu không đủ bộ đặc trưng cho một quốc gia/tuần, API không nên bịa dự báo. Bảng điều khiển cần hiển thị thiếu dữ liệu hoặc bỏ qua điểm đó.

## 10. Hệ thống này có dùng vận hành thật ngay được không?

Chưa. Đây là bản mẫu KLTN chứng minh quy trình hoàn chỉnh từ dữ liệu đến mô hình học máy, API, cơ sở dữ liệu và giao diện. Để vận hành thật cần bổ sung kiểm định y tế, quản trị dữ liệu, theo dõi hệ thống, huấn luyện lại tự động, phát hiện dữ liệu bị lệch theo thời gian, triển khai tự động, bảo mật và quy trình vận hành với nguồn dữ liệu chính thức.

## 11. Vì sao tuần mới nhất của dengue là 2023-W36 dù hiện tại là 2026?

Vì "mới nhất" trên bảng điều khiển là mới nhất theo dữ liệu/dự báo mà hệ thống có, không phải ngày hiện tại ngoài đời. Nếu nguồn dengue hiện có đủ dữ liệu tới 2023-W36, thì 2023-W36 là tuần mới nhất của dengue trong phạm vi dữ liệu hiện có. Gọi đây là MỚI NHẤT của hệ thống chính xác hơn gọi dữ liệu thời gian thực.

## 12. Nếu mức rủi ro High nhưng số ca dự đoán không quá cao thì giải thích sao?

`predicted_cases` là số ca dự đoán tuyệt đối. `risk_level` là mức cảnh báo từ mô hình phân lớp hoặc ngưỡng rủi ro, có thể phản ánh bất thường tương đối theo bệnh, quốc gia, tuần và mùa vụ. Một số ca không cao tuyệt đối vẫn có thể đáng chú ý nếu vượt nền thông thường của quốc gia/bệnh đó.

## 13. Nếu mô hình sai ở một tuần cụ thể thì có làm mất giá trị hệ thống không?

Không. Dự báo dịch bệnh luôn có sai số, nhất là khi dữ liệu giám sát bị trễ, thiếu hoặc có sự kiện bất thường. Giá trị hệ thống nằm ở việc cung cấp quy trình kiểm chứng được: có dự báo, có số ca thực tế để so sánh khi BACKTEST, có chỉ số đánh giá, có phiên bản mô hình và có bảng điều khiển để phân tích sai số.

## 14. Điểm giới hạn lớn nhất hiện tại là gì?

Các giới hạn chính:

- Dữ liệu giám sát dịch bệnh không đồng đều giữa quốc gia và bệnh.
- Dengue không có nguồn dữ liệu thời gian thực toàn cầu ổn định trong repo hiện tại.
- Phân mức rủi ro, đặc biệt lớp High của dengue, còn khó do mất cân bằng và biến động nguồn dữ liệu.
- Bản mẫu chưa có phần vận hành mô hình đầy đủ như theo dõi dữ liệu lệch theo thời gian và huấn luyện lại tự động.

Những giới hạn này cần được trình bày rõ thay vì che giấu.
