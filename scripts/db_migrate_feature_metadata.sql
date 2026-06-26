ALTER TABLE feature_configs
    ADD COLUMN IF NOT EXISTS display_name_vi VARCHAR(150),
    ADD COLUMN IF NOT EXISTS description_vi VARCHAR(500);

WITH catalog (
    disease_code, feature_name, display_name_vi, description_vi,
    source_type, weather_variable, lag_weeks, transform, ar_target, ar_lag_weeks
) AS (
    VALUES
        ('flu', 'flu_log_lag1', 'Số ca cúm tuần trước', 'Giá trị log của số ca cúm ghi nhận trước thời điểm dự báo 1 tuần; phản ánh mức dịch gần nhất.', 'ar_lag', NULL, 0, 'log1p', 'flu_log', 1),
        ('flu', 'flu_log_lag2', 'Số ca cúm trễ 2 tuần', 'Giá trị log của số ca cúm trước thời điểm dự báo 2 tuần; giúp mô hình nhận biết xu hướng ngắn hạn.', 'ar_lag', NULL, 0, 'log1p', 'flu_log', 2),
        ('flu', 'flu_log_lag3', 'Số ca cúm trễ 3 tuần', 'Giá trị log của số ca cúm trước thời điểm dự báo 3 tuần; bổ sung thông tin diễn biến gần đây.', 'ar_lag', NULL, 0, 'log1p', 'flu_log', 3),
        ('flu', 'flu_log_rollmean4', 'Trung bình ca cúm 4 tuần', 'Trung bình trượt giá trị log số ca cúm trong 4 tuần gần nhất; làm mượt dao động ngắn hạn.', 'ar_lag', NULL, 0, 'rolling_mean_4', 'flu_log', NULL),
        ('flu', 'flu_log_rollmean8', 'Trung bình ca cúm 8 tuần', 'Trung bình trượt giá trị log số ca cúm trong 8 tuần gần nhất; phản ánh xu hướng dịch ổn định hơn.', 'ar_lag', NULL, 0, 'rolling_mean_8', 'flu_log', NULL),
        ('flu', 'flu_log_velocity', 'Tốc độ thay đổi ca cúm', 'Mức thay đổi của giá trị log số ca cúm giữa các tuần gần nhất; cho biết dịch đang tăng hay giảm nhanh.', 'ar_lag', NULL, 0, 'difference', 'flu_log', NULL),
        ('flu', 'flu_log_accel', 'Gia tốc thay đổi ca cúm', 'Mức thay đổi của tốc độ ca cúm; cho biết xu hướng tăng hoặc giảm của dịch đang mạnh lên hay chậm lại.', 'ar_lag', NULL, 0, 'second_difference', 'flu_log', NULL),
        ('flu', 'temp_c_lag3', 'Nhiệt độ trễ 3 tuần', 'Nhiệt độ trung bình trước thời điểm dự báo 3 tuần; biểu diễn tác động trễ của nhiệt độ lên lây truyền cúm.', 'weather', 'temp_c', 3, 'none', NULL, NULL),
        ('flu', 'temp_c_lag7', 'Nhiệt độ trễ 7 tuần', 'Nhiệt độ trung bình trước thời điểm dự báo 7 tuần; hỗ trợ nhận biết ảnh hưởng thời tiết kéo dài.', 'weather', 'temp_c', 7, 'none', NULL, NULL),
        ('flu', 'humidity_pct_lag1', 'Độ ẩm trễ 1 tuần', 'Độ ẩm không khí trước thời điểm dự báo 1 tuần; liên quan đến khả năng tồn tại và lây truyền virus cúm.', 'weather', 'humidity_pct', 1, 'none', NULL, NULL),
        ('flu', 'humidity_pct_lag7', 'Độ ẩm trễ 7 tuần', 'Độ ẩm không khí trước thời điểm dự báo 7 tuần; biểu diễn ảnh hưởng độ ẩm theo chu kỳ dài hơn.', 'weather', 'humidity_pct', 7, 'none', NULL, NULL),
        ('flu', 'solar_wm2_lag7', 'Bức xạ mặt trời trễ 7 tuần', 'Bức xạ mặt trời trung bình trước thời điểm dự báo 7 tuần; đại diện điều kiện mùa và mức tiếp xúc ánh sáng.', 'weather', 'solar_wm2', 7, 'none', NULL, NULL),
        ('flu', 'dewpoint_c_lag1', 'Điểm sương trễ 1 tuần', 'Nhiệt độ điểm sương trước thời điểm dự báo 1 tuần; phản ánh lượng ẩm thực tế trong không khí.', 'weather', 'dewpoint_c', 1, 'none', NULL, NULL),
        ('flu', 'iso_week_sin', 'Chu kỳ mùa vụ theo tuần (sin)', 'Thành phần sin mã hóa tuần ISO theo chu kỳ, giúp mô hình hiểu tuần 52 và tuần 1 nằm gần nhau.', 'calendar', NULL, 0, 'cyclic_sin', NULL, NULL),
        ('flu', 'iso_week_cos', 'Chu kỳ mùa vụ theo tuần (cos)', 'Thành phần cos mã hóa tuần ISO theo chu kỳ, kết hợp với thành phần sin để biểu diễn mùa vụ.', 'calendar', NULL, 0, 'cyclic_cos', NULL, NULL),
        ('flu', 'iso_year', 'Xu hướng theo năm', 'Năm ISO của quan sát; giúp mô hình nhận biết thay đổi dài hạn giữa các năm.', 'calendar', NULL, 0, 'none', NULL, NULL),
        ('flu', 'HEMISPHERE_NH', 'Thuộc Bắc bán cầu', 'Biến nhị phân cho biết quốc gia thuộc Bắc bán cầu; hỗ trợ phân biệt mùa dịch giữa hai bán cầu.', 'geographic', NULL, 0, 'one_hot', NULL, NULL),
        ('flu', 'HEMISPHERE_SH', 'Thuộc Nam bán cầu', 'Biến nhị phân cho biết quốc gia thuộc Nam bán cầu; hỗ trợ phân biệt mùa dịch giữa hai bán cầu.', 'geographic', NULL, 0, 'one_hot', NULL, NULL),
        ('dengue', 'deng_log_lag6', 'Số ca Dengue trễ 6 tuần', 'Giá trị log của số ca Dengue trước thời điểm dự báo 6 tuần; phản ánh diễn biến dịch trước đó.', 'ar_lag', NULL, 0, 'log1p', 'deng_log', 6),
        ('dengue', 'deng_log_lag8', 'Số ca Dengue trễ 8 tuần', 'Giá trị log của số ca Dengue trước thời điểm dự báo 8 tuần; giúp mô hình nhận biết xu hướng trung hạn.', 'ar_lag', NULL, 0, 'log1p', 'deng_log', 8),
        ('dengue', 'deng_log_lag10', 'Số ca Dengue trễ 10 tuần', 'Giá trị log của số ca Dengue trước thời điểm dự báo 10 tuần; bổ sung tín hiệu diễn biến theo mùa.', 'ar_lag', NULL, 0, 'log1p', 'deng_log', 10),
        ('dengue', 'deng_log_lag12', 'Số ca Dengue trễ 12 tuần', 'Giá trị log của số ca Dengue trước thời điểm dự báo 12 tuần; phản ánh quán tính dịch trong khoảng ba tháng.', 'ar_lag', NULL, 0, 'log1p', 'deng_log', 12),
        ('dengue', 'deng_log_lag14', 'Số ca Dengue trễ 14 tuần', 'Giá trị log của số ca Dengue trước thời điểm dự báo 14 tuần; cung cấp tín hiệu dịch ở khoảng trễ dài.', 'ar_lag', NULL, 0, 'log1p', 'deng_log', 14),
        ('dengue', 'deng_log_rollmean4', 'Trung bình ca Dengue 4 tuần', 'Trung bình trượt giá trị log số ca Dengue trong 4 tuần gần nhất; làm mượt dao động ngắn hạn.', 'ar_lag', NULL, 0, 'rolling_mean_4', 'deng_log', NULL),
        ('dengue', 'deng_log_rollmean8', 'Trung bình ca Dengue 8 tuần', 'Trung bình trượt giá trị log số ca Dengue trong 8 tuần gần nhất; phản ánh xu hướng dịch ổn định hơn.', 'ar_lag', NULL, 0, 'rolling_mean_8', 'deng_log', NULL),
        ('dengue', 'deng_log_velocity', 'Tốc độ thay đổi ca Dengue', 'Mức thay đổi của giá trị log số ca Dengue giữa các tuần gần nhất; cho biết dịch đang tăng hay giảm nhanh.', 'ar_lag', NULL, 0, 'difference', 'deng_log', NULL),
        ('dengue', 'deng_log_accel', 'Gia tốc thay đổi ca Dengue', 'Mức thay đổi của tốc độ ca Dengue; cho biết xu hướng tăng hoặc giảm của dịch đang mạnh lên hay chậm lại.', 'ar_lag', NULL, 0, 'second_difference', 'deng_log', NULL),
        ('dengue', 'temp_c_lag11', 'Nhiệt độ trễ 11 tuần', 'Nhiệt độ trung bình trước thời điểm dự báo 11 tuần; liên quan đến vòng đời muỗi và tốc độ phát triển virus.', 'weather', 'temp_c', 11, 'none', NULL, NULL),
        ('dengue', 'dewpoint_c_lag8', 'Điểm sương trễ 8 tuần', 'Nhiệt độ điểm sương trước thời điểm dự báo 8 tuần; phản ánh độ ẩm thực tế ảnh hưởng đến môi trường sinh sản của muỗi.', 'weather', 'dewpoint_c', 8, 'none', NULL, NULL),
        ('dengue', 'precip_mm_lag6', 'Lượng mưa trễ 6 tuần', 'Lượng mưa trước thời điểm dự báo 6 tuần; có thể tạo nơi nước đọng thuận lợi cho muỗi sinh sản.', 'weather', 'precip_mm', 6, 'none', NULL, NULL),
        ('dengue', 'humidity_pct_lag1', 'Độ ẩm trễ 1 tuần', 'Độ ẩm không khí trước thời điểm dự báo 1 tuần; ảnh hưởng đến hoạt động và khả năng sống của muỗi truyền bệnh.', 'weather', 'humidity_pct', 1, 'none', NULL, NULL),
        ('dengue', 'solar_wm2_lag16', 'Bức xạ mặt trời trễ 16 tuần', 'Bức xạ mặt trời trước thời điểm dự báo 16 tuần; đại diện điều kiện mùa và môi trường ở khoảng trễ dài.', 'weather', 'solar_wm2', 16, 'none', NULL, NULL),
        ('dengue', 'iso_week_sin', 'Chu kỳ mùa vụ theo tuần (sin)', 'Thành phần sin mã hóa tuần ISO theo chu kỳ, giúp mô hình hiểu tuần 52 và tuần 1 nằm gần nhau.', 'calendar', NULL, 0, 'cyclic_sin', NULL, NULL),
        ('dengue', 'iso_week_cos', 'Chu kỳ mùa vụ theo tuần (cos)', 'Thành phần cos mã hóa tuần ISO theo chu kỳ, kết hợp với thành phần sin để biểu diễn mùa vụ.', 'calendar', NULL, 0, 'cyclic_cos', NULL, NULL),
        ('dengue', 'iso_year', 'Xu hướng theo năm', 'Năm ISO của quan sát; giúp mô hình nhận biết thay đổi dài hạn giữa các năm.', 'calendar', NULL, 0, 'none', NULL, NULL)
)
INSERT INTO feature_configs (
    disease_id, feature_name, display_name_vi, description_vi, source_type,
    weather_variable, lag_weeks, transform, ar_target, ar_lag_weeks,
    is_active, version_tag
)
SELECT
    d.id, c.feature_name, c.display_name_vi, c.description_vi, c.source_type,
    c.weather_variable, c.lag_weeks, c.transform, c.ar_target, c.ar_lag_weeks,
    TRUE, 'production-v1'
FROM catalog c
JOIN diseases d ON d.code = c.disease_code
ON CONFLICT (disease_id, feature_name, version_tag)
DO UPDATE SET
    display_name_vi = EXCLUDED.display_name_vi,
    description_vi = EXCLUDED.description_vi,
    source_type = EXCLUDED.source_type,
    weather_variable = EXCLUDED.weather_variable,
    lag_weeks = EXCLUDED.lag_weeks,
    transform = EXCLUDED.transform,
    ar_target = EXCLUDED.ar_target,
    ar_lag_weeks = EXCLUDED.ar_lag_weeks,
    is_active = TRUE;
