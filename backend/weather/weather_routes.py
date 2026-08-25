"""
FastAPI Routes for Weather Intelligence Module.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from database.connection import get_db
from database.repository import log_weather_history
from weather.weather_service import weather_service, calculate_fao56_et0

router = APIRouter(prefix="/weather", tags=["Weather Intelligence"])


@router.get("")
@router.get("/")
def get_weather_overview(
    state: Optional[str] = Query(None),
    district: Optional[str] = Query(None),
    latitude: Optional[float] = Query(None),
    longitude: Optional[float] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Primary Weather Intelligence Endpoint.
    Returns live meteorology, 7-day forecast, FAO-56 Penman-Monteith ET0, and risk alerts.
    """
    try:
        data = weather_service.get_weather_intelligence(
            state=state, district=district, latitude=latitude, longitude=longitude
        )

        # Log daily weather observation in database
        if db:
            cw = data["current_weather"]
            log_weather_history(
                db=db,
                date_str=datetime.utcnow().strftime("%Y-%m-%d"),
                temp_max=cw["temp_max_c"],
                temp_min=cw["temp_min_c"],
                temp_avg=cw["temperature_c"],
                humidity=cw["relative_humidity_percent"],
                rainfall_mm=cw["precipitation_mm"],
                wind_speed=cw["wind_speed_kmh"],
                solar_radiation=cw["solar_radiation_mj_m2"],
                et0=cw["evapotranspiration_et0_mm"],
                district=district or state or "India",
                weather_condition=cw["weather_condition"]
            )

        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Weather intelligence query failed: {str(e)}")


@router.get("/current")
def get_current_weather_alias(
    state: Optional[str] = Query(None),
    district: Optional[str] = Query(None),
    latitude: Optional[float] = Query(None),
    longitude: Optional[float] = Query(None)
):
    """Returns real-time weather observations."""
    full = weather_service.get_weather_intelligence(
        state=state, district=district, latitude=latitude, longitude=longitude
    )
    return {
        "success": True,
        "location": full["location"],
        "current_weather": full["current_weather"]
    }


@router.get("/forecast")
def get_weather_forecast(
    state: Optional[str] = Query(None),
    district: Optional[str] = Query(None),
    latitude: Optional[float] = Query(None),
    longitude: Optional[float] = Query(None)
):
    """Returns 7-day daily and 24-hour hourly agro-meteorological forecast."""
    full = weather_service.get_weather_intelligence(
        state=state, district=district, latitude=latitude, longitude=longitude
    )
    return {
        "success": True,
        "location": full["location"],
        "forecast_7_day": full["forecast_7_day"],
        "hourly_24h": full["hourly_24h"]
    }


@router.get("/et0")
def calculate_et0_endpoint(
    temp_c: float = Query(28.0),
    temp_min_c: float = Query(22.0),
    temp_max_c: float = Query(34.0),
    humidity_percent: float = Query(65.0),
    wind_speed_kmh: float = Query(12.0),
    solar_radiation_mj_m2: float = Query(18.5)
):
    """Calculates Reference Crop Evapotranspiration (ET0 in mm/day) via FAO-56 Penman-Monteith equation."""
    et0 = calculate_fao56_et0(
        temp_c=temp_c,
        temp_min_c=temp_min_c,
        temp_max_c=temp_max_c,
        humidity_percent=humidity_percent,
        wind_speed_kmh=wind_speed_kmh,
        solar_radiation_mj_m2=solar_radiation_mj_m2
    )
    return {
        "success": True,
        "evapotranspiration_et0_mm_per_day": et0,
        "standard": "FAO-56 Penman-Monteith",
        "irrigation_relevance": f"A standard crop will transpire approximately {et0} mm of water per day."
    }


@router.get("/alerts")
def get_weather_alerts(
    state: Optional[str] = Query(None),
    district: Optional[str] = Query(None),
    latitude: Optional[float] = Query(None),
    longitude: Optional[float] = Query(None)
):
    """Returns active agricultural hazard warnings (Heatwave, Frost, Flood, Blast Risk, Lodging)."""
    full = weather_service.get_weather_intelligence(
        state=state, district=district, latitude=latitude, longitude=longitude
    )
    return {
        "success": True,
        "location": full["location"],
        "alerts": full["alerts"]
    }
