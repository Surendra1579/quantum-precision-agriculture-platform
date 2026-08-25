"""
NDVI (Normalized Difference Vegetation Index) Module.
Formula: NDVI = (NIR - Red) / (NIR + Red)
"""

import numpy as np
from typing import Dict, Any, List, Tuple


def calculate_ndvi(nir: float, red: float) -> float:
    """
    Computes standard NDVI from Near-Infrared (NIR) and Red spectral bands.
    Valid range: [-1.0, 1.0].
    """
    denominator = nir + red
    if abs(denominator) < 1e-6:
        return 0.0
    ndvi = (nir - red) / denominator
    return round(float(np.clip(ndvi, -1.0, 1.0)), 4)


def classify_ndvi(ndvi: float) -> Dict[str, Any]:
    """
    Classifies vegetation density and health status based on NDVI value.
    """
    if ndvi < 0.1:
        return {
            "status": "Barren / Water Body",
            "health": "Inactive",
            "color": "#94a3b8",
            "vigor_percent": 0.0,
            "description": "Bare soil, sand, rock, or standing water body."
        }
    elif ndvi < 0.25:
        return {
            "status": "Sparse / Emergence",
            "health": "Low",
            "color": "#f87171",
            "vigor_percent": round((ndvi / 0.9) * 100, 1),
            "description": "Very low vegetation cover, seed germination, or high stress."
        }
    elif ndvi < 0.45:
        return {
            "status": "Moderate Vegetation",
            "health": "Fair",
            "color": "#fbbf24",
            "vigor_percent": round((ndvi / 0.9) * 100, 1),
            "description": "Developing crop canopy with moderate photosynthetic activity."
        }
    elif ndvi < 0.70:
        return {
            "status": "Dense Crop Canopy",
            "health": "Good",
            "color": "#34d399",
            "vigor_percent": round((ndvi / 0.9) * 100, 1),
            "description": "Healthy vegetative growth with high chlorophyll content."
        }
    else:
        return {
            "status": "Very High Vigor",
            "health": "Optimal",
            "color": "#10b981",
            "vigor_percent": min(100.0, round((ndvi / 0.9) * 100, 1)),
            "description": "Peak canopy density and maximum photosynthetic vigor."
        }


def generate_ndvi_spatial_grid(
    center_lat: float,
    center_lon: float,
    mean_ndvi: float,
    grid_size: int = 5,
    variation: float = 0.06
) -> List[Dict[str, Any]]:
    """
    Generates a localized spatial 2D grid matrix of NDVI values around a plot center.
    Useful for raster rendering and field heatmaps.
    """
    grid_cells = []
    step_deg = 0.0008  # ~80-100 meters per cell
    half = grid_size // 2

    # Deterministic pseudo-random seed based on coordinate hash for stability
    seed_val = int(abs(center_lat * 10000 + center_lon * 1000)) % (2**31)
    rng = np.random.default_rng(seed_val)

    for i in range(-half, half + 1):
        for j in range(-half, half + 1):
            dist_factor = np.exp(-0.2 * (i**2 + j**2))
            noise = rng.uniform(-variation, variation)
            cell_ndvi = round(float(np.clip(mean_ndvi + noise * dist_factor, 0.1, 0.95)), 3)
            cell_class = classify_ndvi(cell_ndvi)

            lat_min = center_lat + (i * step_deg) - (step_deg / 2)
            lat_max = center_lat + (i * step_deg) + (step_deg / 2)
            lon_min = center_lon + (j * step_deg) - (step_deg / 2)
            lon_max = center_lon + (j * step_deg) + (step_deg / 2)

            grid_cells.append({
                "row": i + half,
                "col": j + half,
                "lat": round(center_lat + (i * step_deg), 5),
                "lon": round(center_lon + (j * step_deg), 5),
                "bounds": [[round(lat_min, 5), round(lon_min, 5)], [round(lat_max, 5), round(lon_max, 5)]],
                "ndvi": cell_ndvi,
                "status": cell_class["status"],
                "color": cell_class["color"]
            })

    return grid_cells
