"""
FastAPI Routes for Precision Agriculture Recommendation Module.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException, Body
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.connection import get_db
from database.repository import log_recommendation, get_recommendations_history
from database.models import Recommendations
from recommendation.recommendation_engine import recommendation_engine
from recommendation.crop_advisor import rank_crop_suitability

router = APIRouter(prefix="/recommendation", tags=["Precision Agriculture Recommendations"])


class PrecisionRecommendationRequest(BaseModel):
    Crop: str = Field(default="Rice", description="Target Crop")
    State: str = Field(default="Andhra Pradesh", description="State")
    District: str = Field(default="Guntur", description="District")
    Market: Optional[str] = Field(default=None, description="Mandi Market Name")
    Variety: Optional[str] = Field(default=None, description="Crop Variety")
    Grade: str = Field(default="FAQ", description="Commodity Grade")
    Season: str = Field(default="Kharif", description="Farming Season")
    Crop_Year: int = Field(default=2024, description="Crop Year")
    Area: float = Field(default=5.0, description="Cultivated Area in Acres")
    Soil_Nitrogen: Optional[float] = None
    Soil_Phosphorus: Optional[float] = None
    Soil_Potassium: Optional[float] = None
    Soil_pH: Optional[float] = None
    Latitude: Optional[float] = None
    Longitude: Optional[float] = None


@router.post("")
@router.post("/")
@router.post("/generate")
def generate_recommendation_endpoint(
    data: PrecisionRecommendationRequest,
    db: Session = Depends(get_db)
):
    """
    Primary Precision Agriculture Decision Support API.
    Fuses Hybrid Quantum ML (Yield HQNN + Price VQR), Satellite Indices, Soil Health, and Weather.
    Generates best variety, expected yield, mandi price, profit forecast, 4R fertilizer schedule, and irrigation regime.
    """
    try:
        soil_in = None
        if any([data.Soil_Nitrogen, data.Soil_Phosphorus, data.Soil_Potassium, data.Soil_pH]):
            soil_in = {
                "nitrogen": data.Soil_Nitrogen or 240.0,
                "phosphorus": data.Soil_Phosphorus or 16.0,
                "potassium": data.Soil_Potassium or 210.0,
                "ph": data.Soil_pH or 7.2
            }

        rec = recommendation_engine.generate_recommendation(
            crop=data.Crop,
            state=data.State,
            district=data.District,
            area_acres=data.Area,
            season=data.Season,
            crop_year=data.Crop_Year,
            market=data.Market,
            variety=data.Variety,
            grade=data.Grade,
            soil_input=soil_in,
            latitude=data.Latitude,
            longitude=data.Longitude
        )

        # Log recommendation to Database
        if db:
            log_recommendation(
                db=db,
                date_str=datetime.utcnow().strftime("%Y-%m-%d"),
                recommended_crop=rec["farm_parameters"]["crop"],
                variety=rec["farm_parameters"]["recommended_variety"],
                expected_yield=rec["quantum_predictions"]["quantum_yield_hqnn"]["yield_per_acre_tons"],
                expected_price=rec["quantum_predictions"]["quantum_price_vqr"]["predicted_mandi_price_inr_per_qtl"],
                expected_profit=rec["economic_financial_outlook"]["net_expected_profit_inr"],
                fertilizer_plan=rec["prescriptions"]["fertilizer_plan"],
                irrigation_plan=rec["prescriptions"]["irrigation_plan"],
                full_report=rec,
                risk_level=rec["decision_confidence"]["overall_risk_level"],
                confidence_score=rec["decision_confidence"]["quantum_composite_confidence_percent"]
            )

        return rec
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Precision Recommendation failed: {str(e)}")


@router.get("/crop-suitability")
def get_crop_suitability(
    state: str = Query("Andhra Pradesh"),
    district: Optional[str] = Query("Guntur"),
    season: str = Query("Kharif"),
    ph: float = Query(7.2),
    rainfall_mm: float = Query(950.0)
):
    """Ranks all major agricultural crops for a specific state/soil/climate using Multi-Criteria Decision Analysis."""
    ranked = rank_crop_suitability(
        state=state,
        district=district,
        season=season,
        ph=ph,
        rainfall_mm=rainfall_mm
    )
    return {
        "success": True,
        "state": state,
        "district": district,
        "season": season,
        "ranked_crops": ranked
    }


@router.get("/history")
def get_recommendation_history_list(
    field_id: Optional[int] = Query(None),
    limit: int = Query(20),
    db: Session = Depends(get_db)
):
    """Returns stored recommendation history from database."""
    records = get_recommendations_history(db=db, field_id=field_id, limit=limit)
    return {
        "success": True,
        "count": len(records),
        "recommendations": [r.to_dict() for r in records]
    }
