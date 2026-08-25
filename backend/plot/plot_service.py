"""
Per-Plot Precision Farming Service.
Handles GeoJSON boundary coordinates, geodesic area calculations,
and executes per-plot precision quantum inference and agronomic prescriptions.
"""

import math
import json
import logging
from typing import Dict, Any, List, Optional, Tuple

from recommendation.recommendation_engine import recommendation_engine
from satellite.satellite_service import satellite_service
from soil.soil_service import soil_service
from weather.weather_service import weather_service

logger = logging.getLogger("plot_service")


def calculate_polygon_centroid(coordinates: List[List[float]]) -> Tuple[float, float]:
    """
    Computes centroid (lat, lon) of a polygon vertex ring.
    Coordinates can be [[lat, lon], ...] or [[lon, lat], ...].
    """
    if not coordinates:
        return (20.5937, 78.9629)

    # Standardize coordinate format
    # In GeoJSON: [lon, lat]. In Leaflet: [lat, lon].
    pts = coordinates
    if len(pts) > 0 and isinstance(pts[0], list):
        if len(pts) == 1 and isinstance(pts[0][0], list):
            pts = pts[0]  # Unnest GeoJSON Polygon rings

    lats = []
    lons = []
    for pt in pts:
        if len(pt) >= 2:
            # Detect lat vs lon: Indian latitude ~8-37, longitude ~68-98
            val1, val2 = float(pt[0]), float(pt[1])
            if val1 > 50.0:  # Lon is first
                lons.append(val1)
                lats.append(val2)
            else:  # Lat is first
                lats.append(val1)
                lons.append(val2)

    if not lats or not lons:
        return (20.5937, 78.9629)

    return (round(sum(lats) / len(lats), 5), round(sum(lons) / len(lons), 5))


def calculate_polygon_area_acres(coordinates: List[List[float]]) -> float:
    """
    Computes surface area of a polygon in Acres using the Shoelace formula on a planar projection.
    1 deg latitude ~ 111,320 meters.
    1 deg longitude ~ 111,320 * cos(lat) meters.
    1 Acre = 4046.86 m^2.
    """
    if not coordinates or len(coordinates) < 3:
        return 1.0

    pts = coordinates
    if len(pts) == 1 and isinstance(pts[0], list) and isinstance(pts[0][0], list):
        pts = pts[0]

    if len(pts) < 3:
        return 1.0

    # Ensure closed polygon
    if pts[0] != pts[-1]:
        pts = list(pts) + [pts[0]]

    center_lat, _ = calculate_polygon_centroid(pts)
    lat_m_per_deg = 111320.0
    lon_m_per_deg = 111320.0 * math.cos(math.radians(center_lat))

    # Convert coordinates to local Cartesian (x, y) meters
    xy_points = []
    for pt in pts:
        v1, v2 = float(pt[0]), float(pt[1])
        if v1 > 50.0:  # Lon, Lat
            lon, lat = v1, v2
        else:
            lat, lon = v1, v2
        x = lon * lon_m_per_deg
        y = lat * lat_m_per_deg
        xy_points.append((x, y))

    # Shoelace Formula
    n = len(xy_points)
    area_sq_m = 0.0
    for i in range(n - 1):
        x1, y1 = xy_points[i]
        x2, y2 = xy_points[i + 1]
        area_sq_m += (x1 * y2) - (x2 * y1)

    area_sq_m = abs(area_sq_m) / 2.0
    acres = area_sq_m / 4046.86

    return round(float(max(0.1, acres)), 2)


class PlotService:
    """
    Per-Plot Precision Agriculture Service.
    Executes plot-specific spatial analytics, zonal telemetry clipping, and quantum recommendations.
    """

    def analyze_plot(
        self,
        plot_name: str,
        crop: str,
        state: str,
        district: str,
        area_acres: Optional[float] = None,
        season: str = "Kharif",
        crop_year: int = 2024,
        boundary_geojson: Optional[str] = None,
        center_lat: Optional[float] = None,
        center_lon: Optional[float] = None,
        soil_type: Optional[str] = "Loam"
    ) -> Dict[str, Any]:
        """
        Executes comprehensive per-plot precision analysis.
        """
        # Parse GeoJSON Boundary if supplied
        coords = []
        if boundary_geojson:
            try:
                geom = json.loads(boundary_geojson)
                if geom.get("type") == "Polygon":
                    coords = geom.get("coordinates", [[]])[0]
                elif geom.get("type") == "Feature":
                    coords = geom.get("geometry", {}).get("coordinates", [[]])[0]
            except Exception as e:
                logger.warning(f"Could not parse boundary GeoJSON: {e}")

        # Compute centroid and area if not explicitly given
        if coords and len(coords) >= 3:
            calc_lat, calc_lon = calculate_polygon_centroid(coords)
            center_lat = center_lat or calc_lat
            center_lon = center_lon or calc_lon
            area_acres = area_acres or calculate_polygon_area_acres(coords)
        else:
            center_lat = center_lat or 16.3067
            center_lon = center_lon or 80.4365
            area_acres = area_acres or 5.0

        # Execute Precision Recommendation for this specific plot
        rec_report = recommendation_engine.generate_recommendation(
            crop=crop,
            state=state,
            district=district,
            area_acres=area_acres,
            season=season,
            crop_year=crop_year,
            latitude=center_lat,
            longitude=center_lon
        )

        # Generate Plot Specific Micro-Zone Raster (High-Resolution 5x5 sub-plot grid)
        sat_data = satellite_service.fetch_satellite_data(
            state=state, district=district, latitude=center_lat, longitude=center_lon
        )

        return {
            "success": True,
            "plot_metadata": {
                "plot_name": plot_name,
                "crop": crop.title(),
                "area_acres": area_acres,
                "soil_type": soil_type,
                "center_coordinates": {"latitude": center_lat, "longitude": center_lon},
                "boundary_geojson": boundary_geojson,
                "has_polygon_boundary": len(coords) >= 3
            },
            "per_plot_telemetry": {
                "ndvi": sat_data["indices"]["ndvi"],
                "evi": sat_data["indices"]["evi"],
                "ndwi": sat_data["indices"]["ndwi"],
                "soil_moisture": sat_data["indices"]["soil_moisture"],
                "land_surface_temp_c": sat_data["indices"]["land_surface_temperature_c"],
                "vegetation_health_status": sat_data["classifications"]["overall_field_assessment"]["overall_status"]
            },
            "per_plot_quantum_predictions": rec_report["quantum_predictions"],
            "per_plot_economic_outlook": rec_report["economic_financial_outlook"],
            "per_plot_prescriptions": rec_report["prescriptions"],
            "spatial_micro_zones": sat_data["spatial_raster"]
        }


plot_service = PlotService()
