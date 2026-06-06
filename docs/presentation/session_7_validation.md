# Session 7: Kiểm chứng độc lập bằng năm 2022

> **Mục tiêu thuyết trình:** Trả lời câu hỏi của giáo viên: “Làm sao biết mô hình không chỉ học tốt trên dữ liệu cũ?”  
> Câu trả lời: ngoài kiểm chứng theo thời gian ở Session 6, em còn giữ riêng năm 2022 để kiểm tra lại trên dữ liệu mới hơn, không dùng năm này để huấn luyện chính.

---

## 1. Mạch nói chung

Ở Session 6, em đã kiểm chứng mô hình bằng cách huấn luyện trên các năm trước và kiểm tra trên năm sau. Tuy nhiên, các năm 2014-2019 vẫn nằm trong giai đoạn lịch sử dùng để phát triển mô hình. Vì vậy Session 7 làm thêm một bước kiểm tra độc lập hơn: dùng năm 2022 làm năm giữ lại.

**Hold-out** nghĩa là “giữ riêng một phần dữ liệu không cho mô hình học”, sau đó dùng phần đó để kiểm tra. Trong session này, năm 2022 là phần hold-out.

Cách nói khi trình bày:

“Em dùng năm 2022 như một bài kiểm tra cuối. Mô hình đã được xây dựng từ dữ liệu trước đó, sau đó em đưa năm 2022 vào để xem khi gặp dữ liệu mới hơn thì kết quả còn ổn không.”

---

## 2. Vì sao chọn năm 2022?

| Năm | Cách xử lý | Lý do |
|---|---|---|
| 2020 | Không dùng làm kiểm chứng chính | COVID làm hành vi phòng bệnh, đi lại, đeo khẩu trang và báo cáo ca bệnh thay đổi mạnh |
| 2021 | Không dùng làm kiểm chứng chính | Vẫn còn ảnh hưởng COVID, đặc biệt với cúm |
| 2022 | Dùng làm năm kiểm chứng riêng | Phù hợp hơn để kiểm tra mô hình sau giai đoạn COVID nặng |
| 2023+ | Chưa dùng làm kiểm chứng chính trong bản này | Dữ liệu chưa đồng nhất tại thời điểm làm notebook |

Cách nói khi trình bày:

“Em không chọn 2020-2021 vì đây là giai đoạn quá đặc biệt. Với cúm, số ca có thể giảm mạnh không phải vì quy luật bình thường của bệnh, mà do khẩu trang, giãn cách và thay đổi hành vi. Vì vậy em chọn 2022 để kiểm tra mô hình trên một năm mới hơn nhưng ít bất thường hơn.”

---

## 3. Cell 7.A - Chuẩn bị thời tiết ERA5 năm 2022

Notebook tải lại dữ liệu thời tiết ERA5 cho năm 2022, sau đó xử lý theo cùng cách như các năm huấn luyện.

**ERA5** là bộ dữ liệu thời tiết toàn cầu. Trong đồ án này, ERA5 cung cấp các biến như nhiệt độ, độ ẩm, lượng mưa, bức xạ mặt trời.

Các bước chính:

1. Tải dữ liệu thời tiết năm 2022.
2. Gán dữ liệu thời tiết về từng quốc gia.
3. Gom dữ liệu theo tuần.
4. Tạo các biến thời tiết cần thiết như độ ẩm và điểm sương.
5. Lưu thành file thời tiết tuần cho năm 2022.

Cách nói khi trình bày:

“Để kiểm tra năm 2022 công bằng, em không dùng lại dữ liệu thời tiết cũ. Em tải và xử lý riêng thời tiết năm 2022, sau đó đưa qua cùng quy trình tạo đặc trưng như Session 5.”

---

## 4. Cell 7.1 - Tạo đặc trưng cúm năm 2022

Để dự báo năm 2022, mô hình cần các đặc trưng giống lúc huấn luyện: lịch sử ca bệnh, mùa vụ, bán cầu và thời tiết có độ trễ.

**Warmup** nghĩa là phần dữ liệu quá khứ cần có trước năm dự báo để tính các độ trễ. Ví dụ nếu cần thời tiết trễ 7 tuần, thì đầu năm 2022 phải có dữ liệu cuối năm 2021 để tính đủ đặc trưng.

```python
master_2022 = master[master['iso_year'].isin([2021, 2022])].copy()
features_2022_flu = build_features(master_2022, FLU_FEATURE_CONFIG)
features_2022_flu = features_2022_flu[features_2022_flu['iso_year'] == 2022]
```

Kết quả: tạo được bộ đặc trưng cúm năm 2022 cho khoảng 130 quốc gia.

Cách nói khi trình bày:

“Với cúm, em lấy thêm dữ liệu cuối năm 2021 để tính các biến độ trễ cho đầu năm 2022. Sau khi tính xong, em chỉ giữ lại các dòng thuộc năm 2022 để kiểm chứng.”

---

## 5. Cell 7.2 - Tạo đặc trưng sốt xuất huyết năm 2022

Sốt xuất huyết cần thời gian warmup dài hơn cúm vì các độ trễ thời tiết dài hơn, có biến lên đến 16 tuần.

Vì vậy, để dự báo đầu năm 2022, cần dữ liệu từ cuối năm 2021. Nếu thiếu phần này, các tuần đầu năm 2022 sẽ bị thiếu đặc trưng.

Kết quả: tạo được bộ đặc trưng dengue năm 2022 cho khoảng 26 quốc gia.

Cách nói khi trình bày:

“Sốt xuất huyết cần nhìn xa hơn về quá khứ vì thời tiết ảnh hưởng đến muỗi trước, rồi sau đó mới thể hiện thành ca bệnh. Do đó phần warmup của dengue dài hơn flu.”

---

## 6. Cell 7.3 - Dự báo số ca trên năm 2022

Notebook nạp lại hai mô hình đã chọn ở Session 6:

| Bệnh | Mô hình dùng để dự báo số ca |
|---|---|
| Cúm | LightGBM |
| Sốt xuất huyết | Random Forest |

Sau đó dự báo trên bộ đặc trưng 2022 và so sánh với số ca thực tế.

```python
lgbm_flu = joblib.load(MODELS_DIR / 'lgbm_flu_regressor_v1.pkl')
rf_dengue = joblib.load(MODELS_DIR / 'rf_dengue_regressor_v1.pkl')
```

### Kết quả chính

| Bệnh | R² kiểm chứng Session 6 | R² năm 2022 | Ý nghĩa |
|---|---:|---:|---|
| Cúm | khoảng 0.902 | khoảng 0.78-0.82 | Giảm nhẹ nhưng vẫn dùng được |
| Sốt xuất huyết | khoảng 0.936 | khoảng 0.85-0.88 | Giảm nhẹ, vẫn khá ổn |

**R²** là chỉ số cho biết mô hình giải thích được bao nhiêu phần biến động dữ liệu. R² càng gần 1 càng tốt.

Cách nói khi trình bày:

“Khi đưa sang năm 2022, kết quả có giảm so với kiểm chứng trong giai đoạn cũ. Điều này là bình thường vì năm mới có thể khác dữ liệu huấn luyện. Quan trọng là mô hình không sụp hoàn toàn, vẫn giữ được mức đánh giá chấp nhận được.”

---

## 7. Cell 7.4 - Kiểm tra phân mức rủi ro năm 2022

Ngoài số ca, dashboard còn cần mức rủi ro Low, Medium, High. Vì vậy notebook cũng kiểm tra mô hình phân loại rủi ro trên năm 2022.

**Macro-F1** là chỉ số trung bình F1 của ba lớp Low, Medium, High. Chỉ số này phù hợp vì ta không muốn mô hình chỉ dự đoán tốt lớp nhiều nhất mà bỏ qua lớp High.

| Bệnh | Macro-F1 Session 6 | Macro-F1 năm 2022 | Nhận xét |
|---|---:|---:|---|
| Cúm | khoảng 0.542 | khoảng 0.50 | Vẫn ở mức chấp nhận được |
| Sốt xuất huyết | khoảng 0.475 | khoảng 0.41 | Yếu hơn, đặc biệt ở lớp High |

Cách nói khi trình bày:

“Phân mức rủi ro khó hơn dự báo số ca vì mô hình phải chọn đúng Low, Medium hay High. Với cúm, kết quả còn tương đối ổn. Với sốt xuất huyết, lớp High vẫn là hạn chế vì dữ liệu ít hơn và các đợt dịch lớn trong quá khứ làm mức nền bị ảnh hưởng.”

---

## 8. Cell 7.5 - So sánh Session 6 và năm 2022

| Nội dung | Kiểm chứng Session 6 | Kiểm chứng 2022 | Cách hiểu |
|---|---|---|---|
| Dự báo cúm | R² khoảng 0.902 | R² khoảng 0.80 | Giảm nhưng không mất khả năng dự báo |
| Dự báo dengue | R² khoảng 0.936 | R² khoảng 0.87 | Giảm ít hơn cúm |
| Phân loại cúm | Macro-F1 khoảng 0.542 | Macro-F1 khoảng 0.50 | Dùng được cho cảnh báo mức tổng quát |
| Phân loại dengue | Macro-F1 khoảng 0.475 | Macro-F1 khoảng 0.41 | Cần cải thiện lớp High |

### Phát hiện chính

1. Mô hình vẫn dùng được khi gặp năm mới hơn.
2. Chỉ số giảm là hợp lý vì dữ liệu 2022 không giống hoàn toàn giai đoạn huấn luyện.
3. Dengue giảm ít hơn cúm trong dự báo số ca, có thể vì mẫu bệnh dengue trong dữ liệu ổn định hơn theo vùng nhiệt đới.
4. Phân loại rủi ro, đặc biệt lớp High của dengue, vẫn là điểm cần cải thiện.

**Distribution shift** nghĩa là dữ liệu kiểm tra có phân bố khác dữ liệu huấn luyện. Ví dụ sau COVID, hành vi xã hội thay đổi nên số ca cúm năm 2022 có thể không giống giai đoạn trước COVID.

---

## 9. Cell 7.6 - Lưu kết quả kiểm chứng

Notebook lưu kết quả kiểm chứng năm 2022 để báo cáo và để backend có thể tham chiếu lại.

**Artifact** nghĩa là file kết quả được lưu ra sau khi chạy mô hình, ví dụ file mô hình `.pkl`, file danh sách đặc trưng hoặc file chỉ số đánh giá.

Cách nói khi trình bày:

“Sau khi kiểm chứng, em lưu lại kết quả để hệ thống có dấu vết rõ ràng: mô hình nào, kiểm tra năm nào, chỉ số ra sao. Điều này giúp phần triển khai backend không phụ thuộc vào việc mở notebook thủ công.”

---

## 10. Ý chính Session 7

1. Năm 2022 được giữ riêng để kiểm tra mô hình trên dữ liệu mới hơn.
2. Không dùng 2020-2021 làm kiểm chứng chính vì COVID làm dữ liệu quá bất thường.
3. Chỉ số giảm khi sang 2022 là bình thường, không phải lỗi mô hình.
4. Dự báo số ca vẫn khá ổn; phân loại rủi ro dengue còn yếu ở lớp High.
5. Kết quả đủ để đưa mô hình vào backend của bản mẫu, nhưng cần ghi rõ giới hạn trong báo cáo.

---

## 11. Câu nói thuyết trình cho Session 7

> “Sau khi kiểm chứng theo thời gian ở Session 6, em làm thêm một bước kiểm tra độc lập bằng năm 2022. Năm này không dùng để huấn luyện chính, nên giúp kiểm tra xem mô hình có dùng được trên dữ liệu mới hơn không.”
>
> “Em không chọn 2020-2021 vì hai năm này bị ảnh hưởng rất mạnh bởi COVID. Với cúm, khẩu trang, giãn cách và thay đổi hành vi khám bệnh làm số ca giảm bất thường. Vì vậy 2022 là lựa chọn hợp lý hơn.”
>
> “Kết quả năm 2022 có giảm so với kiểm chứng trước đó, nhưng vẫn ở mức chấp nhận được. Điều này cho thấy mô hình không chỉ học thuộc dữ liệu cũ. Tuy nhiên phần phân loại rủi ro dengue, nhất là lớp High, vẫn là hạn chế cần cải thiện.”
