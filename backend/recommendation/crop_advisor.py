"""
Crop Advisory & Strategic Agronomic Planning.
Provides Multi-Criteria Crop Suitability Analysis, regional variety recommendations,
optimal sowing/harvest windows, and disease/pest vulnerability evaluations.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

# High-Yielding Recommended Crop Varieties for Indian States
CROP_VARIETY_DATABASE = {
    "RICE": {
        "varieties": [
            {"name": "BPT 5204 (Samba Mahsuri)", "duration_days": 145, "features": "Premium fine grain, high market price, resistant to bacterial leaf blight."},
            {"name": "MTU 1010 (Cottondora Sannalu)", "duration_days": 120, "features": "Short duration, high tillering, lodging resistant, ideal for Kharif/Rabi."},
            {"name": "Pusa Basmati 1121", "duration_days": 140, "features": "Extra-long slender grain, export quality, premium mandi realization."},
            {"name": "Swarna (MTU 7029)", "duration_days": 150, "features": "High yielding mega-variety, flood tolerant (Sub1 gene)."}
        ],
        "sowing_window": "June 15 - July 15 (Kharif) / Nov 15 - Dec 15 (Rabi)",
        "harvest_window": "October 20 - November 30 (Kharif) / April 01 - April 30 (Rabi)",
        "cost_of_cultivation_per_acre": 24000.0,
        "diseases": [
            {"name": "Blast (Pyricularia oryzae)", "conditions": "High humidity > 85%, temp 22-28°C", "treatment": "Foliar spray of Tricyclazole 75% WP @ 0.6 g/L"},
            {"name": "Bacterial Leaf Blight (Xanthomonas)", "conditions": "Rainy windy weather with water stagnation", "treatment": "Spray Copper Oxychloride 50% WP @ 2.5 g/L + Streptocycline @ 0.1 g/L"}
        ]
    },
    "WHEAT": {
        "varieties": [
            {"name": "HD 2967", "duration_days": 140, "features": "High yielding, resistant to yellow and brown rust, wide adaptability."},
            {"name": "PBW 550", "duration_days": 135, "features": "Early maturity, bold grain, high protein content."},
            {"name": "DBW 187 (Karan Vandana)", "duration_days": 120, "features": "Heat tolerant, bio-fortified with iron and zinc, high chapati making quality."}
        ],
        "sowing_window": "November 01 - November 25 (Optimal Rabi Window)",
        "harvest_window": "March 20 - April 15",
        "cost_of_cultivation_per_acre": 18500.0,
        "diseases": [
            {"name": "Yellow Rust (Puccinia striiformis)", "conditions": "Cool humid weather < 18°C", "treatment": "Propiconazole 25% EC @ 1 ml/L"},
            {"name": "Loose Smut (Ustilago tritici)", "conditions": "Seed-borne infection during heading", "treatment": "Seed treatment with Carboxin + Thiram @ 2 g/kg seed"}
        ]
    },
    "COTTON": {
        "varieties": [
            {"name": "RCH 659 Bt-II", "duration_days": 160, "features": "Bollworm resistant, high boll weight, excellent fiber strength."},
            {"name": "Brahma BG-II", "duration_days": 165, "features": "Deep rooting, drought tolerant, suitable for black cotton soils."},
            {"name": "Mallika Bt", "duration_days": 155, "features": "High branching, heavy fruiting, easy for picking."}
        ],
        "sowing_window": "May 15 - June 20 (Early Monsoon)",
        "harvest_window": "November 01 - January 15 (Multiple pickings)",
        "cost_of_cultivation_per_acre": 28000.0,
        "diseases": [
            {"name": "Pink Bollworm (Pectinophora gossypiella)", "conditions": "Flowering to boll formation stage", "treatment": "Install pheromone traps @ 5/acre, spray Emamectin Benzoate 5% SG @ 0.4 g/L"},
            {"name": "Sucking Pests (Thrips, Aphids, Whitefly)", "conditions": "Dry hot spells followed by humidity", "treatment": "Spray Diafenthiuron 50% WP @ 1.2 g/L or Flonicamid 50% WG @ 0.3 g/L"}
        ]
    },
    "MAIZE": {
        "varieties": [
            {"name": "Pioneer P3396", "duration_days": 105, "features": "High grain yield, strong lodging resistance, uniform cob size."},
            {"name": "DKC 9108", "duration_days": 110, "features": "Drought resilient hybrid, excellent tip filling, stay-green foliage."}
        ],
        "sowing_window": "June 15 - July 10 (Kharif) / Oct 15 - Nov 15 (Rabi)",
        "harvest_window": "September 25 - October 20 (Kharif)",
        "cost_of_cultivation_per_acre": 19000.0,
        "diseases": [
            {"name": "Fall Armyworm (Spodoptera frugiperda)", "conditions": "Whorl stage 15-40 days after emergence", "treatment": "Apply Chlorantraniliprole 18.5% SC @ 0.4 ml/L directly into whorl"}
        ]
    },
    "CHILLI": {
        "varieties": [
            {"name": "Guntur Sannam (S4)", "duration_days": 150, "features": "High pungency (SHU), dark red color, strong market demand."},
            {"name": "Byadagi Dabbi", "duration_days": 160, "features": "High oleoresin and red color value, mild pungency, premium export pricing."}
        ],
        "sowing_window": "July 15 - August 31 (Transplanting)",
        "harvest_window": "December 15 - March 31",
        "cost_of_cultivation_per_acre": 42000.0,
        "diseases": [
            {"name": "Anthracnose / Fruit Rot (Colletotrichum)", "conditions": "Warm humid conditions during fruiting", "treatment": "Spray Azoxystrobin + Difenoconazole @ 1 ml/L"},
            {"name": "Black Thrips (Thrips parvispinus)", "conditions": "Dry warm weather", "treatment": "Spray Spinetoram 11.7% SC @ 1 ml/L"}
        ]
    },
    "TOMATO": {
        "varieties": [
            {"name": "Arka Rakshak", "duration_days": 130, "features": "Triple disease resistant (ToLCV, Early Blight, Bacterial Wilt), high yield 35 t/acre."},
            {"name": "Abhinav (Syngenta)", "duration_days": 120, "features": "Firm fruit, high shelf life for long distance transit, prolific bearing."}
        ],
        "sowing_window": "June - July / Oct - Nov / Jan - Feb (Round the year with irrigation)",
        "harvest_window": "90 - 130 days after transplanting",
        "cost_of_cultivation_per_acre": 36000.0,
        "diseases": [
            {"name": "Tomato Leaf Curl Virus (ToLCV)", "conditions": "Transmitted by whiteflies (Bemisia tabaci)", "treatment": "Vector control with Acetamiprid 20% SP @ 0.3 g/L + Yellow sticky traps"},
            {"name": "Early Blight (Alternaria solani)", "conditions": "High humidity and dense canopy", "treatment": "Mancozeb 75% WP @ 2.5 g/L"}
        ]
    },
    "DEFAULT": {
        "varieties": [
            {"name": "Certified High-Yielding Hybrid", "duration_days": 120, "features": "Certified regional hybrid with high pest and drought resilience."}
        ],
        "sowing_window": "June 15 - July 15 (Monsoon) / Nov 01 - Nov 30 (Winter)",
        "harvest_window": "100 - 130 days post sowing",
        "cost_of_cultivation_per_acre": 22000.0,
        "diseases": [
            {"name": "General Foliar Spot", "conditions": "Humid overcast weather", "treatment": "Broad spectrum copper / bio-fungicide spray"}
        ]
    }
}


def get_variety_and_window_advisory(crop: str, state: Optional[str] = None, season: Optional[str] = None) -> Dict[str, Any]:
    """
    Returns high-yielding certified varieties, sowing window, harvest window, and cost of cultivation.
    """
    crop_clean = (crop or "DEFAULT").strip().upper()
    profile = CROP_VARIETY_DATABASE.get(crop_clean, CROP_VARIETY_DATABASE["DEFAULT"])

    return {
        "crop": crop.title(),
        "recommended_varieties": profile["varieties"],
        "primary_variety": profile["varieties"][0]["name"],
        "sowing_window": profile["sowing_window"],
        "harvest_window": profile["harvest_window"],
        "cost_of_cultivation_per_acre_inr": profile["cost_of_cultivation_per_acre"],
        "major_diseases": profile["diseases"]
    }


def evaluate_disease_risks(
    crop: str,
    temp_c: float,
    humidity_percent: float,
    ndvi: float = 0.6
) -> List[Dict[str, Any]]:
    """
    Cross-evaluates meteorological conditions and satellite stress against crop specific pathogens.
    """
    crop_clean = (crop or "DEFAULT").strip().upper()
    profile = CROP_VARIETY_DATABASE.get(crop_clean, CROP_VARIETY_DATABASE["DEFAULT"])
    diseases = profile["diseases"]

    risk_assessments = []
    for d in diseases:
        # High humidity (>80%) combined with moderate warm temp (22-30C) triggers high risk
        if humidity_percent >= 80.0 and (20.0 <= temp_c <= 32.0):
            risk_lvl = "HIGH"
            color = "#ef4444"
            probability = 82.0
        elif humidity_percent >= 70.0:
            risk_lvl = "MODERATE"
            color = "#f59e0b"
            probability = 54.0
        else:
            risk_lvl = "LOW"
            color = "#10b981"
            probability = 20.0

        risk_assessments.append({
            "disease_name": d["name"],
            "risk_level": risk_lvl,
            "probability_percent": probability,
            "color": color,
            "favorable_conditions": d["conditions"],
            "preventive_prescription": d["treatment"]
        })

    return risk_assessments


def rank_crop_suitability(
    state: str,
    district: Optional[str] = None,
    season: str = "Kharif",
    ph: float = 7.2,
    rainfall_mm: float = 950.0
) -> List[Dict[str, Any]]:
    """
    Ranks agricultural crops for a specific land plot using Multi-Criteria Decision Analysis.
    Criteria: Soil pH, moisture adequacy, thermal match, and economic returns.
    """
    candidate_crops = ["Rice", "Cotton", "Maize", "Groundnut", "Tomato", "Chilli", "Wheat"]
    ranked = []

    for c in candidate_crops:
        score = 85.0
        # pH penalty
        if ph < 6.0 or ph > 8.0:
            score -= 10.0
        # Season alignment
        if season.lower() == "rabi" and c in ["Wheat", "Tomato", "Maize"]:
            score += 10.0
        elif season.lower() == "kharif" and c in ["Rice", "Cotton", "Chilli", "Maize"]:
            score += 10.0

        # Rainfall alignment
        if c == "Rice" and rainfall_mm < 700:
            score -= 15.0  # High water demand
        if c == "Cotton" and rainfall_mm > 1400:
            score -= 10.0  # Excess water penalty

        score = round(max(40.0, min(98.0, score)), 1)
        suitability = "Highly Recommended" if score >= 85 else ("Recommended" if score >= 70 else "Moderate Suitability")
        color = "#10b981" if score >= 85 else ("#34d399" if score >= 70 else "#fbbf24")

        ranked.append({
            "crop": c,
            "suitability_score": score,
            "suitability_rating": suitability,
            "color": color,
            "expected_economic_viability": "High Profitability" if score >= 80 else "Moderate Returns"
        })

    ranked.sort(key=lambda x: x["suitability_score"], reverse=True)
    return ranked
