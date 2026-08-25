"""
Fertilizer & 4R Nutrient Stewardship Module.
Computes precise split dosages (Basal, 1st Top Dressing, 2nd Top Dressing),
commercial bag counts, micronutrient foliar sprays, and biofertilizers.
"""

from typing import Dict, Any, Optional
from soil.soil_service import soil_service


def generate_fertilizer_prescription(
    crop: str,
    area_acres: float = 1.0,
    soil_data: Optional[Dict[str, Any]] = None,
    target_yield_t_per_acre: Optional[float] = None
) -> Dict[str, Any]:
    """
    Generates comprehensive 4R Nutrient Stewardship fertilizer prescription.
    """
    soil_params = None
    if soil_data:
        # Extract flat dictionary from potential nested structure
        if "parameters" in soil_data:
            soil_params = soil_data["parameters"]
        elif "health_evaluation" in soil_data and "parameters" in soil_data["health_evaluation"]:
            soil_params = soil_data["health_evaluation"]["parameters"]
        else:
            soil_params = soil_data

    # Multiplier based on target yield
    multiplier = 1.0
    if target_yield_t_per_acre is not None and target_yield_t_per_acre > 0:
        # Benchmark yield roughly 2.5 t/acre for grain
        multiplier = max(0.85, min(1.35, target_yield_t_per_acre / 2.5))

    rec = soil_service.recommend_fertilizer(
        crop=crop,
        area_acres=area_acres,
        soil_params=soil_params,
        target_yield_multiplier=multiplier
    )

    # Calculate Commercial 50kg Bags Count
    commercial = rec["commercial_fertilizers_total"]
    bags_dap = round(commercial["dap_kg"] / 50.0, 1)
    bags_urea = round(commercial["urea_kg"] / 45.0, 1)  # Indian urea bags are 45 kg
    bags_mop = round(commercial["mop_kg"] / 50.0, 1)

    rec["packaging_summary"] = {
        "dap_50kg_bags": bags_dap,
        "urea_45kg_bags": bags_urea,
        "mop_50kg_bags": bags_mop,
        "fym_trolleys_approx": round(commercial["fym_tons"] / 2.5, 1)  # 1 tractor trolley ~ 2.5 tons
    }

    # Bio-fertilizer inoculation recommendation
    rec["biofertilizers"] = [
        {"name": "Azotobacter / Rhizobium", "dose": f"{round(area_acres * 2.0, 1)} kg", "application": "Seed treatment / Root dip before planting to fix 20-30 kg atmospheric N/ha"},
        {"name": "Phosphate Solubilizing Bacteria (PSB)", "dose": f"{round(area_acres * 2.0, 1)} kg", "application": "Mix with FYM at basal application to solubilize fixed soil phosphorus"},
        {"name": "Potash Mobilizing Bacteria (KMB)", "dose": f"{round(area_acres * 1.5, 1)} kg", "application": "Soil application at 30 DAS for active potassium uptake"}
    ]

    return rec
