"""
SQLAlchemy ORM Models for Precision Agriculture Decision Support Platform.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from database.connection import Base


class Farm(Base):
    __tablename__ = "farms"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(120), nullable=False)
    owner_name = Column(String(120), nullable=False)
    state = Column(String(80), nullable=False, index=True)
    district = Column(String(80), nullable=False, index=True)
    village = Column(String(100), nullable=True)
    total_area = Column(Float, default=0.0)  # Total acres
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    fields = relationship("Field", back_populates="farm", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "owner_name": self.owner_name,
            "state": self.state,
            "district": self.district,
            "village": self.village,
            "total_area": self.total_area,
            "fields_count": len(self.fields) if self.fields else 0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Field(Base):
    __tablename__ = "fields"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    farm_id = Column(Integer, ForeignKey("farms.id"), nullable=True, index=True)
    name = Column(String(120), nullable=False)
    crop_type = Column(String(80), nullable=True)
    area_acres = Column(Float, default=1.0)
    soil_type = Column(String(80), nullable=True)
    boundary_geojson = Column(Text, nullable=True)  # GeoJSON polygon/multipolygon string
    center_lat = Column(Float, nullable=False, index=True)
    center_lon = Column(Float, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    farm = relationship("Farm", back_populates="fields")
    satellite_records = relationship("SatelliteData", back_populates="field", cascade="all, delete-orphan")
    weather_records = relationship("WeatherHistory", back_populates="field", cascade="all, delete-orphan")
    soil_records = relationship("SoilData", back_populates="field", cascade="all, delete-orphan")
    recommendations = relationship("Recommendations", back_populates="field", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "farm_id": self.farm_id,
            "farm_name": self.farm.name if self.farm else None,
            "name": self.name,
            "crop_type": self.crop_type,
            "area_acres": self.area_acres,
            "soil_type": self.soil_type,
            "boundary_geojson": self.boundary_geojson,
            "center_lat": self.center_lat,
            "center_lon": self.center_lon,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class SatelliteData(Base):
    __tablename__ = "satellite_data"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    field_id = Column(Integer, ForeignKey("fields.id"), nullable=True, index=True)
    district = Column(String(80), nullable=True, index=True)
    date = Column(String(30), nullable=False, index=True)
    ndvi = Column(Float, nullable=False)
    evi = Column(Float, nullable=False)
    ndwi = Column(Float, nullable=True, default=0.0)
    lst_c = Column(Float, nullable=False)
    vhi = Column(Float, nullable=True, default=50.0)  # Vegetation Health Index (0-100)
    cloud_cover = Column(Float, default=0.0)
    raw_data_json = Column(Text, nullable=True)
    source = Column(String(100), default="Sentinel-2 / Open-Meteo Agro")
    created_at = Column(DateTime, default=datetime.utcnow)

    field = relationship("Field", back_populates="satellite_records")

    def to_dict(self):
        return {
            "id": self.id,
            "field_id": self.field_id,
            "district": self.district,
            "date": self.date,
            "ndvi": self.ndvi,
            "evi": self.evi,
            "ndwi": self.ndwi,
            "lst_c": self.lst_c,
            "vhi": self.vhi,
            "cloud_cover": self.cloud_cover,
            "source": self.source,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class WeatherHistory(Base):
    __tablename__ = "weather_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    field_id = Column(Integer, ForeignKey("fields.id"), nullable=True, index=True)
    district = Column(String(80), nullable=True, index=True)
    date = Column(String(30), nullable=False, index=True)
    temp_max = Column(Float, nullable=False)
    temp_min = Column(Float, nullable=False)
    temp_avg = Column(Float, nullable=False)
    humidity = Column(Float, nullable=False)
    rainfall_mm = Column(Float, default=0.0)
    wind_speed = Column(Float, default=0.0)
    solar_radiation = Column(Float, default=0.0)
    et0 = Column(Float, default=0.0)  # Reference Evapotranspiration
    weather_condition = Column(String(80), default="Clear")
    created_at = Column(DateTime, default=datetime.utcnow)

    field = relationship("Field", back_populates="weather_records")

    def to_dict(self):
        return {
            "id": self.id,
            "field_id": self.field_id,
            "district": self.district,
            "date": self.date,
            "temp_max": self.temp_max,
            "temp_min": self.temp_min,
            "temp_avg": self.temp_avg,
            "humidity": self.humidity,
            "rainfall_mm": self.rainfall_mm,
            "wind_speed": self.wind_speed,
            "solar_radiation": self.solar_radiation,
            "et0": self.et0,
            "weather_condition": self.weather_condition,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class SoilData(Base):
    __tablename__ = "soil_data"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    field_id = Column(Integer, ForeignKey("fields.id"), nullable=True, index=True)
    district = Column(String(80), nullable=True, index=True)
    test_date = Column(String(30), nullable=False)
    nitrogen = Column(Float, nullable=False)      # kg/ha
    phosphorus = Column(Float, nullable=False)    # kg/ha
    potassium = Column(Float, nullable=False)     # kg/ha
    ph = Column(Float, nullable=False)
    organic_carbon = Column(Float, nullable=False)  # %
    ec = Column(Float, default=0.5)               # dS/m
    zinc = Column(Float, default=0.8)             # ppm
    iron = Column(Float, default=4.5)             # ppm
    manganese = Column(Float, default=3.0)        # ppm
    copper = Column(Float, default=0.4)           # ppm
    boron = Column(Float, default=0.5)            # ppm
    sulphur = Column(Float, default=10.0)         # ppm
    moisture = Column(Float, default=0.25)        # m3/m3
    health_score = Column(Float, default=70.0)    # 0 - 100
    source = Column(String(100), default="SoilGrids / Lab Report")
    created_at = Column(DateTime, default=datetime.utcnow)

    field = relationship("Field", back_populates="soil_records")

    def to_dict(self):
        return {
            "id": self.id,
            "field_id": self.field_id,
            "district": self.district,
            "test_date": self.test_date,
            "nitrogen": self.nitrogen,
            "phosphorus": self.phosphorus,
            "potassium": self.potassium,
            "ph": self.ph,
            "organic_carbon": self.organic_carbon,
            "ec": self.ec,
            "zinc": self.zinc,
            "iron": self.iron,
            "manganese": self.manganese,
            "copper": self.copper,
            "boron": self.boron,
            "sulphur": self.sulphur,
            "moisture": self.moisture,
            "health_score": self.health_score,
            "source": self.source,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Recommendations(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    field_id = Column(Integer, ForeignKey("fields.id"), nullable=True, index=True)
    date = Column(String(30), nullable=False)
    recommended_crop = Column(String(80), nullable=False)
    variety = Column(String(80), nullable=False)
    expected_yield = Column(Float, nullable=False)      # Tons/Acre
    expected_price = Column(Float, nullable=False)      # Rs./Quintal
    expected_profit = Column(Float, nullable=False)     # Rs./Acre
    fertilizer_plan_json = Column(Text, nullable=False)
    irrigation_plan_json = Column(Text, nullable=False)
    risk_level = Column(String(30), default="Low")      # Low, Moderate, High, Severe
    confidence_score = Column(Float, default=85.0)     # %
    full_report_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    field = relationship("Field", back_populates="recommendations")

    def to_dict(self):
        return {
            "id": self.id,
            "field_id": self.field_id,
            "date": self.date,
            "recommended_crop": self.recommended_crop,
            "variety": self.variety,
            "expected_yield": self.expected_yield,
            "expected_price": self.expected_price,
            "expected_profit": self.expected_profit,
            "fertilizer_plan_json": self.fertilizer_plan_json,
            "irrigation_plan_json": self.irrigation_plan_json,
            "risk_level": self.risk_level,
            "confidence_score": self.confidence_score,
            "full_report_json": self.full_report_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class PredictionHistory(Base):
    __tablename__ = "prediction_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    prediction_type = Column(String(50), nullable=False, index=True)  # 'crop_yield', 'commodity_price', 'recommendation'
    input_params_json = Column(Text, nullable=False)
    output_results_json = Column(Text, nullable=False)
    quantum_confidence = Column(Float, default=80.0)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "prediction_type": self.prediction_type,
            "input_params_json": self.input_params_json,
            "output_results_json": self.output_results_json,
            "quantum_confidence": self.quantum_confidence,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
