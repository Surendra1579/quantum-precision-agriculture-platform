"""
FastAPI Routes for Per-Plot Precision Farming Module.
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException, Body
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.connection import get_db
from database.repository import create_field, get_all_fields, get_field_by_id, delete_field, create_farm, get_all_farms
from database.models import Field as DBField
from plot.plot_service import plot_service, calculate_polygon_area_acres, calculate_polygon_centroid

router = APIRouter(prefix="/plots", tags=["Per-Plot Precision Farming"])


class PlotCreateInput(BaseModel):
    name: str = Field(default="North Field Plot A", description="Plot / Field Name")
    farm_id: Optional[int] = Field(default=None, description="Parent Farm ID")
    crop_type: str = Field(default="Rice", description="Cultivated Crop")
    area_acres: Optional[float] = Field(default=None, description="Plot Area in Acres")
    soil_type: str = Field(default="Loam", description="Soil Texture Type")
    center_lat: Optional[float] = Field(default=None, description="Center Latitude")
    center_lon: Optional[float] = Field(default=None, description="Center Longitude")
    boundary_geojson: Optional[str] = Field(default=None, description="GeoJSON Polygon String")


class PlotAnalysisRequest(BaseModel):
    plot_name: str = Field(default="My Precision Farm Plot", description="Plot Identifier")
    crop: str = Field(default="Rice", description="Target Crop")
    state: str = Field(default="Andhra Pradesh", description="State")
    district: str = Field(default="Guntur", description="District")
    area_acres: Optional[float] = Field(default=5.0, description="Plot Area in Acres")
    season: str = Field(default="Kharif", description="Season")
    crop_year: int = Field(default=2024, description="Crop Year")
    boundary_geojson: Optional[str] = Field(default=None, description="GeoJSON Boundary Coordinates")
    center_lat: Optional[float] = Field(default=None, description="Latitude")
    center_lon: Optional[float] = Field(default=None, description="Longitude")
    soil_type: str = Field(default="Loam", description="Soil Type")


# Standalone Route: POST /plot-analysis (Also supported directly on router)
@router.post("/analyze")
def analyze_plot_endpoint(data: PlotAnalysisRequest):
    """Executes per-plot precision quantum inference and agro-climatic prescriptions."""
    try:
        return plot_service.analyze_plot(
            plot_name=data.plot_name,
            crop=data.crop,
            state=data.state,
            district=data.district,
            area_acres=data.area_acres,
            season=data.season,
            crop_year=data.crop_year,
            boundary_geojson=data.boundary_geojson,
            center_lat=data.center_lat,
            center_lon=data.center_lon,
            soil_type=data.soil_type
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Plot analysis failed: {str(e)}")


@router.get("")
@router.get("/")
def list_plots(db: Session = Depends(get_db)):
    """Lists all registered farm plots with boundary geometries."""
    fields = get_all_fields(db)
    return {
        "success": True,
        "count": len(fields),
        "plots": [f.to_dict() for f in fields]
    }


@router.post("")
@router.post("/")
def create_new_plot(data: PlotCreateInput, db: Session = Depends(get_db)):
    """Registers a new farm plot with GPS center or polygon boundary GeoJSON."""
    lat = data.center_lat or 16.3067
    lon = data.center_lon or 80.4365
    acres = data.area_acres or 2.5

    field = create_field(
        db=db,
        name=data.name,
        center_lat=lat,
        center_lon=lon,
        farm_id=data.farm_id,
        crop_type=data.crop_type,
        area_acres=acres,
        soil_type=data.soil_type,
        boundary_geojson=data.boundary_geojson
    )
    return {
        "success": True,
        "message": f"Plot '{field.name}' created successfully.",
        "plot": field.to_dict()
    }


@router.get("/{plot_id}")
def get_plot_details(plot_id: int, db: Session = Depends(get_db)):
    """Retrieves specific plot metadata and coordinates."""
    field = get_field_by_id(db, plot_id)
    if not field:
        raise HTTPException(status_code=404, detail="Plot not found")
    return {
        "success": True,
        "plot": field.to_dict()
    }


@router.post("/{plot_id}/analyze")
def analyze_saved_plot(
    plot_id: int,
    state: str = Query("Andhra Pradesh"),
    district: str = Query("Guntur"),
    season: str = Query("Kharif"),
    db: Session = Depends(get_db)
):
    """Runs precision quantum analysis on a previously registered plot."""
    field = get_field_by_id(db, plot_id)
    if not field:
        raise HTTPException(status_code=404, detail="Plot not found")

    return plot_service.analyze_plot(
        plot_name=field.name,
        crop=field.crop_type or "Rice",
        state=state,
        district=district,
        area_acres=field.area_acres,
        season=season,
        boundary_geojson=field.boundary_geojson,
        center_lat=field.center_lat,
        center_lon=field.center_lon,
        soil_type=field.soil_type or "Loam"
    )


@router.delete("/{plot_id}")
def delete_saved_plot(plot_id: int, db: Session = Depends(get_db)):
    """Deletes a saved plot."""
    success = delete_field(db, plot_id)
    if not success:
        raise HTTPException(status_code=404, detail="Plot not found")
    return {
        "success": True,
        "message": f"Plot ID {plot_id} deleted successfully."
    }
