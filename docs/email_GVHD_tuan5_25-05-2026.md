**Tiêu đề:** [KLTN-110122016] Báo cáo tiến độ tuần 5 — Phạm Hữu Luân

**Đính kèm:**
- `epiweather_pipeline_diagram.png` (sơ đồ pipeline)
- `database_schema_v2.md` (mô tả CSDL)
- `2026-05-25_session_summary.md` (chi tiết những việc đã làm)

---

Kính gửi Cô,

Em là Luân — sinh viên KLTN Cô đang hướng dẫn. Em xin báo cáo tiến độ tuần 5 (19/05 → 25/05) ạ.

**1) Kết quả mô hình (multi-horizon 4 tuần)**
- Em đã hoàn thành 4 model riêng cho h=1..4 tuần. Kết quả đều vượt benchmark Lowe et al. 2014 (Lancet ID): flu LightGBM h=1 R²=0.866; dengue Random Forest h=1 R²=0.929. Các horizon h=2..4 giảm dần như kỳ vọng nhưng vẫn vượt baseline.
- Validation hold-out 2022 (post-COVID, unseen) cho flu R²≈0.80 và dengue R²≈0.87, cho thấy model generalize được.

**2) Quy trình dự báo sau khi train (pipeline inference)**
- Sau khi có model .pkl, hệ thống tạo feature snapshot theo tuần, sau đó chạy batch predict để tạo dự báo h=1..4 cho từng quốc gia.
- Kết quả dự báo được lưu sẵn để truy vấn nhanh, phù hợp với mô hình phục vụ dashboard theo tuần.
- Phạm vi dữ liệu đang dùng để dự báo:
	- Flu: historical 2010–2019, và realtime/nowcast đến 2026-W21 (WHO FluNet).
	- Dengue: historical 2015–2019, và nowcast đến 2023-W36 (OpenDengue v1.3 batch).

**3) Cách áp dụng lên giao diện**
- Trang bản đồ hiển thị mức nguy cơ Low/Medium/High theo từng quốc gia của tuần đang chọn.
- Trang chi tiết quốc gia hiển thị forecast 4 tuần kế tiếp (h=1..4) và trend lịch sử 52 tuần.
- Analytics hiển thị bảng R² theo horizon và feature importance để giải thích mô hình.

**4) Tài liệu đính kèm**
Em đã đính kèm sơ đồ pipeline và schema CSDL để Cô dễ hình dung luồng tổng thể. Các chi tiết kỹ thuật nhỏ (UI/FE/BE) em xin không liệt kê trong email này để gọn.

**5) Trạng thái MLOps hiện tại**
- Pipeline đã chạy được theo lịch: sync dữ liệu → build features → batch predict; kết quả ghi nhận qua bảng `pipeline_runs` để có audit trail.
- Các bước DQ (data quality checks) và dashboard admin hiển thị lịch sử run là phần đang chuẩn bị cho tuần 6.

**6) Kế hoạch tuần 6**
Hoàn thiện phần trình bày và chuẩn bị demo end-to-end theo đúng luồng dự báo nêu trên.

**7) Lịch demo đề xuất**
Em dự kiến demo lần 1 cho Cô vào **thứ Tư 28/05** hoặc **thứ Sáu 30/05**, khoảng 30 phút end-to-end + Q&A. Cô cho em biết lịch nào tiện cho Cô ạ.

Em cảm ơn Cô rất nhiều. Mong nhận được phản hồi của Cô.

Trân trọng,
Phạm Hữu Luân
MSSV 110122016 — Lớp DA22TTA
Khoa Kỹ thuật và Công nghệ — Trường Đại học Trà Vinh
Email: hulung186@gmail.com
