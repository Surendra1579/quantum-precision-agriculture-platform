"""
EVI (Enhanced Vegetation Index) Module.
Formula: EVI = 2.5 * (NIR - Red) / (NIR + 6 * Red - 7.5 * Blue + 1.0)
Corrects for atmospheric aerosol resistance and canopy background noise.
"""

import numpy as np
from typing import Dict, Any


def calculate_evi(nir: float, red: float, blue: float, G: float = 2.5, C1: float = 6.0, C2: float = 7.5, L: float = 1.0) -> float:
    """
    Computes EVI from Near-Infrared, Red, and Blue spectral bands.
    """
    denominator = nir + (C1 * red) - (C2 * blue) + L
    if abs(denominator) < 1e-6:
        return 0.0
    evi = G * (nir - red) / denominator
    return round(float(np.clip(evi, -1.0, 1.0)), 4)


def classify_evi(evi: float) -> Dict[str, Any]:
    """
    Classifies canopy structural complexity and biomass index.
    """
    if evi < 0.15:
        return {
            "status": "Low Biomass",
            "rating": "Sparse",
            "color": "#f87171",
            "biomass_index": round(evi * 100, 1)
        }
    elif evi < 0.35:
        return {
            "status": "Moderate Biomass",
            "rating": "Developing",
            "color": "#fbbf24",
            "biomass_index": round(evi * 100, 1)
        }
    elif evi < 0.60:
        return {
            "status": "High Biomass",
            "rating": "Dense",
            "color": "#34d399",
            "biomass_index": round(evi * 100, 1)
        }
    else:
        return {
            "status": "Very High Biomass",
            "rating": "Extremely Dense",
            "color": "#10b981",
            "biomass_index": min(100.0, round(evi * 100, 1))
        }
