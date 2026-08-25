"""
Weather Intelligence Module for Precision Agriculture.
Provides real-time observations, 7-day agro-forecasts, FAO-56 Penman-Monteith ET0,
solar radiation metrics, and agro-climatic hazard alerts.
"""

from weather.weather_service import weather_service, calculate_fao56_et0, evaluate_weather_alerts
from weather.weather_routes import router as weather_router

__all__ = [
    "weather_service",
    "calculate_fao56_et0",
    "evaluate_weather_alerts",
    "weather_router",
]
