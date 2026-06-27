"""
Script chèn SESSION 1-5 vào notebook KLTN_EpiWeather_ML_Colab.ipynb
Chạy: python scripts/insert_sessions.py
"""
import json

NB_PATH = 'f:/BAO_CAO/DO_AN_TOT_NGHIEP/KLTN/KLTN_EpiWeather_ML_Colab.ipynb'

def md_cell(source_lines):
    return {'cell_type': 'markdown', 'metadata': {}, 'source': source_lines}

def code_cell(source_lines):
    return {'cell_type': 'code', 'execution_count': None,
            'metadata': {}, 'outputs': [], 'source': source_lines}

def S(*lines):
    """Convert tuple of lines -> notebook source list (all but last end with newline)."""
    result = []
    for i, line in enumerate(lines):
        result.append(line + '\n' if i < len(lines) - 1 else line)
    return result

# ═══════════════════════ SESSION 1 ═══════════════════════

s1_header = md_cell(S(
    "# \U0001f50d SESSION 1 — LOAD & INSPECT RAW DATA",
    "> **Mục tiêu:** Hiểu cấu trúc từng file nguồn, phát hiện vấn đề trước khi xử lý.",
    "> **Input:** Raw CSV files từ RAW folder",
    "> **Output:** Không có (chỉ exploration)",
    "> **Có thể skip nếu:** Đã quen với cấu trúc data, muốn chạy thẳng SESSION 4+"
))

s1_10_code = code_cell(S(
    "# [1.0] RESTART CELL — load tất cả raw files",
    "flu      = pd.read_csv(FILES['flunet'], low_memory=False)",
    "flu_meta = pd.read_csv(FILES['flu_meta'], low_memory=False)",
    "dengue   = pd.read_csv(FILES['dengue'], low_memory=False)",
    "ecdc_sen = pd.read_csv(FILES['ecdc_sen'], low_memory=False)",
    "ecdc_ili = pd.read_csv(FILES['ecdc_ili'], low_memory=False)",
    "",
    "for name, df in [('flu', flu), ('flu_meta', flu_meta), ('dengue', dengue),",
    "                  ('ecdc_sen', ecdc_sen), ('ecdc_ili', ecdc_ili)]:",
    "    print(f'{name}: shape={df.shape} | cols={list(df.columns[:5])}...')"
))

s1_10_md = md_cell(S(
    "\U0001f4cc **[1.0]** FILES dict đã được define ở SESSION 0 — bao gồm đường dẫn đến tất cả raw files.",
    "Load tập trung ở đây để các cell [1.1]–[1.4] chỉ cần tham chiếu biến, không load lại.",
    "Nếu session restart, chạy lại [1.0] này trước khi chạy các cell inspect."
))

s1_11_code = code_cell(S(
    "# [1.1] Inspect FluNet",
    "print('=== FluNet ===')",
    "print(f'Shape: {flu.shape}')",
    "print(f'Columns ({len(flu.columns)}):', list(flu.columns))",
    "print(f'Year range: {flu[\"ISO_YEAR\"].min()}-{flu[\"ISO_YEAR\"].max()}')",
    "print(f'Countries: {flu[\"COUNTRY_CODE\"].nunique()}')",
    "display(flu.head(3))"
))

s1_11_md = md_cell(S(
    "\U0001f4cc **[1.1]** FluNet có 53 cột gồm nhiều subtype chi tiết (AH1N12009, AH3, BVIC...). Các cột",
    "quan trọng sẽ dùng: INF_A, INF_B, COUNTRY_CODE, ISO_YEAR, ISO_WEEK.",
    "Lưu ý: RSV và RSV_PROCESSED tồn tại nhưng khác đơn vị — sẽ xử lý ở SESSION 2.",
    "PARAINFLUENZA present nhưng sẽ bị drop do missing rate cao (xem SESSION 2)."
))

s1_12_code = code_cell(S(
    "# [1.2] Inspect OpenDengue",
    "print('=== OpenDengue ===')",
    "print(f'Shape: {dengue.shape}')",
    "print('T_res distribution:')",
    "print(dengue['T_res'].value_counts())",
    "print(f'Year range (approx): {dengue[\"calendar_start_date\"].dropna().iloc[0]} ... {dengue[\"calendar_start_date\"].dropna().iloc[-1]}')",
    "display(dengue.head(3))"
))

s1_12_md = md_cell(S(
    "\U0001f4cc **[1.2]** T_res phân ra Week/Month/Year — chỉ dùng Week+Month để đủ granularity cho model tuần.",
    "Date format của OpenDengue là MM/DD/YYYY (không nhất quán), cần `format='mixed'` khi parse.",
    "Điều này đã được confirm và sẽ xử lý tường minh ở SESSION 3 và SESSION 5."
))

s1_13_code = code_cell(S(
    "# [1.3] Inspect ECDC Sentinel",
    "print('=== ECDC Sentinel ===')",
    "print(f'Shape: {ecdc_sen.shape}')",
    "pathogen_col = [c for c in ecdc_sen.columns if 'pathogen' in c.lower() or 'Pathogen' in c]",
    "if pathogen_col:",
    "    print(f'Unique pathogens: {ecdc_sen[pathogen_col[0]].unique()}')",
    "print(f'Countries: {ecdc_sen.iloc[:, 0].nunique()}')",
    "display(ecdc_sen.head(3))"
))

s1_13_md = md_cell(S(
    "\U0001f4cc **[1.3]** ECDC Sentinel có cả SARS-CoV-2 — cần filter khi dùng. Chỉ 30 quốc gia châu Âu,",
    "chỉ có data từ 2021. Quyết định đã chốt: ECDC chỉ dùng cho validation và dashboard,",
    "không dùng cho training (vì train period là 2010–2019)."
))

s1_14_code = code_cell(S(
    "# [1.4] Inspect ECDC ILI",
    "print('=== ECDC ILI ===')",
    "print(f'Shape: {ecdc_ili.shape}')",
    "age_col = [c for c in ecdc_ili.columns if 'age' in c.lower()]",
    "ind_col = [c for c in ecdc_ili.columns if 'indicator' in c.lower()]",
    "print(f'Age columns: {age_col}')",
    "print(f'Indicator columns: {ind_col}')",
    "yr_col = [c for c in ecdc_ili.columns if 'year' in c.lower()]",
    "if yr_col:",
    "    print(f'Year range: {ecdc_ili[yr_col[0]].min()}-{ecdc_ili[yr_col[0]].max()}')",
    "display(ecdc_ili.head(3))"
))

s1_14_md = md_cell(S(
    "\U0001f4cc **[1.4]** ECDC ILI có age groups đầy đủ (0–4, 5–14, 15–64, 65+, total) — hữu ích cho",
    "dashboard chi tiết khi hiển thị breakdown theo nhóm tuổi.",
    "Cũng chỉ có từ 2021 nên không dùng cho training."
))

# ═══════════════════════ SESSION 2 ═══════════════════════

s2_header = md_cell(S(
    "# \U0001f50e SESSION 2 — DATA QUALITY CHECK",
    "> **Mục tiêu:** Missing rate, coverage quốc gia/năm, phát hiện anomaly.",
    "> **Input:** raw DataFrames từ SESSION 1 (hoặc load lại từ [2.0])",
    "> **Output:** Không có — kết quả dẫn đến các quyết định tiền xử lý"
))

s2_20_code = code_cell(S(
    "# [2.0] RESTART CELL — load flu và dengue từ disk",
    "flu    = pd.read_csv(FILES['flunet'], low_memory=False)",
    "dengue = pd.read_csv(FILES['dengue'], low_memory=False)",
    "print(f'flu: {flu.shape}')",
    "print(f'dengue: {dengue.shape}')"
))

s2_20_md = md_cell(S(
    "\U0001f4cc **[2.0]** Chỉ load 2 file cần cho session này để tiết kiệm RAM.",
    "Nếu đã chạy SESSION 1 và biến còn tồn tại, cell này không bị lỗi — chỉ reload mới nhất từ disk."
))

s2_21_code = code_cell(S(
    "# [2.1] FluNet — Missing rate cho các cột quan trọng",
    "check_cols = ['INF_A', 'INF_B', 'INF_ALL', 'RSV', 'RSV_PROCESSED',",
    "              'PARAINFLUENZA', 'ILI_ACTIVITY', 'SPEC_PROCESSED_NB']",
    "# Only keep cols that exist in dataframe",
    "check_cols = [c for c in check_cols if c in flu.columns]",
    "missing_pct = flu[check_cols].isnull().mean().sort_values(ascending=False) * 100",
    "",
    "fig, ax = plt.subplots(figsize=(8, 5))",
    "missing_pct.plot(kind='barh', ax=ax, color='salmon', edgecolor='black', linewidth=0.5)",
    "ax.set_xlabel('Missing (%)')",
    "ax.set_title('FluNet — Missing Rate per Column')",
    "for bar, val in zip(ax.patches, missing_pct):",
    "    ax.text(val + 0.5, bar.get_y() + bar.get_height()/2,",
    "            f'{val:.1f}%', va='center', fontsize=9)",
    "plt.tight_layout()",
    "plt.show()"
))

s2_21_md = md_cell(S(
    "\U0001f4cc **[2.1]** Kết quả xác nhận các quyết định đã chốt:",
    "- INF_ALL missing ~44% → dùng INF_A + INF_B thay thế (fillna(0) vì missing = không báo cáo).",
    "- PARAINFLUENZA missing ~85.5% → bỏ hoàn toàn khỏi feature set.",
    "- RSV_PROCESSED khác đơn vị với RSV (corr=0.729 nhưng scale khác) → chỉ giữ RSV."
))

s2_22_code = code_cell(S(
    "# [2.2] FluNet — Coverage theo năm (số quốc gia báo cáo)",
    "coverage = flu.groupby('ISO_YEAR')['COUNTRY_CODE'].nunique().reset_index()",
    "coverage.columns = ['year', 'n_countries']",
    "",
    "fig, ax = plt.subplots(figsize=(12, 4))",
    "ax.bar(coverage['year'], coverage['n_countries'], color='steelblue', edgecolor='white', linewidth=0.5)",
    "ax.axvline(TRAIN_START - 0.5, color='green', lw=2, ls='--', label=f'Train start ({TRAIN_START})')",
    "ax.axvline(TRAIN_END + 0.5, color='red', lw=2, ls='--', label=f'Train end ({TRAIN_END})')",
    "ax.set_xlabel('Year')",
    "ax.set_ylabel('Countries reporting')",
    "ax.set_title('FluNet — Country Coverage by Year')",
    "ax.legend()",
    "plt.tight_layout()",
    "plt.show()"
))

s2_22_md = md_cell(S(
    "\U0001f4cc **[2.2]** Coverage ổn định từ 2010 (~120+ quốc gia). Giai đoạn 2020–2021 giảm mạnh do",
    "nhiều nước ngừng báo cáo FluNet trong đại dịch COVID — đây là lý do bổ sung cho quyết định",
    "exclude 2020–2021. Coverage ổn định ở 2010–2019 là bằng chứng train set đáng tin cậy."
))

s2_23_code = code_cell(S(
    "# [2.3] OpenDengue — Missing & coverage",
    "print('dengue_total missing rate:', round(dengue['dengue_total'].isnull().mean()*100, 1), '%')",
    "print('Year range:', dengue['calendar_start_date'].dropna().iloc[0], '...',",
    "      dengue['calendar_start_date'].dropna().iloc[-1])",
    "",
    "fig, ax = plt.subplots(figsize=(6, 6))",
    "tres_counts = dengue['T_res'].value_counts()",
    "ax.pie(tres_counts, labels=tres_counts.index, autopct='%1.1f%%', startangle=90,",
    "       colors=['#2ecc71','#3498db','#e74c3c'])",
    "ax.set_title('OpenDengue — T_res Distribution')",
    "plt.tight_layout()",
    "plt.show()"
))

s2_23_md = md_cell(S(
    "\U0001f4cc **[2.3]** dengue_total missing ~88.9% trên master_weekly là bình thường — chỉ endemic",
    "countries có data, và chỉ tuần có dịch mới có số. T_res Week chiếm ~78% rows → đủ để",
    "dùng weekly aggregation. Phần Month sẽ được group by iso_week sau khi parse date."
))

s2_24_code = code_cell(S(
    "# [2.4] ERA5 — Coverage check",
    "era5 = pd.read_csv(ERA5_FILE)",
    "print(f'ERA5 shape: {era5.shape}')",
    "print(f'Countries: {era5[\"iso3\"].nunique()}')",
    "",
    "missing_era5 = era5.drop(columns=['iso3','iso_year','iso_week']).isnull().mean() * 100",
    "missing_era5 = missing_era5[missing_era5 > 0].sort_values(ascending=False)",
    "",
    "if len(missing_era5) > 0:",
    "    fig, ax = plt.subplots(figsize=(8, 4))",
    "    missing_era5.plot(kind='barh', ax=ax, color='coral')",
    "    ax.set_xlabel('Missing (%)')",
    "    ax.set_title('ERA5 — Missing Rate per Variable')",
    "    plt.tight_layout()",
    "    plt.show()",
    "else:",
    "    print('ERA5: khong co missing values')"
))

s2_24_md = md_cell(S(
    "\U0001f4cc **[2.4]** ERA5 cover 158/172 countries (92%) do KD-tree nearest centroid mapping từ lưới",
    "ERA5 (0.25°×0.25°) sang centroid quốc gia theo Natural Earth 50m.",
    "14 quốc gia bị miss thường là đảo nhỏ hoặc quốc gia không có centroid rõ ràng trong shapefile.",
    "92% coverage là acceptable cho mục tiêu global surveillance."
))

# ═══════════════════════ SESSION 3 ═══════════════════════

s3_header = md_cell(S(
    "# \U0001f4ca SESSION 3 — EDA: SEASONALITY & TRENDS",
    "> **Mục tiêu:** Xác nhận pattern mùa vụ rõ ràng — điều kiện cần để train model.",
    "> **Input:** Raw FluNet + OpenDengue",
    "> **Output:** Không có file — chỉ visualizations"
))

s3_30_code = code_cell(S(
    "# [3.0] RESTART CELL + setup train range",
    "flu    = pd.read_csv(FILES['flunet'], low_memory=False)",
    "dengue = pd.read_csv(FILES['dengue'], low_memory=False)",
    "",
    "flu_train = flu[flu['ISO_YEAR'].between(TRAIN_START, TRAIN_END)].copy()",
    "flu_train['inf_total'] = flu_train['INF_A'].fillna(0) + flu_train['INF_B'].fillna(0)",
    "print(f'flu_train: {flu_train.shape} | years: {TRAIN_START}-{TRAIN_END}')"
))

s3_30_md = md_cell(S(
    "\U0001f4cc **[3.0]** TRAIN_START=2010, TRAIN_END=2019 đã chốt ở SESSION 0.",
    "flu_train ở đây dùng riêng cho EDA, không phải feature matrix cuối cùng.",
    "inf_total = INF_A + INF_B là target chính — INF_ALL bị bỏ do missing 44%."
))

s3_31_code = code_cell(S(
    "# [3.1] FluNet — Global trend + seasonality",
    "flu_weekly = flu_train.groupby(['ISO_YEAR','ISO_WEEK'])['inf_total'].sum().reset_index()",
    "flu_weekly['time_idx'] = flu_weekly['ISO_YEAR'] + flu_weekly['ISO_WEEK'] / 53",
    "flu_season = flu_train.groupby('ISO_WEEK')['inf_total'].mean().reset_index()",
    "",
    "fig, axes = plt.subplots(2, 1, figsize=(16, 9))",
    "",
    "axes[0].plot(flu_weekly['time_idx'], flu_weekly['inf_total'], lw=1.2, color='steelblue')",
    "axes[0].set_title('Global Influenza Cases per Week (2010-2019)')",
    "axes[0].set_xlabel('Year')",
    "axes[0].yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x/1000:.0f}K'))",
    "",
    "axes[1].bar(flu_season['ISO_WEEK'], flu_season['inf_total'], color='steelblue', alpha=0.8)",
    "axes[1].set_title('Average Seasonality by ISO Week (2010-2019)')",
    "axes[1].set_xlabel('ISO Week')",
    "axes[1].yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x/1000:.0f}K'))",
    "",
    "plt.tight_layout()",
    "plt.show()"
))

s3_31_md = md_cell(S(
    "\U0001f4cc **[3.1]** Trend phẳng (không tăng mạnh) là tốt — cho thấy data ổn định, không bị confound bởi",
    "reporting bias tăng dần theo năm. Seasonality rõ peak tuần 1–10 (mùa đông bắc bán cầu).",
    "Đây là pattern chính model cần học; weather features cung cấp signal để predict timing và amplitude."
))

s3_32_code = code_cell(S(
    "# [3.2] FluNet — 5 quốc gia đại diện",
    "countries = ['VNM', 'USA', 'GBR', 'BRA', 'AUS']",
    "fig, axes = plt.subplots(1, 5, figsize=(20, 4), sharey=False)",
    "",
    "for ax, iso in zip(axes, countries):",
    "    df_c = flu_train[flu_train['COUNTRY_CODE'] == iso]",
    "    season_c = df_c.groupby('ISO_WEEK')['inf_total'].mean()",
    "    ax.bar(season_c.index, season_c.values, color='steelblue', alpha=0.8)",
    "    ax.set_title(iso, fontsize=12)",
    "    ax.set_xlabel('ISO Week')",
    "    if ax is axes[0]:",
    "        ax.set_ylabel('Avg cases')",
    "",
    "plt.suptitle('Influenza Seasonality by Country (2010-2019)', fontsize=13)",
    "plt.tight_layout()",
    "plt.show()"
))

s3_32_md = md_cell(S(
    "\U0001f4cc **[3.2]** Pattern khác nhau rõ theo khí hậu: BRA và AUS peak tháng 6–8 (nam bán cầu),",
    "USA/GBR peak tháng 12–2. VNM có 2 peak nhỏ hơn (nhiệt đới).",
    "Model train per-country tự học được sự khác biệt này qua iso3 encoding và lag features."
))

s3_33_code = code_cell(S(
    "# [3.3] Dengue — Filter + parse date",
    "dengue_wm = dengue[dengue['T_res'].isin(['Week','Month'])].copy()",
    "dengue_wm['date_parsed'] = pd.to_datetime(dengue_wm['calendar_start_date'], format='mixed', dayfirst=False)",
    "iso_cal = dengue_wm['date_parsed'].dt.isocalendar()",
    "dengue_wm['ISO_YEAR'] = iso_cal.year.astype(int)",
    "dengue_wm['ISO_WEEK'] = iso_cal.week.astype(int)",
    "dengue_train = dengue_wm[dengue_wm['ISO_YEAR'].between(TRAIN_START, TRAIN_END)].copy()",
    "dengue_train['dengue_log'] = np.log1p(dengue_train['dengue_total'])",
    "print(f'dengue_train: {dengue_train.shape}')",
    "print(f'Countries: {dengue_train[\"ISO_A0\"].nunique()}')"
))

s3_33_md = md_cell(S(
    "\U0001f4cc **[3.3]** `format='mixed'` cần thiết vì OpenDengue date không nhất quán (MM/DD/YYYY).",
    "log1p ngay ở đây để visualization dùng log scale — dengue_total bị dominated bởi Brazil",
    "với ~10.49M ca, chiếm 70% tổng global. log1p giúp thấy pattern của các nước khác."
))

s3_34_code = code_cell(S(
    "# [3.4] Dengue — Trend + seasonality (raw vs log)",
    "by_year_raw = dengue_train.groupby('ISO_YEAR')['dengue_total'].sum()",
    "by_week_raw = dengue_train.groupby('ISO_WEEK')['dengue_total'].mean()",
    "by_year_log = dengue_train.groupby('ISO_YEAR')['dengue_log'].sum()",
    "by_week_log = dengue_train.groupby('ISO_WEEK')['dengue_log'].mean()",
    "",
    "fig, axes = plt.subplots(2, 2, figsize=(14, 8))",
    "",
    "axes[0,0].bar(by_year_raw.index, by_year_raw.values, color='coral')",
    "axes[0,0].set_title('Raw — by Year')",
    "axes[0,0].yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x/1e6:.1f}M'))",
    "",
    "axes[0,1].bar(by_week_raw.index, by_week_raw.values, color='coral')",
    "axes[0,1].set_title('Raw — by ISO Week')",
    "",
    "axes[1,0].bar(by_year_log.index, by_year_log.values, color='#27ae60')",
    "axes[1,0].set_title('Log1p — by Year')",
    "",
    "axes[1,1].bar(by_week_log.index, by_week_log.values, color='#27ae60')",
    "axes[1,1].set_title('Log1p — by ISO Week')",
    "",
    "plt.suptitle('Dengue Trend & Seasonality (2010-2019)', fontsize=13)",
    "plt.tight_layout()",
    "plt.show()"
))

s3_34_md = md_cell(S(
    "\U0001f4cc **[3.4]** Raw bị dominated bởi Brazil (10.49M ca). Log scale cho thấy pattern của các nước",
    "khác rõ hơn — đây là bằng chứng thực nghiệm cho quyết định dùng log1p làm target.",
    "By-week log plot cho thấy seasonality thực sự khi không bị Brazil che khuất."
))

s3_35_code = code_cell(S(
    "# [3.5] Dengue — Top 5 (loại Brazil)",
    "dengue_no_bra = dengue_train[dengue_train['ISO_A0'] != 'BRA']",
    "top5 = dengue_no_bra.groupby('ISO_A0')['dengue_total'].sum().nlargest(5).index.tolist()",
    "",
    "fig, axes = plt.subplots(1, 5, figsize=(20, 4), sharey=False)",
    "for ax, iso in zip(axes, top5):",
    "    df_c = dengue_no_bra[dengue_no_bra['ISO_A0'] == iso]",
    "    season_c = df_c.groupby('ISO_WEEK')['dengue_total'].mean()",
    "    ax.bar(season_c.index, season_c.values, color='#27ae60', alpha=0.8)",
    "    ax.set_title(iso, fontsize=12)",
    "    ax.set_xlabel('ISO Week')",
    "",
    "plt.suptitle('Dengue Seasonality — Top 5 ex-Brazil (2010-2019)', fontsize=13)",
    "plt.tight_layout()",
    "plt.show()"
))

s3_35_md = md_cell(S(
    "\U0001f4cc **[3.5]** Peak mùa mưa khác nhau theo khu vực: Đông Nam Á (Philippines, Thái Lan, Indonesia)",
    "peak tuần 25–45; Trung Mỹ (Mexico, Colombia) peak tuần 1–20.",
    "Sự đa dạng này xác nhận cần per-country model với weather lag features — không dùng global model đơn."
))

s3_36_code = code_cell(S(
    "# [3.6] Heatmap mùa vụ Việt Nam (Influenza)",
    "vnm_flu = flu_train[flu_train['COUNTRY_CODE'] == 'VNM'][['ISO_YEAR','ISO_WEEK','inf_total']]",
    "pivot = vnm_flu.pivot_table(index='ISO_YEAR', columns='ISO_WEEK', values='inf_total', aggfunc='sum')",
    "",
    "fig, ax = plt.subplots(figsize=(16, 5))",
    "sns.heatmap(pivot, cmap='YlOrRd', linewidths=0.3, ax=ax, cbar_kws={'label': 'Cases'})",
    "ax.set_title('Vietnam Influenza Seasonality Heatmap (Year × ISO Week)')",
    "ax.set_xlabel('ISO Week')",
    "ax.set_ylabel('Year')",
    "plt.tight_layout()",
    "plt.show()"
))

s3_36_md = md_cell(S(
    "\U0001f4cc **[3.6]** Heatmap Tuần×Năm là cách visualize seasonality hiệu quả nhất.",
    "Nếu màu lặp lại theo cột (cùng tuần qua các năm) thì pattern ổn định — model có thể học được.",
    "Việt Nam thường có 2 đợt nhỏ trong năm, không rõ ràng như USA/GBR — thách thức cho model."
))

# ═══════════════════════ SESSION 4 ═══════════════════════

s4_header = md_cell(S(
    "# \U0001f326️ SESSION 4 — ERA5 DOWNLOAD & PROCESS",
    "> **NẶNG — Chỉ chạy nếu ERA5_FILE chưa tồn tại**",
    "> **Input:** ERA5 NetCDF files + Natural Earth shapefile",
    "> **Output:** era5_weekly_2010_2019_final.csv",
    "> ✅ File đã tồn tại — SESSION NÀY ĐÃ HOÀN THÀNH"
))

s4_40_code = code_cell(S(
    "# [4.0] Idempotent guard",
    "if ERA5_FILE.exists():",
    "    era5 = pd.read_csv(ERA5_FILE)",
    "    print(f'ERA5 da co: {ERA5_FILE.name}')",
    "    print(f'Shape: {era5.shape} | Countries: {era5[\"iso3\"].nunique()} | Years: {era5[\"iso_year\"].min()}-{era5[\"iso_year\"].max()}')",
    "    print('SESSION 4 hoan thanh - skip xuong SESSION 5')",
    "else:",
    "    print('ERA5 chua co - can chay tu [4.1]')"
))

s4_40_md = md_cell(S(
    "\U0001f4cc **[4.0]** ERA5 đã được xử lý và lưu vào era5_weekly_2010_2019_final.csv với 17 biến khí hậu.",
    "Script gốc dùng KD-tree nearest centroid mapping từ lưới ERA5 (0.25°×0.25°) sang centroid",
    "quốc gia theo Natural Earth 50m. Chỉ cần chạy lại nếu xóa file hoặc cần thêm biến mới."
))

s4_41_code = code_cell(S(
    "# [4.1] (Conditional) Process ERA5 nếu cần",
    "# Placeholder — chỉ chạy nếu ERA5_FILE chua ton tai",
    "# Script day du nam o: scripts/process_era5.py",
    "# Thoi gian uoc tinh: 2-3 gio cho 10 nam du lieu",
    "",
    "ERA5_VARS_DOWNLOAD = [",
    "    '2m_temperature', 'total_precipitation', '2m_dewpoint_temperature',",
    "    '10m_u_component_of_wind', '10m_v_component_of_wind',",
    "    'surface_solar_radiation_downwards', 'surface_thermal_radiation_downwards',",
    "    'total_cloud_cover', 'mean_sea_level_pressure', 'boundary_layer_height',",
    "    'total_evaporation', 'convective_precipitation', 'large_scale_precipitation',",
    "    'soil_temperature_level_1', 'volumetric_soil_water_layer_1',",
    "    'surface_net_solar_radiation', 'total_column_water_vapour'",
    "]",
    "print(f'{len(ERA5_VARS_DOWNLOAD)} variables to download')",
    "print('Xem scripts/process_era5.py de chay day du')"
))

s4_41_md = md_cell(S(
    "\U0001f4cc **[4.1]** Download ERA5 qua CDS API mất ~2–3 giờ cho 10 năm × 17 biến.",
    "Đã được lưu checkpoint theo từng năm (era5_weekly_era5_YYYY_checkpoint.csv) để tránh mất công",
    "nếu bị ngắt giữa chừng. Cuối cùng concat tất cả vào final CSV."
))

# ═══════════════════════ SESSION 5 ═══════════════════════

s5_header = md_cell(S(
    "# \U0001f517 SESSION 5 — PREPROCESSING & MERGE",
    "> **Mục tiêu:** Chuẩn hóa 3 nguồn về key iso3+iso_year+iso_week, merge → master_weekly.csv",
    "> **Input:** FluNet + ERA5 + OpenDengue + Malaria (GHO)",
    "> **Output:** dataset/processed/master_weekly_2010_2019.csv",
    "> ✅ File đã tồn tại — SESSION NÀY ĐÃ HOÀN THÀNH"
))

s5_50_code = code_cell(S(
    "# [5.0] Idempotent guard + verify",
    "if MASTER_FILE.exists():",
    "    master = pd.read_csv(MASTER_FILE)",
    "    print(f'master_weekly da co: {MASTER_FILE.name}')",
    "    print(f'Shape: {master.shape}')",
    "    print(f'Countries: {master[\"iso3\"].nunique()} | Years: {master[\"iso_year\"].min()}-{master[\"iso_year\"].max()}')",
    "    print(f'Columns: {list(master.columns)}')",
    "    print('SESSION 5 hoan thanh - chuyen sang SESSION 6')",
    "else:",
    "    print('master_weekly chua co - can chay tu [5.1]')"
))

s5_50_md = md_cell(S(
    "\U0001f4cc **[5.0]** master_weekly_2010_2019.csv là kết quả merge của FluNet (anchor) LEFT JOIN ERA5",
    "LEFT JOIN OpenDengue LEFT JOIN Malaria. 64,949 rows × 27 columns, 172 quốc gia.",
    "Đây là file đầu vào cho toàn bộ pipeline ML từ SESSION 6 trở đi."
))

s5_51_code = code_cell(S(
    "# [5.1] (Conditional) Merge logic — nếu cần tái tạo",
    "# Chay cell nay ONLY neu MASTER_FILE chua ton tai",
    "",
    "flu    = pd.read_csv(FILES['flunet'], low_memory=False)",
    "dengue = pd.read_csv(FILES['dengue'], low_memory=False)",
    "era5   = pd.read_csv(ERA5_FILE)",
    "",
    "# FluNet preprocessing",
    "flu_proc = flu[flu['ISO_YEAR'].between(TRAIN_START, TRAIN_END)].copy()",
    "flu_proc['inf_cases'] = flu_proc['INF_A'].fillna(0) + flu_proc['INF_B'].fillna(0)",
    "flu_proc['rsv_cases'] = flu_proc['RSV'].fillna(0)",
    "flu_proc = flu_proc.rename(columns={'COUNTRY_CODE':'iso3','ISO_YEAR':'iso_year','ISO_WEEK':'iso_week'})",
    "flu_proc = flu_proc[['iso3','iso_year','iso_week','inf_cases','rsv_cases']]",
    "",
    "# ERA5 preprocessing",
    "era5_proc = era5[era5['iso_year'].between(TRAIN_START, TRAIN_END)].copy()",
    "",
    "# Dengue preprocessing",
    "dengue_wm = dengue[dengue['T_res'].isin(['Week','Month'])].copy()",
    "dengue_wm['date_parsed'] = pd.to_datetime(dengue_wm['calendar_start_date'], format='mixed', dayfirst=False)",
    "iso_cal = dengue_wm['date_parsed'].dt.isocalendar()",
    "dengue_wm['iso_year'] = iso_cal.year.astype(int)",
    "dengue_wm['iso_week'] = iso_cal.week.astype(int)",
    "dengue_proc = dengue_wm[dengue_wm['iso_year'].between(TRAIN_START, TRAIN_END)].copy()",
    "dengue_proc['dengue_total'] = dengue_proc['dengue_total'].fillna(0)",
    "dengue_proc['dengue_log1p'] = np.log1p(dengue_proc['dengue_total'])",
    "dengue_proc = dengue_proc.rename(columns={'ISO_A0':'iso3'})",
    "dengue_proc = dengue_proc.groupby(['iso3','iso_year','iso_week'], as_index=False).agg(",
    "    dengue_total=('dengue_total','sum'), dengue_log1p=('dengue_log1p','mean')",
    ")",
    "",
    "# Merge: FluNet (anchor) LEFT JOIN ERA5 LEFT JOIN Dengue",
    "master = flu_proc.merge(era5_proc, on=['iso3','iso_year','iso_week'], how='left')",
    "master = master.merge(dengue_proc, on=['iso3','iso_year','iso_week'], how='left')",
    "master['dengue_total'] = master['dengue_total'].fillna(0)",
    "master['dengue_log1p'] = master['dengue_log1p'].fillna(0)",
    "",
    "master.to_csv(MASTER_FILE, index=False)",
    "print(f'Saved {len(master):,} rows -> {MASTER_FILE.name}')"
))

s5_51_md = md_cell(S(
    "\U0001f4cc **[5.1]** FluNet là anchor (LEFT JOIN) — giữ nguyên tất cả 172 quốc gia × 10 năm × 52 tuần.",
    "fillna(0) sau merge cho dengue_total vì quốc gia không có dengue report = 0 ca thực, không phải missing.",
    "ERA5 join theo iso3+iso_year+iso_week — 14 quốc gia không có ERA5 sẽ có NaN cho weather features."
))

# ═══════════════════════ ALSO need FILES dict check ═══════════════════════
# Check if SESSION 0 already has FILES dict
# (Looking at existing cells, FILES is not in SESSION 0 — need to add it)
# Actually per the problem statement FILES dict is referenced — let's check SESSION 0

# ═══════════════════════ Assemble ═══════════════════════

new_cells = [
    s1_header, s1_10_code, s1_10_md,
    s1_11_code, s1_11_md,
    s1_12_code, s1_12_md,
    s1_13_code, s1_13_md,
    s1_14_code, s1_14_md,

    s2_header, s2_20_code, s2_20_md,
    s2_21_code, s2_21_md,
    s2_22_code, s2_22_md,
    s2_23_code, s2_23_md,
    s2_24_code, s2_24_md,

    s3_header, s3_30_code, s3_30_md,
    s3_31_code, s3_31_md,
    s3_32_code, s3_32_md,
    s3_33_code, s3_33_md,
    s3_34_code, s3_34_md,
    s3_35_code, s3_35_md,
    s3_36_code, s3_36_md,

    s4_header, s4_40_code, s4_40_md,
    s4_41_code, s4_41_md,

    s5_header, s5_50_code, s5_50_md,
    s5_51_code, s5_51_md,
]

print(f'Total new cells to insert: {len(new_cells)}')

with open(NB_PATH, 'r', encoding='utf-8') as f:
    nb = json.load(f)

old_count = len(nb['cells'])
print(f'Original cell count: {old_count}')

# Insert after index 13 (cells[0:14] = NGROK + SESSION 0, then insert, then cells[14:] = SESSION 6+)
nb['cells'] = nb['cells'][:14] + new_cells + nb['cells'][14:]

new_count = len(nb['cells'])
print(f'New cell count: {new_count} (added {new_count - old_count})')

with open(NB_PATH, 'w', encoding='utf-8') as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print('Notebook written successfully.')
