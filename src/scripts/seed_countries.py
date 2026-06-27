"""
Seed bảng countries từ master_weekly_v1.csv.

Lấy:
  - iso3, iso2, country_name từ pycountry
  - who_region từ mapping (khớp với loader.py)
  - latitude, longitude từ tập centroid chuẩn (Natural Earth)

Chạy:
  cd KLTN
  python scripts/seed_countries.py
"""

import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import pycountry
import psycopg2
from psycopg2.extras import execute_batch
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:111111111@localhost:5432/kltn_epiweather",
)
MASTER_CSV = os.path.join(os.path.dirname(__file__), "../data/processed/master_weekly_v1.csv")

# ── WHO region mapping (đồng bộ với backend/app/ml/loader.py) ────────────────
WHO_REGIONS = {
    "AFR": ["DZA","AGO","BEN","BWA","BFA","BDI","CPV","CMR","CAF","TCD","COM","COG","COD","CIV",
            "GNQ","ERI","SWZ","ETH","GAB","GMB","GHA","GIN","GNB","KEN","LSO","LBR","MDG","MWI",
            "MLI","MRT","MUS","MOZ","NAM","NER","NGA","RWA","STP","SEN","SYC","SLE","ZAF","SSD",
            "TGO","UGA","TZA","ZMB","ZWE"],
    "AMR": ["ATG","ARG","BHS","BRB","BLZ","BOL","BRA","CAN","CHL","COL","CRI","CUB","DMA","DOM",
            "ECU","SLV","GRD","GTM","GUY","HTI","HND","JAM","MEX","NIC","PAN","PRY","PER","KNA",
            "LCA","VCT","SUR","TTO","USA","URY","VEN","ABW","AIA","CYM"],
    "EMR": ["AFG","BHR","DJI","EGY","IRN","IRQ","JOR","KWT","LBN","LBY","MAR","OMN","PAK","PSE",
            "QAT","SAU","SOM","SDN","SYR","TUN","ARE","YEM"],
    "EUR": ["ALB","AND","ARM","AUT","AZE","BLR","BEL","BIH","BGR","HRV","CYP","CZE","DNK","EST",
            "FIN","FRA","GEO","DEU","GRC","HUN","ISL","IRL","ISR","ITA","KAZ","KGZ","LVA","LTU",
            "LUX","MLT","MCO","MNE","NLD","MKD","NOR","POL","PRT","MDA","ROU","RUS","SMR","SRB",
            "SVK","SVN","ESP","SWE","CHE","TJK","TUR","TKM","UKR","GBR","UZB"],
    "SEAR": ["BGD","BTN","PRK","IND","IDN","MDV","MMR","NPL","LKA","THA","TLS"],
    "WPR": ["AUS","BRN","KHM","CHN","COK","FJI","JPN","KIR","LAO","MYS","MHL","FSM","MNG","NRU",
            "NZL","NIU","PLW","PNG","PHL","KOR","WSM","SGP","SLB","TON","TUV","VUT","VNM","HKG","MAC","NCL"],
}
ISO3_TO_REGION = {iso: reg for reg, isos in WHO_REGIONS.items() for iso in isos}

# Bổ sung WHO region encoding (dùng cho ML feature)
REGION_ENC = {"AFR": 0, "AMR": 1, "EMR": 2, "EUR": 3, "SEAR": 4, "WPR": 5}

# ── Approximate centroids (lat, lon) cho 163 nước trong dataset ──────────────
# Nguồn: Natural Earth 1:110m — tọa độ trọng tâm hành chính
CENTROIDS = {
    "AFG": (33.9, 67.7), "AGO": (-11.2, 17.9), "ALB": (41.2, 20.2), "AND": (42.5, 1.5),
    "ARE": (24.0, 54.0), "ARG": (-38.4, -63.6), "ARM": (40.1, 45.0), "ATG": (17.1, -61.8),
    "AUS": (-25.3, 133.8), "AUT": (47.5, 14.6), "AZE": (40.1, 47.6), "BGD": (23.7, 90.4),
    "BEL": (50.5, 4.5), "BEN": (9.3, 2.3), "BFA": (12.4, -1.6), "BGR": (42.7, 25.5),
    "BHR": (26.0, 50.6), "BIH": (44.2, 17.9), "BLR": (53.7, 28.0), "BLZ": (17.2, -88.5),
    "BOL": (-16.3, -63.6), "BRA": (-14.2, -51.9), "BRB": (13.2, -59.6), "BRN": (4.5, 114.7),
    "BTN": (27.5, 90.4), "BWA": (-22.3, 24.7), "CAF": (6.6, 20.9), "CAN": (56.1, -106.3),
    "CHE": (47.0, 8.2), "CHL": (-35.7, -71.5), "CHN": (35.9, 104.2), "CIV": (7.5, -5.5),
    "CMR": (3.9, 11.5), "COD": (-4.0, 21.8), "COG": (-0.2, 15.8), "COK": (-21.2, -159.8),
    "COL": (4.1, -72.9), "COM": (-11.9, 43.3), "CPV": (16.0, -24.0), "CRI": (9.7, -83.8),
    "CUB": (22.0, -80.0), "CYM": (19.3, -81.4), "CYP": (35.1, 33.4), "CZE": (49.8, 15.5),
    "DEU": (51.2, 10.5), "DJI": (11.8, 42.6), "DMA": (15.4, -61.4), "DNK": (56.3, 9.5),
    "DOM": (18.7, -70.2), "DZA": (28.0, 3.0), "ECU": (-1.8, -78.2), "EGY": (26.8, 30.8),
    "ERI": (15.2, 39.8), "ESP": (40.5, -3.7), "EST": (58.6, 25.0), "ETH": (9.1, 40.5),
    "FIN": (64.0, 26.0), "FJI": (-16.6, 179.4), "FRA": (46.2, 2.2), "GAB": (-0.8, 11.6),
    "GBR": (55.4, -3.4), "GEO": (42.3, 43.4), "GHA": (7.9, -1.0), "GIN": (11.0, -10.9),
    "GMB": (13.4, -15.3), "GNB": (11.8, -15.2), "GNQ": (1.7, 10.3), "GRC": (39.1, 22.0),
    "GRD": (12.1, -61.7), "GTM": (15.8, -90.2), "GUY": (5.0, -58.9), "HKG": (22.4, 114.1),
    "HND": (15.2, -86.2), "HRV": (45.1, 15.2), "HTI": (18.9, -72.3), "HUN": (47.2, 19.5),
    "IDN": (-0.8, 113.9), "IND": (20.6, 79.1), "IRL": (53.4, -8.2), "IRN": (32.4, 53.7),
    "IRQ": (33.2, 43.7), "ISL": (64.9, -18.7), "ISR": (31.0, 34.9), "ITA": (41.9, 12.6),
    "JAM": (18.1, -77.3), "JOR": (30.6, 36.2), "JPN": (36.2, 138.3), "KAZ": (48.0, 66.9),
    "KEN": (-1.3, 36.9), "KGZ": (41.2, 74.8), "KHM": (12.6, 104.9), "KIR": (-3.4, -168.7),
    "KNA": (17.4, -62.8), "KOR": (36.0, 128.0), "KWT": (29.3, 47.5), "LAO": (19.9, 102.5),
    "LBN": (33.9, 35.5), "LBR": (6.4, -9.4), "LBY": (26.3, 17.2), "LCA": (13.9, -60.0),
    "LSO": (-29.6, 28.2), "LTU": (55.2, 23.9), "LUX": (49.8, 6.1), "LVA": (56.9, 24.6),
    "MAC": (22.2, 113.5), "MAR": (31.8, -7.1), "MDA": (47.4, 28.4), "MDG": (-18.8, 46.9),
    "MDV": (3.2, 73.2), "MEX": (23.6, -102.6), "MHL": (7.1, 171.2), "MKD": (41.6, 21.7),
    "MLI": (17.6, -2.0), "MLT": (35.9, 14.4), "MMR": (17.1, 96.0), "MNG": (46.9, 103.8),
    "MCO": (43.7, 7.4), "MOZ": (-17.3, 35.0), "MRT": (21.0, -11.0), "MUS": (-20.3, 57.6),
    "MWI": (-13.3, 34.3), "MYS": (4.2, 108.0), "NAM": (-22.4, 17.1), "NCL": (-20.9, 165.6),
    "NER": (17.6, 8.1), "NGA": (9.1, 8.7), "NIC": (12.9, -85.2), "NIU": (-19.1, -169.9),
    "NLD": (52.1, 5.3), "NOR": (60.5, 8.5), "NPL": (28.4, 84.1), "NRU": (-0.5, 166.9),
    "NZL": (-40.9, 174.9), "OMN": (21.5, 55.9), "PAK": (30.4, 69.3), "PAN": (8.5, -80.8),
    "PER": (-9.2, -75.0), "PHL": (12.9, 121.8), "PLW": (7.5, 134.6), "PNG": (-6.3, 143.9),
    "POL": (51.9, 19.1), "PRK": (40.3, 127.5), "PRY": (-23.4, -58.4), "PSE": (31.9, 35.2),
    "PRT": (39.4, -8.2), "QAT": (25.4, 51.2), "ROU": (45.9, 24.9), "RUS": (61.5, 105.3),
    "RWA": (-1.9, 29.9), "SAU": (24.0, 45.1), "SDN": (12.9, 30.2), "SEN": (14.5, -14.5),
    "SGP": (1.4, 103.8), "SLB": (-9.6, 160.2), "SLE": (8.5, -11.8), "SLV": (13.8, -88.9),
    "SMR": (43.9, 12.5), "SOM": (5.2, 46.2), "SRB": (44.0, 21.0), "SSD": (7.9, 30.2),
    "STP": (0.2, 6.6), "SUR": (3.9, -56.0), "SVK": (48.7, 19.7), "SVN": (46.2, 14.8),
    "SWE": (60.1, 18.6), "SWZ": (-26.5, 31.5), "SYC": (-4.7, 55.5), "SYR": (34.8, 38.0),
    "TCD": (15.5, 18.7), "TGO": (8.6, 0.8), "THA": (15.9, 100.9), "TJK": (38.9, 71.3),
    "TKM": (40.0, 60.0), "TLS": (-8.9, 125.7), "TON": (-21.2, -175.2), "TTO": (10.7, -61.2),
    "TUN": (33.9, 9.5), "TUR": (38.9, 35.2), "TUV": (-8.5, 179.2), "TZA": (-6.4, 34.9),
    "UGA": (1.4, 32.3), "UKR": (48.4, 31.2), "URY": (-32.5, -55.8), "USA": (37.1, -95.7),
    "UZB": (41.4, 63.0), "VCT": (12.9, -61.2), "VEN": (6.4, -66.6), "VNM": (14.1, 108.3),
    "VUT": (-15.4, 166.9), "WSM": (-13.8, -172.1), "YEM": (15.6, 48.5),
    "ZAF": (-29.0, 25.1), "ZMB": (-13.1, 27.8), "ZWE": (-20.0, 30.0),
    "ABW": (12.5, -70.0), "AIA": (18.2, -63.1), "CYM": (19.3, -81.4),
    "BHS": (25.0, -77.4), "LKA": (7.9, 80.8), "MNE": (42.7, 19.4),
    "PRI": (18.2, -66.6), "PYF": (-17.7, -149.4), "TWN": (23.7, 121.0),
    "VIR": (18.3, -64.9),
}


def build_rows(iso3_list: list[str]) -> list[dict]:
    rows = []
    for iso3 in iso3_list:
        try:
            c = pycountry.countries.get(alpha_3=iso3)
            name = c.name if c else iso3
            iso2 = c.alpha_2 if c else None
        except Exception:
            name, iso2 = iso3, None

        region = ISO3_TO_REGION.get(iso3)
        region_enc = REGION_ENC.get(region) if region else None
        lat, lon = CENTROIDS.get(iso3, (None, None))

        rows.append({
            "iso3": iso3,
            "iso2": iso2,
            "country_name": name,
            "who_region": region,
            "who_region_enc": region_enc,
            "latitude": lat,
            "longitude": lon,
        })
    return rows


def main():
    # Lấy danh sách iso3 từ master CSV
    df = pd.read_csv(MASTER_CSV, usecols=["iso3"])
    iso3_list = sorted(df["iso3"].unique().tolist())
    print(f"Tìm thấy {len(iso3_list)} nước trong master CSV")

    rows = build_rows(iso3_list)
    missing_centroid = [r["iso3"] for r in rows if r["latitude"] is None]
    if missing_centroid:
        print(f"[CẢNH BÁO] Không có centroid cho: {missing_centroid}")

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    sql = """
    INSERT INTO countries (iso3, iso2, country_name, who_region, who_region_enc, latitude, longitude)
    VALUES (%(iso3)s, %(iso2)s, %(country_name)s, %(who_region)s, %(who_region_enc)s,
            %(latitude)s, %(longitude)s)
    ON CONFLICT (iso3) DO UPDATE SET
        iso2           = EXCLUDED.iso2,
        country_name   = EXCLUDED.country_name,
        who_region     = EXCLUDED.who_region,
        who_region_enc = EXCLUDED.who_region_enc,
        latitude       = EXCLUDED.latitude,
        longitude      = EXCLUDED.longitude
    """
    execute_batch(cur, sql, rows, page_size=100)
    conn.commit()
    cur.close()
    conn.close()

    print(f"Đã insert/update {len(rows)} nước vào bảng countries")


if __name__ == "__main__":
    main()
