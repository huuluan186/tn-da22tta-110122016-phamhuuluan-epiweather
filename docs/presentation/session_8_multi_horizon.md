# Session 8: Dự báo 4 tuần tiếp theo

> **Mục tiêu thuyết trình:** Giải thích vì sao dashboard có biểu đồ dự báo 4 tuần tới, các điểm dự báo đó được tạo ra như thế nào, và vì sao không chỉ dùng một mô hình dự báo tuần kế tiếp.

---

## 1. Mạch nói chung

Các session trước chủ yếu dự báo cho tuần kế tiếp. Nhưng khi dùng dashboard, người xem thường không chỉ muốn biết tuần tới tăng hay giảm, mà còn muốn nhìn xu hướng trong vài tuần tiếp theo để chuẩn bị.

Vì vậy Session 8 mở rộng bài toán thành dự báo 4 tuần tới:

| Ký hiệu | Ý nghĩa |
|---|---|
| h=1 | Dự báo tuần kế tiếp |
| h=2 | Dự báo sau 2 tuần |
| h=3 | Dự báo sau 3 tuần |
| h=4 | Dự báo sau 4 tuần |

**Horizon** nghĩa là “mốc thời gian dự báo trong tương lai”. Trong file này, horizon h=4 nghĩa là dự báo số ca sau 4 tuần.

Cách nói khi trình bày:

“Session 8 phục vụ trực tiếp biểu đồ 4 tuần trên dashboard. Tại một tuần hiện tại, hệ thống tạo ra bốn dự báo: tuần sau, sau 2 tuần, sau 3 tuần và sau 4 tuần.”

---

## 2. Vì sao v5 chưa đủ?

v5 chỉ có mô hình dự báo h=1, tức là tuần kế tiếp. Nhưng yêu cầu của đề tài là dự báo theo giai đoạn, nên chỉ một tuần là chưa đủ.

Người dùng cần trả lời các câu hỏi như:

1. Tuần tới nguy cơ tăng hay giảm?
2. Hai tuần nữa tình hình có tiếp tục tăng không?
3. Khoảng một tháng nữa xu hướng có đáng lo không?

Vì vậy v6 thêm dự báo h=1, h=2, h=3, h=4.

---

## 3. Hai cách dự báo nhiều tuần

| Cách | Giải thích | Ưu điểm | Hạn chế |
|---|---|---|---|
| Dự báo lặp lại | Dự báo tuần 1, rồi lấy kết quả đó làm đầu vào để dự báo tuần 2 | Chỉ cần một mô hình | Nếu tuần 1 sai, lỗi có thể kéo sang tuần 2, 3, 4 |
| Dự báo trực tiếp từng mốc | Huấn luyện riêng mô hình cho h=1, h=2, h=3, h=4 | Giảm lỗi cộng dồn | Cần huấn luyện nhiều mô hình hơn |

**Recursive** nghĩa là dự báo lặp lại: kết quả dự báo trước được đưa lại vào mô hình để dự báo bước sau.

**Lỗi cộng dồn** nghĩa là sai số ở tuần trước làm các tuần sau sai theo. Ví dụ dự báo tuần 1 cao hơn thực tế, rồi lấy kết quả cao đó để dự báo tuần 2, thì tuần 2 cũng có thể bị kéo sai.

Notebook chọn cách **dự báo trực tiếp từng mốc**. Nghĩa là:

- Một mô hình riêng cho h=1.
- Một mô hình riêng cho h=2.
- Một mô hình riêng cho h=3.
- Một mô hình riêng cho h=4.

Cách nói khi trình bày:

“Em không lấy dự báo tuần 1 để đoán tiếp tuần 2, vì như vậy lỗi có thể cộng dồn. Em huấn luyện riêng từng mốc dự báo để mỗi tuần tương lai được học trực tiếp từ dữ liệu thật trong quá khứ.”

---

## 4. Cell 8.1 - Tạo mục tiêu dự báo 4 tuần cho cúm

Tại mỗi dòng dữ liệu, notebook tạo thêm 4 cột mục tiêu:

| Cột | Ý nghĩa |
|---|---|
| `target_h1` | Số ca tuần W+1 |
| `target_h2` | Số ca tuần W+2 |
| `target_h3` | Số ca tuần W+3 |
| `target_h4` | Số ca tuần W+4 |

```python
for h in [1, 2, 3, 4]:
    df[f'target_h{h}'] = df.groupby('iso3')[target_col].shift(-h)
```

`shift(-h)` nghĩa là lấy giá trị ở tương lai h tuần để làm nhãn huấn luyện. Việc này chỉ dùng khi tạo dữ liệu huấn luyện, không phải lúc dự báo thật.

Vẫn phải dùng `groupby('iso3')` để không lấy nhầm tương lai của quốc gia khác.

Cách nói khi trình bày:

“Tại một tuần W, em tạo nhãn cho tuần W+1 đến W+4. Khi huấn luyện, mô hình h=4 học cách dự báo số ca sau 4 tuần. Khi chạy thật, mô hình chỉ nhìn các đặc trưng hiện tại và cho ra dự báo tương ứng.”

---

## 5. Cell 8.2 - Tạo mục tiêu dự báo 4 tuần cho dengue

Dengue làm cùng logic như cúm, chỉ khác model cuối cùng là Random Forest thay vì LightGBM.

Một số dòng cuối dữ liệu sẽ bị bỏ vì không có đủ tương lai để tạo `target_h4`. Ví dụ tuần cuối cùng của dữ liệu không thể biết sau 4 tuần là bao nhiêu nếu dữ liệu đã kết thúc.

Cách nói khi trình bày:

“Việc bỏ vài dòng cuối là bình thường. Muốn huấn luyện dự báo sau 4 tuần thì mỗi dòng phải có đủ số ca thật sau 4 tuần để làm đáp án.”

---

## 6. Cell 8.3 - Kiểm chứng nhiều mốc cho cúm

Với cúm, notebook dùng LightGBM vì đây là mô hình tốt nhất đã chọn ở Session 6.

```python
for h in [1, 2, 3, 4]:
    model = LGBMRegressor(...)
    model.fit(X_train, y_train_h)
```

**Tham số** là các thiết lập của mô hình, ví dụ số cây, độ sâu của cây, tốc độ học. Ở session này, notebook giữ lại tham số tốt từ Session 6 vì bộ đặc trưng không thay đổi nhiều.

Cách nói khi trình bày:

“Với cúm, em giữ LightGBM vì Session 6 đã chứng minh đây là mô hình tốt nhất cho cúm. Sau đó em huấn luyện 4 bản LightGBM riêng cho 4 mốc dự báo.”

---

## 7. Cell 8.4 - Lưu 4 mô hình cúm

Kết quả tạo 4 file mô hình:

| File | Dự báo |
|---|---|
| `lgbm_flu_regressor_h1_v1.pkl` | Tuần kế tiếp |
| `lgbm_flu_regressor_h2_v1.pkl` | Sau 2 tuần |
| `lgbm_flu_regressor_h3_v1.pkl` | Sau 3 tuần |
| `lgbm_flu_regressor_h4_v1.pkl` | Sau 4 tuần |

Kết quả kiểm chứng:

| Mốc | R² cúm |
|---|---:|
| h=1 | 0.8661 |
| h=2 | 0.8293 |
| h=3 | 0.7928 |
| h=4 | 0.7573 |

Cách nói khi trình bày:

“Càng dự báo xa thì độ chính xác giảm dần. Đây là điều bình thường vì dự báo sau 4 tuần khó hơn dự báo tuần sau.”

---

## 8. Cell 8.5 - Kiểm chứng và lưu 4 mô hình dengue

Với dengue, notebook dùng Random Forest vì đây là mô hình tốt nhất đã chọn ở Session 6.

| File | Dự báo |
|---|---|
| `rf_dengue_regressor_h1_v1.pkl` | Tuần kế tiếp |
| `rf_dengue_regressor_h2_v1.pkl` | Sau 2 tuần |
| `rf_dengue_regressor_h3_v1.pkl` | Sau 3 tuần |
| `rf_dengue_regressor_h4_v1.pkl` | Sau 4 tuần |

Kết quả kiểm chứng:

| Mốc | R² dengue |
|---|---:|
| h=1 | 0.9292 |
| h=2 | 0.9191 |
| h=3 | 0.9086 |
| h=4 | 0.8981 |

Cách nói khi trình bày:

“Dengue giảm chậm hơn cúm khi dự báo xa hơn. Điều này có thể do dengue trong dữ liệu có độ trễ dài hơn và mẫu bệnh ổn định hơn ở các vùng nhiệt đới.”

---

## 9. Cell 8.6 - So sánh kết quả theo từng mốc

| Mốc dự báo | Cúm LightGBM | Dengue Random Forest |
|---|---:|---:|
| h=1 | 0.8661 | 0.9292 |
| h=2 | 0.8293 | 0.9191 |
| h=3 | 0.7928 | 0.9086 |
| h=4 | 0.7573 | 0.8981 |

### Phát hiện 1: Dự báo xa hơn thì khó hơn

Cả hai bệnh đều giảm R² từ h=1 đến h=4. Điều này hợp lý vì càng xa hiện tại, càng có nhiều yếu tố chưa biết.

### Phát hiện 2: Dengue giảm chậm hơn cúm

| Nội dung | Cúm | Dengue |
|---|---:|---:|
| R² h=1 | 0.8661 | 0.9292 |
| R² h=4 | 0.7573 | 0.8981 |
| Mức giảm | 0.1088 | 0.0311 |

Giải thích dễ hiểu:

1. Cúm thay đổi nhanh hơn theo mùa và theo hành vi con người.
2. Dengue có độ trễ dài hơn vì liên quan đến muỗi và môi trường.
3. Các đặc trưng dengue dùng nhiều tuần quá khứ nên vẫn còn tín hiệu khi dự báo xa hơn.

### Phát hiện 3: Vì sao h=1 ở v6 thấp hơn v5?

v5 chỉ cần dự báo tuần kế tiếp. v6 phải tạo đủ nhãn cho 4 tuần tương lai, nên phải bỏ một số dòng cuối dữ liệu không có đủ tương lai. Dữ liệu huấn luyện ít hơn một chút, nên h=1 của v6 có thể thấp hơn v5.

Cách nói khi trình bày:

“Đây là đánh đổi hợp lý. v5 tốt hơn một chút ở dự báo 1 tuần, nhưng v6 cho được cả chuỗi 4 tuần để hiển thị trên dashboard.”

---

## 10. So sánh v5 và v6

| Nội dung | v5 | v6 |
|---|---|---|
| Số tuần dự báo | 1 tuần | 4 tuần |
| Số mô hình dự báo cho mỗi bệnh | 1 | 4 |
| Phục vụ biểu đồ 4 tuần | Chưa đủ | Đủ |
| Độ chính xác h=1 | Cao hơn nhẹ | Thấp hơn nhẹ do bỏ bớt dòng cuối |
| Giá trị thực tế | Dự báo ngắn hạn | Nhìn được xu hướng gần 1 tháng |

Kết luận: v6 cần thiết để đáp ứng yêu cầu dự báo theo giai đoạn và để frontend có đủ dữ liệu vẽ biểu đồ 4 tuần.

---

## 11. Nếu giáo viên hỏi về tham chiếu nghiên cứu

Trong file cũ có nhắc Lowe et al. 2014 như một mốc tham khảo cho dự báo dengue.

**Benchmark** nghĩa là mốc tham khảo để so sánh. Nó không có nghĩa là hai bài toán giống hệt nhau, mà chỉ giúp đặt kết quả của mình vào bối cảnh.

Cách nói an toàn:

“Em dùng các công trình trước như một mốc tham khảo, nhưng không nói rằng so sánh là tuyệt đối giống nhau, vì dữ liệu, quốc gia và cách chia tập có thể khác. Điểm chính là kết quả của mô hình nằm trong mức hợp lý và không thấp bất thường so với các hướng nghiên cứu trước.”

---

## 12. Ý chính Session 8

1. Session 8 mở rộng từ dự báo 1 tuần sang dự báo 4 tuần.
2. `h=1,2,3,4` là các mốc dự báo trong tương lai.
3. Notebook dùng 4 mô hình riêng để tránh lỗi cộng dồn.
4. Cúm giảm rõ hơn khi dự báo xa; dengue giữ ổn định hơn.
5. v6 thấp hơn v5 nhẹ ở h=1 nhưng đổi lại có chuỗi dự báo đủ 4 tuần.
6. Kết quả phục vụ trực tiếp biểu đồ “Dự báo 4 tuần tới” trên dashboard.

---

## 13. Câu nói thuyết trình cho Session 8

> “Session 8 là phần mở rộng để dashboard có biểu đồ dự báo 4 tuần tới. Trước đó mô hình chủ yếu dự báo tuần kế tiếp, còn ở đây em tạo dự báo cho h=1, h=2, h=3 và h=4.”
>
> “Em không dùng cách dự báo lặp lại vì nếu tuần 1 sai thì sai số có thể kéo sang tuần 2, tuần 3 và tuần 4. Thay vào đó, em huấn luyện riêng từng mô hình cho từng mốc dự báo.”
>
> “Kết quả cho thấy càng dự báo xa thì độ chính xác giảm, điều này là bình thường. Với cúm, R² giảm từ khoảng 0.866 ở tuần 1 xuống 0.757 ở tuần 4. Với dengue, R² giảm ít hơn, từ khoảng 0.929 xuống 0.898.”
>
> “Kết luận là v6 cần thiết cho yêu cầu dự báo theo giai đoạn. Dù h=1 thấp hơn v5 nhẹ do phải bỏ một số dòng cuối, v6 có giá trị hơn cho giao diện vì tạo được chuỗi dự báo 4 tuần.”
