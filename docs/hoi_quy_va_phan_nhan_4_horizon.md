# Hồi quy và phân nhãn cho 4 horizon — tóm tắt thuyết trình

(Mô tả đúng hệ thống đang chạy, đã đối chiếu code backend và frontend.)

## Hai bài toán tách riêng

- Hồi quy: dự báo số ca (con số cụ thể).
- Phân nhãn rủi ro: xếp mức Low / Medium / High.

## Hồi quy: 4 mô hình cho 4 horizon

Horizon là mốc tương lai: h=1 là tuần kế tiếp, h=4 là sau 4 tuần.

Mỗi bệnh huấn luyện riêng 4 mô hình, mỗi mô hình một mốc (h=1..4). Tách riêng thay vì lấy dự báo tuần này đút vào dự báo tuần sau, để tránh sai số cộng dồn. Cúm dùng LightGBM, dengue dùng Random Forest.

R² (kiểm định chéo walk-forward):

| Mốc | Cúm | Dengue |
|---|---:|---:|
| h=1 | 0.866 | 0.929 |
| h=2 | 0.829 | 0.919 |
| h=3 | 0.793 | 0.909 |
| h=4 | 0.757 | 0.898 |

Càng dự báo xa, độ chính xác càng giảm.

## Phân nhãn rủi ro: hệ thống đang chạy hai cơ chế, ở hai chỗ khác nhau

**1. Nhãn theo từng horizon bằng ngưỡng endemic channel (Bortman 1999).**
Hiện trên trang chủ, khi chọn một quốc gia, ở ô "Mức độ 4 tuần tới". Mỗi tuần trong 4 tuần có một nhãn riêng. Cách tính: mô hình hồi quy ra số ca từng tuần, rồi so số ca đó với mức nền lịch sử của chính quốc gia, đúng tuần ISO đó:
- baseline = trung bình số ca lịch sử cùng tuần (cúm lấy 2010–2018, dengue 2015–2018).
- upper = baseline + 2σ.
- Low: số ca < baseline. Medium: baseline ≤ số ca < upper. High: số ca ≥ upper.

Nhãn này tính trực tiếp lúc gọi API, không lưu trong database, không dùng mô hình phân lớp.

**2. Nhãn của tuần hiện tại bằng mô hình phân lớp XGBClassifier.**
Hiện ở màu bản đồ cảnh báo, danh sách cảnh báo, và thẻ "Nhóm rủi ro" trên trang chi tiết. Tiến trình batch chạy trước: với mỗi quốc gia ở tuần mới nhất, chạy hồi quy h=1 ra số ca và chạy XGBClassifier ra `risk_level` cùng `risk_probability = P(High)`, rồi ghi vào bảng `predictions` với horizon_weeks = 1. Database chỉ giữ nhãn cho tuần đó (h=1), không có nhãn cho h=2, h=3, h=4.

## Một chỗ cần biết để khỏi nói nhầm

Biểu đồ "Dự báo 4 tuần" trên trang chi tiết quốc gia chỉ vẽ số ca, dải tin cậy và R², không hiển thị nhãn rủi ro. Nhãn 4 tuần theo Bortman nằm ở ô "Mức độ 4 tuần tới" trên trang chủ, không nằm trên biểu đồ này.

## Câu chốt với thầy

Dự báo số ca dùng 4 mô hình hồi quy cho 4 horizon. Phân mức rủi ro thì hệ thống dùng hai cách tùy chỗ hiển thị: ô "Mức độ 4 tuần tới" trên trang chủ áp ngưỡng endemic channel lên số ca dự báo để ra nhãn cho cả 4 tuần; còn màu bản đồ và thẻ "Nhóm rủi ro" là kết quả mô hình phân lớp XGBClassifier cho tuần hiện tại.

## Luồng khi người dùng chọn một năm/tuần khác (trang chi tiết quốc gia)

1. Người dùng nhập tuần và năm rồi bấm Áp dụng. Frontend gọi API forecast cho (bệnh, quốc gia, năm, tuần) đó.
2. Backend kiểm tra tuần chọn có nằm trong khoảng dữ liệu hợp lệ không; nếu vượt thì báo lỗi.
3. Lấy bộ đặc trưng đã tính sẵn của quốc gia tại đúng tuần đó (feature snapshot). Nếu không có thì báo không có dữ liệu.
4. Tính 4 tuần đích h=1..4 từ tuần đang chọn (xử lý đúng khi vắt qua năm).
5. Lần lượt chạy 4 mô hình hồi quy trên cùng bộ đặc trưng, ra số ca và R² cho từng mốc.
6. Trả về 4 điểm dự báo; biểu đồ trên trang chi tiết vẽ chuỗi số ca 4 tuần này.

Chọn tuần quá khứ chính là chế độ "kiểm thử quá khứ": mô hình chỉ nhìn đặc trưng tại tuần đó, không nhìn tương lai, nên có thể đối chiếu dự báo với số ca thật đã xảy ra.

Tài liệu chi tiết: `docs/presentation/session_8_multi_horizon.md` (hồi quy 4 horizon), `docs/presentation/ml_pipeline.md` mục 3.5–3.7 (phân nhãn và tóm tắt multi-horizon).
