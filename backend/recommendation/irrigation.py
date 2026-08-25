"""
Irrigation & Crop Water Requirement Engine.
Computes stage-wise crop evapotranspiration (ETc = ET0 * Kc), soil moisture deficit,
irrigation intervals, and volumetric water requirement in Liters / Acre.
"""

from typing import Dict, Any, Optional, List

# FAO Crop Coefficients (Kc) for Growth Stages
CROP_KC_PROFILES = {
    "RICE": {"kc_ini": 1.05, "kc_mid": 1.20, "kc_end": 0.90, "total_water_mm": 1200.0, "root_depth_m": 0.6, "method": "Intermittent Flooding / AWD"},
    "WHEAT": {"kc_ini": 0.40, "kc_mid": 1.15, "kc_end": 0.40, "total_water_mm": 450.0, "root_depth_m": 1.0, "method": "Border Strip / Sprinkler"},
    "COTTON": {"kc_ini": 0.45, "kc_mid": 1.15, "kc_end": 0.70, "total_water_mm": 700.0, "root_depth_m": 1.2, "method": "Drip Irrigation / Alternate Furrow"},
    "MAIZE": {"kc_ini": 0.40, "kc_mid": 1.15, "kc_end": 0.60, "total_water_mm": 500.0, "root_depth_m": 1.0, "method": "Furrow / Sprinkler"},
    "SUGARCANE": {"kc_ini": 0.40, "kc_mid": 1.25, "kc_end": 0.75, "total_water_mm": 1800.0, "root_depth_m": 1.5, "method": "Subsurface Drip Irrigation"},
    "TOMATO": {"kc_ini": 0.60, "kc_mid": 1.15, "kc_end": 0.80, "total_water_mm": 600.0, "root_depth_m": 0.8, "method": "Drip with Polyethylene Mulch"},
    "CHILLI": {"kc_ini": 0.60, "kc_mid": 1.05, "kc_end": 0.80, "total_water_mm": 550.0, "root_depth_m": 0.8, "method": "Drip Irrigation"},
    "ONION": {"kc_ini": 0.50, "kc_mid": 1.05, "kc_end": 0.75, "total_water_mm": 450.0, "root_depth_m": 0.4, "method": "Micro-Sprinkler / Drip"},
    "GROUNDNUT": {"kc_ini": 0.40, "kc_mid": 1.10, "kc_end": 0.60, "total_water_mm": 500.0, "root_depth_m": 0.8, "method": "Sprinkler / Furrow"},
    "PULSES": {"kc_ini": 0.40, "kc_mid": 1.05, "kc_end": 0.40, "total_water_mm": 350.0, "root_depth_m": 0.8, "method": "Sprinkler / Ridge & Furrow"},
    "SOYABEAN": {"kc_ini": 0.40, "kc_mid": 1.15, "kc_end": 0.50, "total_water_mm": 450.0, "root_depth_m": 0.9, "method": "Sprinkler / Broad Bed Furrow"},
    "DEFAULT": {"kc_ini": 0.45, "kc_mid": 1.10, "kc_end": 0.60, "total_water_mm": 550.0, "root_depth_m": 0.8, "method": "Drip / Furrow"}
}


def calculate_crop_irrigation_schedule(
    crop: str,
    area_acres: float = 1.0,
    et0_mm_per_day: float = 4.5,
    soil_moisture_fraction: float = 0.25,
    growth_stage: str = "mid",
    soil_type: str = "Loam"
) -> Dict[str, Any]:
    """
    Computes precise scientific irrigation schedule and water volumetric demand.
    1 mm of water depth on 1 Acre = 4,046.86 Liters.
    """
    crop_clean = (crop or "DEFAULT").strip().upper()
    profile = CROP_KC_PROFILES.get(crop_clean, CROP_KC_PROFILES["DEFAULT"])

    # Determine current Kc factor
    if growth_stage.lower() == "initial":
        kc = profile["kc_ini"]
    elif growth_stage.lower() in ["late", "end", "harvest"]:
        kc = profile["kc_end"]
    else:
        kc = profile["kc_mid"]

    # Crop Evapotranspiration ETc = ET0 * Kc (mm/day)
    etc_mm_day = round(et0_mm_per_day * kc, 2)

    # Soil Available Water Capacity (AWC) in mm/m
    awc_map = {"Sandy": 70.0, "Loam": 140.0, "Clay": 180.0, "Black Soil": 170.0, "Red Soil": 120.0}
    awc = awc_map.get(soil_type, 140.0)

    # Readily Available Water (RAW) = p * AWC * RootDepth (p ~ 0.5 for most field crops)
    raw_mm = round(0.5 * (awc / 1000.0) * (profile["root_depth_m"] * 1000.0), 1)

    # Irrigation Interval (days) = RAW / ETc
    raw_mm_safe = max(15.0, raw_mm)
    interval_days = max(2, min(14, int(round(raw_mm_safe / max(0.5, etc_mm_day)))))

    # If current soil moisture is depleted (< 0.18 m3/m3), trigger immediate irrigation
    urgency = "Normal"
    if soil_moisture_fraction < 0.18:
        urgency = "Immediate (Soil Moisture Depleted)"
        interval_days = 1
    elif soil_moisture_fraction < 0.22:
        urgency = "Moderate (Irrigate within 48 hours)"

    # Water Volume per Irrigation Cycle
    depth_per_irrigation_mm = round(etc_mm_day * interval_days, 1)
    liters_per_acre_per_cycle = round(depth_per_irrigation_mm * 4046.86, 0)
    total_cycle_liters = round(liters_per_acre_per_cycle * area_acres, 0)

    # Total Seasonal Water Requirement
    total_season_liters = round(profile["total_water_mm"] * 4046.86 * area_acres, 0)

    # Critical Irrigation Growth Stages
    critical_stages = [
        {"stage": "Crown Root Initiation / Active Tillering", "timing": "20 - 25 DAS", "water_stress_impact": "High yield penalty if water stressed"},
        {"stage": "Panicle Initiation / Booting", "timing": "45 - 55 DAS", "water_stress_impact": "Causes floret abortion and reduces spikelet number"},
        {"stage": "Flowering / Grain Filling (Milking)", "timing": "70 - 85 DAS", "water_stress_impact": "Critical for grain weight; drought causes shriveled grains"}
    ]

    return {
        "crop": crop.title(),
        "cultivated_area_acres": area_acres,
        "current_growth_stage": growth_stage.title(),
        "crop_coefficient_kc": kc,
        "daily_crop_water_loss_etc_mm": etc_mm_day,
        "reference_evapotranspiration_et0_mm": et0_mm_per_day,
        "recommended_irrigation_method": profile["method"],
        "schedule": {
            "irrigation_interval_days": interval_days,
            "application_depth_mm": depth_per_irrigation_mm,
            "liters_per_acre_per_cycle": liters_per_acre_per_cycle,
            "total_water_liters_this_cycle": total_cycle_liters,
            "urgency_level": urgency
        },
        "seasonal_water_budget": {
            "total_seasonal_water_depth_mm": profile["total_water_mm"],
            "total_seasonal_liters": total_season_liters,
            "savings_with_drip_percent": "40 - 55% water saving over flood irrigation"
        },
        "critical_growth_stages": critical_stages,
        "smart_advice": f"Apply {depth_per_irrigation_mm} mm ({liters_per_acre_per_cycle:,.0f} Liters/Acre) every {interval_days} days using {profile['method']}."
    }
