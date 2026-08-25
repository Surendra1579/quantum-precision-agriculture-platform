"""
Soil Property & Health Scoring Engine.
Implements Indian Council of Agricultural Research (ICAR) & Soil Health Card standards
for NPK rating, micronutrient critical limits, Soil Health Index (0-100), and pH correction.
"""

from typing import Dict, Any, List, Tuple


# ICAR Standard Benchmarks for Indian Agricultural Soils
NUTRIENT_BENCHMARKS = {
    "nitrogen": {"low": 280.0, "high": 560.0, "unit": "kg/ha", "weight": 0.20},
    "phosphorus": {"low": 10.0, "high": 25.0, "unit": "kg/ha", "weight": 0.18},
    "potassium": {"low": 110.0, "high": 280.0, "unit": "kg/ha", "weight": 0.15},
    "organic_carbon": {"low": 0.50, "high": 0.75, "unit": "%", "weight": 0.18},
    "ph": {"optimal_min": 6.5, "optimal_max": 7.5, "unit": "pH", "weight": 0.12},
    "ec": {"normal_max": 1.0, "critical": 2.0, "unit": "dS/m", "weight": 0.07},
    "zinc": {"critical": 0.6, "unit": "ppm", "weight": 0.02},
    "iron": {"critical": 4.5, "unit": "ppm", "weight": 0.02},
    "manganese": {"critical": 2.0, "unit": "ppm", "weight": 0.02},
    "copper": {"critical": 0.2, "unit": "ppm", "weight": 0.02},
    "boron": {"critical": 0.5, "unit": "ppm", "weight": 0.02},
    "sulphur": {"critical": 10.0, "unit": "ppm", "weight": 0.02},
}


def calculate_npk_adequacy(n: float, p: float, k: float) -> Dict[str, Any]:
    """
    Evaluates macro-nutrient status (Low, Medium, High) against ICAR benchmarks.
    """
    def _status(val: float, low: float, high: float) -> Tuple[str, str, float]:
        if val < low:
            return "Deficient", "#ef4444", round((val / low) * 50, 1)
        elif val <= high:
            return "Optimal", "#10b981", round(50 + ((val - low) / (high - low)) * 35, 1)
        else:
            return "Excess / High", "#3b82f6", 100.0

    n_stat, n_color, n_pct = _status(n, NUTRIENT_BENCHMARKS["nitrogen"]["low"], NUTRIENT_BENCHMARKS["nitrogen"]["high"])
    p_stat, p_color, p_pct = _status(p, NUTRIENT_BENCHMARKS["phosphorus"]["low"], NUTRIENT_BENCHMARKS["phosphorus"]["high"])
    k_stat, k_color, k_pct = _status(k, NUTRIENT_BENCHMARKS["potassium"]["low"], NUTRIENT_BENCHMARKS["potassium"]["high"])

    return {
        "nitrogen": {"value": n, "unit": "kg/ha", "status": n_stat, "color": n_color, "adequacy_percent": n_pct},
        "phosphorus": {"value": p, "unit": "kg/ha", "status": p_stat, "color": p_color, "adequacy_percent": p_pct},
        "potassium": {"value": k, "unit": "kg/ha", "status": k_stat, "color": k_color, "adequacy_percent": k_pct},
        "npk_ratio_observed": f"{round(n/max(k, 1), 1)} : {round(p/max(k, 1), 1)} : 1.0",
        "npk_ratio_ideal": "4.0 : 2.0 : 1.0"
    }


def calculate_ph_corrections(ph: float, soil_type: str = "Loam") -> Dict[str, Any]:
    """
    Calculates soil conditioner requirements (Gypsum for sodic/alkaline, Lime for acidic).
    """
    if ph < 6.0:
        lime_kg_acre = round(max(0, (6.5 - ph) * 400.0), 0)
        return {
            "soil_reaction": "Acidic",
            "condition": "Soil acidity limits phosphorus availability and microbial nitrogen fixation.",
            "remediation": "Apply Agricultural Lime (CaCO3) / Dolomite.",
            "amendment_name": "Agricultural Lime (CaCO3)",
            "quantity_kg_per_acre": lime_kg_acre,
            "application_timing": "Apply 3-4 weeks before sowing during primary tillage."
        }
    elif ph > 7.8:
        gypsum_kg_acre = round(max(0, (ph - 7.5) * 500.0), 0)
        return {
            "soil_reaction": "Alkaline / Calcareous",
            "condition": "High pH limits Zinc, Iron, and Phosphorus absorption.",
            "remediation": "Apply Mineral Gypsum (CaSO4.2H2O) and organic compost.",
            "amendment_name": "Mineral Gypsum",
            "quantity_kg_per_acre": gypsum_kg_acre,
            "application_timing": "Incorporate with pre-sowing irrigation to flush excess sodium."
        }
    else:
        return {
            "soil_reaction": "Neutral / Optimal",
            "condition": "Ideal soil reaction for maximum nutrient bioavailability.",
            "remediation": "No chemical pH amendment required.",
            "amendment_name": "None",
            "quantity_kg_per_acre": 0.0,
            "application_timing": "Maintain organic matter with green manuring."
        }


def diagnose_soil_deficiencies(soil_params: Dict[str, float]) -> List[Dict[str, Any]]:
    """
    Generates a structured deficiency diagnosis report for all deficient macro & micronutrients.
    """
    deficiencies = []
    
    # Nitrogen
    n_val = soil_params.get("nitrogen", 240.0)
    if n_val < NUTRIENT_BENCHMARKS["nitrogen"]["low"]:
        deficiencies.append({
            "nutrient": "Nitrogen (N)",
            "category": "Macronutrient",
            "severity": "High" if n_val < 180 else "Moderate",
            "symptom": "Stunted vegetative growth, chlorosis (yellowing of older lower leaves).",
            "corrective_action": "Apply split dose of Urea / Neem-Coated Urea or Azotobacter biofertilizer."
        })

    # Phosphorus
    p_val = soil_params.get("phosphorus", 12.0)
    if p_val < NUTRIENT_BENCHMARKS["phosphorus"]["low"]:
        deficiencies.append({
            "nutrient": "Phosphorus (P)",
            "category": "Macronutrient",
            "severity": "High" if p_val < 7.0 else "Moderate",
            "symptom": "Poor root elongation, purplish tint on lower foliage, delayed flowering.",
            "corrective_action": "Apply DAP (Di-Ammonium Phosphate) or Single Super Phosphate (SSP) with PSB culture."
        })

    # Potassium
    k_val = soil_params.get("potassium", 180.0)
    if k_val < NUTRIENT_BENCHMARKS["potassium"]["low"]:
        deficiencies.append({
            "nutrient": "Potassium (K)",
            "category": "Macronutrient",
            "severity": "High" if k_val < 80 else "Moderate",
            "symptom": "Marginal leaf scorch, weak stalk strength, susceptibility to lodging and pests.",
            "corrective_action": "Apply Muriate of Potash (MOP / 0-0-60) at basal stage."
        })

    # Organic Carbon
    oc_val = soil_params.get("organic_carbon", 0.55)
    if oc_val < NUTRIENT_BENCHMARKS["organic_carbon"]["low"]:
        deficiencies.append({
            "nutrient": "Organic Carbon (OC)",
            "category": "Soil Organic Matter",
            "severity": "Critical" if oc_val < 0.35 else "Moderate",
            "symptom": "Low cation exchange capacity, poor moisture retention, degraded soil microbiome.",
            "corrective_action": "Incorporate 4-5 Tons/Acre Farm Yard Manure (FYM) or Vermicompost."
        })

    # Micronutrients
    micros = [
        ("zinc", "Zinc (Zn)", 0.6, "Khaira disease, interveinal chlorosis in young leaves", "Foliar spray of 0.5% Zinc Sulphate + 0.25% Lime"),
        ("iron", "Iron (Fe)", 4.5, "Complete bleaching of young emerging shoots", "Apply Ferrous Sulphate (FeSO4) @ 10 kg/acre or 1% foliar spray"),
        ("boron", "Boron (B)", 0.5, "Hollow heart, cracked stems, poor grain/fruit set", "Soil application of Borax @ 4 kg/acre"),
        ("sulphur", "Sulphur (S)", 10.0, "Yellowing of young upper leaves (oilseed yield decline)", "Apply Gypsum or SSP containing 12% available sulphur"),
    ]

    for key, name, crit_val, symptom, action in micros:
        val = soil_params.get(key, crit_val + 0.1)
        if val < crit_val:
            deficiencies.append({
                "nutrient": name,
                "category": "Micronutrient",
                "severity": "Moderate",
                "symptom": symptom,
                "corrective_action": action
            })

    return deficiencies


def evaluate_soil_health(soil_params: Dict[str, float]) -> Dict[str, Any]:
    """
    Computes Soil Health Index (0 - 100) combining physical, chemical, and biological factors.
    """
    n = soil_params.get("nitrogen", 260.0)
    p = soil_params.get("phosphorus", 14.0)
    k = soil_params.get("potassium", 190.0)
    oc = soil_params.get("organic_carbon", 0.55)
    ph = soil_params.get("ph", 7.2)
    ec = soil_params.get("ec", 0.6)
    moist = soil_params.get("moisture", 0.25)
    zn = soil_params.get("zinc", 0.8)
    fe = soil_params.get("iron", 4.8)
    b = soil_params.get("boron", 0.6)
    s = soil_params.get("sulphur", 12.0)

    # Sub-scores (0 - 100)
    n_score = min(100.0, (n / 350.0) * 100.0)
    p_score = min(100.0, (p / 20.0) * 100.0)
    k_score = min(100.0, (k / 220.0) * 100.0)
    oc_score = min(100.0, (oc / 0.75) * 100.0)
    
    # pH score (bell curve around 7.0)
    ph_score = max(20.0, 100.0 - (abs(ph - 7.0) * 35.0))
    # EC score (lower is better, > 2.0 is salinity stress)
    ec_score = max(20.0, 100.0 - (max(0.0, ec - 0.8) * 50.0))
    # Moisture score
    moist_score = min(100.0, (moist / 0.30) * 100.0) if moist <= 0.30 else max(30.0, 100.0 - (moist - 0.30) * 200.0)
    # Micronutrient sub-score
    micro_score = (
        (min(1.0, zn / 0.6) + min(1.0, fe / 4.5) + min(1.0, b / 0.5) + min(1.0, s / 10.0)) / 4.0
    ) * 100.0

    # Composite Weighted Soil Health Index
    total_score = round(
        (0.20 * n_score) +
        (0.15 * p_score) +
        (0.12 * k_score) +
        (0.20 * oc_score) +
        (0.13 * ph_score) +
        (0.06 * ec_score) +
        (0.07 * moist_score) +
        (0.07 * micro_score),
        1
    )
    total_score = max(10.0, min(100.0, total_score))

    if total_score >= 80.0:
        grade = "Grade A (Highly Fertile)"
        badge_color = "#10b981"
        verdict = "Excellent nutrient balance and soil physical structure."
    elif total_score >= 65.0:
        grade = "Grade B (Moderately Fertile)"
        badge_color = "#34d399"
        verdict = "Good productive capacity. Targeted fertilization recommended."
    elif total_score >= 45.0:
        grade = "Grade C (Sub-Optimal / Stressed)"
        badge_color = "#fbbf24"
        verdict = "Nutrient imbalances detected. Requires organic carbon enhancement."
    else:
        grade = "Grade D (Severely Degraded)"
        badge_color = "#ef4444"
        verdict = "High deficiency/salinity. Comprehensive soil rejuvenation required."

    npk_eval = calculate_npk_adequacy(n, p, k)
    ph_remedy = calculate_ph_corrections(ph)
    deficiency_list = diagnose_soil_deficiencies(soil_params)

    return {
        "soil_health_score": total_score,
        "soil_grade": grade,
        "badge_color": badge_color,
        "verdict": verdict,
        "sub_scores": {
            "nitrogen_score": round(n_score, 1),
            "phosphorus_score": round(p_score, 1),
            "potassium_score": round(k_score, 1),
            "organic_matter_score": round(oc_score, 1),
            "ph_neutrality_score": round(ph_score, 1),
            "salinity_ec_score": round(ec_score, 1),
            "micronutrient_score": round(micro_score, 1)
        },
        "npk_analysis": npk_eval,
        "ph_correction_report": ph_remedy,
        "deficiencies": deficiency_list,
        "parameters": {
            "nitrogen": n,
            "phosphorus": p,
            "potassium": k,
            "ph": ph,
            "organic_carbon": oc,
            "ec": ec,
            "moisture": moist,
            "zinc": zn,
            "iron": fe,
            "boron": b,
            "sulphur": s
        }
    }
