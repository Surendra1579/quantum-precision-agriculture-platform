"""
FastAPI Routes for Satellite Intelligence Module.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from database.connection import get_db
from database.repository import log_satellite_data
from satellite.satellite_service import satellite_service

router = APIRouter(prefix="/satellite", tags=["Satellite Intelligence"])


@router.get("")
@router.get("/")
def get_satellite_overview(
    state: Optional[str] = Query(None, description="Indian State Name"),
    district: Optional[str] = Query(None, description="District Name"),
    village: Optional[str] = Query(None, description="Village or Locality"),
    latitude: Optional[float] = Query(None, description="Plot Center Latitude"),
    longitude: Optional[float] = Query(None, description="Plot Center Longitude"),
    db: Session = Depends(get_db)
):
    """
    Primary Satellite Intelligence Endpoint.
    Fetches Sentinel-2 / Landsat indices (NDVI, EVI, NDWI, VHI, LST),
    spatial heatmaps, and vegetative stress classifications.
    """
    try:
        data = satellite_service.fetch_satellite_data(
            state=state,
            district=district,
            village=village,
            latitude=latitude,
            longitude=longitude
        )

        # Log satellite observation to database
        if db:
            log_satellite_data(
                db=db,
                date_str=data["satellite_metadata"]["acquisition_date"],
                ndvi=data["indices"]["ndvi"],
                evi=data["indices"]["evi"],
                ndwi=data["indices"]["ndwi"],
                lst_c=data["indices"]["land_surface_temperature_c"],
                vhi=data["indices"]["vhi"],
                cloud_cover=data["satellite_metadata"]["cloud_cover_percent"],
                district=district or state or "India",
                raw_data=data,
                source=data["satellite_metadata"]["source"]
            )

        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Satellite intelligence retrieval failed: {str(e)}")


@router.get("/indices")
def get_satellite_indices(
    state: Optional[str] = Query(None),
    district: Optional[str] = Query(None),
    latitude: Optional[float] = Query(None),
    longitude: Optional[float] = Query(None)
):
    """Returns calculated multi-spectral indices (NDVI, EVI, NDWI, VHI, LST)."""
    full_data = satellite_service.fetch_satellite_data(
        state=state, district=district, latitude=latitude, longitude=longitude
    )
    return {
        "success": True,
        "coordinates": full_data["coordinates"],
        "indices": full_data["indices"],
        "classifications": full_data["classifications"]
    }


@router.get("/timeseries")
def get_satellite_timeseries(
    state: Optional[str] = Query(None),
    district: Optional[str] = Query(None),
    latitude: Optional[float] = Query(None),
    longitude: Optional[float] = Query(None)
):
    """Returns 12-month historical vegetation and thermal trajectory."""
    full_data = satellite_service.fetch_satellite_data(
        state=state, district=district, latitude=latitude, longitude=longitude
    )
    return {
        "success": True,
        "coordinates": full_data["coordinates"],
        "historical_timeseries": full_data["historical_timeseries"]
    }


@router.get("/field-health")
def get_field_health(
    state: Optional[str] = Query(None),
    district: Optional[str] = Query(None),
    latitude: Optional[float] = Query(None),
    longitude: Optional[float] = Query(None)
):
    """Returns high-resolution field stress analysis and 2D spatial heatmap raster."""
    full_data = satellite_service.fetch_satellite_data(
        state=state, district=district, latitude=latitude, longitude=longitude
    )
    return {
        "success": True,
        "overall_field_assessment": full_data["classifications"]["overall_field_assessment"],
        "spatial_raster": full_data["spatial_raster"]
    }
