# Session 3: Merge → master_weekly_v1.csv (Notebook v5/v6)

> **Mục tiêu thuyết trình:** Người chấm hiểu merge data nhiều nguồn là phần dễ sai nhất — date format khác, country code khác, granularity khác. Một dòng merge sai = toàn bộ training meaningless.

---

## 1. Vấn đề: 3 dataset, 3 schema

| Nguồn | Key time | Key country | Granularity |
|---|---|---|---|
| FluNet | `ISO_YEAR, ISO_WEEK` | `COUNTRY_CODE` (ISO3 hoặc X09-X12 cho UK) | Weekly |
| OpenDengue | `calendar_start_date` (date) | `adm_0_iso` (ISO3) | Weekly + Monthly + Year |
| ERA5 (post-process) | `iso_year, iso_week` | `iso3` | Weekly broadcast từ monthly |

→ Phải **chuẩn hóa cả 3 về (iso3, iso_year, iso_week)** trước khi merge.

---

## 2. Cell 3.1 — Chuẩn bị FluNet

```python
# UK aggregation X09-X12 → GBR
flu['iso3'] = flu['COUNTRY_CODE'].replace({'X09': 'GBR', 'X10': 'GBR', 'X11': 'GBR', 'X12': 'GBR'})
# Sum INF_A + INF_B → influenza_total
flu['influenza_total'] = flu['INF_A'].fillna(0) + flu['INF_B'].fillna(0)
flu = flu.groupby(['iso3', 'ISO_YEAR', 'ISO_WEEK'])['influenza_total'].sum().reset_index()
flu.columns = ['iso3', 'iso_year', 'iso_week', 'influenza_total']
```

**UK aggregation X09-X12:** WHO không có mã GBR tổng hợp, England (X09) + Scotland (X10) + Wales (X11) + Northern Ireland (X12) báo cáo riêng → em sum thành GBR.

→ Sau prep: FluNet 113K rows → 75K rows (sau khi gộp + dedupe).

---

## 3. Cell 3.2 — Chuẩn bị Dengue

```python
# Convert calendar_start_date → ISO week
dengue['iso_year'] = pd.to_datetime(dengue['calendar_start_date']).dt.isocalendar().year
dengue['iso_week'] = pd.to_datetime(dengue['calendar_start_date']).dt.isocalendar().week
# Filter T_res = Week, period training 2015-2019
dengue = dengue[dengue['T_res'].isin(['Week', 'Month']) & dengue['iso_year'].between(2015, 2019)]
dengue = dengue.rename(columns={'adm_0_iso': 'iso3', 'dengue_total': 'dengue_cases'})
```

**T_res handling:** Một số nước báo cáo Month thay Week → broadcast monthly → weekly đều theo proportion.

---

## 4. Cell 3.3 — Verify country coverage

```python
# Coverage matrix: nước nào có data cả 3 nguồn
flu_countries    = set(flu['iso3'].unique())     # 189 nước
dengue_countries = set(dengue['iso3'].unique())  # 35 nước (2015-2019)
era5_countries   = set(era5['iso3'].unique())    # 197 nước

both_disease_era5 = (flu_countries | dengue_countries) & era5_countries
# 163 nước có ít nhất 1 disease + có ERA5
```

**163 nước** = intersection set sau khi merge (chi tiết ở 3.6).

---

## 5. Cell 3.4, 3.5 — Merge từng cặp

```python
# FluNet + ERA5 (left join — giữ tất cả flu rows, gắn weather nếu có)
flu_era5 = flu.merge(era5, on=['iso3', 'iso_year', 'iso_week'], how='left')

# Dengue + ERA5 (left join tương tự)
dengue_era5 = dengue.merge(era5, on=['iso3', 'iso_year', 'iso_week'], how='left')
```

**Loại join chọn:**

| Join | Khi nào dùng | Lý do |
|---|---|---|
| `inner` | Giữ rows chung 2 bảng | Mất data → KHÔNG dùng |
| **`left`** | Giữ tất cả flu/dengue rows | Đảm bảo không mất disease data, weather NaN sẽ fillna sau |
| `outer` | Giữ tất cả rows từ cả 2 | Inflate rows lên gấp đôi → KHÔNG dùng |

---

## 6. Cell 3.6 — Combine flu + dengue + ERA5

```python
# Outer join flu+dengue trên (iso3, year, week) để giữ tất cả country
master = flu_era5.merge(
    dengue_era5[['iso3', 'iso_year', 'iso_week', 'dengue_cases']],
    on=['iso3', 'iso_year', 'iso_week'], how='outer',
)
master.to_csv(PROCESSED / 'master_weekly_v1.csv', index=False)
```

---

## 7. Cell 3.7 — Sanity check master file

| Property | Value |
|---|---|
| **Shape** | **61,112 × 27 cols** |
| Size | 20.9 MB |
| Countries | **163** |
| Time | 2010-2019 (520 ISO weeks) |

**Breakdown rows:**

| Type | Rows | Mô tả |
|------|------|-------|
| Chỉ flu (no dengue) | 52,750 | Châu Âu, Bắc Mỹ, Bắc Á |
| Chỉ dengue (no flu) | 1,947 | Một số đảo nhỏ tropical |
| **Cả flu + dengue** | **6,415** | Brazil, Thailand, Vietnam, Mexico, Indonesia |

**Coverage 92% dân số thế giới.** Mất 21 nước flu + 30 nước dengue do KD-tree không match đảo nhỏ Pacific (Tuvalu, Nauru, Maldives) → known limitation.

---

## 8. Bugs critical đã fix

### Bug 1: Path `dataset/epidemic/processed/` vs `dataset/processed/`

Lúc đầu lưu master vào `dataset/epidemic/processed/` — nhưng master là **cross-domain** (epidemic + weather), không thuộc riêng epidemic.

**Fix:** chuyển lên top-level `dataset/processed/`.

### Bug 2: Linux case-sensitive `Dataset` vs `dataset`

Drive cũ dùng `Dataset/` (D viết hoa). Linux case-sensitive — Colab `pd.read_csv('dataset/...')` báo not found.

**Fix:** rename toàn bộ về lowercase + sửa pipeline.

---

## Key Insights Session 3 (slide thuyết trình)

1. **Merge ≠ join SQL** — phải xử lý date format, country code mismatch, granularity TRƯỚC khi join. 80% effort pre-processing, 20% là `pd.merge`.
2. **Outer join cho flu+dengue, left join cho ERA5** — quyết định join type quan trọng. Sai = mất data hoặc inflate rows.
3. **UK aggregation X09-X12 → GBR** — domain knowledge không có trong docs, chỉ phát hiện qua EDA coverage matrix.
4. **163 nước = 92% world coverage** — known limitation do KD-tree mapping ERA5 (Session 2), document rõ.
5. **Master = single source of truth** — sau Session 3, không bao giờ chạy lại Session 1-2 nữa. Mọi feature engineering và training đọc từ `master_weekly_v1.csv`.

---

## Câu nói thuyết trình cho Session 3

> "Sau Session 1-2 em có 3 nguồn riêng: FluNet 113 nghìn rows, OpenDengue 18 nghìn rows weekly, ERA5 102 nghìn rows. Session 3 là **merge thành 1 master**."
>
> "Quyết định khó nhất là **loại join**. Em dùng **outer join flu+dengue** (giữ tất cả country) và **left join ERA5** (gắn weather vào, không loại country thiếu weather match)."
>
> [NHẤN MẠNH] "Domain knowledge em phát hiện qua EDA coverage: **WHO không có mã GBR cho UK**, mà tách thành X09 (England), X10 (Scotland), X11 (Wales), X12 (Northern Ireland). Em sum 4 mã này thành GBR. Đây là 1 dòng code nhưng nếu thiếu thì UK biến mất khỏi map."
>
> "Output: `master_weekly_v1.csv` **61,112 rows × 27 cols**, **163 quốc gia × 2010-2019**. Trong đó 52K rows chỉ có flu, 2K chỉ có dengue, **6.4K cả 2** — đây là intersection Brazil/Thailand/Vietnam/Mexico."
>
> "Coverage **92% dân số thế giới**, mất 53 đảo nhỏ Pacific do KD-tree không match — known limitation em document trong báo cáo."
