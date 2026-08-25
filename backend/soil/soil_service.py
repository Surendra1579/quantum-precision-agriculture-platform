"""
Soil Service: Regional soil profiling, soil test report parsing, and target-yield fertilizer calculations.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from soil.soil_prediction import evaluate_soil_health, NUTRIENT_BENCHMARKS

logger = logging.getLogger("soil_service")

# Regional Indian Soil Profiles (ICAR Soil Survey & SoilGrids benchmarks)
REGIONAL_SOIL_PROFILES = {
    "ANDHRA PRADESH": {
        "soil_type": "Red Sandy Loam / Black Clay",
        "nitrogen": 220.0,
        "phosphorus": 18.5,
        "potassium": 240.0,
        "ph": 7.4,
        "organic_carbon": 0.52,
        "ec": 0.45,
        "zinc": 0.75,
        "iron": 5.2,
        "boron": 0.55,
        "sulphur": 11.2,
        "moisture": 0.26,
        "source": "ICAR-NBSS&LUP & SoilGrids Regional Survey"
    },
    "TELANGANA": {
        "soil_type": "Red Sandy (Chalka) & Deep Black",
        "nitrogen": 210.0,
        "phosphorus": 16.0,
        "potassium": 210.0,
        "ph": 7.6,
        "organic_carbon": 0.48,
        "ec": 0.50,
        "zinc": 0.65,
        "iron": 4.8,
        "boron": 0.48,
        "sulphur": 9.5,
        "moisture": 0.23,
        "source": "ICAR-NBSS&LUP & SoilGrids Regional Survey"
    },
    "TAMIL NADU": {
        "soil_type": "Red Loam / Coastal Alluvium",
        "nitrogen": 235.0,
        "phosphorus": 17.0,
        "potassium": 225.0,
        "ph": 7.1,
        "organic_carbon": 0.55,
        "ec": 0.55,
        "zinc": 0.80,
        "iron": 5.6,
        "boron": 0.58,
        "sulphur": 12.0,
        "moisture": 0.25,
        "source": "ICAR-NBSS&LUP & SoilGrids Regional Survey"
    },
    "KARNATAKA": {
        "soil_type": "Red Laterite & Black Soil",
        "nitrogen": 245.0,
        "phosphorus": 19.0,
        "potassium": 250.0,
        "ph": 6.8,
        "organic_carbon": 0.62,
        "ec": 0.40,
        "zinc": 0.85,
        "iron": 6.0,
        "boron": 0.60,
        "sulphur": 13.5,
        "moisture": 0.28,
        "source": "ICAR-NBSS&LUP & SoilGrids Regional Survey"
    },
    "MAHARASHTRA": {
        "soil_type": "Medium to Deep Black Cotton Soil (Vertisol)",
        "nitrogen": 195.0,
        "phosphorus": 14.5,
        "potassium": 280.0,
        "ph": 7.9,
        "organic_carbon": 0.50,
        "ec": 0.65,
        "zinc": 0.60,
        "iron": 4.2,
        "boron": 0.50,
        "sulphur": 10.0,
        "moisture": 0.24,
        "source": "ICAR-NBSS&LUP & SoilGrids Regional Survey"
    },
    "GUJARAT": {
        "soil_type": "Alluvial Sandy Loam & Medium Black",
        "nitrogen": 180.0,
        "phosphorus": 15.0,
        "potassium": 260.0,
        "ph": 8.1,
        "organic_carbon": 0.42,
        "ec": 0.75,
        "zinc": 0.55,
        "iron": 3.9,
        "boron": 0.45,
        "sulphur": 8.5,
        "moisture": 0.21,
        "source": "ICAR-NBSS&LUP & SoilGrids Regional Survey"
    },
    "PUNJAB": {
        "soil_type": "Alluvial Loam (Indo-Gangetic Plain)",
        "nitrogen": 260.0,
        "phosphorus": 24.0,
        "potassium": 210.0,
        "ph": 7.5,
        "organic_carbon": 0.65,
        "ec": 0.35,
        "zinc": 0.90,
        "iron": 6.5,
        "boron": 0.65,
        "sulphur": 14.0,
        "moisture": 0.32,
        "source": "ICAR-NBSS&LUP & SoilGrids Regional Survey"
    },
    "UTTAR PRADESH": {
        "soil_type": "Gangetic Alluvial Silt Loam",
        "nitrogen": 230.0,
        "phosphorus": 18.0,
        "potassium": 195.0,
        "ph": 7.3,
        "organic_carbon": 0.58,
        "ec": 0.42,
        "zinc": 0.72,
        "iron": 5.1,
        "boron": 0.52,
        "sulphur": 11.0,
        "moisture": 0.29,
        "source": "ICAR-NBSS&LUP & SoilGrids Regional Survey"
    },
    "DEFAULT": {
        "soil_type": "Agricultural Loam",
        "nitrogen": 225.0,
        "phosphorus": 16.5,
        "potassium": 220.0,
        "ph": 7.2,
        "organic_carbon": 0.54,
        "ec": 0.50,
        "zinc": 0.70,
        "iron": 4.8,
        "boron": 0.50,
        "sulphur": 10.5,
        "moisture": 0.25,
        "source": "National Soil Health Survey Baseline"
    }
}

# Standard Crop Recommended Nutrient Doses (N-P-K kg/acre)
CROP_NUTRIENT_DOSES = {
    "RICE": {"N": 48.0, "P": 24.0, "K": 24.0, "duration_days": 125, "fym_tons": 4.0},
    "WHEAT": {"N": 50.0, "P": 25.0, "K": 20.0, "duration_days": 130, "fym_tons": 3.5},
    "COTTON": {"N": 60.0, "P": 30.0, "K": 30.0, "duration_days": 160, "fym_tons": 5.0},
    "MAIZE": {"N": 48.0, "P": 24.0, "K": 20.0, "duration_days": 105, "fym_tons": 3.5},
    "SUGARCANE": {"N": 100.0, "P": 40.0, "K": 50.0, "duration_days": 330, "fym_tons": 8.0},
    "GROUNDNUT": {"N": 10.0, "P": 20.0, "K": 20.0, "duration_days": 115, "fym_tons": 3.0},
    "PULSES": {"N": 10.0, "P": 20.0, "K": 10.0, "duration_days": 90, "fym_tons": 2.5},
    "SOYABEAN": {"N": 12.0, "P": 24.0, "K": 16.0, "duration_days": 100, "fym_tons": 3.0},
    "TOMATO": {"N": 60.0, "P": 40.0, "K": 40.0, "duration_days": 120, "fym_tons": 6.0},
    "CHILLI": {"N": 60.0, "P": 30.0, "K": 30.0, "duration_days": 150, "fym_tons": 5.0},
    "ONION": {"N": 45.0, "P": 25.0, "K": 35.0, "duration_days": 110, "fym_tons": 5.0},
    "DEFAULT": {"N": 40.0, "P": 20.0, "K": 20.0, "duration_days": 120, "fym_tons": 4.0}
}


class SoilService:
    """
    Soil Intelligence Service.
    Retrieves soil profiles, processes soil tests, and computes customized fertilizer prescriptions.
    """

    def get_soil_profile(
        self,
        state: Optional[str] = None,
        district: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Retrieves regional soil profile and calculates health score.
        """
        st_clean = (state or "DEFAULT").strip().upper()
        profile = REGIONAL_SOIL_PROFILES.get(st_clean, REGIONAL_SOIL_PROFILES["DEFAULT"]).copy()
        
        # Run health evaluation
        health_eval = evaluate_soil_health(profile)

        return {
            "success": True,
            "location": {
                "state": state or "Auto Baseline",
                "district": district or "Auto Baseline",
                "latitude": latitude,
                "longitude": longitude
            },
            "soil_type": profile.get("soil_type", "Agricultural Loam"),
            "health_evaluation": health_eval,
            "source": profile.get("source", "SoilGrids / ICAR")
        }

    def recommend_fertilizer(
        self,
        crop: str,
        area_acres: float = 1.0,
        soil_params: Optional[Dict[str, float]] = None,
        target_yield_multiplier: float = 1.0
    ) -> Dict[str, Any]:
        """
        Calculates exact commercial fertilizer quantities (Urea, DAP, MOP, SSP, Micronutrients)
        adjusted for existing soil test results and target yield.
        """
        crop_clean = (crop or "DEFAULT").strip().upper()
        base_dose = CROP_NUTRIENT_DOSES.get(crop_clean, CROP_NUTRIENT_DOSES["DEFAULT"])

        # Soil test adjustment factor
        # If soil is low, increase dose by 25%; if high, decrease by 25%
        soil_n = soil_params.get("nitrogen", 225.0) if soil_params else 225.0
        soil_p = soil_params.get("phosphorus", 16.5) if soil_params else 16.5
        soil_k = soil_params.get("potassium", 220.0) if soil_params else 220.0

        n_adj = 1.25 if soil_n < 200 else (0.80 if soil_n > 400 else 1.0)
        p_adj = 1.25 if soil_p < 12 else (0.80 if soil_p > 25 else 1.0)
        k_adj = 1.25 if soil_k < 120 else (0.80 if soil_k > 280 else 1.0)

        # Net required nutrient kg per acre
        net_n = base_dose["N"] * n_adj * target_yield_multiplier
        net_p = base_dose["P"] * p_adj * target_yield_multiplier
        net_k = base_dose["K"] * k_adj * target_yield_multiplier

        # Commercial Fertilizer Calculations:
        # Option A: DAP + Urea + MOP
        # DAP (18% N, 46% P2O5) -> 1 kg DAP = 0.46 kg P and 0.18 kg N
        dap_kg_acre = round(net_p / 0.46, 1)
        n_from_dap = dap_kg_acre * 0.18
        remaining_n = max(0.0, net_n - n_from_dap)
        urea_kg_acre = round(remaining_n / 0.46, 1)  # Urea is 46% N
        # MOP (60% K2O) -> 1 kg MOP = 0.60 kg K
        mop_kg_acre = round(net_k / 0.60, 1)

        # Farm Yard Manure (FYM)
        fym_tons_total = round(base_dose["fym_tons"] * area_acres, 1)

        # Micronutrient additions
        zinc_sulphate_kg_acre = 10.0 if (soil_params and soil_params.get("zinc", 0.8) < 0.6) else 5.0
        borax_kg_acre = 4.0 if (soil_params and soil_params.get("boron", 0.5) < 0.5) else 0.0

        # Split Application Schedule
        # Basal Dose: 100% DAP + 100% MOP + 33% Urea + 100% FYM
        # 1st Top Dressing (Tillering / Vegetative @ 25-30 days): 33% Urea
        # 2nd Top Dressing (Panicle / Flowering @ 50-60 days): 34% Urea
        schedule = [
            {
                "stage": "Basal Application (At Sowing / Transplanting)",
                "timing": "Day 0 (During final land preparation)",
                "fertilizers": {
                    "dap_kg": round(dap_kg_acre * area_acres, 1),
                    "urea_kg": round(urea_kg_acre * 0.33 * area_acres, 1),
                    "mop_kg": round(mop_kg_acre * area_acres, 1),
                    "fym_tons": fym_tons_total,
                    "zinc_sulphate_kg": round(zinc_sulphate_kg_acre * area_acres, 1)
                },
                "instructions": "Incorporate FYM and basal fertilizers thoroughly into the soil 5-7 cm below seed depth."
            },
            {
                "stage": "First Top Dressing (Vegetative / Tillering Stage)",
                "timing": "25 - 30 days after sowing",
                "fertilizers": {
                    "urea_kg": round(urea_kg_acre * 0.33 * area_acres, 1),
                    "biofertilizer": "Azotobacter / PSB culture (2 kg/acre foliar spray)"
                },
                "instructions": "Broadcast Urea after weeding when soil has adequate moisture. Avoid waterlogged conditions."
            },
            {
                "stage": "Second Top Dressing (Panicle Initiation / Flowering)",
                "timing": "50 - 60 days after sowing",
                "fertilizers": {
                    "urea_kg": round(urea_kg_acre * 0.34 * area_acres, 1),
                    "micronutrient_spray": "0.5% Multi-micronutrient liquid spray (2 ml / liter of water)"
                },
                "instructions": "Apply final nitrogen booster to optimize grain filling and reduce spikelet sterility."
            }
        ]

        return {
            "crop": crop.title(),
            "cultivated_area_acres": area_acres,
            "nutrient_requirements_kg_per_acre": {
                "nitrogen_n": round(net_n, 1),
                "phosphorus_p": round(net_p, 1),
                "potassium_k": round(net_k, 1)
            },
            "commercial_fertilizers_total": {
                "dap_kg": round(dap_kg_acre * area_acres, 1),
                "urea_kg": round(urea_kg_acre * area_acres, 1),
                "mop_kg": round(mop_kg_acre * area_acres, 1),
                "fym_tons": fym_tons_total,
                "zinc_sulphate_kg": round(zinc_sulphate_kg_acre * area_acres, 1),
                "borax_kg": round(borax_kg_acre * area_acres, 1)
            },
            "commercial_fertilizers_per_acre": {
                "dap_kg": dap_kg_acre,
                "urea_kg": urea_kg_acre,
                "mop_kg": mop_kg_acre,
                "fym_tons": base_dose["fym_tons"],
                "zinc_sulphate_kg": zinc_sulphate_kg_acre,
                "borax_kg": borax_kg_acre
            },
            "application_schedule": schedule,
            "scientific_rationale": "4R Nutrient Stewardship (Right Source, Right Rate, Right Time, Right Place) formulated based on ICAR guidelines."
        }


soil_service = SoilService()


def fetch_regional_soil_profile(state: Optional[str] = None, district: Optional[str] = None) -> Dict[str, Any]:
    return soil_service.get_soil_profile(state=state, district=district)


def recommend_fertilizer_dosage(crop: str, area_acres: float = 1.0, soil_params: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
    return soil_service.recommend_fertilizer(crop=crop, area_acres=area_acres, soil_params=soil_params)
