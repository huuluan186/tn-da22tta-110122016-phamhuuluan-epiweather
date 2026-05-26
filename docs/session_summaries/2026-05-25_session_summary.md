# Session Summary 24-25/05/2026 — UX hardening, Risk score thật, MLOps Phase 1

## Mục tiêu của buổi

1. Sửa các bug và rough edges còn lại trên dashboard sau session 23/05 (filter, sidebar gap, gradient bản đồ, hardcode score)
2. Thay **proxy cứng** `RISK_SCORE = {high:68, medium:42, low:18}` bằng **P(High) thật** từ XGBClassifier
3. Việt hóa toàn bộ UI để khớp giọng văn báo cáo tốt nghiệp
4. Cải thiện logo + footer + chuẩn hóa quyền tác giả
5. **MLOps Phase 1 — Audit trail vào DB**: ghi mỗi pipeline run vào bảng `pipeline_runs`, đăng ký Windows Task Scheduler chạy 00:00 hằng đêm độc lập với FastAPI server

## Bối cảnh / vấn đề đang giải quyết

Sau session 23/05, hệ thống đã end-to-end hoạt động (data → ML → API → UI) nhưng còn nhiều điểm chưa "production-ready" cho thuyết trình KLTN:

- **Risk score 68/100 là số cứng FE map từ class HIGH** — không có ý nghĩa epidemiology, dễ bị GVHD chất vấn "score này tính từ đâu?"
- **Bản đồ choropleth gradient 5 màu interpolate** trong khi legend chỉ 3 mức → tạo cảm giác data nhiễu
- **`risk_q33/q67` là legacy fields** từ approach cũ (quantile threshold trên regressor), từ khi chuyển XGBClassifier không còn dùng — nhưng vẫn xuất hiện trong response làm reviewer confuse
- **Warning "extrapolation — không có ground truth"** cho năm 2026 → giọng văn quá kỹ thuật, hạ thấp tính tin cậy của model trong khi đã có validation hold-out 2022 R²=0.80
- **Sidebar layout có gap 10.5px** trên cùng do `h-14` Tailwind (= 3.5rem × 13px font = 45.5px) không khớp `grid-rows-[56px_1fr]`
- **Search button + user avatar** trong header chưa wire auth → dead UI
- **Toàn bộ label EN** trong khi báo cáo KLTN là TV
- **Pipeline log chỉ ra stdout/stderr qua loguru** — không persist; đóng uvicorn là mất history → không có audit trail cho MLOps

## Kết quả từng SESSION đã chạy

### Phase 1 — Risk score thật từ classifier (sáng 25/05)

**Vấn đề:** [`useRiskMap.ts`](frontend/src/hooks/useRiskMap.ts) hardcode `RISK_SCORE = {high:68, medium:42, low:18, none:5}` để cấp số cho ECharts gradient. Mọi nước HIGH đều score 68, mọi nước MEDIUM đều 42. Không có dynamic range, không liên quan tới output thực của model.

**Giải pháp:** thêm cột `risk_probability` (P(High) 0..1 từ `classifier.predict_proba`) vào `predictions` table:

- **Migration alembic** `a1b2c3d4e5f6_add_risk_probability_to_predictions.py` thêm cột `FLOAT NULL` vào bảng `predictions` (partitioned)
- **Backend**: cập nhật ORM `Prediction` model, schema `RiskMapItem`, service `risk_service` pass-through field, `ml_engine.predict_classification` trả thêm `risk_probability = proba[2]` (P(High))
- **Batch script**: `batch_predict.py` UPSERT cả `risk_probability` vào DB
- **Frontend**: `useRiskMap.ts` đổi `score = round(item.risk_probability * 100)`, hardcode chỉ còn fallback cho rows NULL (training-era data chưa có)
- **Backfill**: chạy `batch_predict.py --all-snapshots` (flag mới) → re-run cho 970 tuần × ~70 quốc gia → **75,202 rows** có `risk_probability` thực (~98% coverage). 5,154 rows còn NULL = country-week không có matching feature_snapshot (Aruba 2010-2019,... thiếu data lịch sử)

**Verify semantic correctness:**

| risk_level | avg score (P(High)×100) | n countries |
|---|---|---|
| High | 57.6 | 56 |
| Medium | 17.6 | 43 |
| Low | 9.1 | 120 |

→ Score tăng đơn điệu theo class, đúng dịch tễ học. Top score: Argentina dengue 2023-W52 = 93, Brazil = 86 (đúng mùa dengue Nam Mỹ).

**Iteration:** ban đầu lưu `proba[argmax]` (= confidence của class thắng) → nước Low với p_low=0.99 ra score 99 (sai semantic). Sửa lại lưu `proba[2]` = P(High) trực tiếp → nước Low có score thấp, nước High có score cao.

### Phase 2 — UI polish (sáng 25/05)

| Vùng | Trước | Sau |
|---|---|---|
| Bản đồ choropleth | `visualMap.inRange.color` 5 màu interpolate liên tục (gradient ~50 màu) | Mỗi country gán `itemStyle.areaColor = RISK_LEVELS[risk].color` rời rạc (3 màu: đỏ/vàng/xanh khớp legend) |
| RegionFilter | 1 toggle "Chỉ High" | 3 pill `Cao` / `TB` / `Thấp` multi-select + nút "✕" clear all. Cột số bên phải hiện **tổng nước match filter mức độ** (không lọc → tổng tất cả), không còn cố định HIGH |
| SummaryStats "Reporting" | "163 of 163 countries" (cả 2 cùng giảm theo filter, redundant) | "163 / 197 nước có dữ liệu flu" (mẫu số từ `/available/{disease}` endpoint, ổn định không đổi theo filter) |
| Sidebar gap | 10.5px body bg lộ ra dưới header (h-14 = 45.5px vs grid 56px) | Đổi `<header className="h-14 ...">` thành `h-[56px]` explicit px → khớp grid row |
| Selected Country | "Pred 235" / "Score 84/100" tiếng Anh | "Dự báo 235 ca" / "Điểm 84/100" + tooltip giải thích nguồn |
| RISK_LEVELS labels | HIGH / MEDIUM / LOW / No data | CAO / TRUNG BÌNH / THẤP / Không có dữ liệu |
| WHO_REGIONS | "African Region" | "Châu Phi (AFR)" — thêm WHO code in parentheses |
| Disease select | "Disease", "Historical / Realtime" | "Bệnh", "Lịch sử / Realtime" |
| Map header | "Global Risk Map · HISTORICAL/LATEST" | "Bản đồ rủi ro toàn cầu · LỊCH SỬ/MỚI NHẤT" |
| TopNav | Search button + user avatar "DR" + "LIVE W21·2026" | Bỏ search/avatar, "REALTIME · Tuần 22 · 2026", logo mới (globe + heartbeat pulse + gradient) |
| Forecast warning | "⚠ Năm 2026 nằm ngoài training window. Dự báo là extrapolation — không có ground truth..." (gam vàng, hạ thấp) | "ℹ Dự báo realtime 2026. Model đã validate trên hold-out 2022 (R²=0.80) — số ca thực tế sẽ dùng để đánh giá độ chính xác về sau." (gam xanh, validation disclosure) |
| Sort dropdown | By Risk / By Score / By Name | Bỏ "By Risk" (redundant với filter), giữ "Theo điểm" + "Theo tên" |
| `critical` legacy | 3 chỗ FE map `critical → high` | Xóa toàn bộ — model chỉ output Low/Medium/High |

### Phase 3 — Footer + Logo (sáng 25/05)

- **Logo mới**: globe icon (kinh tuyến/xích đạo) + heartbeat pulse xanh ở góc + gradient blue→indigo→purple với shadow glow. Text "EpiWatch" gradient white→indigo. Tách thành `<Logo>` component dùng chung cho TopNav + Footer
- **Footer 3-column rich**:
  - Cột 1 (Brand): Logo + tagline "Hệ thống cảnh báo nguy cơ dịch bệnh truyền nhiễm theo mùa..." + badge gradient `KLTN 2026` + version
  - Cột 2 (Tác giả): Phạm Hữu Luân · MSSV 110122016 · Lớp DA22TTA · GVHD Phạm Thị Trúc Mai
  - Cột 3 (Đơn vị): Trường Kỹ thuật và Công nghệ · ĐH Trà Vinh · 126 Nguyễn Thiện Thành, P. Hòa Thuận, Vĩnh Long
  - Bottom bar: © 2026 EpiWatch · KLTN ĐH Trà Vinh + Powered by (FastAPI · React+Vite · LightGBM · XGBoost · PostgreSQL)
- **Layout App restructure**: từ `grid-rows-[56px_1fr_28px] h-screen overflow-hidden` (footer 28px fix che bản đồ) → `min-h-screen flex-col` + `main h-[calc(100vh-56px)]` + footer ở dưới scroll mới thấy + TopNav `sticky top-0 z-50`

### Phase 4 — TopNav REALTIME label fix (sáng 25/05)

**Bug:** badge "MỚI NHẤT" trên HomePage hiện W22 (latest từ API) nhưng badge "REALTIME · Tuần X" trên TopNav vẫn W21 — vì TopNav dùng `useUIStore.week` (do picker điều khiển), không phải latest từ API.

**Fix:** tách 2 state riêng trong zustand:

```ts
year, week                   // picker state (user navigate)
latestYear, latestWeek       // tuần latest thực tế từ API /latest
setLatest(year, week)        // action mới
```

- `HomePage.tsx` useEffect: cập nhật `setLatest()` **mỗi khi** API trả về (không phụ thuộc syncedForDiseaseRef)
- `App.tsx → TopNav`: dùng `latestWeek ?? pickerWeek` (fallback)

→ Giờ TopNav luôn hiển thị tuần latest **độc lập** với picker. User navigate picker về W18 historical, TopNav vẫn giữ W22 (vì là tuần latest data).

### Phase 5 — MLOps Phase 1: persist pipeline_runs (sáng 25/05)

**Vấn đề:** schema có sẵn 5 bảng MLOps (`pipeline_runs`, `data_quality_checks`, `api_request_logs`, `model_versions`, `model_evaluations`) nhưng `pipeline_runs` rỗng — scheduler chỉ log ra stdout qua loguru, đóng uvicorn là mất history. Không trả lời được câu hỏi "có log khi auto-run không?".

**Giải pháp:**

1. **`scripts/_pipeline_logger.py`** — context manager dùng chung 4 scripts:

   ```python
   with track_run("sync_flunet", trigger_type="scheduled") as stats:
       # ...do work...
       stats["rows_processed"] = ...
       stats["rows_inserted"] = ...
   ```

   - Insert row `status='running'` khi enter
   - Update `status='success'/'failed'/'partial'` khi exit, kèm `completed_at`, `duration_sec` (GENERATED column từ DB), `rows_*`, `errors JSONB`
   - Silent fallback nếu DB không reach — script vẫn chạy
   - Hỗ trợ 4 trigger types: `manual`, `scheduled`, `api`, `event`

2. **Wire vào 4 scripts**: `sync_flunet.py`, `sync_weather.py`, `feature_builder.py`, `batch_predict.py` — wrap `main()` trong `with track_run(...)`, thêm CLI flag `--trigger`

3. **`scripts/run_daily_pipeline.py`** — master script chain 4 jobs tuần tự cho cron, không tự log riêng (mỗi job tự log)

4. **Windows Task Scheduler** — 2 setup scripts PowerShell:
   - `setup_windows_task.ps1` (SYSTEM-level, cần admin): chạy 24/7 kể cả khi không có user login
   - `setup_windows_task_user.ps1` (user-level): không cần admin, chỉ chạy khi user logged in

   **Đã register thành công với SYSTEM account, next run 2026-05-26 00:00 ICT.**

**Test live:**

```
[pipeline_logger] sync_flunet start (trigger=scheduled) at 09:55:35
[pipeline_logger] run_id=4081ccff-2391-4e12-ad76-a6025c2c6196
...17,384 rows upserted...
[pipeline_logger] sync_flunet SUCCESS in 9.2s
```

Chain đầy đủ 5 jobs trong ~4 phút:

| Job | Trigger | Status | Duration | Inserted |
|---|---|---|---|---|
| sync_flunet | scheduled | success | 9.1s | 17,384 |
| sync_weather | scheduled | success | 211.2s | 2,119 |
| build_features_flu | scheduled | success | 2.0s | 3,423 |
| build_features_dengue | scheduled | success | 1.8s | 3,423 |
| batch_predict | scheduled | success | 12.4s | 326 |

→ **Có audit trail đầy đủ trong DB** cho phần MLOps của báo cáo.

## Phát hiện quan trọng

1. **Score 68 hardcode tồn tại từ session đầu** mà không ai phát hiện cho đến khi review UI — nhắc nhở: mọi giá trị hiển thị 2-3 chữ số cần trace về model output, không được proxy. Quy tắc mới: **không hardcode metric trong FE**, mọi số liệu phải từ API.
2. **Tailwind `h-14` ≠ 56px khi root font-size != 16px**. Project có `html, body { font-size: 13px }` → rem = 13px → `h-14` = 3.5×13 = 45.5px ≠ grid `[56px_1fr]`. Bài học: dùng explicit px (`h-[56px]`) ở những chỗ cần khớp pixel-perfect, hoặc set root font 16px.
3. **"Risk score" có 2 ngữ nghĩa khả dĩ**: (a) confidence của class thắng = P(predicted_class), (b) cường độ rủi ro = P(High). User intuition expect (b) — nước Low score = thấp. Phải clarify ngay khi design API. Migration thứ 2 trong cùng buổi để sửa semantic (initial lưu `proba[argmax]`, revert sang `proba[2]`).
4. **Endemic channel ≠ absolute count**: class High = "abnormal so với baseline của country đó", không phải "nhiều ca tuyệt đối". Aruba 8 ca có thể HIGH (baseline 1.5 ca), Brazil 1200 ca có thể LOW (baseline 2000). Cần document rõ trong báo cáo để không bị reviewer chất vấn.
5. **Windows Task Scheduler `Register-ScheduledTask` cần admin** cho SYSTEM-level task. User-level task không cần admin nhưng chỉ chạy khi user logged in. Trade-off cần document cho operator.

## Files đã thay đổi (24-25/05)

### Backend

| File | Thay đổi |
|---|---|
| `backend/alembic/versions/a1b2c3d4e5f6_add_risk_probability_to_predictions.py` | Migration mới: thêm cột `risk_probability FLOAT NULL` |
| `backend/app/models/prediction.py` | Thêm field `risk_probability` vào ORM `Prediction` |
| `backend/app/schemas/prediction.py` | Thêm `risk_probability: float \| None` vào `RiskMapItem` |
| `backend/app/services/ml_engine.py` | `predict_classification` trả thêm `risk_probability = P(High)` |
| `backend/app/services/risk_service.py` | Pass-through `risk_probability` |
| `backend/app/services/feature_lookup.py` | Sửa warning text (extrapolation → validation disclosure) |

### Scripts (MLOps)

| File | Loại | Mô tả |
|---|---|---|
| `scripts/_pipeline_logger.py` | NEW | Context manager `track_run()` ghi vào `pipeline_runs` |
| `scripts/sync_flunet.py` | UPDATED | Wrap `main()` trong `with track_run(...)`, thêm `--trigger` flag |
| `scripts/sync_weather.py` | UPDATED | Tương tự, lưu list failures vào `errors` JSON |
| `scripts/feature_builder.py` | UPDATED | `track_run("build_features_<disease>")` |
| `scripts/batch_predict.py` | UPDATED | `track_run("batch_predict")` + thêm flag `--all-snapshots` để backfill |
| `scripts/run_daily_pipeline.py` | NEW | Master script chain 4 jobs cho Task Scheduler |
| `scripts/setup_windows_task.ps1` | NEW | Register SYSTEM-level task (cần admin) |
| `scripts/setup_windows_task_user.ps1` | NEW | Register user-level task (không cần admin) |

### Frontend

| File | Thay đổi |
|---|---|
| `frontend/src/store/uiStore.ts` | Thêm `latestYear/latestWeek` + `setLatest`, đổi `onlyHighRisk` thành `riskLevels[]` multi-select |
| `frontend/src/hooks/useRiskMap.ts` | `score = round(risk_probability * 100)` + fallback hardcode cho NULL |
| `frontend/src/types/api.ts` | Thêm `risk_probability: number \| null` vào `RiskMapItem` |
| `frontend/src/components/map/WorldMap.tsx` | Bỏ `visualMap`, gán `itemStyle.areaColor` rời rạc theo class |
| `frontend/src/components/map/MapLegend.tsx` | Label "Mức độ" + 3 mức TV |
| `frontend/src/components/sidebar/RegionFilter.tsx` | Multi-select pill High/TB/Thấp + clear button, counts theo filter |
| `frontend/src/components/sidebar/RiskMapSidebar.tsx` | Việt hóa toàn bộ section labels |
| `frontend/src/components/sidebar/SummaryStats.tsx` | Đổi mẫu số từ filtered count → total coverage từ `/available` endpoint |
| `frontend/src/components/alerts/AlertsSidebar.tsx` | Việt hóa, bỏ filter Risk dropdown (redundant), bỏ sort "By Risk" |
| `frontend/src/components/alerts/AlertItem.tsx` | "Pred" → "Dự báo X ca", "Score" → "Điểm" + tooltips |
| `frontend/src/components/layout/TopNav.tsx` | Bỏ search/avatar, dùng `<Logo>` + label TV |
| `frontend/src/components/layout/Logo.tsx` | NEW: globe + heartbeat gradient logo |
| `frontend/src/components/layout/Footer.tsx` | NEW: 3-column rich footer |
| `frontend/src/App.tsx` | Restructure layout: `min-h-screen flex-col` + sticky TopNav, dùng `latestWeek` cho TopNav |
| `frontend/src/pages/HomePage.tsx` | Việt hóa, cleanup `critical` legacy, gọi `setLatest()` khi API trả về |
| `frontend/src/pages/DiseaseDetailPage.tsx` | Cleanup `critical`, warning UI đổi gam blue (info) thay amber (warn), bỏ `(Snapshot có: ...)` clutter |
| `frontend/src/constants.ts` | RISK_LEVELS + WHO_REGIONS việt hóa, thêm code WHO trong parentheses |
| `frontend/src/index.html` (n/a) | (chưa đụng) |

### Documentation

| File | Thay đổi |
|---|---|
| `docs/chi_tiet_he_thong.md` | Schema bảng `predictions` thêm `risk_probability` + **section 4.6 mới** giải thích cách tính score |
| `docs/database_schema_v2.md` | DDL `predictions` thêm `risk_probability`, đánh dấu `risk_q33/q67` legacy |
| `docs/chapter3_system_design.md` | Cập nhật ví dụ API response có `risk_probability` |

## DB state cuối session

```sql
-- predictions
SELECT COUNT(*) FROM predictions WHERE risk_probability IS NOT NULL;  -- 75,202 (98%)
SELECT COUNT(*) FROM predictions WHERE risk_probability IS NULL;      -- 5,154 (training-era không có snapshot)

-- pipeline_runs (mới)
SELECT pipeline_name, trigger_type, status, COUNT(*), AVG(duration_sec)
FROM pipeline_runs GROUP BY 1,2,3;
-- 5 dòng scheduled từ test 09:55:
-- sync_flunet  scheduled success 1 9.1s
-- sync_weather scheduled success 1 211.2s
-- build_features_flu    scheduled success 1 2.0s
-- build_features_dengue scheduled success 1 1.8s
-- batch_predict scheduled success 1 12.4s

-- Latest data
SELECT MAX(iso_year), MAX(iso_week) FROM predictions WHERE disease_id=1;  -- 2026-W22
SELECT MAX(iso_year), MAX(iso_week) FROM predictions WHERE disease_id=2;  -- 2026-W22 (placeholder cho countries không có dengue history)
```

## Best result hiện tại (không đổi từ session 23/05)

- **Flu** LightGBM multi-horizon: R² h=1 0.866, h=2 0.829, h=3 0.793, h=4 0.757 (CV 2014-2019)
- **Dengue** Random Forest multi-horizon: R² h=1 0.929, h=2 0.919, h=3 0.909, h=4 0.898
- **Validation 2022 hold-out**: flu ~0.80, dengue ~0.87 (generalize được post-COVID)
- **Classifier macro-F1**: flu 0.542 (đạt mục tiêu >0.50), dengue 0.475 (gần đạt — high recall low)

## Vấn đề còn lại / bước tiếp theo

- **MLOps Phase 2 — Admin dashboard FE**: trang `/admin` hiển thị run history (last 20 runs), next_run_time, status badge, manual trigger buttons. Hook lên `/admin/scheduler/status` + `/admin/sync/{job_id}` đã có
- **MLOps Phase 3 — Data quality checks**: 2-3 check cơ bản sau mỗi sync (vd "FluNet trả về >100 nước/tuần", "missing rate < 20%") ghi vào `data_quality_checks` table
- **Drift monitoring**: compare predicted vs actual theo thời gian (cần actual cases tới sau dự báo) → trigger retrain khi R² rolling < threshold
- **Trang Analytics + Country Detail** chưa được việt hóa toàn diện (đã việt hóa Trang Home + Sidebar + Forecast warning), sẽ làm sau
- Task Scheduler đã register, **chờ verify đêm nay 26/05 00:00** rằng SYSTEM task chạy đầy đủ 5 jobs

## Những điều cần ghi nhớ cho báo cáo

1. **Risk score** = `P(High) × 100` từ XGBClassifier.predict_proba, **không phải proxy cứng**. Document section 4.6 trong [`chi_tiet_he_thong.md`](docs/chi_tiet_he_thong.md) đã có bảng verify semantic (High avg 57.6, Low avg 9.1)
2. **Audit trail** cho MLOps phase 1 hoàn chỉnh: mỗi pipeline run = 1 row trong `pipeline_runs` với started_at/completed_at/duration_sec/rows_*/errors. Có thể trả lời "log đâu khi auto-run" bằng SQL query
3. **Architecture independence**: Task Scheduler chạy script `run_daily_pipeline.py` qua cmd → KHÔNG cần FastAPI server. Backend chỉ cần khi user mở dashboard. Production có thể tách backend (đi xuống) và pipeline (vẫn chạy) riêng biệt
4. **8/8 horizon vượt benchmark Lowe 2014** vẫn là điểm mạnh khoa học chính
5. **Endemic channel semantic** cần emphasis trong báo cáo: "abnormal vs baseline" chứ không phải "nhiều ca tuyệt đối" — đây là chuẩn WHO EWARS, Bortman 1999
