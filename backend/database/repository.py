"""
Database Repository: CRUD functions for Farms, Fields, Telemetry, and Predictions.
"""

import json
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from database.models import (
    Farm,
    Field,
    SatelliteData,
    WeatherHistory,
    SoilData,
    Recommendations,
    PredictionHistory,
)


# =========================================================
# FARM CRUD
# =========================================================

def create_farm(db: Session, name: str, owner_name: str, state: str, district: str, village: Optional[str] = None, total_area: float = 0.0) -> Farm:
    farm = Farm(
        name=name,
        owner_name=owner_name,
        state=state,
        district=district,
        village=village,
        total_area=total_area,
    )
    db.add(farm)
    db.commit()
    db.refresh(farm)
    return farm


def get_all_farms(db: Session) -> List[Farm]:
    return db.query(Farm).order_by(Farm.created_at.desc()).all()


def get_farm_by_id(db: Session, farm_id: int) -> Optional[Farm]:
    return db.query(Farm).filter(Farm.id == farm_id).first()


def delete_farm(db: Session, farm_id: int) -> bool:
    farm = get_farm_by_id(db, farm_id)
    if farm:
        db.delete(farm)
        db.commit()
        return True
    return False


# =========================================================
# FIELD / PLOT CRUD
# =========================================================

def create_field(
    db: Session,
    name: str,
    center_lat: float,
    center_lon: float,
    farm_id: Optional[int] = None,
    crop_type: Optional[str] = None,
    area_acres: float = 1.0,
    soil_type: Optional[str] = None,
    boundary_geojson: Optional[str] = None,
) -> Field:
    field = Field(
        farm_id=farm_id,
        name=name,
        crop_type=crop_type,
        area_acres=area_acres,
        soil_type=soil_type,
        boundary_geojson=boundary_geojson,
        center_lat=center_lat,
        center_lon=center_lon,
    )
    db.add(field)
    db.commit()
    db.refresh(field)
    return field


def get_all_fields(db: Session) -> List[Field]:
    return db.query(Field).order_by(Field.created_at.desc()).all()


def get_field_by_id(db: Session, field_id: int) -> Optional[Field]:
    return db.query(Field).filter(Field.id == field_id).first()


def delete_field(db: Session, field_id: int) -> bool:
    field = get_field_by_id(db, field_id)
    if field:
        db.delete(field)
        db.commit()
        return True
    return False


# =========================================================
# SATELLITE DATA LOGGING
# =========================================================

def log_satellite_data(
    db: Session,
    date_str: str,
    ndvi: float,
    evi: float,
    lst_c: float,
    field_id: Optional[int] = None,
    district: Optional[str] = None,
    ndwi: float = 0.0,
    vhi: float = 50.0,
    cloud_cover: float = 0.0,
    raw_data: Optional[Dict[str, Any]] = None,
    source: str = "Sentinel-2 / Open-Meteo Agro",
) -> SatelliteData:
    record = SatelliteData(
        field_id=field_id,
        district=district,
        date=date_str,
        ndvi=ndvi,
        evi=evi,
        ndwi=ndwi,
        lst_c=lst_c,
        vhi=vhi,
        cloud_cover=cloud_cover,
        raw_data_json=json.dumps(raw_data, default=str) if raw_data else None,
        source=source,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_satellite_history(db: Session, field_id: Optional[int] = None, district: Optional[str] = None, limit: int = 30) -> List[SatelliteData]:
    query = db.query(SatelliteData)
    if field_id:
        query = query.filter(SatelliteData.field_id == field_id)
    elif district:
        query = query.filter(SatelliteData.district.ilike(f"%{district}%"))
    return query.order_by(SatelliteData.created_at.desc()).limit(limit).all()


# =========================================================
# WEATHER HISTORY LOGGING
# =========================================================

def log_weather_history(
    db: Session,
    date_str: str,
    temp_max: float,
    temp_min: float,
    temp_avg: float,
    humidity: float,
    rainfall_mm: float = 0.0,
    wind_speed: float = 0.0,
    solar_radiation: float = 0.0,
    et0: float = 0.0,
    field_id: Optional[int] = None,
    district: Optional[str] = None,
    weather_condition: str = "Clear",
) -> WeatherHistory:
    record = WeatherHistory(
        field_id=field_id,
        district=district,
        date=date_str,
        temp_max=temp_max,
        temp_min=temp_min,
        temp_avg=temp_avg,
        humidity=humidity,
        rainfall_mm=rainfall_mm,
        wind_speed=wind_speed,
        solar_radiation=solar_radiation,
        et0=et0,
        weather_condition=weather_condition,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_weather_history(db: Session, field_id: Optional[int] = None, district: Optional[str] = None, limit: int = 30) -> List[WeatherHistory]:
    query = db.query(WeatherHistory)
    if field_id:
        query = query.filter(WeatherHistory.field_id == field_id)
    elif district:
        query = query.filter(WeatherHistory.district.ilike(f"%{district}%"))
    return query.order_by(WeatherHistory.created_at.desc()).limit(limit).all()


# =========================================================
# SOIL DATA LOGGING
# =========================================================

def log_soil_data(
    db: Session,
    test_date: str,
    nitrogen: float,
    phosphorus: float,
    potassium: float,
    ph: float,
    organic_carbon: float,
    field_id: Optional[int] = None,
    district: Optional[str] = None,
    ec: float = 0.5,
    zinc: float = 0.8,
    iron: float = 4.5,
    manganese: float = 3.0,
    copper: float = 0.4,
    boron: float = 0.5,
    sulphur: float = 10.0,
    moisture: float = 0.25,
    health_score: float = 70.0,
    source: str = "SoilGrids / Lab Report",
) -> SoilData:
    record = SoilData(
        field_id=field_id,
        district=district,
        test_date=test_date,
        nitrogen=nitrogen,
        phosphorus=phosphorus,
        potassium=potassium,
        ph=ph,
        organic_carbon=organic_carbon,
        ec=ec,
        zinc=zinc,
        iron=iron,
        manganese=manganese,
        copper=copper,
        boron=boron,
        sulphur=sulphur,
        moisture=moisture,
        health_score=health_score,
        source=source,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_latest_soil_data(db: Session, field_id: Optional[int] = None, district: Optional[str] = None) -> Optional[SoilData]:
    query = db.query(SoilData)
    if field_id:
        query = query.filter(SoilData.field_id == field_id)
    elif district:
        query = query.filter(SoilData.district.ilike(f"%{district}%"))
    return query.order_by(SoilData.created_at.desc()).first()


# =========================================================
# RECOMMENDATIONS LOGGING
# =========================================================

def log_recommendation(
    db: Session,
    date_str: str,
    recommended_crop: str,
    variety: str,
    expected_yield: float,
    expected_price: float,
    expected_profit: float,
    fertilizer_plan: Dict[str, Any],
    irrigation_plan: Dict[str, Any],
    full_report: Dict[str, Any],
    field_id: Optional[int] = None,
    risk_level: str = "Low",
    confidence_score: float = 85.0,
) -> Recommendations:
    record = Recommendations(
        field_id=field_id,
        date=date_str,
        recommended_crop=recommended_crop,
        variety=variety,
        expected_yield=expected_yield,
        expected_price=expected_price,
        expected_profit=expected_profit,
        fertilizer_plan_json=json.dumps(fertilizer_plan, default=str),
        irrigation_plan_json=json.dumps(irrigation_plan, default=str),
        risk_level=risk_level,
        confidence_score=confidence_score,
        full_report_json=json.dumps(full_report, default=str),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_recommendations_history(db: Session, field_id: Optional[int] = None, limit: int = 20) -> List[Recommendations]:
    query = db.query(Recommendations)
    if field_id:
        query = query.filter(Recommendations.field_id == field_id)
    return query.order_by(Recommendations.created_at.desc()).limit(limit).all()


# =========================================================
# PREDICTION HISTORY LOGGING
# =========================================================

def log_prediction(
    db: Session,
    prediction_type: str,
    input_params: Dict[str, Any],
    output_results: Dict[str, Any],
    quantum_confidence: float = 80.0,
) -> PredictionHistory:
    record = PredictionHistory(
        prediction_type=prediction_type,
        input_params_json=json.dumps(input_params, default=str),
        output_results_json=json.dumps(output_results, default=str),
        quantum_confidence=quantum_confidence,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_recent_predictions(db: Session, limit: int = 15) -> List[PredictionHistory]:
    return db.query(PredictionHistory).order_by(PredictionHistory.timestamp.desc()).limit(limit).all()
