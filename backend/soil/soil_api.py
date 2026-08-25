"""
FastAPI Routes for Soil Intelligence Module.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException, Body
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.connection import get_db
from database.repository import log_soil_data
from soil.soil_service import soil_service
from soil.soil_prediction import evaluate_soil_health

router = APIRouter(prefix="/soil", tags=["Soil Intelligence"])


class SoilAnalysisInput(BaseModel):
    state: Optional[str] = "Andhra Pradesh"
    district: Optional[str] = "Guntur"
    nitrogen: float = Field(default=240.0, description="Nitrogen in kg/ha")
    phosphorus: float = Field(default=16.0, description="Phosphorus in kg/ha")
    potassium: float = Field(default=210.0, description="Potassium in kg/ha")
    ph: float = Field(default=7.2, description="Soil pH value (4.0 - 10.0)")
    organic_carbon: float = Field(default=0.55, description="Organic Carbon %")
    ec: float = Field(default=0.5, description="Electrical Conductivity in dS/m")
    moisture: float = Field(default=0.25, description="Soil Moisture in m³/m³")
    zinc: float = Field(default=0.75, description="Zinc in ppm")
    iron: float = Field(default=4.8, description="Iron in ppm")
    boron: float = Field(default=0.52, description="Boron in ppm")
    sulphur: float = Field(default=11.0, description="Sulphur in ppm")


class FertilizerRequestInput(BaseModel):
    crop: str = "Rice"
    area_acres: float = Field(default=5.0, description="Cultivated Land in Acres")
    nitrogen: Optional[float] = None
    phosphorus: Optional[float] = None
    potassium: Optional[float] = None
    ph: Optional[float] = None
    zinc: Optional[float] = None
    boron: Optional[float] = None


@router.get("")
@router.get("/")
def get_soil_overview(
    state: Optional[str] = Query(None),
    district: Optional[str] = Query(None),
    latitude: Optional[float] = Query(None),
    longitude: Optional[float] = Query(None)
):
    """Retrieves regional soil profile, Soil Health Score (0-100), and NPK status."""
    try:
        return soil_service.get_soil_profile(
            state=state, district=district, latitude=latitude, longitude=longitude
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Soil profile retrieval failed: {str(e)}")


@router.get("/profile")
def get_soil_profile_alias(
    state: Optional[str] = Query(None),
    district: Optional[str] = Query(None),
    latitude: Optional[float] = Query(None),
    longitude: Optional[float] = Query(None)
):
    """Alias for /soil profile."""
    return soil_service.get_soil_profile(
        state=state, district=district, latitude=latitude, longitude=longitude
    )


@router.post("/analyze")
def analyze_soil_test(
    data: SoilAnalysisInput,
    db: Session = Depends(get_db)
):
    """
    Evaluates manual or laboratory soil test parameters.
    Returns Soil Health Index (0-100), NPK balance rating, pH amendments, and deficiency diagnosis.
    """
    params = data.dict()
    eval_result = evaluate_soil_health(params)

    if db:
        log_soil_data(
            db=db,
            district=data.district or data.state or "India",
            test_date=datetime.utcnow().strftime("%Y-%m-%d"),
            nitrogen=data.nitrogen,
            phosphorus=data.phosphorus,
            potassium=data.potassium,
            ph=data.ph,
            organic_carbon=data.organic_carbon,
            ec=data.ec,
            zinc=data.zinc,
            iron=data.iron,
            boron=data.boron,
            sulphur=data.sulphur,
            moisture=data.moisture,
            health_score=eval_result["soil_health_score"],
            source="Manual User Test / Lab Card"
        )

    return {
        "success": True,
        "location": {"state": data.state, "district": data.district},
        "evaluation": eval_result
    }


@router.post("/recommend-fertilizer")
def get_fertilizer_prescription(data: FertilizerRequestInput):
    """
    Generates target-yield commercial fertilizer recommendations (Urea, DAP, MOP, SSP, Micronutrients)
    and 3-stage split application calendar based on 4R Nutrient Stewardship.
    """
    soil_dict = {
        "nitrogen": data.nitrogen if data.nitrogen is not None else 225.0,
        "phosphorus": data.phosphorus if data.phosphorus is not None else 16.5,
        "potassium": data.potassium if data.potassium is not None else 220.0,
        "zinc": data.zinc if data.zinc is not None else 0.75,
        "boron": data.boron if data.boron is not None else 0.52,
    }
    return soil_service.recommend_fertilizer(
        crop=data.crop,
        area_acres=data.area_acres,
        soil_params=soil_dict
    )


@router.post("/upload-card")
def upload_soil_health_card(
    report_data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """
    Parses digital Soil Health Card JSON payload and runs comprehensive diagnostic analysis.
    """
    extracted_params = {
        "nitrogen": float(report_data.get("nitrogen", report_data.get("N", 240.0))),
        "phosphorus": float(report_data.get("phosphorus", report_data.get("P", 16.0))),
        "potassium": float(report_data.get("potassium", report_data.get("K", 210.0))),
        "ph": float(report_data.get("ph", report_data.get("pH", 7.2))),
        "organic_carbon": float(report_data.get("organic_carbon", report_data.get("OC", 0.55))),
        "ec": float(report_data.get("ec", report_data.get("EC", 0.5))),
        "moisture": float(report_data.get("moisture", 0.25)),
        "zinc": float(report_data.get("zinc", report_data.get("Zn", 0.75))),
        "iron": float(report_data.get("iron", report_data.get("Fe", 4.8))),
        "boron": float(report_data.get("boron", report_data.get("B", 0.52))),
        "sulphur": float(report_data.get("sulphur", report_data.get("S", 11.0))),
    }

    eval_result = evaluate_soil_health(extracted_params)

    if db:
        log_soil_data(
            db=db,
            district=str(report_data.get("district", "India")),
            test_date=datetime.utcnow().strftime("%Y-%m-%d"),
            nitrogen=extracted_params["nitrogen"],
            phosphorus=extracted_params["phosphorus"],
            potassium=extracted_params["potassium"],
            ph=extracted_params["ph"],
            organic_carbon=extracted_params["organic_carbon"],
            ec=extracted_params["ec"],
            zinc=extracted_params["zinc"],
            iron=extracted_params["iron"],
            boron=extracted_params["boron"],
            sulphur=extracted_params["sulphur"],
            moisture=extracted_params["moisture"],
            health_score=eval_result["soil_health_score"],
            source="Soil Health Card Upload"
        )

    return {
        "success": True,
        "card_parsed": True,
        "evaluation": eval_result
    }
