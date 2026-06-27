"""Cau hinh duong dan va hang so cho toan bo pipeline KLTN."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Project root = thu muc cha cua scripts/ -- khong phu thuoc CWD
_ROOT = Path(__file__).resolve().parent.parent

load_dotenv(_ROOT / '.env')

# ── Epidemic data paths ───────────────────────────────────────────────────────
EPIDEMIC_DIR = _ROOT / 'dataset' / 'epidemic'
RAW          = EPIDEMIC_DIR / 'raw'

FILES = {
    'flunet'   : RAW / 'VIW_FNT.csv',
    'flu_meta' : RAW / 'VIW_FLU_METADATA.csv',
    'flu_bak'  : RAW / 'influenza_weekly.csv',
    'dengue'   : RAW / 'National_extract_V1_3.csv',
    'ecdc_sen' : RAW / 'sentinelTestsDetectionsPositivity.csv',
    'ecdc_ili'  : RAW / 'ILIARIRates.csv',
}

# ── Weather data paths ────────────────────────────────────────────────────────
WEATHER_DIR       = _ROOT / 'dataset' / 'weather'
ERA5_RAW_DIR      = WEATHER_DIR / 'era5_raw'      # era5_{year}/ folders vao day
WEATHER_PROCESSED = WEATHER_DIR / 'processed'      # era5_weekly CSV

ERA5_FILE = WEATHER_PROCESSED / 'era5_weekly_2010_2019_final.csv'

# ── Final merged output ───────────────────────────────────────────────────────
PROCESSED   = _ROOT / 'dataset' / 'processed'     # file cuoi cung
OUTPUT_FILE = PROCESSED / 'master_weekly_2010_2019.csv'

# Tao thu muc neu chua co
ERA5_RAW_DIR.mkdir(parents=True, exist_ok=True)
WEATHER_PROCESSED.mkdir(parents=True, exist_ok=True)
PROCESSED.mkdir(parents=True, exist_ok=True)

# ── Time periods ──────────────────────────────────────────────────────────────
TRAIN_START = 2010
TRAIN_END   = 2019
VAL_YEAR    = 2022
COVID_YEARS = [2020, 2021]

# ── ERA5 / CDS API ────────────────────────────────────────────────────────────
CDS_KEY      = os.getenv('CDS_KEY', '')
DOWNLOAD_DIR = str(ERA5_RAW_DIR)   # download vao era5_raw/, sau do chuyen vao era5_{year}/
