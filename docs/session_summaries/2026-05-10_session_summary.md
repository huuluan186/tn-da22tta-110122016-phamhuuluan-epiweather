# Session Summary — 10/05/2026 — Thiết kế DB + Load data + Báo cáo Chương 3

## Tóm tắt nhanh

**Trạng thái cuối ngày:** Schema PostgreSQL 5 tầng thiết kế xong và chạy được. DB `kltn_epiweather` đã load đầy đủ dữ liệu thực từ Colab. Markdown note [9.4b] đã thêm vào notebook. Báo cáo Chương 3 đã được viết hoàn chỉnh theo đúng cấu trúc đề cương và văn phong học thuật.

**Kết quả nổi bật:**
- **Schema PostgreSQL 5 tầng** — catalog-driven, JSONB, partitioning, MLOps native — hoàn chỉnh
- **DB load thành công:** 63,873 rows disease_cases + 63,873 predictions, model_evaluations với metrics thực (Flu R²=0.7906, Dengue R²=0.8494)
- **Chương 3 hoàn chỉnh:** 7 mục, 3 hình, 4 bảng, văn xuôi học thuật, trích dẫn [1]–[7]

---

## Bối cảnh

Tiếp nối session 09/05 (SESSION 9 validation xong, cell [9.4b] export metrics JSON đã chạy trên Colab). Hôm nay: thiết kế và tạo DB → viết ETL load_db.py → fix lỗi → download model_metrics.json thực → re-run → viết báo cáo chương 3.

---

## Việc đã làm

### 1. Thiết kế schema PostgreSQL 5 tầng ✅

**Vấn đề ban đầu:** Schema cũ có hardcode `CHECK (disease IN ('flu','dengue'))`, 17 cột riêng cho ERA5, không có versioning model. Cần redesign để catalog-driven và production-ready.

**Kiến trúc 5 tầng được thiết kế:**

| Tầng | Bảng chính | Đặc điểm |
|---|---|---|
| 0 — Địa lý | `countries` | 149 quốc gia, lưu sẵn `who_region_enc` |
| 1 — Catalog | `diseases`, `data_sources`, `weather_variables` | Thêm bệnh mới = INSERT 1 row |
| 2 — Observations | `disease_cases`, `weather_observations` | Partition theo `iso_year`; JSONB cho ERA5 |
| 3 — ML Pipeline | `model_versions`, `model_evaluations`, `risk_thresholds`, `predictions` | Versioning + audit đầy đủ |
| 4 — MLOps | `pipeline_runs`, `data_quality_checks`, `api_request_logs` | Production monitoring |
| MV | `mv_latest_predictions` | Materialized view cho dashboard |

**Quyết định thiết kế quan trọng:**
- JSONB cho `weather_observations.data` — 17 biến ERA5 trong 1 cột, thêm biến mới chỉ cần INSERT
- Partition theo `iso_year` cho `disease_cases`, `weather_observations`, `predictions`
- `api_request_logs` partition theo `requested_at` (yêu cầu đặc biệt: partition key phải nằm trong PRIMARY KEY)

**Files tạo:**
- `docs/database_schema_v2.md` — tài liệu schema đầy đủ với DDL, ERD, design notes
- `scripts/db_init.sql` — DDL hoàn chỉnh với seed data (2 diseases, 5 data_sources, 18 weather_variables)

**Lỗi gặp phải và cách fix:**
- `api_request_logs PRIMARY KEY (id)` → fix thành `PRIMARY KEY (id, requested_at)` vì PostgreSQL yêu cầu partition key phải trong PK

---

### 2. Viết load_db.py — loại bỏ toàn bộ hardcode ✅

**Yêu cầu:** Không hardcode bất kỳ giá trị nào — train period, val year, model paths, algorithm name, metrics — tất cả phải đọc từ file.

**Giải pháp `load_configs()`:**
```python
def load_configs():
    """Single source of truth: feature_list.json + model_metrics.json."""
    with open(FEATURE_JSON) as f:
        features = json.load(f)
    with open(METRICS_JSON) as f:
        metrics = json.load(f)
    train_start, train_end = map(int, features["meta"]["train_period"].split("-"))
    val_year = int(features["meta"]["val_year"])
    model_paths = {
        disease: MODELS_DIR / cfg["artifact"]
        for disease, cfg in metrics.items()
    }
    return features, metrics, train_start, train_end, val_year, model_paths
```

**Các nguồn dữ liệu:**
- `train_period`, `val_year` ← `feature_list.json["meta"]`
- `algorithm` ← `type(model).__name__` (đọc từ pkl)
- `version`, `description`, metrics ← `model_metrics.json`
- `model paths` ← `model_metrics.json["artifact"]`

**Lỗi gặp phải và cách fix:**

| Lỗi | Nguyên nhân | Fix |
|---|---|---|
| `column "is_flu_country" does not exist` | Schema v2 không có cột này | Xóa khỏi INSERT countries |
| `UnicodeEncodeError` (emoji ❌✅) | Windows cp1252 | `sys.stdout.reconfigure(encoding="utf-8", errors="replace")` |
| `schema "np" does not exist` | psycopg2 không hiểu numpy float64 | Đăng ký adapter cho np.int64, np.float64, np.bool_ |
| `MODEL_FLU undefined` | Sau refactor xóa hardcoded paths | Derive từ `model_metrics.json["artifact"]` |
| `password authentication failed` | Sai password PostgreSQL | User cung cấp đúng password "111111111" |

---

### 3. Chạy db_init.sql + load_db.py lần đầu ✅

**Quy trình:**
1. Tạo DB: `CREATE DATABASE kltn_epiweather;`
2. Chạy `scripts/db_init.sql` — tạo toàn bộ schema, partition, seed catalog
3. Download các file cần thiết từ Google Drive về local:
   - `models/xgb_flu_final.pkl` (1.4 MB)
   - `models/xgb_dengue_final.pkl` (1.2 MB)
   - `models/feature_list.json`, `models/flu_risk_thresholds.csv`
   - `dataset/processed/features_flu_2010_2019.csv` (15 MB, 70,056 × 17 cols)
   - `dataset/processed/features_dengue_2010_2019.csv` (1.6 MB, 6,313 × 19 cols)
4. Chạy `python scripts/load_db.py`

---

### 4. Thêm cell [9.4b] vào notebook + re-run với metrics thực ✅

**Cell [9.4b] (đã thêm vào notebook session hôm qua, chạy hôm nay):** Export toàn bộ evaluation metrics từ validation set 2022 ra `model_metrics.json` — single source of truth cho load_db.py. Thay vì hardcode từng giá trị, load_db.py đọc file này trực tiếp.

**Output Colab:**
```
Saved model_metrics.json -> /content/drive/MyDrive/KLTN/outputs/model_metrics.json
Flu R²=0.7906 | Macro F1=0.7161
Dengue R²=0.8494 | Macro F1=0.8476
```

**Markdown note [9.4b]** insert tại idx 149 (giữa code cell [9.4b] và code cell [9.5]).

**Re-run load_db.py** sau khi download model_metrics.json thực → model_evaluations được load với số liệu chính xác.

**Verify model_evaluations:**

| Disease | eval_set | R² | MAE | Macro F1 | N |
|---|---|---|---|---|---|
| flu | val_2022 | 0.7906 | 0.5395 | 0.7161 | 11,446 |
| dengue | val_2022 | 0.8494 | 0.4907 | 0.8476 | 1,537 |

**DB row counts cuối ngày:**

| Bảng | Rows |
|---|---|
| countries | 149 |
| disease_cases | 63,873 |
| predictions | 63,873 |
| model_versions | 2 |
| model_evaluations | 2 |
| risk_thresholds | 164 |
| feature_configs | 28 |

---

### 5. Viết báo cáo Chương 3 ✅

**File:** `docs/chapter3_system_design.md`

**Cấu trúc theo đề cương:**

| Mục | Tiêu đề | Trạng thái |
|---|---|---|
| 3.1 | Kiến trúc tổng thể hệ thống | ✅ Hoàn chỉnh |
| 3.2 | Cài đặt môi trường và công cụ | ✅ Hoàn chỉnh |
| 3.3 | Thiết kế pipeline ETL | ✅ Hoàn chỉnh |
| 3.4 | Thiết kế cơ sở dữ liệu (ERD) | ✅ Hoàn chỉnh |
| 3.5 | Thiết kế mô hình học máy | ✅ Hoàn chỉnh |
| 3.6 | Thiết kế Backend API | ✅ Hoàn chỉnh (thiết kế, chưa build) |
| 3.7 | Thiết kế giao diện Frontend | ✅ Hoàn chỉnh (wireframe, chưa build) |

**Điểm khác biệt so với phiên bản cũ:**
- Văn xuôi học thuật liên kết — đúng phong cách chương 1, 2 (không dùng bullet list nặng)
- Hình minh họa (Hình 3.1–3.5) và bảng (Bảng 3.1–3.4) đánh số đúng chuẩn báo cáo
- Trích dẫn [1]–[7] nhất quán với chương 1, 2
- Gắn lý thuyết với số liệu thực: log1p R² 0.488→0.791, Medium F1 0.06→0.52
- Công thức XGBoost và Prophet
- Chú thích rõ: phần 3.6–3.7 là thiết kế, không phải kết quả — đúng vì Chương 3 là "Phân tích & Thiết kế"

**Về kế hoạch thực hiện:** Tuần 3 (4/5–10/5) theo đề cương viết Chương 3 phần Kiến trúc, ETL, ERD — đúng tiến độ. Backend API (tuần 6) và Frontend (tuần 7) được mô tả ở dạng thiết kế. **Không cần điều chỉnh kế hoạch.**

---

## Files đã thay đổi

| File | Thay đổi |
|---|---|
| `docs/database_schema_v2.md` | Tạo mới — tài liệu schema 5 tầng đầy đủ |
| `scripts/db_init.sql` | Tạo mới — DDL hoàn chỉnh, seed catalog |
| `scripts/load_db.py` | Tạo mới — ETL loader, zero hardcode, numpy adapters |
| `models/model_metrics.json` | Thay bằng file thực từ Colab |
| `models/xgb_flu_final.pkl` | Download từ Drive (1.4 MB) |
| `models/xgb_dengue_final.pkl` | Download từ Drive (1.2 MB) |
| `models/feature_list.json` | Download từ Drive |
| `models/flu_risk_thresholds.csv` | Download từ Drive |
| `dataset/processed/features_flu_2010_2019.csv` | Download từ Drive (15 MB) |
| `dataset/processed/features_dengue_2010_2019.csv` | Download từ Drive (1.6 MB) |
| `.gitignore` | Cập nhật: track pkl models + feature CSVs, ignore ERA5 raw |
| `KLTN_EpiWeather_ML_Colab.ipynb` | Thêm markdown note [9.4b] tại idx 149 |
| `docs/chapter3_system_design.md` | Viết lại hoàn toàn — 7 mục, văn phong báo cáo KLTN |

---

## Còn lại / Chưa làm

- [ ] **FastAPI backend** — build /predict, /risk-map, /countries endpoints (tuần 6)
- [ ] **React frontend** — bản đồ Leaflet choropleth + dashboard (tuần 7)
- [ ] **Docker Compose** — đóng gói toàn hệ thống (tuần 8)
- [ ] **Chương 4** — Kết quả thực nghiệm (tuần 8–9)
- [ ] **Chương 5** — Kết luận (tuần 8–9)

---

## Ghi nhớ cho buổi sau

- **DB đã sẵn sàng:** mọi bảng đều có dữ liệu thực, có thể bắt đầu FastAPI trực tiếp
- **Tuần 4 (11/5–17/5) theo đề cương:** EDA + CCF + feature engineering — đã làm xong rồi. Có thể dành tuần 4 bắt đầu FastAPI sớm hơn kế hoạch 1–2 tuần
- **Chương 3 phần 3.6, 3.7 cần bổ sung** sau khi build xong Backend và Frontend (thêm screenshot, kết quả API test)
- **Chú ý:** flu sMAPE=72.98% cao nhưng bình thường — nhiều tuần có giá trị thực gần 0, sMAPE không ổn định với giá trị nhỏ. Cần giải thích rõ trong Chương 4
