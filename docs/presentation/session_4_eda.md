# Session 4: Phân tích dữ liệu và chọn độ trễ thời tiết

> **Mục tiêu khi thuyết trình:** Session này không phải để khoe code hay đọc hết biểu đồ. Mục tiêu là giải thích cho giáo viên hiểu vì sao trước khi huấn luyện mô hình, em phải xem dữ liệu có lệch không, có theo mùa không, có đủ tin cậy theo thời gian không, và thời tiết nên được đưa vào mô hình với độ trễ bao nhiêu tuần.
>
> **Câu chốt của session:** Em không đưa dữ liệu vào mô hình một cách máy móc. Em kiểm tra dữ liệu trước, rồi mới quyết định cách biến đổi số ca, chọn giai đoạn huấn luyện, thêm yếu tố mùa vụ và chọn độ trễ thời tiết.

---

## 1. Mạch thuyết trình chung

Ở session này, em làm bước phân tích dữ liệu trước khi xây dựng mô hình. Lý do là dữ liệu bệnh truyền nhiễm thường không đều: có tuần rất ít ca, nhưng cũng có tuần bùng phát rất mạnh. Nếu bỏ qua bước này, mô hình có thể học sai trọng tâm hoặc bị một vài đợt dịch lớn chi phối.

Em đi qua 6 nhóm kiểm tra:

| Cell | Nội dung kiểm tra | Giá trị khi thuyết trình |
|---|---|---|
| 4.1 | Số ca bệnh có bị lệch quá mạnh không | Giải thích vì sao dùng `log1p` |
| 4.2 | Dữ liệu theo nước và theo năm có đủ không | Giải thích vì sao chọn giai đoạn huấn luyện |
| 4.3 | Bệnh có mùa vụ không | Giải thích vì sao thêm thông tin tuần trong năm và bán cầu |
| 4.4 | Thời tiết ảnh hưởng sau bao nhiêu tuần | Giải thích vì sao chọn độ trễ theo dữ liệu |
| 4.5 | Xem một vài quốc gia tiêu biểu | Kiểm tra kết quả có hợp lý trên ví dụ thật |
| 4.6 | Tổng hợp quyết định | Liên kết sang bước tạo đặc trưng và huấn luyện mô hình |

Khi nói với giáo viên, không cần đọc từng dòng code. Chỉ cần nhấn mạnh: mỗi biểu đồ trong phần này đều dẫn đến một quyết định cụ thể cho mô hình.

---

## 2. Cell 4.1 - Kiểm tra phân bố số ca và dùng log1p

### Giáo viên cần hiểu gì?

Số ca bệnh không phân bố đều. Phần lớn các tuần có số ca thấp, nhưng một số tuần bùng phát dịch có số ca rất cao. Nếu đưa số ca gốc vào mô hình, các đợt bùng phát lớn có thể làm mô hình tập trung quá nhiều vào vài điểm cực đoan.

Ví dụ trong dữ liệu:

| Bệnh | Độ lệch trước log | Trung vị | Giá trị rất lớn |
|---|---:|---:|---:|
| Cúm | 25.6 | 14 | 152,341 ca |
| Sốt xuất huyết | 12.6 | 11 | 146,000 ca |

Sau khi dùng `log1p`, độ lệch giảm mạnh:

| Bệnh | Độ lệch sau log1p |
|---|---:|
| Cúm | 1.04 |
| Sốt xuất huyết | 0.93 |

### Cách nói khi trình bày

“Ở cell này, em kiểm tra xem số ca bệnh có bị lệch quá nhiều hay không. Kết quả cho thấy hầu hết các tuần có số ca thấp, nhưng một số tuần dịch bùng phát thì số ca rất lớn. Nếu dùng số ca gốc, mô hình dễ bị các tuần bùng phát chi phối.

Vì vậy em dùng biến đổi `log1p`. Có thể hiểu đơn giản là cách này làm các giá trị quá lớn bớt áp đảo hơn, nhưng vẫn giữ được thứ tự tăng giảm của số ca. Sau khi biến đổi, dữ liệu cân bằng hơn, giúp mô hình học ổn định hơn.”

### Code chỉ dùng để minh họa

```python
master['inf_log1p'] = np.log1p(master['influenza_total'])
master['dengue_log1p'] = np.log1p(master['dengue_cases'])
```

### Ý cần nhấn mạnh

`log1p` không phải là thao tác trang trí. Đây là quyết định quan trọng để mô hình không bị vài đỉnh dịch rất lớn làm lệch.

---

## 3. Cell 4.2 - Kiểm tra độ phủ dữ liệu theo nước và theo năm

### Giáo viên cần hiểu gì?

Không phải năm nào dữ liệu cũng có chất lượng như nhau. Một số năm có nhiều nước báo cáo đầy đủ, một số năm bị thiếu hoặc bị ảnh hưởng bởi COVID-19. Vì vậy em không dùng toàn bộ dữ liệu một cách tự động, mà chọn giai đoạn phù hợp hơn để huấn luyện.

Kết quả chính:

| Bệnh | Quan sát quan trọng | Quyết định |
|---|---|---|
| Cúm | 2020-2021 số nước vẫn báo cáo, nhưng số ca giảm bất thường do các biện pháp phòng COVID | Huấn luyện chủ yếu trên giai đoạn 2010-2019 |
| Sốt xuất huyết | 2010-2014 còn ít nước, từ 2015-2019 dữ liệu ổn hơn | Huấn luyện chủ yếu trên giai đoạn 2015-2019 |

### Cách nói khi trình bày

“Ở cell này, em không chỉ xem có bao nhiêu dòng dữ liệu, mà xem dữ liệu có đủ đều theo nước và theo năm hay không.

Với cúm, giai đoạn 2020-2021 là giai đoạn đặc biệt vì COVID-19 làm thay đổi hành vi đi lại, đeo khẩu trang và giãn cách. Số ca cúm giảm rất mạnh, không phản ánh mùa cúm bình thường. Nếu dùng giai đoạn này để huấn luyện, mô hình có thể học nhầm rằng cúm tự nhiên giảm sâu.

Với sốt xuất huyết, các năm đầu có ít quốc gia hơn nên chưa đủ đại diện. Vì vậy em chọn giai đoạn từ 2015-2019 làm phần chính để huấn luyện.”

### Ý cần nhấn mạnh

Chọn giai đoạn huấn luyện không phải là bỏ dữ liệu tùy ý. Đó là cách tránh cho mô hình học từ những năm bất thường hoặc thiếu đại diện.

---

## 4. Cell 4.3 - Kiểm tra mùa vụ theo bán cầu

### Giáo viên cần hiểu gì?

Bệnh truyền nhiễm, đặc biệt là cúm, thường có mùa vụ. Nhưng mùa đông ở Bắc bán cầu và Nam bán cầu không trùng nhau, nên đỉnh cúm cũng bị lệch theo vị trí địa lý.

Kết quả trong dữ liệu:

| Khu vực | Tuần đỉnh cúm |
|---|---:|
| Bắc bán cầu | Khoảng tuần 6 |
| Nam bán cầu | Khoảng tuần 28 |
| Độ lệch | Khoảng 22 tuần |

### Cách nói khi trình bày

“Ở cell này, em kiểm tra xem dữ liệu sau khi ghép có phản ánh đúng quy luật mùa vụ hay không. Kết quả cho thấy cúm ở Bắc bán cầu thường đạt đỉnh khoảng đầu năm, còn Nam bán cầu đạt đỉnh khoảng giữa năm. Hai đỉnh này lệch nhau khoảng 22 tuần, gần bằng nửa năm.

Điều này quan trọng vì nó cho thấy dữ liệu sau khi xử lý là hợp lý về mặt thực tế. Đồng thời, nó cũng giải thích vì sao mô hình cần biết quốc gia thuộc bán cầu nào và tuần hiện tại là tuần thứ mấy trong năm.”

### Ý cần nhấn mạnh

Cell này không chỉ để vẽ biểu đồ mùa vụ. Nó là bằng chứng cho thấy cần đưa thông tin mùa trong năm và bán cầu vào mô hình.

---

## 5. Cell 4.4 - Chọn độ trễ thời tiết

### Giáo viên cần hiểu gì?

Thời tiết tuần này không nhất thiết làm số ca bệnh tăng ngay trong tuần này. Có thể phải sau vài tuần tác động mới thể hiện trong số ca báo cáo. Vì vậy em cần chọn “độ trễ”, tức là lấy thời tiết của bao nhiêu tuần trước để dự đoán số ca hiện tại.

Không nên dùng cùng một độ trễ cho mọi bệnh, vì cúm và sốt xuất huyết có cơ chế lây khác nhau:

| Bệnh | Cách lây chính | Ý nghĩa về độ trễ |
|---|---|---|
| Cúm | Lây trực tiếp qua đường hô hấp | Độ trễ thường ngắn hơn |
| Sốt xuất huyết | Phụ thuộc vào muỗi truyền bệnh | Độ trễ thường dài hơn vì liên quan vòng đời muỗi |

### Cách nói khi trình bày

“Ở cell này, câu hỏi em đặt ra là: thời tiết ở tuần nào thì liên quan nhiều nhất đến số ca bệnh hiện tại?

Nếu chọn thủ công, ví dụ luôn lấy thời tiết trước 1, 2, 3 tuần cho mọi bệnh, thì cách đó hơi đơn giản quá. Cúm và sốt xuất huyết khác nhau: cúm lây trực tiếp giữa người với người, còn sốt xuất huyết cần có muỗi truyền bệnh. Thời tiết có thể ảnh hưởng đến muỗi, sau đó muỗi phát triển, rồi mới truyền bệnh sang người. Vì vậy độ trễ của sốt xuất huyết hợp lý là dài hơn cúm.

Em dùng phân tích tương quan theo nhiều độ trễ để xem ở độ trễ nào thời tiết liên quan mạnh nhất với số ca bệnh. Nói đơn giản, em thử từ 0 đến 24 tuần và chọn khoảng thời gian có tín hiệu rõ nhất.”

### Kết quả chính

| Bệnh | Yếu tố thời tiết | Độ trễ được chọn |
|---|---|---:|
| Cúm | Nhiệt độ | 3 tuần |
| Cúm | Độ ẩm | 7 tuần |
| Cúm | Bức xạ mặt trời | 7 tuần |
| Cúm | Điểm sương | 2 tuần |
| Sốt xuất huyết | Nhiệt độ | 11 tuần |
| Sốt xuất huyết | Độ ẩm | 1 tuần |
| Sốt xuất huyết | Lượng mưa | 6 tuần |
| Sốt xuất huyết | Điểm sương | 8 tuần |
| Sốt xuất huyết | Bức xạ mặt trời | 16 tuần |

### Cách đọc biểu đồ để chọn độ trễ

Biểu đồ này là phần quan trọng nhất của cell 4.4. Mỗi đường màu là một yếu tố thời tiết. Trục ngang là độ trễ `k`, tức là lấy thời tiết trước bao nhiêu tuần để so với số ca bệnh ở hiện tại. Trục dọc là mức liên hệ giữa thời tiết và số ca bệnh. Giá trị càng xa đường 0 thì tín hiệu càng rõ.

Cách chọn độ trễ:

1. Nhìn từng đường thời tiết riêng.
2. Tìm điểm cao nhất hoặc thấp nhất xa đường 0 nhất.
3. Lấy tuần `k` tại điểm đó làm độ trễ đại diện cho biến thời tiết đó.
4. Nếu đường nằm trên 0, nghĩa là biến đó tăng thì số ca thường tăng theo sau một khoảng trễ. Nếu đường nằm dưới 0, nghĩa là biến đó tăng thì số ca thường giảm, hoặc ngược lại.

Ví dụ với biểu đồ cúm bên trái:

| Đường trên biểu đồ | Cách đọc từ biểu đồ | Độ trễ chọn |
|---|---|---:|
| Nhiệt độ | Đường nhiệt độ nằm dưới 0 và âm mạnh nhất khoảng tuần 3 | 3 tuần |
| Độ ẩm | Đường độ ẩm tăng lên và đạt mức dương rõ nhất khoảng tuần 7 | 7 tuần |
| Bức xạ mặt trời | Đường bức xạ mặt trời âm mạnh nhất khoảng tuần 7 | 7 tuần |
| Điểm sương | Đường điểm sương âm rõ hơn ở khoảng tuần 2, sau đó yếu dần | 2 tuần |

Ý nghĩa khi nói: với cúm, các tín hiệu mạnh thường nằm ở khoảng 2-7 tuần, tức là thời tiết có liên hệ tương đối ngắn hạn với số ca cúm. Điều này hợp lý vì cúm lây trực tiếp giữa người với người.

Ví dụ với biểu đồ sốt xuất huyết bên phải:

| Đường trên biểu đồ | Cách đọc từ biểu đồ | Độ trễ chọn |
|---|---|---:|
| Nhiệt độ | Đường nhiệt độ tăng dần và đạt mức cao nhất khoảng tuần 10-11 | 11 tuần |
| Độ ẩm | Đường độ ẩm cao nhất ở gần tuần 1, sau đó giảm dần | 1 tuần |
| Lượng mưa | Đường lượng mưa đạt vùng cao nhất khoảng tuần 5-6 | 6 tuần |
| Điểm sương | Đường điểm sương cao rõ nhất khoảng tuần 6-8 | 8 tuần |
| Bức xạ mặt trời | Đường bức xạ mặt trời tăng dần và mạnh hơn ở các tuần muộn | 16 tuần |

Ý nghĩa khi nói: với sốt xuất huyết, nhiều tín hiệu mạnh rơi vào khoảng 6-16 tuần. Độ trễ dài hơn cúm vì thời tiết không chỉ ảnh hưởng trực tiếp đến người bệnh, mà còn ảnh hưởng đến môi trường sống và vòng phát triển của muỗi trước khi ca bệnh được ghi nhận.

### Lưu ý khi diễn giải dấu âm/dương

Không phải đường âm là “không quan trọng”. Đường âm vẫn quan trọng nếu nó nằm xa đường 0. Ví dụ ở biểu đồ cúm, nhiệt độ và bức xạ mặt trời có tương quan âm khá rõ. Có thể diễn giải đơn giản là: khi nhiệt độ hoặc ánh nắng cao hơn thì số ca cúm sau đó thường thấp hơn; ngược lại, khi thời tiết lạnh hơn hoặc ít nắng hơn thì cúm dễ tăng hơn.

Vì vậy, khi chọn độ trễ, em không chỉ nhìn đường nào cao nhất theo hướng dương, mà nhìn điểm nào xa đường 0 nhất. Đây là lý do có những biến được chọn ở điểm âm, ví dụ nhiệt độ và bức xạ mặt trời của cúm.

### Ý nghĩa tượng trưng của vài độ trễ

| Ví dụ | Cách hiểu khi thuyết trình |
|---|---|
| Cúm - nhiệt độ trễ 3 tuần | Khi thời tiết lạnh hơn, môi trường có thể thuận lợi hơn cho cúm lây lan. Vì cúm lây trực tiếp giữa người với người nên tín hiệu thường xuất hiện sau vài tuần, không quá dài. |
| Cúm - độ ẩm/bức xạ mặt trời trễ 7 tuần | Độ ẩm và ánh nắng có thể liên quan đến khả năng virus tồn tại trong môi trường và hành vi sinh hoạt trong mùa lạnh. Độ trễ 7 tuần cho thấy đây là tín hiệu mùa vụ rộng hơn, không phải tác động tức thì trong một tuần. |
| Sốt xuất huyết - nhiệt độ trễ 11 tuần | Nhiệt độ ảnh hưởng đến muỗi và quá trình truyền bệnh. Muỗi cần thời gian phát triển, truyền bệnh sang người, người bệnh ủ bệnh rồi ca bệnh mới được ghi nhận, nên độ trễ dài hơn cúm là hợp lý. |
| Sốt xuất huyết - lượng mưa trễ 6 tuần | Mưa có thể tạo nơi nước đọng cho muỗi sinh sản. Sau đó cần thêm vài tuần để muỗi phát triển và làm tăng nguy cơ truyền bệnh. |
| Sốt xuất huyết - bức xạ mặt trời trễ 16 tuần | Đây là tín hiệu dài hạn hơn, có thể phản ánh điều kiện mùa trong năm thay vì tác động trực tiếp ngay lập tức. Khi trình bày, chỉ nên nói đây là yếu tố hỗ trợ mô hình nhận diện bối cảnh mùa vụ. |

### Câu nói ngắn để trả lời giáo viên

“Các độ trễ này được chọn vì em thử nhiều khoảng trễ khác nhau và chọn khoảng có tín hiệu rõ nhất trong dữ liệu. Về mặt thực tế, cúm có độ trễ ngắn hơn vì lây trực tiếp giữa người với người. Sốt xuất huyết có độ trễ dài hơn vì thời tiết ảnh hưởng đến muỗi trước, sau đó mới ảnh hưởng đến số ca bệnh được ghi nhận. Vì vậy bảng này vừa dựa trên dữ liệu, vừa phù hợp với hiểu biết thực tế về hai bệnh.”

### Code chỉ dùng để minh họa

```python
def ccf(x, y, max_lag=24):
    return [
        np.corrcoef(
            x[:-lag] if lag > 0 else x,
            y[lag:] if lag > 0 else y
        )[0, 1]
        for lag in range(max_lag + 1)
    ]
```

### Ý cần nhấn mạnh

Em không kết luận rằng thời tiết là nguyên nhân duy nhất gây dịch. Thời tiết chỉ là một nhóm yếu tố hỗ trợ dự đoán. Mô hình vẫn cần thêm lịch sử số ca, mùa vụ và đặc điểm từng quốc gia.

---

## 6. Cell 4.5 - Xem các quốc gia tiêu biểu

### Giáo viên cần hiểu gì?

Sau khi phân tích toàn bộ dữ liệu, em xem thêm một vài quốc gia cụ thể để kiểm tra kết quả có hợp lý trong thực tế hay không. Đây là bước giúp tránh trường hợp biểu đồ tổng hợp nhìn đúng nhưng từng quốc gia lại bất thường.

Các ví dụ chính trong giai đoạn 2017-2019:

| Quốc gia | Số tuần | Tổng ca cúm | Tổng ca sốt xuất huyết | Điều quan sát được |
|---|---:|---:|---:|---|
| Brazil | 156 | 13,498 | 3,225,010 | Sốt xuất huyết rất lớn, cúm nhỏ hơn nhiều |
| USA | 156 | 750,468 | 1,933 | Cúm rất rõ theo mùa, sốt xuất huyết gần như không đáng kể |
| Việt Nam | 155 | 1,493 | 0 | Dữ liệu giai đoạn này chỉ thể hiện cúm, chưa có dengue trong nguồn đang dùng |

### Cách nói khi trình bày

“Ở cell này, em chọn một vài quốc gia tiêu biểu để kiểm tra lại kết quả phân tích. Em không chỉ nhìn bảng tổng hợp toàn cầu, mà nhìn từng nước để xem mô hình có đang gặp các tình huống rất khác nhau hay không.

Brazil là ví dụ nghiêng mạnh về sốt xuất huyết: trong giai đoạn 2017-2019 có hơn 3.2 triệu ca sốt xuất huyết, trong khi cúm chỉ khoảng 13.5 nghìn ca. Trên biểu đồ, đường sốt xuất huyết cao hơn rất nhiều và có các đợt tăng lớn. Trường hợp này củng cố lý do phải dùng `log1p`, vì nếu dùng số ca gốc thì Brazil có thể chi phối mô hình sốt xuất huyết.

USA là ví dụ ngược lại: cúm rất mạnh, hơn 750 nghìn ca trong 2017-2019, còn sốt xuất huyết rất thấp. Trên biểu đồ, đường cúm có mùa vụ rõ, tăng mạnh vào mùa lạnh và giảm vào mùa ấm. Trường hợp này giúp kiểm tra lại phần mùa vụ của cúm.

Việt Nam trong giai đoạn này có 155 tuần dữ liệu, nhưng tổng dengue bằng 0 trong nguồn dữ liệu đang dùng. Vì vậy khi trình bày em không nên nói Việt Nam là ví dụ có cả cúm và sốt xuất huyết. Cách nói đúng hơn là: Việt Nam là ví dụ để thấy dữ liệu theo từng nước có thể không đầy đủ cho mọi bệnh, nên phần đánh giá cần tách theo từng bệnh và từng nguồn dữ liệu.

Những ví dụ này giúp em kiểm tra rằng các quyết định ở trên không chỉ đúng trên bảng số liệu tổng hợp, mà còn hợp lý khi nhìn vào từng quốc gia cụ thể.”

### Cách đọc biểu đồ case study

Biểu đồ có 3 phần tương ứng Brazil, USA và Việt Nam. Trục trái là số ca bệnh theo thang log, nên các mức chênh lệch lớn vẫn nhìn được trên cùng một biểu đồ. Đường xanh là cúm, đường cam là sốt xuất huyết, đường xám nét đứt là nhiệt độ.

Khi trình bày, nên đọc theo hướng so sánh:

| Quốc gia | Cách đọc trên biểu đồ | Ý nghĩa thuyết trình |
|---|---|---|
| Brazil | Đường cam cao hơn đường xanh rất nhiều | Brazil đại diện cho nơi sốt xuất huyết nổi bật, dễ tạo các giá trị cực lớn |
| USA | Đường xanh tăng giảm theo mùa rất rõ | USA đại diện cho cúm mùa, phù hợp với phân tích mùa vụ ở cell 4.3 |
| Việt Nam | Chỉ có đường cúm, không có đường dengue trong giai đoạn này | Cần cẩn thận với độ phủ dữ liệu; không phải nước nào cũng đủ dữ liệu cho cả hai bệnh |

### Câu nói ngắn nếu giáo viên hỏi

“Cell này dùng 3 quốc gia để kiểm tra lại bằng ví dụ thật. Brazil cho thấy dengue có thể rất lớn, USA cho thấy cúm có mùa vụ rõ, còn Việt Nam cho thấy dữ liệu từng bệnh theo từng nước có thể chưa đầy đủ. Vì vậy các bước trước như dùng `log1p`, kiểm tra mùa vụ và kiểm tra độ phủ dữ liệu là cần thiết.”

---

## 7. Cell 4.6 - Tổng hợp quyết định sau phân tích dữ liệu

### Giáo viên cần hiểu gì?

Cell cuối không tạo thêm phát hiện mới, mà gom lại các quyết định để chuyển sang bước tạo đặc trưng và huấn luyện mô hình.

| Quyết định | Lý do | Dùng ở bước sau |
|---|---|---|
| Dùng `log1p` cho số ca cúm và sốt xuất huyết | Số ca bị lệch mạnh do các đỉnh dịch lớn | Tạo biến mục tiêu |
| Cúm huấn luyện trên 2010-2019 | 2020-2021 bị ảnh hưởng bởi COVID | Huấn luyện mô hình cúm |
| Sốt xuất huyết huấn luyện trên 2015-2019 | Các năm đầu còn ít quốc gia | Huấn luyện mô hình sốt xuất huyết |
| Thêm thông tin bán cầu | Đỉnh mùa cúm lệch khoảng 22 tuần | Tạo đặc trưng mùa vụ |
| Dùng độ trễ thời tiết riêng cho từng bệnh | Cúm và sốt xuất huyết có cơ chế lây khác nhau | Tạo đặc trưng thời tiết |
| Chừa thời gian khởi động trước khi dự đoán | Cần có đủ dữ liệu quá khứ cho các độ trễ | Chuẩn bị tập dữ liệu huấn luyện |

### Cách nói khi trình bày

“Cell cuối cùng là phần tổng hợp. Sau khi phân tích dữ liệu, em chốt lại các quyết định để dùng cho session tiếp theo. Nghĩa là session 4 không đứng riêng lẻ, mà là nền để tạo đặc trưng ở session 5 và huấn luyện mô hình ở session 6.”

---

## 8. Bản nói ngắn gọn khi demo Session 4

“Ở session 4, em phân tích dữ liệu trước khi huấn luyện mô hình. Em không đưa dữ liệu vào mô hình ngay, vì dữ liệu bệnh truyền nhiễm thường có các đợt bùng phát rất lớn, có mùa vụ và có thể bị ảnh hưởng bởi các giai đoạn đặc biệt như COVID.

Đầu tiên, em thấy số ca bệnh bị lệch rất mạnh: đa số tuần có ít ca, nhưng một số tuần có số ca rất cao. Vì vậy em dùng `log1p` để giảm ảnh hưởng của các đỉnh dịch quá lớn.

Tiếp theo, em kiểm tra dữ liệu theo năm và theo quốc gia. Với cúm, giai đoạn 2020-2021 bị ảnh hưởng bởi COVID nên không đại diện cho mùa cúm bình thường. Với sốt xuất huyết, các năm đầu có ít quốc gia hơn, nên em chọn giai đoạn ổn định hơn để huấn luyện.

Sau đó, em kiểm tra mùa vụ. Kết quả cho thấy đỉnh cúm ở Bắc bán cầu và Nam bán cầu lệch nhau khoảng 22 tuần. Điều này vừa xác nhận dữ liệu hợp lý, vừa giải thích vì sao mô hình cần thông tin về tuần trong năm và bán cầu.

Phần quan trọng nhất là chọn độ trễ thời tiết. Thời tiết không nhất thiết ảnh hưởng đến số ca ngay lập tức. Cúm thường có độ trễ ngắn hơn vì lây trực tiếp qua đường hô hấp. Sốt xuất huyết có độ trễ dài hơn vì liên quan đến vòng đời muỗi. Vì vậy em chọn độ trễ dựa trên dữ liệu thay vì tự đặt cố định cho mọi bệnh.

Kết luận của session này là: các quyết định như dùng `log1p`, chọn giai đoạn huấn luyện, thêm mùa vụ, thêm bán cầu và chọn độ trễ thời tiết đều có cơ sở từ dữ liệu. Đây là nền tảng để bước sau tạo đặc trưng và huấn luyện mô hình.”

---

## 9. Nếu giáo viên hỏi nhanh

**Vì sao phải dùng `log1p`?**

Vì số ca bệnh có vài đỉnh dịch rất lớn. `log1p` giúp giảm ảnh hưởng quá mạnh của các giá trị đó, để mô hình học ổn định hơn.

**Vì sao không dùng toàn bộ dữ liệu để huấn luyện?**

Vì không phải giai đoạn nào cũng đại diện tốt. Ví dụ 2020-2021 bị ảnh hưởng bởi COVID nên cúm giảm bất thường; nếu dùng để huấn luyện, mô hình có thể học sai quy luật bình thường.

**Vì sao cần bán cầu?**

Vì mùa cúm ở Bắc bán cầu và Nam bán cầu lệch nhau gần nửa năm. Nếu không có thông tin này, mô hình khó học đúng mùa vụ theo từng quốc gia.

**Vì sao thời tiết phải có độ trễ?**

Vì thời tiết hôm nay có thể ảnh hưởng đến số ca sau vài tuần, không nhất thiết ảnh hưởng ngay. Đặc biệt với sốt xuất huyết, thời tiết còn ảnh hưởng đến muỗi trước khi ca bệnh được ghi nhận.

**Có phải mô hình kết luận thời tiết gây dịch không?**

Không. Thời tiết chỉ là một nhóm yếu tố hỗ trợ dự đoán. Kết quả cần được hiểu là hỗ trợ đánh giá nguy cơ, không phải kết luận y tế tuyệt đối.
