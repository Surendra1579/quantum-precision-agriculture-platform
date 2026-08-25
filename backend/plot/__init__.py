"""
Per-Plot Precision Farming Module.
Provides Farm & Field boundary management, GeoJSON parsing, and plot-specific quantum decision support.
"""

from plot.plot_service import plot_service, calculate_polygon_area_acres, calculate_polygon_centroid
from plot.plot_routes import router as plot_router

__all__ = [
    "plot_service",
    "calculate_polygon_area_acres",
    "calculate_polygon_centroid",
    "plot_router",
]
