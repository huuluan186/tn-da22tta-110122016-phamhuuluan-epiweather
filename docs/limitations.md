# Hạn chế của hệ thống

## So sánh đồng thời Influenza và Dengue

Hệ thống sử dụng hai pipeline dữ liệu và hai bộ mô hình riêng. Về kỹ thuật, hệ
thống có thể dự đoán cả Influenza và Dengue cho cùng một quốc gia nếu quốc gia
đó có feature snapshot hợp lệ của cả hai bệnh.

Tuy nhiên, kết quả mới nhất của hai bệnh không đồng thời về phạm vi quốc gia và
thời gian:

| Phạm vi mới nhất | Influenza | Dengue |
|---|---:|---:|
| Quốc gia có dự báo | 163 | 56 |
| Tuần dữ liệu mới nhất | 2026-W22 | 2023-W36 |

- 56 quốc gia có dự báo Dengue đều nằm trong tập quốc gia có dự báo Influenza.
- 107 quốc gia còn lại hiện chỉ có dự báo Influenza.
- Dengue bị giới hạn bởi độ phủ và cutoff của OpenDengue v1.3.
- Kết quả mới nhất của hai bệnh cho cùng một quốc gia không được xem là dự báo
  tại cùng thời điểm.
- Muốn so sánh trực tiếp hai bệnh phải chọn cùng quốc gia và cùng tuần lịch sử
  mà cả hai pipeline đều có feature snapshot hợp lệ.

Đây là hạn chế của độ phủ và độ trễ nguồn dữ liệu bệnh, không phải giới hạn khả
năng chạy nhiều mô hình của hệ thống.

