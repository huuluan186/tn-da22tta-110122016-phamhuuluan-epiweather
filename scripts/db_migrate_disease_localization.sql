ALTER TABLE diseases
    ADD COLUMN IF NOT EXISTS display_name_vi VARCHAR(100),
    ADD COLUMN IF NOT EXISTS description_vi TEXT;

UPDATE diseases
SET
    display_name_vi = 'Cúm mùa',
    description_vi = 'Bệnh hô hấp theo mùa, lây qua giọt bắn và tiếp xúc gần.'
WHERE code = 'flu';

UPDATE diseases
SET
    display_name_vi = 'Sốt xuất huyết Dengue',
    description_vi = 'Bệnh do muỗi truyền, bùng phát mạnh theo mùa mưa và khí hậu nóng ẩm.'
WHERE code = 'dengue';
