"""
End-to-End Quantum API Verification Test Suite
Tests all FastAPI endpoints with TestClient.
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from fastapi.testclient import TestClient
from main import app, quantum_engine

client = TestClient(app)

def run_tests():
    print("=" * 70)
    print("RUNNING END-TO-END HYBRID QUANTUM API TESTS")
    print("=" * 70)

    # 1. Reload quantum models in engine
    quantum_engine.load_models()

    # 2. Test Home & Health
    res = client.get("/")
    assert res.status_code == 200, f"Home endpoint failed: {res.text}"
    print("[PASS] GET / ->", res.json()["message"])

    res = client.get("/health")
    assert res.status_code == 200
    health_data = res.json()
    assert health_data["yield_model"] == "loaded", "Yield model not loaded in health check"
    assert health_data["price_model"] == "loaded", "Price model not loaded in health check"
    print(f"[PASS] GET /health -> Yield: {health_data['yield_model']} | Price: {health_data['price_model']} | Backend: {health_data['quantum_backend']}")

    # 3. Test Dropdown APIs
    res = client.get("/states")
    assert res.status_code == 200
    states = res.json()
    assert len(states) > 0
    print(f"[PASS] GET /states -> {len(states)} states found (e.g. {states[:3]})")

    res = client.get("/districts/Andhra Pradesh")
    assert res.status_code == 200
    districts = res.json()
    assert len(districts) > 0
    print(f"[PASS] GET /districts/Andhra Pradesh -> {len(districts)} districts")

    res = client.get("/markets/Andhra Pradesh/Guntur")
    assert res.status_code == 200
    markets = res.json()
    assert len(markets) > 0
    print(f"[PASS] GET /markets/Andhra Pradesh/Guntur -> {len(markets)} markets")

    res = client.get("/yield-options")
    assert res.status_code == 200
    yield_opts = res.json()
    assert len(yield_opts["crops"]) > 0
    print(f"[PASS] GET /yield-options -> Crops: {len(yield_opts['crops'])}, Seasons: {len(yield_opts['seasons'])}")

    # 4. Test Geospatial Geocoding API (/geocode)
    test_districts = [
        ("Andhra Pradesh", "Guntur", 16.3067, 80.4365),
        ("Andhra Pradesh", "Prakasam", 15.5057, 80.0499),
        ("Andhra Pradesh", "Krishna", 16.1800, 81.1300),
        ("Andhra Pradesh", "Anakapalli", 17.6896, 83.0033),
        ("Andhra Pradesh", "Visakhapatnam", 17.6868, 83.2185),
        ("Telangana", "Hyderabad", 17.3850, 78.4867),
        ("Karnataka", "Bengaluru", 12.9716, 77.5946),
        ("Tamil Nadu", "Chennai", 13.0827, 80.2707),
    ]

    for state, dist, exp_lat, exp_lon in test_districts:
        res = client.get(f"/geocode?state={state}&district={dist}")
        assert res.status_code == 200, f"Geocode failed for {dist}, {state}: {res.text}"
        data = res.json()
        assert "latitude" in data and "longitude" in data
        assert abs(data["latitude"] - exp_lat) < 0.5, f"Lat mismatch for {dist}: {data['latitude']} vs {exp_lat}"
        assert abs(data["longitude"] - exp_lon) < 0.5, f"Lon mismatch for {dist}: {data['longitude']} vs {exp_lon}"
        print(f"[PASS] GET /geocode?state={state}&district={dist} -> ({data['latitude']}, {data['longitude']}) [Source: {data.get('source')}]")

    # Test invalid location 404
    res_inv = client.get("/geocode?state=InvalidStateXYZ&district=NonExistentDistrict123")
    assert res_inv.status_code == 404
    print("[PASS] GET /geocode for invalid location correctly returned 404 Location not found.")

    # 5. Test Satellite Weather API
    res = client.get("/satellite-weather?state=Andhra+Pradesh&district=Guntur")
    assert res.status_code == 200
    sat_data = res.json()
    assert "ndvi" in sat_data and "soil_moisture" in sat_data
    print(f"[PASS] GET /satellite-weather -> NDVI: {sat_data['ndvi']}, Soil Moist: {sat_data['soil_moisture']}, LST: {sat_data['land_surface_temperature_c']} C")

    # 5. Test Quantum Crop Yield Prediction (/predict-yield & /predict-crop)
    yield_payload = {
        "Crop": "Rice",
        "Crop_Year": 2024,
        "Season": "Kharif",
        "State": "Andhra Pradesh",
        "District": "Guntur",
        "Area": 10.0,
        "Annual_Rainfall": None,  # Test auto-rainfall detection
        "Fertilizer": 850.0,
        "Pesticide": 45.0
    }

    res = client.post("/predict-yield", json=yield_payload)
    assert res.status_code == 200, f"/predict-yield failed: {res.text}"
    yield_res = res.json()
    assert yield_res["success"] is True
    assert yield_res["predicted_yield_per_acre"] > 0
    assert "quantum_confidence_score" in yield_res
    assert "satellite_data" in yield_res
    print(f"[PASS] POST /predict-yield -> Yield: {yield_res['predicted_yield_per_acre']} t/acre | Total: {yield_res['total_production_tons']} Tons | Quantum Confidence: {yield_res['quantum_confidence_score']}% | Rainfall: {yield_res['annual_rainfall_used']} mm ({yield_res['rainfall_source']})")

    res_alias = client.post("/predict-crop", json=yield_payload)
    assert res_alias.status_code == 200
    print(f"[PASS] POST /predict-crop (alias) -> Yield: {res_alias.json()['predicted_yield_per_acre']} t/acre")

    # 6. Test Quantum Commodity Price Forecast (/predict-price)
    price_payload = {
        "State": "Gujarat",
        "District": "Amreli",
        "Market": "Damnagar",
        "Commodity": "Cotton",
        "Variety": "Other",
        "Grade": "FAQ",
        "Prediction_Date": "2026-08-21"
    }

    res = client.post("/predict-price", json=price_payload)
    assert res.status_code == 200, f"/predict-price failed: {res.text}"
    price_res = res.json()
    assert price_res["success"] is True
    assert price_res["predicted_price"] > 0
    assert "quantum_confidence_score" in price_res
    assert "price_confidence_interval" in price_res
    print(f"[PASS] POST /predict-price -> Predicted Price: Rs. {price_res['predicted_price']}/Qtl | Range: Rs. {price_res['price_confidence_interval']['lower_bound']} - Rs. {price_res['price_confidence_interval']['upper_bound']} | Confidence: {price_res['quantum_confidence_score']}%")

    # 7. Test Quantum Circuit Metadata & Telemetry
    res = client.get("/quantum/circuit")
    assert res.status_code == 200
    circ_data = res.json()
    assert "crop_yield_circuit" in circ_data
    print(f"[PASS] GET /quantum/circuit -> Qubits: {circ_data['crop_yield_circuit']['n_qubits']}, Depth: {circ_data['crop_yield_circuit']['circuit_depth']}, Total Gates: {circ_data['crop_yield_circuit']['total_quantum_gates']}")

    # 8. Test Model Status
    res = client.get("/model-status")
    assert res.status_code == 200
    status_data = res.json()
    print(f"[PASS] GET /model-status -> Framework: {status_data['quantum_framework']}")

    print("=" * 70)
    print("ALL TESTS PASSED SUCCESSFULLY! 100% QUANTUM PRODUCTION READY.")
    print("=" * 70)

if __name__ == "__main__":
    run_tests()
