# Session Summary 23/05/2026 — Dengue Nowcast Extension + MLOps Pipeline hoàn thiện

## Mục tiêu của buổi

1. Mở rộng dengue từ historical-only (2010-2019) sang nowcast (2021-2023-W36) từ OpenDengue v1.3 batch
2. Hoàn thiện disease-aware UI: WeekPicker, year validation, applied state reset khi đổi disease
3. Bịt các lỗ hổng MLOps: scheduler build features cả 2 bệnh, manual nowcast trigger, batch_predict range mode
4. Verify end-to-end: DB → backend API → frontend
5. Soạn email gửi cô Phạm Thị Trúc Mai báo cáo tiến độ

## Bối cảnh / vấn đề đang giải quyết

- Sau session 21/05, Phase D đã có multi-horizon model (R² flu h=1 0.866, dengue h=1 0.929) nhưng:
  - Dengue chỉ predict được 2010-2019 (training era) — không có realtime
  - Scheduler chỉ build features flu, bỏ qua dengue
  - WeekPicker hardcode năm cố định, không phân biệt phạm vi flu vs dengue
  - Khi switch flu → dengue, frontend không reset year/week/applied state → hiển thị sai
- User nêu vấn đề: "predict dengue 2021-2023 từ đâu khi training chỉ tới 2019?" → giải pháp: dùng OpenDengue v1.3 batch (có ground truth tới 2023-W36) thay vì giả lập

## Kết quả từng SESSION đã chạy

### Phase 1 — Mở rộng dataset dengue (sáng)

- **Load OpenDengue v1.3 2021-2023 vào DB**: 56 quốc gia, 2021 (52w), 2022 (52w), 2023 (36w) → tổng ~7,900 dòng disease_cases mới
- **Sync Open-Meteo Archive 2020-2023** cho 56 quốc gia dengue (warmup cần đến 2020 để có lag-16 cho 2021-W01)
- **Build dengue feature snapshots 2020-2023**: chạy `feature_builder.py --disease dengue --from-year 2020 --to-year 2023`
- Kết quả: feature_snapshots dengue tăng từ ~5,926 (2015-2019) lên ~13,734 (thêm 7,808 rows 2020-2023)

### Phase 2 — Frontend disease-aware (chiều)

| File | Thay đổi |
|---|---|
| `uiStore.ts` | `DISEASE_DEFAULTS` per-disease; `setDisease` reset year/week/selectedIso3 |
| `HomePage.tsx` | `prevDiseaseRef` reset `applied` state khi switch disease |
| `WeekPicker.tsx` | `DISEASE_CONFIG` per-disease year/week range, hint label |
| `RiskMapSidebar.tsx` | Pass `disease` prop xuống WeekPicker |
| `DiseaseDetailPage.tsx` | `VALID_YEARS` per-disease, hint text dưới picker |

→ Switch flu (2026-W21) sang dengue (2023-W36) hoạt động đúng, không kéo state cũ

### Phase 3 — MLOps + Backend honesty (chiều-tối)

| File | Thay đổi | Vai trò |
|---|---|---|
| `scheduler.py` | `job_build_features` chạy cả flu + dengue; thêm `job_build_features_dengue_nowcast` | Fix gap MLOps |
| `admin.py` | Add `build_features_dengue_nowcast` vào valid jobs; safer `result.get("returncode", 0)` | Manual trigger cho OpenDengue batch release mới |
| `feature_lookup.py` | `DENGUE_NOWCAST_YEARS = {2021, 2022, 2023}`; warning phân biệt nowcast vs extrapolation | Trung thực với GVHD: dengue có ground truth, flu 2026 không |
| `schemas/prediction.py` | Add `is_nowcast: bool = False` vào DataCoverage | FE hiển thị badge phân biệt |
| `batch_predict.py` | Add `--from-week`/`--to-week` range mode | Predict batch nowcast không cần inline Python |

### Phase 4 — Backfill predictions + verify (tối)

- Inline batch_predict cho dengue 2023 W24-W36 (728 rows upserted)
- Xóa nhầm W37-W52 do task cũ chạy thừa (-784 rows, sau bị task cũ ghi lại → xóa lần 2 -112 rows)
- Final state: dengue 2023 = 36 weeks × 56 countries = 2,016 rows (đúng cutoff OpenDengue)
- **Verify backend API:**
  - `GET /risk-map/flu/latest` → 2026-W21, 163 countries ✓
  - `GET /risk-map/dengue/latest` → 2023-W36, 56 countries ✓ (Top 5: BRA 8820, MEX 6633, PER 3455, VNM 3250, NIC 3030)

## Phát hiện quan trọng

**1. Dengue degradation gentler so với flu — confirm session 21/05:**

Dengue lag dài (6-14 tuần) → AR signal phủ xa hơn flu lag (1-7 tuần). Cộng với pattern endemic năm cả 12 tháng ở vùng nhiệt đới → RF dengue mất chỉ ~0.010 R²/horizon, LGBM flu mất ~0.036/horizon. Đây là **insight epidemiological** không phải artifact của model.

**2. OpenDengue ground truth khoảng "vàng" cho nowcast:**

OpenDengue v1.3 batch-released tới 2023-W36. **Không phải extrapolation mù** — có thể compare prediction vs actual trên 2021-2023 để validate. Lý do dừng W36: từ 2024 OpenDengue chỉ có 23 đảo Pacific (sparse), 2025 zero weekly rows.

**3. Brazil dominate dengue ngay cả 2023:**

Brazil predict 8,820 cases tuần W36/2023 — gấp ~1.3× Mexico, ~2.5× Peru. Confirm decision log1p transform là đúng — không log1p, Brazil sẽ "drown out" tất cả nước khác trong gradient.

**4. Frontend state-leak khi switch disease — bug khó nhận thấy:**

zustand global state giữ year/week khi switch disease. Nếu flu đang xem 2026-W21, switch sang dengue thì uiStore.year = 2026 không hợp lệ với dengue (max 2023). Phải reset trong action `setDisease`, không phải trong component. Trade-off: mất context user đang xem, nhưng tránh confusion lớn hơn.

**5. Scheduler chỉ build flu — silent MLOps gap:**

`job_build_features` hardcode `--disease flu`. Nếu deploy lên production, dengue features sẽ stale từ tuần đầu. Đã fix bằng cách chạy cả 2 và return max(returncode) để CI catch failure.

## Files đã thay đổi

| File | Thay đổi | Loại |
|---|---|---|
| `frontend/src/store/uiStore.ts` | DISEASE_DEFAULTS + reset on switch | EDIT |
| `frontend/src/pages/HomePage.tsx` | prevDiseaseRef → reset applied | EDIT |
| `frontend/src/components/sidebar/WeekPicker.tsx` | DISEASE_CONFIG | REWRITE |
| `frontend/src/components/sidebar/RiskMapSidebar.tsx` | Pass disease prop | EDIT |
| `frontend/src/pages/DiseaseDetailPage.tsx` | VALID_YEARS + hint text | EDIT |
| `backend/app/services/scheduler.py` | build_features cả 2 bệnh + dengue nowcast job | EDIT |
| `backend/app/api/v1/endpoints/admin.py` | Add nowcast trigger | EDIT |
| `backend/app/services/feature_lookup.py` | Nowcast-aware warning | EDIT |
| `backend/app/schemas/prediction.py` | is_nowcast field | EDIT |
| `scripts/batch_predict.py` | --from-week/--to-week range | EDIT |
| DB | +7,808 feature_snapshots, +2,016 dengue 2023 predictions | DATA |

## Còn lại / chưa làm

- [ ] **Gửi email cho cô** — draft đã viết xong, đang chờ user gửi
- [ ] **Update Notion** — upload session summary này lên workspace root
- [ ] **Verify FE end-to-end** — manual test switch disease, click country → DiseaseDetailPage
- [ ] **Báo cáo Chương 4** — thực nghiệm + kết quả (cần viết)
- [ ] **Báo cáo Chương 5** — kết luận (cần viết)
- [ ] **CI/CD** — GitHub Actions chạy `npx tsc --noEmit` + backend pytest mỗi PR (sau demo)
- [ ] **Model registry** — bảng `model_versions` đã có schema nhưng chưa auto-register (sau demo)

## Những điều cần ghi nhớ cho báo cáo

**Câu chuyện khoa học mạnh cho Chương 4:**

> "Hệ thống mở rộng phạm vi dự báo theo 2 chiều: (1) **chiều ngang** — multi-horizon h=1..4 tuần (Phase C-1 ngày 21/05), R² duy trì > 0.75 sau 4 tuần flu, > 0.89 dengue, vượt benchmark Lowe 2014. (2) **chiều dọc** — nowcast realtime: flu 2026-W21 từ WHO FluNet API, dengue 2021-2023-W36 từ OpenDengue v1.3 batch (Phase A + nowcast extension ngày 23/05). Kết hợp 2 chiều → forecast có thể nói 'Tại Brazil tuần này (W21/2026 flu hoặc W36/2023 dengue), risk = High, 1,081 ca cúm dự kiến tuần tới, 8,820 ca dengue tuần tới'."

**Điểm khác biệt với baseline literature:**

- Lowe 2014: dengue Brazil 1 quốc gia, monthly grain → mình 56 quốc gia, weekly grain
- CDC FluSight: flu 1 quốc gia (US), seasonal → mình 163 quốc gia toàn cầu, all-year
- WHO EWARS: cảnh báo dựa endemic channel only → mình add multi-horizon ML predict + classifier

**Decision đã chốt cho thesis (consolidated):**

| Quyết định | Ngày chốt | Lý do |
|---|---|---|
| Hybrid Regression + Classification | 16/05 | Đáp ứng cả 2 yêu cầu đề tài: số ca + mức nguy cơ |
| Multi-horizon h=1..4 thay vì recursive | 21/05 | Tránh error propagation, mỗi h có model riêng |
| Dengue nowcast 2021-2023-W36 từ OpenDengue batch | 23/05 | Có ground truth, không phải extrapolation mù |
| Disease-aware UI state (reset on switch) | 23/05 | Tránh confusion, year/week khác phạm vi flu vs dengue |
| Scheduler build cả flu + dengue | 23/05 | Production deploy không bị stale features |

**Number tham chiếu cho slide:**

- Flu: 163 countries, 2026-W02 đến W21 (20 tuần realtime), R² h=1 0.866 → h=4 0.757
- Dengue: 56 countries, 2010-2019 train + 2021-2023-W36 nowcast, R² h=1 0.929 → h=4 0.898
- DB: 16 tables logic + 31 partitions, 87,668 disease_cases, 75,202 feature_snapshots, 74,983 predictions
- Pipeline: 4 cron jobs (sync_flunet Mon 10h, sync_weather daily 6h, build_features Mon 11h, batch_predict Mon 11h30)
