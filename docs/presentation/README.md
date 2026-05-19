# Thuyết trình lại Pipeline ML — EpiWeather KLTN

> **Giọng văn:** Mình đang nói chuyện trực tiếp với bạn — một người chưa biết gì về dự án này.
> Không phải tài liệu kỹ thuật để tự đọc. Đọc như nghe thuyết trình.

---

## Bức tranh toàn cảnh trước khi bắt đầu

Trước khi vào từng session, mình muốn bạn hiểu **bài toán mình đang giải là gì**.

**Câu hỏi:** Nếu cho bạn dữ liệu thời tiết tuần này — nhiệt độ, độ ẩm, lượng mưa — của một quốc gia bất kỳ trên thế giới, bạn có thể **dự báo nguy cơ bùng phát dịch cúm và sốt xuất huyết** vài tuần tới không?

Đó là bài toán của mình. Nghe đơn giản, nhưng có rất nhiều thứ ẩn bên dưới:
- Dữ liệu đến từ **4 nguồn khác nhau**, định dạng khác nhau, độ phủ khác nhau
- **172 quốc gia**, mỗi nước mùa bệnh khác nhau
- Dữ liệu thời tiết ở dạng **lưới địa lý 0.25°**, không phải theo quốc gia
- Mô hình phải vừa **dự báo số ca** vừa **phân loại mức nguy cơ** Low/Medium/High
- Kết quả cuối phải chạy được trên **server thực tế** phục vụ dashboard

---

## Sơ đồ pipeline tổng thể

```
[Nguồn dữ liệu]
  WHO FluNet  ──┐
  OpenDengue  ──┤
  ERA5 ECMWF  ──┤──► [ETL + Feature Engineering] ──► [XGBoost Model]
  WHO Malaria ──┘                                          │
                                                           ▼
                                                   [Predictions 2022]
                                                           │
                                                           ▼
                                               [Risk Classification]
                                               Low / Medium / High
                                                           │
                                                           ▼
                                               [PostgreSQL + FastAPI]
                                                   (Dashboard)
```

---

## Danh sách các session

| File | Session | Nội dung |
|------|---------|----------|
| [session_0_1_setup_load.md](session_0_1_setup_load.md) | 0–1 | Setup môi trường + Load dữ liệu thô |
| [session_2_3_eda.md](session_2_3_eda.md) | 2–3 | Kiểm tra chất lượng dữ liệu + Phân tích mùa vụ |
| [session_4_era5.md](session_4_era5.md) | 4 | Tải và xử lý dữ liệu khí hậu ERA5 |
| [session_5_merge.md](session_5_merge.md) | 5 | Tích hợp 4 nguồn thành master dataset |
| [session_6_lag_analysis.md](session_6_lag_analysis.md) | 6 | Phân tích độ trễ thời tiết → dịch bệnh |
| [session_7_features.md](session_7_features.md) | 7 | Feature engineering |
| [session_8_training.md](session_8_training.md) | 8 | Huấn luyện XGBoost + Optuna |
| [session_9_evaluation.md](session_9_evaluation.md) | 9 | Đánh giá 2022 + Risk classification + Export |
| [hanh_trinh_cai_thien.md](hanh_trinh_cai_thien.md) | — | Hành trình 6 lần cải thiện model |

---

## Kết quả cuối (spoiler)

| Model | R² (2022) | Macro F1 Risk |
|-------|-----------|---------------|
| XGBoost Flu | **0.791** | **0.72** |
| XGBoost Dengue | **0.849** | **0.85** |

Flu R² bắt đầu từ **0.488** — cải thiện lên **0.791** chỉ bằng 1 thay đổi (log transform target). Chi tiết trong [hanh_trinh_cai_thien.md](hanh_trinh_cai_thien.md).
