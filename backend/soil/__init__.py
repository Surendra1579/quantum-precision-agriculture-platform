"""
Soil Intelligence Module for Precision Agriculture.
Provides Soil Health Indexing (0-100), NPK balance analysis, SoilGrids integration,
deficiency diagnosis, and scientific fertilizer dosage recommendations.
"""

from soil.soil_prediction import (
    evaluate_soil_health,
    calculate_npk_adequacy,
    diagnose_soil_deficiencies,
    calculate_ph_corrections,
)
from soil.soil_service import soil_service, fetch_regional_soil_profile, recommend_fertilizer_dosage
from soil.soil_api import router as soil_router

__all__ = [
    "evaluate_soil_health",
    "calculate_npk_adequacy",
    "diagnose_soil_deficiencies",
    "calculate_ph_corrections",
    "soil_service",
    "fetch_regional_soil_profile",
    "recommend_fertilizer_dosage",
    "soil_router",
]
