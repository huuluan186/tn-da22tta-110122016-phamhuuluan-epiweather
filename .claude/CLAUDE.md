# CLAUDE.md — Hướng dẫn cho Claude trong project KLTN

## Mô tả project
Xây dựng hệ thống cảnh báo nguy cơ dịch bệnh theo mùa dựa trên dữ liệu y tế
và thời tiết toàn cầu (Graduation Thesis / KLTN).

**Sinh viên:** Phạm Hữu Luân | MSSV: 110122016 | Lớp: DA22TTA
**Notion workspace:** https://www.notion.so/3463e0d79ba581ef8297fed2f51620c4

### Mô tả gốc từ khoa (input authoritative — KHÔNG được bỏ qua)

Hệ thống cảnh báo nguy cơ dịch bệnh từ dữ liệu y tế và thời tiết toàn cầu cần có các chức năng:

1. **Thu thập dữ liệu** từ các API (OpenWeatherMap, WHO GHO, hoặc nguồn khác)
2. **Phân tích tương quan** giữa sự xuất hiện bệnh truyền nhiễm theo mùa/điều kiện thời tiết
3. **Đề xuất mô hình ML** (SARIMA/Prophet/LSTM/RF/XGBoost/…) cho **kết quả dự báo dịch bệnh có thể diễn ra theo từng giai đoạn/mùa/tháng**
4. **Báo cáo + dashboard** với biểu đồ thống kê, phân tích, **cảnh báo mức độ** — HOẶC bản đồ cảnh báo dịch bệnh toàn cầu (Global Epidemic Warning Map)
5. **Tra cứu chi tiết** thông tin phân tích chuyên sâu theo từng loại bệnh

**Tech stack gợi ý:** Python/FastAPI, React/Leaflet/Tailwind/Recharts, PostgreSQL/MongoDB.

**Parse semantic mô tả gốc** — bài toán bản chất là:
- "khả năng diễn ra" = predict case_count (regression) + probability output từ classifier
- "cảnh báo mức độ" = Low/Medium/High từ endemic channel thresholds
- "theo giai đoạn/mùa/tháng" = weekly grain, seasonal features
- Bài toán: Supervised Learning — Time-Series Regression (primary) + Ordinal Classification (derived)
- Cần CẢ regression metrics (RMSE/MAE/R²) VÀ classification metrics (Precision/Recall/F1)

### Hướng giải quyết — chỉnh lại 16/05/2026

**Approach: Hybrid — Regression + Classification, so sánh**

Đề tài yêu cầu cả "dự báo dịch bệnh có thể diễn ra" (regression, số ca)
lẫn "cảnh báo mức độ" (classification, Low/Med/High).
Làm cả hai, so sánh = đóng góp khoa học cho báo cáo.

Nhánh A — Regression:
  XGBoost / LightGBM / Random Forest Regressor
  Target: log1p(case_count)
  Metrics: RMSE, MAE, R²
  Dùng cho: dashboard biểu đồ trend
  Risk level: apply endemic channel threshold SAU predict

Nhánh B — Classification:
  XGBClassifier (multi:softprob, num_class=3)
  Target: endemic channel label per (iso3, week_of_year)
    Low = cases < baseline
    Medium = baseline <= cases < baseline + 2σ
    High = cases >= baseline + 2σ
  Metrics: macro-F1, AUC OvR, Precision/Recall per class
  Dùng cho: bản đồ cảnh báo Leaflet choropleth

Baseline: Prophet (seasonality benchmark) + Naive same-week-last-year

Optuna hyperparameter tuning: chạy sau initial training,
chỉ tune model tốt nhất từ bảng so sánh ban đầu.

Bảng so sánh BẮT BUỘC trong SESSION cuối:
- Regression: Prophet vs Naive vs XGBoost vs LightGBM vs RF → RMSE, MAE, R²
- Classification: XGBClassifier vs Regressor+threshold → macro-F1, AUC
- Quyết định model cho production dựa trên bảng này

References: Bortman 1999, Lowe et al. 2016, WHO EWARS, CDC FluSight

## Tài liệu tham khảo nội bộ

> **ĐỌC TRƯỚC KHI LÀM BẤT KỲ VIỆC GÌ:**
> - [`.claude/guides/ML_EXPERT_MINDSET.md`](.claude/guides/ML_EXPERT_MINDSET.md) — tư duy ML engineer production, framework ra quyết định
> - [`.claude/guides/NOTEBOOK_GUIDE.md`](.claude/guides/NOTEBOOK_GUIDE.md) — quy tắc viết notebook Colab
> - [`.claude/guides/ml_data_workflow.md`](.claude/guides/ml_data_workflow.md) — quy trình chuẩn data → model

---

## Quy tắc viết commit message

Tuân theo **Conventional Commits**: `<type>(<scope>): <short description>`

Format: 1 câu mô tả đầy đủ ý nghĩa. **Không dùng** dạng list bullet, không dùng nhiều dòng mô tả.

### Types

| Type | Khi dùng |
|---|---|
| `feat` | Tính năng mới |
| `fix` | Sửa bug |
| `docs` | Chỉ thay đổi tài liệu |
| `style` | Code style (formatting, không đổi logic) |
| `refactor` | Tái cấu trúc, không fix bug cũng không thêm feature |
| `perf` | Cải thiện hiệu năng |
| `test` | Thêm hoặc cập nhật tests |
| `chore` | Build process, dependencies, tooling |
| `ci` | CI/CD configuration |

### Scopes

| Scope | Phạm vi |
|---|---|
| `api` | Backend routers, services |
| `db` | Models, migrations |
| `worker` | Background job processing |
| `ai` | AI providers, embedding, LLM |
| `mcp` | MCP server integration |
| `ui` | Frontend components, pages |
| `auth` | Authentication, RBAC |
| `config` | Settings, environment |
| `deps` | Dependency updates |

### Ví dụ đúng

```
feat(api): add bulk delete endpoint for sources
fix(worker): handle empty PDF files during ingestion
docs: update HOW_TO_RUN with Neo4j setup
refactor(ui): extract color picker into reusable component
chore(deps): bump fastapi to 0.115.0
feat: add dataset_description.md with flu and dengue feature column definitions
docs: correct ERA5 coverage stats and fix master dataset shape in session4_5 documentation
```

Scope là optional — bỏ qua nếu thay đổi không thuộc scope cụ thể nào.

---

## Ngôn ngữ & Thuật ngữ
- Trả lời bằng **tiếng Việt**
- Giữ nguyên thuật ngữ kỹ thuật bằng tiếng Anh (training, loss, overfitting,
  dataset, pipeline, feature engineering, lag time, KD-tree, etc.)
- **BẮT BUỘC: Tiếng Việt phải có dấu đầy đủ** — trong notebook cells (markdown,
  code comments, print/string), summary blocks, chat replies, mọi document.
  - SAI: `KET QUA SESSION`, `Van de con lai`, `Generalize XUAT SAC`, `Khong bi anh huong`
  - ĐÚNG: `KẾT QUẢ SESSION`, `Vấn đề còn lại`, `Generalize xuất sắc`, `Không bị ảnh hưởng`
  - Áp dụng cho cả `print(f'KET QUA...')` trong code Python — KHÔNG được viết telex/không dấu
  - Báo cáo tốt nghiệp + slide GVHD yêu cầu chính tả chuẩn — đây không phải optional
  - Riêng tên file/biến/path vẫn giữ ASCII không dấu (Python convention)

---

## Quy tắc làm việc với Notebook

### Workflow chuẩn
```
Claude gửi code 1 cell → người dùng chạy → paste output → Claude PHÂN TÍCH RÕ output (giảng giải từng con số, biểu đồ, ý nghĩa thực tế)
→ gửi ghi chú markdown để user paste → chạy cell tiếp theo
```
**KHÔNG** gửi cả session một lượt rồi mới phân tích.
**KHÔNG** chỉ tự hiểu rồi điều khiển user chạy tiếp — phải giảng cho user hiểu trước.

### Quy tắc phân tích output cell (BẮT BUỘC)
Sau khi user paste output, Claude PHẢI:
1. Đọc từng con số quan trọng — nêu rõ giá trị, không generalize
2. Giải thích ý nghĩa thực tế — số này nói lên điều gì?
3. So sánh với kỳ vọng hoặc baseline — tốt/xấu/bình thường?
4. Đọc biểu đồ kỹ nếu có — mô tả pattern, peak, anomaly
5. Cảnh báo bất thường nếu có — outlier, data leak, bug?
6. Quyết định bước tiếp theo — output này dẫn đến hành động gì?
7. Ghi chú kết quả tốt nhất hiện tại — để so sánh với cải thiện sau

Viết như đang thuyết trình cho người mới:
không giả định người đọc biết context, giải thích đủ nhưng không dài dòng.
Tuyệt đối tránh: "OK output đẹp, chạy cell tiếp theo nhé"

### Quy tắc EDA + check data (BẮT BUỘC làm kĩ)
Không bỏ qua, không rút gọn. Mỗi dataset mới phải đi qua:
1. **Schema check**: dtypes, shape, columns, sample rows
2. **Missing analysis**: % missing per column, pattern (MCAR/MAR/MNAR), missing theo thời gian/quốc gia
3. **Distribution**: histogram, boxplot, log-scale nếu skewed; per-country, per-year, per-season
4. **Outlier**: z-score, IQR, domain-based threshold; visualize và quyết định xử lý
5. **Time coverage**: start/end date per (country, disease); gap detection
6. **Cross-validation logic**: train/val/test split không leakage; walk-forward CV scheme
7. **Sanity check**: tổng số ca có hợp lý không? Top countries có đúng dịch tễ học không? Mùa peak có khớp lý thuyết không?
8. **Label quality check** (cho classification): class balance per country, baseline có ý nghĩa, threshold reasonable

### Quy tắc train nhiều model + so sánh (BẮT BUỘC)
Không train 1 model duy nhất. Phải có ít nhất:
- Baseline naive: predict same-week-last-year
- Statistical baseline: Prophet
- Tree-based regression: XGBoost Regressor, LightGBM Regressor, Random Forest Regressor
- Tree-based classification: XGBClassifier (endemic channel labels)

Mỗi model: cùng feature set, cùng CV scheme, cùng metric.

Bảng so sánh BẮT BUỘC:
- Regression: RMSE, MAE, R², inference time per model
- Classification: macro-F1, AUC OvR, P/R per class
- Cross-compare: Regressor+threshold vs Classifier trực tiếp
- Optuna tuning chỉ cho top 1-2 model, ghi rõ before/after tuning

Quyết định model production dựa trên bảng này.

### Cấu trúc notebook
- 1 file `.ipynb` duy nhất cho toàn bộ pipeline ML
- Chia theo SESSION có heading rõ ràng
- Mỗi code cell có **markdown cell ghi chú** ngay bên dưới
- Ghi chú = lý do + quyết định + cảnh báo, KHÔNG chỉ tóm tắt kết quả

### Format ghi chú markdown cell

Viết như đang thuyết trình cho 1 người mới, không phải viết văn nhưng phải:
- Giải thích rõ đang làm gì, vì sao làm bước này
- Kết quả cụ thể (con số, không nói chung chung)
- Phân tích ý nghĩa: con số này tốt/xấu/bình thường so với gì?
- Ảnh hưởng đến quyết định sau: dựa vào kết quả này thì bước tiếp làm gì?
- Nếu có biểu đồ: đọc kỹ biểu đồ, mô tả pattern thấy được, giải thích ý nghĩa
- Không vẽ biểu đồ "cho có" — mỗi plot phải phục vụ 1 phân tích cụ thể

Format chuẩn:
```
**[x.x] Tên bước**

Mô tả ngắn gọn mục đích. Kết quả chính:

- Flu coverage: 189 quốc gia, 2010-2019 (trung bình 165 nước/năm báo cáo)
- Missing rate weather: 8.2% — dưới ngưỡng 20%, chấp nhận được
- Phát hiện: Brazil chiếm 71% tổng ca dengue toàn cầu — cần log1p transform

Quyết định: dùng log1p cho dengue target, giữ nguyên flu (phân bố đỡ skewed hơn).
Bước tiếp: merge disease + weather theo iso3 x ISO_WEEK.
```

KHÔNG dùng emoji hay icon. Không dùng heading # (nhỏ hơn session header).
Giữ format sạch, dễ scan, đúng chuẩn Jupyter notebook chuyên nghiệp.

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

## Quy tắc tổng kết cuối buổi (BẮT BUỘC)

**Khi nào trigger:**
- Người dùng nói "tổng kết", "kết thúc buổi", "ghi lại session"
- Trước khi context window gần đầy (~85% capacity, hoặc khi compact warning xuất hiện)
- Sau khi hoàn thành một milestone lớn (ví dụ: chạy xong toàn bộ session 5–8)

**Quy trình 2 bước:**

1. **Tạo file MD local** tại `docs/session_summaries/YYYY-MM-DD_session_summary.md`:
   - Mục tiêu của buổi
   - Bối cảnh / vấn đề đang giải quyết
   - Kết quả từng SESSION đã chạy (bảng + bullets)
   - Phát hiện quan trọng (nổi bật bằng **bold**)
   - Files đã thay đổi (table)
   - Còn lại / chưa làm (bullets có status)
   - Những điều cần ghi nhớ cho báo cáo

2. **Upload Notion** ở workspace root level (KHÔNG phải sub-page của Master Notebook):
   - Title: `Session Summary DD/MM/YYYY — <chủ đề chính>`
   - Icon: 📝
   - Dùng `mcp__claude_ai_Notion__notion-create-pages`
   - Xem các mẫu summary đã có trên Notion làm template

**Format chuẩn:** xem `docs/session_summaries/2026-05-05_session_summary.md` làm template.

**KHÔNG được:**
- Bỏ qua bước này dù người dùng "có vẻ vội"
- Tổng kết ngắn trong chat thay vì tạo file (file giữ nguyên context cho session sau, chat thì mất)
- Quên upload Notion (file local không truy cập được từ thiết bị khác)

---

## Decisions đã chốt (không thay đổi trừ khi có lý do rõ)

### Data decisions (giữ nguyên)
| Quyết định | Lý do |
|---|---|
| Target: `INF_A + INF_B` (không dùng `INF_ALL`) | INF_ALL missing 44% |
| `fillna(0)` cho INF_A, INF_B | Missing = không báo cáo, không phải = 0 ca |
| Train: 2010–2019 | Coverage ổn định, tránh COVID |
| Validation: 2022 | Test generalization post-COVID |
| Exclude: 2020–2021 | NPI + reporting bias làm flu giảm ~99% artificially (KHÔNG phải do coverage giảm — 2020-2021 vẫn 166-167 nước, ngang 2019) |
| Bỏ PARAINFLUENZA | Missing 85.5% |
| Bỏ RSV_PROCESSED | Khác đơn vị với RSV, corr=0.729 |
| UK: X09–X12 gộp | WHO không có mã GBR tổng hợp |
| ECDC: chỉ dùng validation+dashboard | Chỉ có từ 2021 |
| ERA5: 197 countries (flu) / 41 countries (dengue) | KD-tree centroid mapping từ lưới 721×1440 |
| ERA5: 17 biến | Đủ theo lý thuyết hô hấp + vector-borne |
| Lag Influenza: CCF-optimal {temp:4w, hum:8w, sol:8w, dew:2w} | Cross-correlation SESSION 6 |
| Lag Dengue: CCF-optimal {temp:0, hum:2w, sol:4w, prec:0} | Mosquito breeding cycle |
| ERA5 2022 cho validation (thay Open-Meteo) | Nhất quán với training pipeline |
| Walk-forward CV (val_year 2014–2019) | Standard time-series CV, tránh data leakage |

### ML decisions (chỉnh lại 16/05/2026 — hybrid approach)
| Quyết định | Lý do |
|---|---|
| Task: Regression + Classification hybrid | So sánh cả hai, đóng góp cho báo cáo |
| Label regression: log1p(case_count) | Long-tail, log compress cải thiện R² |
| Label classification: Endemic channel per (iso3, week_of_year) | Bortman 1999, WHO EWARS |
| Models regression: XGBoost, LightGBM, Random Forest, Prophet | So sánh 4 models, chọn tốt nhất |
| Model classification: XGBClassifier (multi:softprob) | Probability output, optimize F1 |
| Optuna tuning: sau initial comparison | Chỉ tune top model, 50-100 trials |
| Transform: log1p cho flu + dengue | Giữ nguyên, đã chứng minh hiệu quả |
| Metrics regression: RMSE, MAE, R² | Chuẩn time-series forecasting |
| Metrics classification: macro-F1, AUC OvR, P/R per class | Chuẩn multi-class |
| CV: walk-forward 6 folds (val 2014-2019) | Standard time-series CV |
| Train 2010-2019, skip 2020-2021, validate 2022 | Giữ nguyên |

---

## Tech stack

| Tầng | Lựa chọn |
|---|---|
| Backend | FastAPI (Python) |
| ML | XGBoost + LightGBM + RF (so sánh) + Prophet (baseline) + Optuna (tuning) |
| Database | PostgreSQL |
| Frontend | React + Tailwind + Leaflet.js |
| Deploy | Docker Compose |
| Weather historical | ERA5 (ECMWF) — 17 biến |
| Weather realtime | OpenWeatherMap API |

## Documentation Workflow

Notion workspace vẫn hoạt động:
- Quyết định quan trọng + session summary → update Notion
- Code + annotation confirmed → update Notion Master Notebook
- Nội dung báo cáo → docs/ folder local (backup)

---

## Ghi nhận kết quả sau mỗi session

Sau mỗi session hoàn thành, Claude PHẢI tạo block tổng kết ngay cuối session
trong notebook (markdown cell). Block này phục vụ 2 mục đích:
(1) người dùng dựa vào đó viết slide thuyết trình cho GVHD sau này,
(2) khi mở lại notebook, đọc block này biết ngay session đó đã làm gì, kết quả ra sao.

Format chuẩn:

---
**KET QUA SESSION X** (ngày/tháng/năm)

Mục tiêu: 1 câu mô tả session này làm gì.

Kết quả chính:
- [Metric/con số quan trọng nhất]
- [Metric/con số thứ 2]
- [Phát hiện đáng chú ý]

Quyết định đã chốt:
- [Quyết định 1 + lý do ngắn gọn]
- [Quyết định 2 + lý do ngắn gọn]

Files tạo ra:
- data/processed/ten_file.csv (shape, mô tả ngắn)
- ml_models/ten_model_vN.pkl (metrics)

Best result hiện tại:
- Flu: model X, R² = x.xxx, RMSE = x.xxx
- Dengue: model Y, R² = x.xxx, RMSE = x.xxx

Van de con lai / buoc tiep theo:
- [Nếu có issue chưa giải quyết]
---

Quy tắc:
- Không dùng emoji/icon
- Ghi đủ con số cụ thể, không nói chung chung
- Ghi rõ file nào đã tạo, version nào
- Ghi rõ best result để session sau so sánh
- Block này là "tóm tắt cho người mới đọc" — không giả định người đọc biết context

---

## Quy tắc đặt tên file — versioning

KHÔNG BAO GIỜ ghi đè file cũ. Mỗi lần cải thiện (thay đổi feature, tune, đổi transform...)
tạo file MỚI với hậu tố version tăng dần. File cũ giữ nguyên để so sánh và rollback.

### Data files

ten_file_v1.csv → ten_file_v2.csv → ten_file_v3.csv

Ví dụ:
  master_weekly_v1.csv          <- merge lần đầu
  master_weekly_v2.csv          <- fix ERA5 coverage
  features_flu_v1.csv           <- feature set ban đầu
  features_flu_v2.csv           <- thêm rolling mean
  features_flu_v3.csv           <- thêm weather lag theo CCF mới

### Model files

ten_model_vN.pkl

Ví dụ:
  xgb_flu_regressor_v1.pkl      <- default params
  xgb_flu_regressor_v2.pkl      <- sau Optuna tuning
  lgbm_flu_regressor_v1.pkl     <- LightGBM lần đầu
  xgb_flu_classifier_v1.pkl     <- classification model
  xgb_dengue_regressor_v1.pkl   <- dengue model

### Kèm theo mỗi model .pkl, PHẢI có:

  xgb_flu_regressor_v2_features.json    <- danh sách features dùng để train
  xgb_flu_regressor_v2_metrics.json     <- RMSE, MAE, R², training date, notes

### Bảng theo dõi versions (ghi trong notebook cuối SESSION 6 và 7)

| File | Version | Thay đổi | Flu R² | Dengue R² | Ghi chú |
|---|---|---|---|---|---|
| xgb_flu_regressor | v1 | Default params, 12 features | 0.xxx | - | Baseline |
| xgb_flu_regressor | v2 | Optuna 60 trials | 0.xxx | - | +x% improvement |
| lgbm_flu_regressor | v1 | Default params, same features | 0.xxx | - | So sánh với XGB |
| xgb_dengue_regressor | v1 | Default params, 14 features | - | 0.xxx | Baseline |

### Quy tắc version number

- v1 = lần đầu tạo file
- v2, v3, ... = mỗi lần cải thiện/thay đổi đáng kể
- KHÔNG dùng v0 (bắt đầu từ v1)
- KHÔNG xóa file cũ — giữ tất cả versions trên Drive
- File mới nhất = version số cao nhất
- Khi load trong code, dùng biến constant:
  CURRENT_FLU_MODEL = MODELS_DIR / 'xgb_flu_regressor_v2.pkl'
  (cập nhật constant khi có version mới, không hardcode trong cell)

### Pattern trong code

```python
# ĐÚNG — version rõ ràng, không ghi đè
model_path = MODELS_DIR / 'xgb_flu_regressor_v2.pkl'
joblib.dump(model, model_path)

features_path = MODELS_DIR / 'xgb_flu_regressor_v2_features.json'
with open(features_path, 'w') as f:
    json.dump({'features': FEATURE_COLS, 'target': TARGET_FLU,
               'version': 'v2', 'date': '2026-05-17',
               'note': 'After Optuna 60 trials'}, f, indent=2)

metrics_path = MODELS_DIR / 'xgb_flu_regressor_v2_metrics.json'
with open(metrics_path, 'w') as f:
    json.dump({'rmse': float(rmse), 'mae': float(mae), 'r2': float(r2),
               'cv_folds': 6, 'optuna_trials': 60,
               'best_params': study.best_params}, f, indent=2)

# SAI — ghi đè file cũ, mất kết quả
model_path = MODELS_DIR / 'xgb_flu_regressor.pkl'  # <- không có version
```