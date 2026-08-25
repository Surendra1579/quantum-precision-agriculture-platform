"""
Vegetation Health & Multi-Index Crop Stress Module.
Implements NDWI, VCI, TCI, VHI (Vegetation Health Index), and Composite Field Stress Assessment.
"""

import numpy as np
from typing import Dict, Any, Optional


def calculate_ndwi(nir: float, swir: float) -> float:
    """
    Computes Gao's Normalized Difference Water Index (Canopy Moisture Content).
    Formula: NDWI = (NIR - SWIR) / (NIR + SWIR)
    Range: -1.0 to 1.0. Positive values indicate high canopy water content.
    """
    denominator = nir + swir
    if abs(denominator) < 1e-6:
        return 0.0
    ndwi = (nir - swir) / denominator
    return round(float(np.clip(ndwi, -1.0, 1.0)), 4)


def calculate_vci(ndvi: float, ndvi_min: float = 0.15, ndvi_max: float = 0.85) -> float:
    """
    Computes Vegetation Condition Index (VCI) in percentage [0, 100].
    VCI = ((NDVI - NDVI_min) / (NDVI_max - NDVI_min)) * 100
    """
    if ndvi_max <= ndvi_min:
        return 50.0
    vci = ((ndvi - ndvi_min) / (ndvi_max - ndvi_min)) * 100.0
    return round(float(np.clip(vci, 0.0, 100.0)), 2)


def calculate_tci(lst_c: float, lst_min: float = 18.0, lst_max: float = 42.0) -> float:
    """
    Computes Temperature Condition Index (TCI) in percentage [0, 100].
    TCI = ((LST_max - LST) / (LST_max - LST_min)) * 100
    High temperature implies thermal stress -> lower TCI.
    """
    if lst_max <= lst_min:
        return 50.0
    tci = ((lst_max - lst_c) / (lst_max - lst_min)) * 100.0
    return round(float(np.clip(tci, 0.0, 100.0)), 2)


def calculate_vhi(ndvi: float, lst_c: float, weight_vci: float = 0.5) -> Dict[str, Any]:
    """
    Computes Vegetation Health Index (VHI) combining moisture/vigor condition (VCI) and thermal condition (TCI).
    Formula: VHI = alpha * VCI + (1 - alpha) * TCI
    Standard drought / crop health scale:
    - > 60: Optimal / Healthy
    - 40 - 60: Moderate / Mild Stress
    - 30 - 40: Moderate Drought / Stressed
    - 20 - 30: Severe Drought
    - < 20: Extreme Agricultural Drought
    """
    vci = calculate_vci(ndvi)
    tci = calculate_tci(lst_c)
    vhi = round(float((weight_vci * vci) + ((1.0 - weight_vci) * tci)), 2)

    if vhi >= 65.0:
        health_status = "Optimal"
        drought_category = "No Drought / High Vigor"
        color = "#10b981"
    elif vhi >= 45.0:
        health_status = "Moderate"
        drought_category = "Mild / Normal Vegetation"
        color = "#34d399"
    elif vhi >= 30.0:
        health_status = "Stressed"
        drought_category = "Moderate Agricultural Stress"
        color = "#fbbf24"
    elif vhi >= 20.0:
        health_status = "Severely Stressed"
        drought_category = "Severe Drought Hazard"
        color = "#f97316"
    else:
        health_status = "Extreme Stress"
        drought_category = "Extreme Crop Failure Risk"
        color = "#ef4444"

    return {
        "vhi": vhi,
        "vci": vci,
        "tci": tci,
        "health_status": health_status,
        "drought_category": drought_category,
        "indicator_color": color
    }


def assess_crop_stress(
    ndvi: float,
    evi: float,
    ndwi: float,
    lst_c: float,
    soil_moisture: float
) -> Dict[str, Any]:
    """
    Comprehensive multi-spectral crop stress assessment matrix.
    Combines photosynthetic activity (NDVI), biomass volume (EVI), canopy hydration (NDWI),
    soil moisture, and thermal stress (LST).
    """
    vhi_data = calculate_vhi(ndvi, lst_c)
    
    # Assess component stress factors
    water_stress = "Severe" if ndwi < -0.1 or soil_moisture < 0.15 else ("Moderate" if ndwi < 0.2 or soil_moisture < 0.25 else "Adequate")
    canopy_vigor = "High" if ndvi > 0.6 else ("Moderate" if ndvi > 0.35 else "Low")
    thermal_status = "Hot" if lst_c > 35.0 else ("Cool" if lst_c < 18.0 else "Optimal")

    # Overall Field Health Score (0 - 100)
    health_score = round(
        0.35 * (ndvi * 100) +
        0.25 * (vhi_data["vhi"]) +
        0.20 * max(0, min(100, (ndwi + 0.5) * 100)) +
        0.20 * max(0, min(100, (soil_moisture / 0.45) * 100)),
        1
    )
    health_score = float(np.clip(health_score, 0.0, 100.0))

    if health_score >= 75.0:
        overall_status = "Optimal"
        badge_color = "#10b981"
        summary = "Field demonstrates excellent vegetative vigor, optimal canopy moisture, and low thermal stress."
    elif health_score >= 55.0:
        overall_status = "Moderate"
        badge_color = "#34d399"
        summary = "Crop growth is on track. Monitor soil moisture and prepare next scheduled irrigation cycle."
    elif health_score >= 40.0:
        overall_status = "Stressed"
        badge_color = "#fbbf24"
        summary = "Canopy water deficit detected. Early signs of moisture stress or nitrogen deficiency."
    else:
        overall_status = "Severely Stressed"
        badge_color = "#ef4444"
        summary = "High crop stress alert. Immediate irrigation, micro-nutrient spray, and pest inspection advised."

    return {
        "field_health_score": health_score,
        "overall_status": overall_status,
        "badge_color": badge_color,
        "vhi_metrics": vhi_data,
        "water_stress": water_stress,
        "canopy_vigor": canopy_vigor,
        "thermal_status": thermal_status,
        "summary": summary
    }
