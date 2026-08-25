"""
Satellite Intelligence Module for Precision Agriculture.
Provides Sentinel-2, Landsat, and Earth Engine multi-spectral indices (NDVI, EVI, NDWI, VHI, LST).
"""

from satellite.ndvi import calculate_ndvi, classify_ndvi, generate_ndvi_spatial_grid
from satellite.evi import calculate_evi, classify_evi
from satellite.lst import calculate_lst, calculate_thermal_stress
from satellite.vegetation import calculate_ndwi, calculate_vhi, assess_crop_stress
from satellite.satellite_service import satellite_service, fetch_satellite_intelligence
from satellite.satellite_routes import router as satellite_router

__all__ = [
    "calculate_ndvi",
    "classify_ndvi",
    "generate_ndvi_spatial_grid",
    "calculate_evi",
    "classify_evi",
    "calculate_lst",
    "calculate_thermal_stress",
    "calculate_ndwi",
    "calculate_vhi",
    "assess_crop_stress",
    "satellite_service",
    "fetch_satellite_intelligence",
    "satellite_router",
]
