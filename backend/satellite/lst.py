"""
Land Surface Temperature (LST) & Thermal Stress Module.
Derives surface skin temperature (°C) and thermal stress anomalies from Thermal Infrared (TIR) bands and NDVI.
"""

import numpy as np
from typing import Dict, Any, Tuple


def calculate_fvc(ndvi: float, ndvi_soil: float = 0.15, ndvi_veg: float = 0.85) -> float:
    """
    Computes Fractional Vegetation Cover (FVC) from NDVI.
    FVC = ((NDVI - NDVI_soil) / (NDVI_veg - NDVI_soil))^2
    """
    if ndvi <= ndvi_soil:
        return 0.0
    if ndvi >= ndvi_veg:
        return 1.0
    val = (ndvi - ndvi_soil) / (ndvi_veg - ndvi_soil)
    return round(float(val ** 2), 4)


def calculate_emissivity(fvc: float, eps_soil: float = 0.96, eps_veg: float = 0.985, d_eps: float = 0.005) -> float:
    """
    Computes surface emissivity based on Fractional Vegetation Cover.
    eps = eps_veg * FVC + eps_soil * (1 - FVC) + d_eps
    """
    emissivity = (eps_veg * fvc) + (eps_soil * (1.0 - fvc)) + d_eps
    return round(float(emissivity), 4)


def calculate_lst(brightness_temp_k: float, emissivity: float, wavelength_um: float = 10.8) -> float:
    """
    Computes Land Surface Temperature in Celsius using Split-Window / Single-Channel Model.
    LST = BT / (1 + (lambda * BT / rho) * ln(emissivity)) - 273.15
    rho = h * c / sigma = 14388 um*K
    """
    rho = 14388.0
    if emissivity <= 0:
        emissivity = 0.97

    denom = 1.0 + ((wavelength_um * brightness_temp_k / rho) * np.log(emissivity))
    lst_k = brightness_temp_k / denom
    lst_c = lst_k - 273.15
    return round(float(lst_c), 2)


def calculate_thermal_stress(lst_c: float, ambient_temp_c: float, crop_optimal_temp: float = 27.0) -> Dict[str, Any]:
    """
    Evaluates canopy thermal stress index based on canopy-to-air temperature differential (CWSI proxy).
    """
    temp_diff = lst_c - ambient_temp_c  # If canopy is warmer than air, transpiration is constrained (water stress)

    if lst_c > 38.0 or temp_diff > 4.0:
        stress_level = "Severe Heat Stress"
        color = "#ef4444"
        risk_score = 85.0
        recommendation = "Immediate irrigation required. Evaporative cooling needed to prevent enzyme degradation."
    elif lst_c > 32.0 or temp_diff > 1.5:
        stress_level = "Moderate Thermal Stress"
        color = "#f59e0b"
        risk_score = 55.0
        recommendation = "Soil moisture depletion detected. Schedule irrigation within 24-48 hours."
    elif lst_c < 12.0:
        stress_level = "Cold / Frost Stress"
        color = "#38bdf8"
        risk_score = 65.0
        recommendation = "Low temperature may inhibit nutrient uptake and retard vegetative development."
    else:
        stress_level = "Optimal Thermal Range"
        color = "#10b981"
        risk_score = 15.0
        recommendation = "Canopy temperature is ideal for active transpiration and photosynthesis."

    return {
        "land_surface_temperature_c": lst_c,
        "ambient_temperature_c": ambient_temp_c,
        "canopy_air_differential_c": round(temp_diff, 2),
        "thermal_stress_level": stress_level,
        "risk_score": risk_score,
        "indicator_color": color,
        "recommendation": recommendation
    }
