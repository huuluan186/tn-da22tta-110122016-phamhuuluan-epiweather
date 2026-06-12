import os
from dotenv import load_dotenv
import psycopg2

load_dotenv(r"f:/BAO_CAO/DO_AN_TOT_NGHIEP/KLTN/backend/.env")
db_url = os.getenv("DATABASE_URL", "postgresql://postgres:111111111@localhost:5432/kltn_epiweather")

conn = psycopg2.connect(db_url)
cur = conn.cursor()

cur.execute(
    """
    SELECT COALESCE(SUM(dc.raw_count), 0), COUNT(DISTINCT dc.iso3)
    FROM disease_cases dc
    JOIN diseases d ON d.id = dc.disease_id
    WHERE d.code = 'flu'
      AND dc.iso_year = 2019
      AND dc.iso_week = 2
    """
)
total, countries = cur.fetchone()

cur.execute(
    """
    SELECT COUNT(*)
    FROM disease_cases dc
    JOIN diseases d ON d.id = dc.disease_id
    WHERE d.code = 'flu'
      AND dc.iso_year BETWEEN 2010 AND 2019
      AND dc.raw_count > 0
    """
)
train_rows = cur.fetchone()[0]

print({
    "flu_2019_w2_total_raw_count": int(total),
    "countries_with_data": int(countries),
    "training_rows_2010_2019_positive": int(train_rows),
})

cur.close()
conn.close()
