# CLAUDE.md — Hướng dẫn cho Claude trong project KLTN

## Mô tả project
Xây dựng hệ thống cảnh báo nguy cơ dịch bệnh theo mùa dựa trên dữ liệu y tế
và thời tiết toàn cầu (Graduation Thesis / KLTN).

**Sinh viên:** Phạm Hữu Luân | MSSV: 110122016 | Lớp: DA22TTA
**Notion workspace:** https://www.notion.so/3463e0d79ba581ef8297fed2f51620c4

---

## Ngôn ngữ & Thuật ngữ
- Trả lời bằng **tiếng Việt**
- Giữ nguyên thuật ngữ kỹ thuật bằng tiếng Anh (training, loss, overfitting,
  dataset, pipeline, feature engineering, lag time, KD-tree, etc.)

---

## Quy tắc làm việc với Notebook

### Workflow chuẩn
```
Claude gửi code 1 cell → người dùng chạy → paste output → Claude phân tích
→ gửi ghi chú markdown → chạy cell tiếp theo
```
**KHÔNG** gửi cả session một lượt rồi mới phân tích.

### Cấu trúc notebook
- 1 file `.ipynb` duy nhất cho toàn bộ pipeline ML
- Chia theo SESSION có heading rõ ràng
- Mỗi code cell có **markdown cell ghi chú** ngay bên dưới
- Ghi chú = lý do + quyết định + cảnh báo, KHÔNG chỉ tóm tắt kết quả

### Format ghi chú markdown cell
```
📌 **[x.x]** Đoạn văn tự nhiên giải thích lý do, phân tích, quyết định.
Có thể dùng bullet list nếu cần liệt kê.
Không dùng # heading to như session header.
```

### Khi Colab/Jupyter restart
Chỉ cần chạy lại cell RESTART để load biến — không chạy lại toàn bộ session
nặng (ERA5 process, download...) vì data đã lưu vào file CSV.

---

## Cấu trúc thư mục project

```
KLTN_EpiWeather/
├── .claude/              ← Hướng dẫn cho Claude (file này)
├── data/
│   ├── raw/              ← Data gốc chưa xử lý
│   │   ├── VIW_FNT.csv
│   │   ├── National_extract_V1_3.csv
│   │   └── era5_raw/     ← ERA5 NetCDF files (2010-2019)
│   └── processed/        ← Data đã xử lý, sẵn sàng dùng
│       ├── era5_weekly_2010_2019_final.csv
│       └── master_weekly_2010_2019.csv
├── notebooks/
│   └── KLTN_EpiWeather_ML.ipynb
├── scripts/
│   ├── config.py         ← Đường dẫn tập trung
│   └── process_era5.py   ← Chạy 1 lần để tạo era5_weekly.csv
└── requirements.txt
```

---

## Quy tắc viết code

### Python style
- Dùng `pathlib.Path` thay vì `os.path.join`
- Mỗi function có docstring ngắn gọn
- Constants viết HOA ở đầu file hoặc trong `config.py`
- Tên biến rõ ràng: `flu_train` thay vì `df1`

### Idempotent — chạy lại không bị lỗi
```python
# Luôn check file tồn tại trước khi process
if OUTPUT_FILE.exists():
    print(f'✅ File đã có: {OUTPUT_FILE.name} — bỏ qua')
    df = pd.read_csv(OUTPUT_FILE)
else:
    # process...
    df.to_csv(OUTPUT_FILE, index=False)
```

### Session independence
Mỗi session đọc input từ CSV, ghi output ra CSV — không phụ thuộc
vào biến của session trước.

---

## Quy tắc cập nhật Notion

| Tình huống | Làm gì |
|---|---|
| Phân tích output từng cell | Gửi trong chat |
| Ghi chú markdown cho cell | Gửi trong chat (người dùng tự thêm vào notebook) |
| Quyết định quan trọng | Update Notion |
| Session summary cuối ngày | Tạo trang mới trong Notion |
| Code đã confirm hoàn chỉnh | Update Notion Master Notebook |
| Đề cương thay đổi | Update trang Đề cương trên Notion |

**Notion pages quan trọng:**
- Master Notebook: `3463e0d7-9ba5-816f-9475-d1bfb6e94a5f`
- Đề cương: `3463e0d7-9ba5-8140-8fda-c2f646ec28f0`
- Pipeline Tasks DB: `c7aa3ba9-3ef9-44e2-8935-66b49796f295`

---

## Decisions đã chốt (không thay đổi trừ khi có lý do rõ)

| Quyết định | Lý do |
|---|---|
| Target: `INF_A + INF_B` (không dùng `INF_ALL`) | INF_ALL missing 44% |
| `fillna(0)` cho INF_A, INF_B | Missing = không báo cáo, không phải = 0 ca |
| Train: 2010–2019 | Coverage ổn định, tránh COVID |
| Validation: 2022 | Test generalization post-COVID |
| Exclude: 2020–2021 | COVID disruption — pattern sai |
| `log1p` cho Dengue | Brazil dominated 70% tổng ca |
| Bỏ PARAINFLUENZA | Missing 85.5% |
| Bỏ RSV_PROCESSED | Khác đơn vị với RSV, corr=0.729 |
| UK: X09–X12 gộp | WHO không có mã GBR tổng hợp |
| ECDC: chỉ dùng validation+dashboard | Chỉ có từ 2021 |
| ERA5: 158/172 countries (92%) | KD-tree centroid limitation |
| ERA5: 17 biến | Đủ theo lý thuyết hô hấp + vector-borne |
| Lag Influenza: 1–3 tuần | Incubation + reporting delay |
| Lag Dengue: 6–14 tuần | Mosquito breeding cycle |

---

## Tech stack

| Tầng | Lựa chọn |
|---|---|
| Backend | FastAPI (Python) |
| ML | XGBoost + Prophet (baseline) |
| Database | PostgreSQL |
| Frontend | React + Tailwind + Leaflet.js |
| Deploy | Docker Compose |
| Weather historical | ERA5 (ECMWF) — 17 biến |
| Weather realtime | OpenWeatherMap API |
