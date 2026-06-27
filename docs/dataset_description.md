# Mo ta Dataset - KLTN EpiWeather ML

**Sinh vien:** Pham Huu Luan | MSSV: 110122016 | Lop: DA22TTA  
**De tai:** Xay dung he thong canh bao nguy co dich benh theo mua dua tren du lieu y te va thoi tiet toan cau

---

## Tong quan

Dataset da qua feature engineering nam trong thu muc `data/processed/`. Hai file chinh duoc dung lam input huan luyen mo hinh:

| File | Benh | So hang | So cot | Quoc gia | Giai doan |
|---|---|---:|---:|---:|---|
| `features_flu_v1.csv` | Influenza (cum) | 55,208 | 21 | 143 | 2010-2019 |
| `features_dengue_v1.csv` | Dengue (sot xuat huyet) | 5,926 | 20 | 35 | 2015-2019 |

Trong moi file:

- Cac cot `iso3`, `iso_week`, `iso_year` la cot dinh danh/thoi gian.
- Cot tong ca benh goc la `influenza_total` hoac `dengue_total`.
- Cot target hoi quy la `flu_log` hoac `deng_log`, duoc tinh bang `log1p(cases)`.
- Cot target phan lop rui ro la `flu_risk_class` hoac `dengue_risk_class`.
- Cac cot con lai la feature dua vao mo hinh.

---

## 1. `features_flu_v1.csv`

### 1.1. Thong tin file

| Thuoc tinh | Gia tri |
|---|---:|
| So hang | 55,208 |
| So cot | 21 |
| So quoc gia | 143 |
| Nam | 2010-2019 |
| So feature dung cho model | 16 |

### 1.2. Danh sach cot

| Nhom | Cot |
|---|---|
| ID/time | `iso3`, `iso_week`, `iso_year` |
| Raw target | `influenza_total` |
| Regression target | `flu_log` |
| Classification target | `flu_risk_class` |
| Feature columns | 16 cot ben duoi |

### 1.3. Feature columns

| Nhom | Features | Y nghia |
|---|---|---|
| AR target lag | `flu_log_lag1`, `flu_log_lag2`, `flu_log_lag3` | So ca cum da log1p cua 1, 2, 3 tuan truoc trong cung quoc gia |
| AR rolling mean | `flu_log_rollmean4`, `flu_log_rollmean8` | Trung binh truot 4 va 8 tuan gan nhat cua so ca cum da log1p |
| Weather lag - temp | `temp_c_lag3`, `temp_c_lag7` | Nhiet do trung binh tre 3 va 7 tuan |
| Weather lag - humid | `humidity_pct_lag1`, `humidity_pct_lag7` | Do am tuong doi tre 1 va 7 tuan |
| Weather lag - solar | `solar_wm2_lag7` | Buc xa mat troi tre 7 tuan |
| Weather lag - dewpoint | `dewpoint_c_lag1` | Nhiet do diem suong tre 1 tuan |
| Cyclic time | `iso_week_sin`, `iso_week_cos` | Ma hoa tuan trong nam theo chu ky sin/cos de tuan 52 gan tuan 1 |
| Linear time | `iso_year` | Tin hieu xu huong theo nam |
| Categorical | `HEMISPHERE_NH`, `HEMISPHERE_SH` | One-hot bac ban cau/nam ban cau, vi mua cum lech nhau giua hai ban cau |

### 1.4. Target va cot khong phai feature

| Cot | Vai tro | Mo ta |
|---|---|---|
| `iso3` | ID/stratify | Ma quoc gia ISO 3166-1 alpha-3. Dung de group theo quoc gia khi tao lag va stratify CV, khong phai feature so chinh |
| `iso_week` | ID/time | Tuan ISO trong nam |
| `influenza_total` | Raw target | Tong ca Influenza A + B |
| `flu_log` | Regression target | `log1p(influenza_total)`, dung lam y cho bai toan du bao so ca |
| `flu_risk_class` | Classification target | Nhan rui ro `Low`, `Medium`, `High` theo endemic channel |

### 1.5. Vi sao dung cac nhom feature nay?

**AR lag va rolling mean** la nhom quan trong nhat. Dich benh co tinh tu hoi quy: so ca tuan nay thuong lien quan manh den so ca cac tuan gan truoc. Rolling mean giup lam muot nhieu bao cao tuan.

**Weather lag** duoc tao vi thoi tiet anh huong den dieu kien lay truyen nhung tac dong co do tre. Cac lag duoc chon tu phan tich CCF o Session 4, khong chon tuy y.

**Cyclic time** giup mo hinh hieu tinh mua vu. Neu dua `iso_week` truc tiep theo dang 1-52, mo hinh co the hieu nham tuan 52 rat xa tuan 1. Dung sin/cos bien no thanh chu ky tron.

**Hemisphere encoding** chi dung cho flu vi mua cum o bac ban cau va nam ban cau lech nhau.

---

## 2. `features_dengue_v1.csv`

### 2.1. Thong tin file

| Thuoc tinh | Gia tri |
|---|---:|
| So hang | 5,926 |
| So cot | 20 |
| So quoc gia | 35 |
| Nam | 2015-2019 |
| So feature dung cho model | 15 |

### 2.2. Danh sach cot

| Nhom | Cot |
|---|---|
| ID/time | `iso3`, `iso_week`, `iso_year` |
| Raw target | `dengue_total` |
| Regression target | `deng_log` |
| Classification target | `dengue_risk_class` |
| Feature columns | 15 cot ben duoi |

### 2.3. Feature columns

| Nhom | Features | Y nghia |
|---|---|---|
| AR target lag | `deng_log_lag6`, `deng_log_lag8`, `deng_log_lag10`, `deng_log_lag12`, `deng_log_lag14` | So ca dengue da log1p cua 6-14 tuan truoc |
| AR rolling mean | `deng_log_rollmean4`, `deng_log_rollmean8` | Trung binh truot 4 va 8 tuan gan nhat |
| Weather lag - temp | `temp_c_lag11` | Nhiet do trung binh tre 11 tuan |
| Weather lag - dewpoint | `dewpoint_c_lag8` | Nhiet do diem suong tre 8 tuan |
| Weather lag - precip | `precip_mm_lag6` | Luong mua tre 6 tuan |
| Weather lag - humid | `humidity_pct_lag1` | Do am tuong doi tre 1 tuan |
| Weather lag - solar | `solar_wm2_lag16` | Buc xa mat troi tre 16 tuan |
| Cyclic time | `iso_week_sin`, `iso_week_cos` | Ma hoa mua vu theo tuan trong nam |
| Linear time | `iso_year` | Tin hieu xu huong theo nam |

Dengue dung lag dai hon flu vi chu trinh lan truyen lien quan den muoi Aedes, mua, nhiet do, thoi gian u benh va do tre bao cao. File dengue khong dung feature ban cau vi du lieu chu yeu nam o vung nhiet doi, mua vu khong tach ro theo bac/nam ban cau nhu cum.

### 2.4. Target va cot khong phai feature

| Cot | Vai tro | Mo ta |
|---|---|---|
| `iso3` | ID/stratify | Ma quoc gia ISO 3166-1 alpha-3 |
| `iso_week` | ID/time | Tuan ISO trong nam |
| `dengue_total` | Raw target | Tong ca dengue theo tuan |
| `deng_log` | Regression target | `log1p(dengue_total)`, dung lam y cho bai toan du bao so ca |
| `dengue_risk_class` | Classification target | Nhan rui ro `Low`, `Medium`, `High` |

---

## 3. Nguon du lieu goc

| Nguon | Noi dung | Vai tro |
|---|---|---|
| WHO FluNet (`VIW_FNT.csv`) | Ca Influenza A/B theo tuan | Tao `influenza_total`, `flu_log`, AR features va risk label |
| OpenDengue v1.3 (`National_extract_V1_3.csv`) | Ca dengue theo tuan | Tao `dengue_total`, `deng_log`, AR features va risk label |
| ERA5 / Open-Meteo archive | Nhiet do, do am, mua, buc xa, dewpoint | Tao weather lag features |
| Natural Earth / country metadata | Ma quoc gia, toa do, ban cau | Map thoi tiet theo quoc gia va tao hemisphere features |

---

## 4. Quy tac tao feature

### 4.1. Log1p target

Ca benh co phan phoi lech phai rat manh: mot so quoc gia lon co hang nghin den hang chuc nghin ca, trong khi nhieu nuoc nho chi co vai ca. Vi vay target duoc bien doi:

```text
flu_log  = log1p(influenza_total)
deng_log = log1p(dengue_total)
```

`log1p(x)` tuong duong `log(x + 1)`, giup xu ly duoc ca truong hop `x = 0`.

### 4.2. Lag trong cung quoc gia

Tat ca lag features duoc tao theo tung quoc gia:

```python
df.groupby("iso3")[col].shift(lag)
```

Quy tac nay tranh ro ri du lieu giua cac quoc gia. Vi du Brazil tuan 1 khong duoc lay nham so ca tu tuan cuoi cua USA.

### 4.3. Rolling mean khong nhin tuong lai

Rolling mean dung `shift(1)` truoc khi tinh trung binh, de gia tri cua tuan hien tai khong bi dua nguoc vao feature:

```python
x.shift(1).rolling(window).mean()
```

### 4.4. Drop NaN sau khi tao lag

Nhung hang dau moi quoc gia co the bi thieu lag vi chua co du lich su. Cac hang nay duoc drop truoc khi train model. Do do so hang cua file features nho hon so hang raw ban dau.

---

## 5. Ghi chu thuyet trinh nhanh

Khi bi hoi "dataset co feature gi?", co the tra loi ngan gon:

> "File `features_flu_v1.csv` co 16 feature: 5 feature lich su ca benh, 6 feature thoi tiet co do tre, 2 feature mua vu sin/cos, `iso_year`, va 2 cot ban cau. Target hoi quy la `flu_log`, target phan lop la `flu_risk_class`. File dengue tuong tu nhung dung lag dai hon, 6-16 tuan, vi dengue lien quan den chu ky muoi va do tre moi truong."

---

## 6. Luu y va han che du lieu

- Training bo qua giai doan COVID-19 2020-2021 vi pattern bao cao va lan truyen bi dich chuyen manh.
- Missing report duoc xu ly can trong; voi cac buoc build feature, grid theo quoc gia-tuan giup giu lai nhieu dong hon truoc khi tao lag.
- Weather duoc map theo quoc gia tu du lieu khi hau toan cau; cac quoc gia nho/dao nho co the thieu coverage hoac bi loai neu khong co du lieu on dinh.
- Dengue co so quoc gia va so hang it hon flu, nen do on dinh va kha nang tong quat hoa can duoc dien giai than trong hon.
