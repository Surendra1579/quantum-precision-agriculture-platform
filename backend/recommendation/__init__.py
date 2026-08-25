"""
Precision Agriculture Recommendation Engine.
Fuses Hybrid Quantum ML (Yield HQNN + Price VQR), Satellite Intelligence, Soil Health, and Weather Data.
"""

from recommendation.fertilizer import generate_fertilizer_prescription
from recommendation.irrigation import calculate_crop_irrigation_schedule
from recommendation.crop_advisor import rank_crop_suitability, get_variety_and_window_advisory, evaluate_disease_risks
from recommendation.recommendation_engine import recommendation_engine, generate_precision_recommendation
from recommendation.recommendation_api import router as recommendation_router

__all__ = [
    "generate_fertilizer_prescription",
    "calculate_crop_irrigation_schedule",
    "rank_crop_suitability",
    "get_variety_and_window_advisory",
    "evaluate_disease_risks",
    "recommendation_engine",
    "generate_precision_recommendation",
    "recommendation_router",
]
