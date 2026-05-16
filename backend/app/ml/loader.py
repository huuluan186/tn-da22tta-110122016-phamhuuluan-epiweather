import pickle
from pathlib import Path

import numpy as np

# global champion models  {disease: champ_dict}
_global: dict = {}
# per-region models  {disease: {region: champ_dict}}
_regional: dict = {"flu": {}, "dengue": {}}

ISO3_TO_REGION: dict[str, str] = {}

_WHO_REGIONS = {
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

for _reg, _isos in _WHO_REGIONS.items():
    for _iso in _isos:
        ISO3_TO_REGION[_iso] = _reg


def load_models(models_dir: Path) -> None:
    """Load global champion + per-region models từ MODELS_DIR."""
    for disease in ("flu", "dengue"):
        p = models_dir / f"champion_{disease}_xgboost_tuned.pkl"
        if p.exists():
            with open(p, "rb") as f:
                _global[disease] = pickle.load(f)

    for disease in ("flu", "dengue"):
        for region in ("AFR", "AMR", "EMR", "EUR", "SEAR", "WPR"):
            p = models_dir / f"champion_{disease}_xgb_{region}.pkl"
            if p.exists():
                with open(p, "rb") as f:
                    _regional[disease][region] = pickle.load(f)

    loaded = {d: list(_regional[d].keys()) for d in ("flu", "dengue")}
    print(f"[loader] global models: {list(_global.keys())}")
    print(f"[loader] regional models: {loaded}")


def predict(disease: str, iso3: str, feature_values: dict) -> dict:
    """
    Predict risk cho 1 (disease, country, week).
    Trả về {'risk_level': str, 'p_low': float, 'p_med': float, 'p_high': float, 'model_used': str}
    """
    region = ISO3_TO_REGION.get(iso3.upper(), "UNK")
    champ = _regional[disease].get(region) or _global.get(disease)
    if champ is None:
        raise ValueError(f"No model loaded for disease={disease}")

    model     = champ["model"]
    features  = champ["features"]
    threshold = champ.get("threshold")

    X = np.array([[feature_values.get(f, 0.0) for f in features]])
    proba = model.predict_proba(X)[0]

    if threshold is not None:
        pred = 2 if proba[2] > threshold else int(np.argmax(proba[:2]))
    else:
        pred = int(np.argmax(proba))

    label_map = {0: "Low", 1: "Medium", 2: "High"}
    model_used = f"region:{region}" if region in _regional[disease] else "global"

    return {
        "risk_level": label_map[pred],
        "p_low":      round(float(proba[0]), 4),
        "p_med":      round(float(proba[1]), 4),
        "p_high":     round(float(proba[2]), 4),
        "model_used": model_used,
    }


def get_features(disease: str) -> list[str]:
    champ = _global.get(disease)
    return champ["features"] if champ else []


def loaded_diseases() -> list[str]:
    return list(_global.keys())
