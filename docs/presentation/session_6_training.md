# Session 6: Huấn luyện và so sánh mô hình (Notebook v5/v6)

> **Dùng khi demo lần 1:** Không cần trình bày quá sâu bảng thuật toán. Chỉ cần nói hệ thống đã so sánh nhiều mô hình, chọn mô hình tốt nhất riêng cho cúm và dengue, sau đó xuất file `.pkl` để backend sử dụng.
>
> **Mục tiêu thuyết trình:** Người chấm hiểu vì sao không chỉ huấn luyện một mô hình duy nhất. Notebook so sánh 5 mô hình dự báo số ca và 1 mô hình phân mức rủi ro, dùng cùng bộ đặc trưng và cùng cách kiểm chứng để chọn mô hình phù hợp.

---

## Bản đọc khi thuyết trình

Ở session này, em huấn luyện và so sánh mô hình. Em không chọn sẵn một mô hình rồi mặc định tin rằng nó tốt, mà thử nhiều mô hình trên cùng một bộ dữ liệu, cùng bộ đặc trưng và cùng cách kiểm chứng.

Vì dữ liệu là dữ liệu theo thời gian, em không chia train/test ngẫu nhiên. Nếu chia ngẫu nhiên, mô hình có thể học thông tin từ tương lai để dự đoán quá khứ, làm kết quả đánh giá cao không thật. Thay vào đó, em dùng cách kiểm chứng theo thời gian: huấn luyện trên các năm trước và kiểm tra trên năm sau. Cách này gần hơn với tình huống vận hành thật, vì tại một tuần cụ thể hệ thống chỉ biết dữ liệu quá khứ.

Với bài toán dự báo số ca, em so sánh cả mô hình đơn giản và mô hình học máy. Mô hình đơn giản như "lấy cùng tuần năm trước" được dùng làm mốc nền. Nếu học máy không vượt được mốc này thì không có lý do để dùng học máy. Kết quả cho thấy các mô hình học máy, đặc biệt là LightGBM cho cúm và Random Forest cho dengue, vượt rõ rệt so với cách đơn giản.

Điểm đáng chú ý là mô hình tốt nhất không giống nhau cho hai bệnh. Cúm có dữ liệu rộng hơn, LightGBM hoạt động tốt. Dengue có dữ liệu ít hơn và nhiều nhiễu hơn, Random Forest ổn định hơn. Điều này giúp em bảo vệ rằng mỗi bệnh cần mô hình riêng, không dùng một mô hình chung cho tất cả.

Ngoài dự báo số ca, em còn huấn luyện mô hình phân mức rủi ro Low/Medium/High. Mô hình này phục vụ trực tiếp cho bản đồ màu, cảnh báo và bộ lọc rủi ro trên dashboard. Kết quả phân mức rủi ro của dengue còn hạn chế ở lớp High, và em trình bày trung thực đây là hạn chế của dữ liệu và cách tạo nhãn, không xem đó là lỗi giao diện.

Sau khi chọn mô hình, notebook lưu các file `.pkl` cùng danh sách đặc trưng và chỉ số đánh giá. Các file này là thứ backend nạp lại để chạy dự báo, thay vì frontend gọi notebook trực tiếp.

---

## 1. Cell 6.1 - Kiểm chứng theo thời gian

### Vì sao KHÔNG dùng K-fold random?

K-fold ngẫu nhiên sẽ trộn dữ liệu trước/sau → **rò rỉ dữ liệu**: mô hình có thể học từ tương lai để dự đoán quá khứ, làm chỉ số R² cao không thật.

### Kiểm chứng theo thời gian 6 lần:

```
Fold 1: train 2010-2013 → val 2014
Fold 2: train 2010-2014 → val 2015
Fold 3: train 2010-2015 → val 2016
Fold 4: train 2010-2016 → val 2017
Fold 5: train 2010-2017 → val 2018
Fold 6: train 2010-2018 → val 2019
```

→ Luôn huấn luyện bằng dữ liệu **trước** năm kiểm chứng. Cách này gần với tình huống thật: tại thời điểm T, hệ thống chỉ biết dữ liệu trước T.

```python
def walk_forward_splits(df, val_years=[2014,2015,2016,2017,2018,2019]):
    for val_year in val_years:
        train_idx = df[df['iso_year'] < val_year].index
        val_idx   = df[df['iso_year'] == val_year].index
        yield train_idx, val_idx
```

---

## 2. 5 mô hình dự báo số ca - vì sao chọn 5

Mục tiêu ở đây không phải thử model cho nhiều, mà là tạo một phép so sánh có ý nghĩa. Em chọn các model theo vai trò khác nhau:

| Model | Vai trò trong thí nghiệm | Lý do đưa vào |
|---|---|---|
| Naive | Mốc nền rất đơn giản | Kiểm tra xem học máy có thật sự hơn cách lấy cùng tuần năm trước không |
| Prophet | Mô hình chuỗi thời gian truyền thống | Kiểm tra liệu mô hình chuyên về mùa vụ/thời gian có đủ tốt không |
| XGBoost | Mô hình cây tăng cường phổ biến | Là lựa chọn mạnh, thường dùng cho dữ liệu bảng |
| LightGBM | Mô hình cây tăng cường nhanh hơn | Thử biến thể tối ưu tốc độ và hiệu quả trên dữ liệu lớn |
| Random Forest | Mô hình nhiều cây độc lập | Kiểm tra phương án ổn định hơn khi dữ liệu ít hoặc nhiễu |

Vì vậy, các model này không được chọn đại. Chúng đại diện cho ba mức: cách dự báo đơn giản, mô hình chuỗi thời gian, và nhóm học máy trên dữ liệu bảng.

### Nhóm so sánh nền (2 mô hình)

**1. Naive — Same Week Last Year (SWLY)** — Cell 6.2

Dự đoán số ca tuần W năm Y bằng số ca của đúng tuần W năm Y-1.

Mô hình này dùng để làm mốc tối thiểu. Nếu học máy không vượt được Naive, thì mô hình học máy không có nhiều giá trị thực tế.

**2. Prophet (per country) — top 30 nước** — Cell 6.3

Prophet là mô hình chuỗi thời gian, thường dùng để bắt xu hướng và mùa vụ.

Prophet được đưa vào để kiểm tra xem một mô hình chuyên về chuỗi thời gian có xử lý tốt dữ liệu bệnh theo tuần không.

### Nhóm mô hình cây quyết định (3 mô hình)

**3. XGBoost Regressor** — Cell 6.4: mô hình cây tăng cường mạnh, phổ biến với dữ liệu dạng bảng.

**4. LightGBM Regressor** — Cell 6.5: gần giống XGBoost nhưng thường nhanh hơn, phù hợp khi dữ liệu nhiều dòng.

**5. Random Forest Regressor** — Cell 6.6: nhiều cây độc lập rồi lấy trung bình, thường ổn định khi dữ liệu nhiễu.

### Vì sao thử 3 mô hình cây thay vì chỉ XGBoost?

- XGBoost phổ biến nhưng không chắc luôn tốt nhất cho mọi bệnh.
- LightGBM có thể tốt hơn khi dữ liệu nhiều và cần tốc độ.
- Random Forest có thể ổn định hơn với dữ liệu ít, nhiễu hoặc có đỉnh bất thường.
- So sánh nhiều model giúp quyết định dựa trên kết quả kiểm chứng, không dựa trên cảm tính.

---

## 3. Luồng huấn luyện chung

```python
def run_cv(model_fn, features_df, target_col, splits):
    """Run walk-forward CV, return mean metrics."""
    metrics_per_fold = []
    for fold_idx, (train_idx, val_idx) in enumerate(splits):
        X_train = features_df.loc[train_idx, FEATURE_COLS]
        y_train = features_df.loc[train_idx, target_col]
        X_val   = features_df.loc[val_idx, FEATURE_COLS]
        y_val   = features_df.loc[val_idx, target_col]
        
        model = model_fn()
        model.fit(X_train, y_train)
        y_pred = model.predict(X_val)
        
        rmse = np.sqrt(mean_squared_error(y_val, y_pred))
        mae  = mean_absolute_error(y_val, y_pred)
        r2   = r2_score(y_val, y_pred)
        metrics_per_fold.append({'fold': fold_idx, 'rmse': rmse, 'mae': mae, 'r2': r2})
    
    return pd.DataFrame(metrics_per_fold)
```

Mọi mô hình dùng **cùng bộ đặc trưng, cùng cách chia kiểm chứng, cùng chỉ số đánh giá** nên việc so sánh công bằng.

### Dùng metric gì?

Em dùng 3 chỉ số chính:

| Metric | Cách hiểu đơn giản | Khi đọc kết quả |
|---|---|---|
| RMSE | Sai số trung bình nhưng phạt nặng các lỗi lớn | Càng thấp càng tốt |
| MAE | Sai số tuyệt đối trung bình, dễ hiểu hơn RMSE | Càng thấp càng tốt |
| R² | Mô hình giải thích được bao nhiêu phần biến động dữ liệu | Càng gần 1 càng tốt |

Vì số ca đã được biến đổi `log1p`, RMSE và MAE ở đây là sai số trên thang log, không phải sai số trực tiếp theo số ca thô.

Cách đọc nhanh:

- `R² = 0.90` nghĩa là mô hình giải thích được khoảng 90% biến động của dữ liệu kiểm chứng.
- `R² = 0` nghĩa là mô hình không tốt hơn việc đoán trung bình.
- `R² < 0` nghĩa là mô hình còn tệ hơn đoán trung bình, như Prophet với dengue trong kết quả này.
- RMSE lớn hơn MAE nhiều thường cho thấy có một số điểm dự báo sai rất mạnh.

---

## 4. Cell 6.7 - Kết quả dự báo số ca

### Bảng so sánh trung bình qua các lần kiểm chứng

| Model | Flu RMSE | Flu MAE | Flu R² | Dengue RMSE | Dengue MAE | Dengue R² |
|---|---:|---:|---:|---:|---:|---:|
| Naive | 1.2431 | 0.8868 | 0.5599 | 2.0230 | 1.3622 | 0.4869 |
| Prophet | 1.4194 | 1.1388 | 0.4286 | 3.2300 | 2.3267 | -0.2815 |
| XGBoost | 0.5908 | 0.4302 | 0.9007 | 0.7661 | **0.4725** | 0.9314 |
| LightGBM | **0.5882** | **0.4281** | **0.9015** | 0.7657 | 0.4792 | 0.9313 |
| Random Forest | 0.5952 | 0.4396 | 0.8992 | **0.7439** | 0.4828 | **0.9359** |

### Phát hiện 1: Nhóm mô hình cây vượt cách dự báo đơn giản

Với cúm, Naive đạt R² khoảng 0.56, trong khi nhóm XGBoost/LightGBM/Random Forest đạt khoảng 0.90. Với sốt xuất huyết, Naive đạt R² khoảng 0.49, còn nhóm mô hình cây đạt khoảng 0.93.

Điều này chứng minh mô hình học máy không chỉ “trang trí”, mà thật sự học thêm được từ lịch sử gần, thời tiết có độ trễ và mùa vụ.

### Phát hiện 2: Prophet R² âm với dengue (-0.282)

Prophet hoạt động kém với dengue, R² trung bình âm. Nghĩa là mô hình này dự báo còn kém hơn cách đoán trung bình trong một số năm.

Lý do hợp lý là dengue có nhiều đợt tăng mạnh, dữ liệu giữa các nước không đều và không chỉ có một mùa vụ mượt như Prophet thường giả định. Vì vậy nhóm mô hình cây phù hợp hơn trong đồ án này.

### Phát hiện 3: Mô hình tốt nhất khác nhau theo bệnh

Với cúm, LightGBM tốt nhất: RMSE 0.5882, MAE 0.4281, R² 0.9015. XGBoost và Random Forest cũng rất sát, nhưng LightGBM nhỉnh hơn và có lợi thế tốc độ.

Với dengue, Random Forest tốt nhất theo R² và RMSE: RMSE 0.7439, R² 0.9359. XGBoost có MAE thấp nhất một chút, nhưng Random Forest có tổng thể ổn hơn theo R²/RMSE.

Kết luận chọn model:

| Bệnh | Model chọn | Lý do |
|---|---|---|
| Cúm | LightGBM | R² cao nhất, RMSE/MAE thấp nhất, chạy nhanh |
| Sốt xuất huyết | Random Forest | R² và RMSE tốt nhất, ổn định hơn với dữ liệu dengue ít và nhiễu hơn |

Điểm cần nói rõ: em không dùng một model chung cho cả hai bệnh. Mỗi bệnh có đặc điểm dữ liệu khác nhau nên model tốt nhất cũng khác nhau.

---

## 5. Cell 6.8 - Phân mức rủi ro bằng XGBClassifier

Ngoài dự báo số ca, dashboard còn cần nhãn rủi ro `Low`, `Medium`, `High` để tô màu bản đồ và lọc các khu vực đáng chú ý. Vì vậy em huấn luyện thêm mô hình phân loại bằng XGBoost.

Lý do dùng XGBClassifier:

| Lý do | Giải thích |
|---|---|
| Dữ liệu là dạng bảng | Các đặc trưng đã tạo ở Session 5 phù hợp với mô hình cây |
| Có quan hệ phi tuyến | Rủi ro không tăng tuyến tính theo một biến duy nhất |
| Cần xác suất cho từng mức | `multi:softprob` cho ra xác suất Low/Medium/High |
| Có thể xử lý mất cân bằng lớp | Các mức Low/Medium/High không chia đều tuyệt đối |

```python
clf = XGBClassifier(
    objective='multi:softprob',
    num_class=3,
    eval_metric='mlogloss',
    class_weight='balanced',
)
```

### Metric cho phân loại

| Metric | Ý nghĩa | Cách đọc |
|---|---|---|
| Precision | Trong các mẫu model dự đoán là một lớp, bao nhiêu mẫu đúng | Cao nghĩa là ít báo nhầm |
| Recall | Trong các mẫu thật sự thuộc một lớp, model bắt được bao nhiêu | Cao nghĩa là ít bỏ sót |
| F1-score | Trung bình cân bằng giữa precision và recall | Càng cao càng tốt |
| Macro-F1 | Trung bình F1 của Low, Medium, High, coi 3 lớp quan trọng như nhau | Phù hợp khi các lớp không đều |
| AUC OvR | Khả năng tách từng lớp so với các lớp còn lại | Càng gần 1 càng tốt |

Ở đây em ưu tiên `macro-F1` vì dashboard cần cả ba mức Low/Medium/High. Nếu chỉ nhìn accuracy, model có thể dự đoán tốt lớp nhiều nhất nhưng bỏ qua lớp High.

### Kết quả phân mức rủi ro

| Bệnh | Số fold | Macro-F1 trung bình | AUC OvR trung bình | Nhận xét |
|---|---:|---:|---:|---|
| Cúm | 6 | **0.5422** | **0.7438** | Phân loại dùng được, đặc biệt bắt được khá nhiều tuần High |
| Sốt xuất huyết | 3 | 0.4749 | 0.7242 | Còn yếu ở lớp High, cần cải thiện nhãn và dữ liệu |

### Đọc classification report như thế nào?

Với cúm ở fold cuối năm 2019:

| Lớp | Precision | Recall | F1 | Cách hiểu |
|---|---:|---:|---:|---|
| Low | 0.71 | 0.24 | 0.36 | Khi model nói Low thì khá đúng, nhưng bỏ sót nhiều tuần Low |
| Medium | 0.62 | 0.76 | 0.68 | Lớp Medium ổn nhất |
| High | 0.44 | 0.60 | 0.51 | Model bắt được 60% tuần High, chấp nhận được cho cảnh báo |

Với dengue ở fold cuối năm 2019:

| Lớp | Precision | Recall | F1 | Cách hiểu |
|---|---:|---:|---:|---|
| Low | 0.72 | 0.44 | 0.55 | Lớp Low tương đối ổn |
| Medium | 0.46 | 0.78 | 0.58 | Model hay kéo nhiều mẫu về Medium |
| High | 0.26 | 0.14 | 0.18 | Lớp High yếu, bỏ sót nhiều tuần nguy cơ cao |

### Lý do dengue lớp High thấp

Với dengue, lớp High khó hơn vì dữ liệu ít hơn, giữa các nước không đều, và các đợt dịch lớn làm mức nền các năm sau tăng cao. Khi baseline tăng, ít tuần được gán nhãn High hơn, làm model có ít ví dụ High để học.

Đây là hạn chế thực tế của cách tạo nhãn theo mức nền, không phải lỗi code. Kiểm chứng theo thời gian giúp phát hiện hạn chế này.

**Hướng cải thiện** đề xuất trong báo cáo:
1. Thử ngưỡng cảnh báo riêng theo quốc gia hoặc theo vùng.
2. Bổ sung dữ liệu dengue nhiều năm hơn để lớp High có thêm ví dụ.
3. Thử cách học chú ý hơn vào lớp hiếm, ví dụ tăng trọng số cho lớp High.
4. Kiểm tra lại cách tạo nhãn khi có một đợt dịch cực lớn làm baseline các năm sau tăng cao.

### Câu nói thuyết trình cho phần classifier

“Phần dự báo số ca cho biết số ca dự kiến, còn phần phân loại rủi ro dùng để phục vụ dashboard: tô màu Low, Medium, High. Em dùng macro-F1 vì không muốn model chỉ giỏi lớp nhiều nhất mà bỏ qua lớp High. Kết quả cúm đạt macro-F1 khoảng 0.54, dùng được cho cảnh báo. Dengue thấp hơn, macro-F1 khoảng 0.47 và lớp High còn yếu, nên em xem đây là hạn chế cần cải thiện chứ không che đi.”

---

## 6. Cell 6.9 - Tinh chỉnh tham số bằng Optuna

Optuna là công cụ tự động thử nhiều bộ tham số khác nhau để tìm bộ tham số tốt hơn. Nói đơn giản, thay vì em tự đoán `max_depth`, `learning_rate`, `n_estimators`, Optuna sẽ thử nhiều tổ hợp và chọn tổ hợp cho điểm kiểm chứng tốt nhất.

Ở bước này, em chỉ tinh chỉnh mô hình đã thắng, không tinh chỉnh cả 5 mô hình. Lý do là nếu tinh chỉnh tất cả thì tốn thời gian tính toán rất nhiều, trong khi mục tiêu chính là cải thiện model cuối cùng.

Khi thuyết trình, không cần đi sâu từng tham số. Chỉ cần nói Optuna trả lời câu hỏi: “Sau khi đã chọn được model tốt nhất, nếu chỉnh tham số có làm kết quả tăng đáng kể không?”

```python
def objective(trial):
    params = {
        'n_estimators':    trial.suggest_int('n_estimators', 100, 500),
        'max_depth':       trial.suggest_int('max_depth', 3, 12),
        'learning_rate':   trial.suggest_float('learning_rate', 0.01, 0.3),
        'num_leaves':      trial.suggest_int('num_leaves', 16, 128),
        'min_child_samples': trial.suggest_int('min_child_samples', 5, 50),
    }
    cv_results = run_cv(lambda: LGBMRegressor(**params), features, target, splits)
    return cv_results['r2'].mean()
```

### Improvement Optuna

| Model | Before tuning | After 60 trials | Δ |
|---|---|---|---|
| LightGBM (flu) | 0.9018 | **0.9019** | +0.0001 |
| Random Forest (dengue) | 0.9359 | **0.9366** | +0.0007 |

Mức cải thiện rất nhỏ, cho thấy bộ đặc trưng lịch sử ca bệnh đã chứa tín hiệu mạnh; tinh chỉnh tham số không làm thay đổi nhiều.

Điểm có thể trình bày: kết quả tốt chủ yếu đến từ đặc trưng đúng và cách kiểm chứng đúng, không chỉ đến từ việc chỉnh tham số. Khi lịch sử ca bệnh đã giải thích phần lớn tín hiệu, Optuna chỉ cải thiện rất nhỏ.

### Cách nói khi thuyết trình Optuna

“Sau khi so sánh mô hình, em dùng Optuna để tinh chỉnh tham số cho model đã thắng. Kết quả là LightGBM cho cúm chỉ tăng R² từ 0.9018 lên 0.9019, Random Forest cho dengue tăng từ 0.9359 lên 0.9366. Mức tăng rất nhỏ. Điều này cho thấy phần quan trọng hơn trong đồ án không phải là chỉnh tham số thật nhiều, mà là chuẩn bị đặc trưng đúng: lịch sử ca bệnh, mùa vụ, bán cầu và thời tiết có độ trễ.”

### Kết luận từ Optuna

| Kết luận | Ý nghĩa |
|---|---|
| Tinh chỉnh có cải thiện nhưng rất ít | Model ban đầu đã khá tốt |
| Đặc trưng quan trọng hơn tham số | Session 4 và 5 có vai trò lớn |
| Không nên tốn quá nhiều thời gian vào tuning | Nên ưu tiên dữ liệu, nhãn rủi ro và kiểm chứng |

---

## 7. Cell 6.10 - Lưu mô hình cuối cùng v1

```
ml_models/
├── lgbm_flu_regressor_v1.pkl        (1.8 MB) — best LGBM v5
├── lgbm_flu_regressor_v1_features.json
├── lgbm_flu_regressor_v1_metrics.json
├── rf_dengue_regressor_v1.pkl       (34.6 MB) — best RF v5
├── rf_dengue_regressor_v1_features.json
├── rf_dengue_regressor_v1_metrics.json
├── xgb_flu_classifier_v1.pkl        (3.9 MB)
├── xgb_flu_classifier_v1_features.json
├── xgb_flu_classifier_v1_metrics.json
├── xgb_dengue_classifier_v1.pkl     (2.9 MB)
├── xgb_dengue_classifier_v1_features.json
└── xgb_dengue_classifier_v1_metrics.json
```

Mỗi `.pkl` đi kèm:
- `_features.json` - danh sách cột đặc trưng dùng để huấn luyện.
- `_metrics.json` - chỉ số đánh giá, ngày huấn luyện và tham số chính.

---

## 8. Feature Importance (preview Session 9 v5)

**Flu (XGBoost importance):**
- Top 3: `flu_log_lag1` 54%, `flu_log_lag2` 31%, `flu_log_lag3` 8%.
- Nghĩa là số ca các tuần gần nhất là tín hiệu mạnh nhất.
- Thời tiết, mùa vụ và bán cầu vẫn có vai trò, nhưng nhỏ hơn lịch sử ca bệnh.

**Dengue (XGBoost importance):**
- Top 1 là `deng_log_rollmean4` khoảng 70%, tiếp theo là `rollmean8` và `lag6`.
- Nghĩa là dengue phụ thuộc mạnh vào mức bệnh gần đây, đặc biệt là trung bình vài tuần gần nhất.
- Các biến mưa, độ ẩm, mùa vụ và nhiệt độ vẫn xuất hiện trong top 10, đúng với ý tưởng thời tiết là yếu tố hỗ trợ.

Kết luận quan trọng: lịch sử ca bệnh là yếu tố chính, thời tiết là yếu tố bổ trợ. Vì vậy dashboard nên được hiểu là công cụ hỗ trợ đánh giá nguy cơ, không phải hệ thống kết luận rằng thời tiết là nguyên nhân duy nhất gây dịch.

---

## 9. Rút ra gì và cải thiện tiếp ra sao?

### So với cách làm đơn giản hoặc các công trình chỉ dùng chuỗi thời gian

Kết quả cho thấy chỉ dùng chuỗi thời gian đơn giản như Prophet chưa đủ tốt, đặc biệt với dengue. Cách làm của đồ án tốt hơn ở chỗ kết hợp nhiều nhóm thông tin:

| Nhóm thông tin | Vai trò |
|---|---|
| Lịch sử ca bệnh | Tín hiệu mạnh nhất, phản ánh đà lây lan hiện tại |
| Mùa vụ | Giúp mô hình biết tuần hiện tại nằm ở giai đoạn nào trong năm |
| Bán cầu | Giúp cúm phân biệt mùa ở Bắc bán cầu và Nam bán cầu |
| Thời tiết có độ trễ | Bổ sung bối cảnh môi trường, đặc biệt cho dengue |
| Kiểm chứng theo thời gian | Đánh giá gần với tình huống triển khai thật |

### Cần cải thiện gì tiếp?

Kết quả dự báo số ca đã tốt, nhưng vẫn có hướng cải thiện:

1. Dữ liệu dengue cần rộng và đều hơn theo quốc gia.
2. Nhãn High của dengue cần được nghiên cứu thêm vì các đợt dịch lớn có thể làm baseline các năm sau tăng cao.
3. Có thể thử ngưỡng cảnh báo riêng theo quốc gia hoặc theo vùng thay vì dùng cùng quy tắc cho mọi nơi.
4. Có thể bổ sung dữ liệu dân số, mật độ dân cư, di chuyển, biện pháp y tế hoặc chỉ số giám sát muỗi nếu có.
5. Có thể kiểm tra độ ổn định sau khi thêm dữ liệu 2020-2023, nhưng phải xử lý cẩn thận vì COVID làm thay đổi quy luật bệnh.

---

## Ý chính Session 6 (slide thuyết trình)

1. **Kiểm chứng theo thời gian** phù hợp hơn chia ngẫu nhiên cho dữ liệu theo tuần.
2. **So sánh 5 mô hình dự báo số ca** - không chọn mô hình theo cảm tính.
3. **Mô hình tốt nhất khác nhau theo bệnh**: LightGBM cho cúm, Random Forest cho dengue.
4. **R² khoảng 0.90+ so với Naive 0.56** cho thấy học máy có giá trị trong bài toán này.
5. **Tinh chỉnh tham số cải thiện ít** vì đặc trưng lịch sử ca bệnh đã rất mạnh.
6. **Lịch sử ca bệnh là tín hiệu chính, thời tiết là yếu tố bổ trợ**.
7. **Phân mức High của dengue còn hạn chế** - cần trình bày trung thực là hạn chế của dữ liệu và cách tạo nhãn.

---

## Câu nói thuyết trình cho Session 6

> "Ở session 6, em không huấn luyện một mô hình duy nhất rồi chọn luôn. Em so sánh 5 mô hình dự báo số ca và một mô hình phân mức rủi ro. Tất cả dùng cùng bộ đặc trưng, cùng cách kiểm chứng theo thời gian và cùng chỉ số đánh giá, nên kết quả so sánh công bằng."
>
> "Năm mô hình dự báo gồm Naive, Prophet, XGBoost, LightGBM và Random Forest. Naive là mốc đơn giản: lấy cùng tuần năm trước. Prophet là mô hình chuỗi thời gian. Ba mô hình còn lại là nhóm mô hình cây, phù hợp với dữ liệu bảng có nhiều đặc trưng."
>
> [CHUYỂN SLIDE — bảng kết quả]
>
> "Em dùng RMSE, MAE và R². RMSE và MAE càng thấp càng tốt; R² càng gần 1 càng tốt. Với cúm, LightGBM tốt nhất với R² 0.9015. Với sốt xuất huyết, Random Forest tốt nhất với R² 0.9359."
>
> "**3 phát hiện:**"
>
> "Phát hiện 1: nhóm mô hình cây vượt rõ mô hình Naive. Với cúm, R² tăng từ khoảng 0.56 lên khoảng 0.90. Với sốt xuất huyết, R² tăng từ khoảng 0.49 lên khoảng 0.93. Điều này cho thấy học máy có giá trị thật, không chỉ dùng cho có."
>
> "Phát hiện 2: Prophet không phù hợp với dengue trong dữ liệu này. R² trung bình của Prophet cho dengue bị âm, nghĩa là còn kém hơn cách đoán trung bình. Lý do có thể là dengue có nhiều đợt tăng mạnh và dữ liệu giữa các nước không đều."
>
> [NHẤN MẠNH] "Phát hiện 3: mô hình tốt nhất khác nhau theo bệnh. Cúm chọn LightGBM vì chỉ số tốt nhất và chạy nhanh. Dengue chọn Random Forest vì R² và RMSE tốt nhất, ổn định hơn với dữ liệu dengue nhỏ và nhiễu hơn. Em không chọn XGBoost chỉ vì nó phổ biến, mà chọn theo kết quả kiểm chứng."
>
> "Phân mức rủi ro: **flu macro-F1 0.542 đạt** mục tiêu. **Dengue F1(High) 0.30 - em trình bày trung thực đây là hạn chế**: đỉnh dịch Brazil 2016 làm mức nền 2017-2018 tăng cao, nên ít tuần vượt ngưỡng High. Đây là hạn chế thực tế của cách tạo nhãn theo mức nền; kiểm chứng theo thời gian giúp phát hiện ra, không nên che đi."
>
> "Optuna được dùng sau khi đã chọn model thắng để thử tối ưu tham số. Sau 60 lần thử, cải thiện rất nhỏ, chỉ khoảng 0.0001 đến 0.0007 R². Điều này cho thấy kết quả tốt chủ yếu đến từ đặc trưng đúng và cách kiểm chứng đúng, không phải chỉ nhờ chỉnh tham số."
