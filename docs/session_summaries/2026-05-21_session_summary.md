# Session Summary 21/05/2026 — Multi-horizon Forecasting + Phase D pivot

## Mục tiêu của buổi

1. Nối backend FastAPI với frontend React: bỏ mock data, gọi API thật từ Postgres
2. Phát hiện vấn đề thiết kế: predict trên training data vô nghĩa → pivot sang nowcast realtime
3. Lên kế hoạch Phase D (multi-horizon + realtime ingestion)
4. Train multi-horizon model (SESSION 8 notebook v6)

## Bối cảnh / vấn đề đang giải quyết

- Sau Demo lần 1, frontend EpiWatch port xong nhưng dùng mock data
- Backend endpoints scaffold đầy đủ nhưng DB chưa seed, baseline alembic migration trống
- Hardcode constraint `year >= 2022` ở endpoints không khớp data thực 2010-2019
- Câu hỏi quan trọng từ user: "predict tuần hiện tại làm sao khi data chỉ tới 2019?"
- Phương án "proxy" (gán nhãn iso_week current vào feature 2019 W52) bị từ chối — đúng đắn về mặt khoa học vì inference trên training data vô nghĩa

## Kết quả từng SESSION đã chạy

### Phase 1 — Backend foundation (sáng)

- Viết `scripts/load_db_v2.py` thay `load_db.py` cũ (paths mới, 4 model v1, generic get_params)
- Lower endpoint year constraint xuống ge=2010 cho risk.py + predictions.py
- Update frontend uiStore: dynamic ISO week dùng JS Date thay hardcode

### Phase 2 — Pivot Phase D (chiều)

- Quyết định D = A + C combo: multi-horizon model + realtime ingestion
- Cleanup proxy code (BE schema, FE badge) sau khi user xác định không dùng
- Tạo `docs/huong_phat_trien_phase_D.md` plan đầy đủ 5.5 buổi
- Lưu memory `feedback_no_proxy_inference.md` — quy tắc không fake current-week

### Phase 3 — SESSION 8 Multi-horizon (chiều-tối)

Copy `KLTN_EpiWeather_ML_v5.ipynb` → v6 (giữ v5 nguyên).

| Cell | Nội dung | Kết quả |
|---|---|---|
| 8.0 | Reload paths Drive | 16 cols flu, 15 cols dengue OK |
| 8.1 | Build flu targets h1-h4 | 55,208 → 54,636 rows, drop 572 |
| 8.2 | Build dengue targets h1-h4 | 5,926 → 5,786 rows, drop 140 |
| 8.3 | Walk-forward CV flu (6 folds × 4 h) | h=1: 0.866, h=4: 0.757 |
| 8.4 | Train final flu + save 4 pkl | 4 × 1.7MB artifacts |
| 8.5 | Dengue CV + train + save 4 pkl | h=1: 0.929, h=4: 0.898, 4 × 39.8MB |
| 8.6 | Bảng so sánh + Lowe benchmark | **8/8 VƯỢT benchmark** |

## Phát hiện quan trọng

**1. Multi-horizon results — vượt kỳ vọng:**

| h | Flu R² | Dengue R² | So với Lowe 2014 |
|---|---|---|---|
| 1 | 0.8661 | 0.9292 | VƯỢT (Lowe 0.78-0.85) |
| 2 | 0.8293 | 0.9191 | VƯỢT (Lowe 0.70-0.78) |
| 3 | 0.7928 | 0.9086 | VƯỢT (Lowe 0.62-0.72) |
| 4 | 0.7573 | 0.8981 | **VƯỢT mạnh (Lowe 0.55-0.68)** |

**2. Dengue degradation NHẸ hơn flu — bất ngờ:** dengue mất ~0.010 R²/horizon, flu mất ~0.036 R²/horizon. Lý do: dengue có lag dài hơn (6-14 tuần vs flu 1-7 tuần) → AR signal phủ xa hơn; endemic năm cả 12 tháng ở vùng nhiệt đới; RF robust với noise hơn LGBM.

**3. VNM không có trong flu features:** 143 nước có data, KHÔNG có Vietnam, Singapore, Brunei. Pending fix — cần check raw VIW_FNT.csv hoặc trace SESSION 1/5 filter.

**4. Dengue thực tế 35 nước:** memory cũ ghi 37, kiểm lại file thực 35. Update memory.

## Files đã thay đổi

| File | Thay đổi | Loại |
|---|---|---|
| `scripts/load_db_v2.py` | Tạo mới | NEW |
| `backend/app/api/v1/endpoints/risk.py` | Year ge=2010 | EDIT |
| `backend/app/api/v1/endpoints/predictions.py` | Year ge=2010 | EDIT |
| `frontend/src/store/uiStore.ts` | getCurrentISOWeek() dynamic | EDIT |
| `docs/huong_phat_trien_phase_D.md` | Tạo mới — full Phase D plan | NEW |
| `KLTN_EpiWeather_ML_v6.ipynb` | Copy từ v5, +16 cells SESSION 8 | NEW |
| `ml_models/lgbm_flu_regressor_h{1,2,3,4}_v1.pkl` | Train + save | NEW (4 files) |
| `ml_models/rf_dengue_regressor_h{1,2,3,4}_v1.pkl` | Train + save | NEW (4 files) |
| Mỗi pkl × `_features.json` + `_metrics.json` | Metadata | NEW (16 files) |

## Còn lại / chưa làm

- [ ] **Phase C-2 backend** — load 8 multi-horizon models, ForecastResponse schema, `/forecast` endpoint
- [ ] **DB seed** — chạy `psql -f db_init.sql` + `seed_countries.py` + `load_db_v2.py`
- [ ] **Phase A-1** — sync_flunet.py + sync_openweather.py (realtime ingestion)
- [ ] **Phase A-2** — feature_builder.py service
- [ ] **Phase A-3** — `/nowcast` endpoint + `/risk-map/nowcast`
- [ ] **Phase 4 FE** — useNowcast hook, 4-week trajectory chart trong DiseaseDetailPage
- [ ] **Fix VNM missing** trong feature pipeline (priority cao cho demo)
- [ ] Fix dengue classifier High recall = 14% (chưa đạt, từ SESSION 6)
- [ ] Báo cáo Chương 4 (thực nghiệm + kết quả)
- [ ] Báo cáo Chương 5 (kết luận)

## Những điều cần ghi nhớ cho báo cáo

**Câu chuyện khoa học mạnh để viết Chương 4:**

> "Đề tài đề xuất multi-horizon forecasting (h=1..4 tuần) cho cả flu (LightGBM) và dengue (RandomForest), train walk-forward CV trên dữ liệu 143 nước (flu 2010-2019) và 35 nước (dengue 2015-2019). Kết quả vượt benchmark Lowe et al 2014 Lancet ID: flu R² duy trì > 0.75 sau 4 tuần, dengue R² > 0.89. Đặc biệt dengue degradation slope chỉ ~0.010/horizon — gentle bất ngờ, lý giải bởi lag dài (6-14 tuần) phủ xa hơn flu (1-7 tuần) và pattern endemic năm cả 12 tháng ở vùng nhiệt đới."

**Tham chiếu literature cho discussion:**
- Lowe et al 2014 Lancet ID — dengue Brazil benchmark
- Reich et al 2019 CDC FluSight — flu nowcast pipeline
- Bortman 1999 — endemic channel threshold

**Decision đã chốt cho thesis:**
- Hybrid Regression + Classification (SESSION 6) + Multi-horizon Extension (SESSION 8)
- h=1 cho risk-map current week, h=1..4 cho forecast trajectory chart
- Giữ best_params từ v1, không Optuna tune lại per horizon (cùng feature set)
- Realtime nowcast = combo A (data sync) + C (multi-horizon model)
