"""
Comprehensive Unit, Integration, and FastAPI End-to-End Test Suite
for Quantum Precision Agriculture Decision Support Platform.
"""

import sys
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from fastapi.testclient import TestClient
from main import app, quantum_engine
from database.connection import init_db, SessionLocal
import database.repository as repo
from satellite.ndvi import calculate_ndvi, classify_ndvi, generate_ndvi_spatial_grid
from satellite.evi import calculate_evi, classify_evi
from satellite.lst import calculate_lst, calculate_fvc, calculate_emissivity, calculate_thermal_stress
from satellite.vegetation import calculate_ndwi, calculate_vhi, assess_crop_stress
from soil.soil_prediction import evaluate_soil_health, calculate_npk_adequacy, calculate_ph_corrections, diagnose_soil_deficiencies
from weather.weather_service import calculate_fao56_et0, evaluate_weather_alerts
from recommendation.fertilizer import generate_fertilizer_prescription
from recommendation.irrigation import calculate_crop_irrigation_schedule
from plot.plot_service import calculate_polygon_area_acres, calculate_polygon_centroid

client = TestClient(app)


class TestSatelliteModule(unittest.TestCase):
    """Unit Tests for Satellite Multi-Spectral Calculations."""

    def test_ndvi_calculation(self):
        # High vegetation: NIR=0.8, Red=0.1 -> (0.8-0.1)/(0.8+0.1) = 0.7778
        ndvi = calculate_ndvi(nir=0.8, red=0.1)
        self.assertAlmostEqual(ndvi, 0.7778, places=3)
        self.assertTrue(0.7 <= ndvi <= 1.0)

        # Water body / negative NDVI
        ndvi_water = calculate_ndvi(nir=0.1, red=0.3)
        self.assertTrue(ndvi_water < 0.0)

    def test_ndvi_classification(self):
        good = classify_ndvi(0.60)
        self.assertEqual(good["health"], "Good")
        optimal = classify_ndvi(0.75)
        self.assertEqual(optimal["health"], "Optimal")
        stressed = classify_ndvi(0.20)
        self.assertEqual(stressed["health"], "Low")

    def test_evi_calculation(self):
        evi = calculate_evi(nir=0.7, red=0.15, blue=0.08)
        self.assertTrue(0.0 <= evi <= 1.0)
        evi_cls = classify_evi(evi)
        self.assertIn("biomass_index", evi_cls)

    def test_lst_and_emissivity(self):
        fvc = calculate_fvc(0.65)
        self.assertTrue(0.0 <= fvc <= 1.0)
        eps = calculate_emissivity(fvc)
        self.assertTrue(0.96 <= eps <= 0.99)
        lst_c = calculate_lst(brightness_temp_k=305.15, emissivity=eps)
        self.assertTrue(20.0 <= lst_c <= 45.0)

    def test_ndwi_and_vhi(self):
        ndwi = calculate_ndwi(nir=0.6, swir=0.3)
        self.assertTrue(ndwi > 0)
        vhi = calculate_vhi(ndvi=0.65, lst_c=30.0)
        self.assertTrue(0.0 <= vhi["vhi"] <= 100.0)
        self.assertIn(vhi["health_status"], ["Optimal", "Moderate", "Stressed", "Severely Stressed", "Extreme Stress"])

    def test_spatial_grid_generation(self):
        grid = generate_ndvi_spatial_grid(center_lat=16.30, center_lon=80.43, mean_ndvi=0.60, grid_size=5)
        self.assertEqual(len(grid), 25)
        self.assertTrue("bounds" in grid[0])
        self.assertTrue("ndvi" in grid[0])


class TestSoilModule(unittest.TestCase):
    """Unit Tests for Soil Scoring, NPK Adequacy, and Fertilizer Calculations."""

    def test_soil_health_evaluation(self):
        params = {
            "nitrogen": 280.0,
            "phosphorus": 18.0,
            "potassium": 220.0,
            "ph": 7.2,
            "organic_carbon": 0.65,
            "ec": 0.45,
            "moisture": 0.28,
            "zinc": 0.85,
            "iron": 5.0,
            "boron": 0.55,
            "sulphur": 12.0
        }
        eval_res = evaluate_soil_health(params)
        self.assertTrue(70.0 <= eval_res["soil_health_score"] <= 100.0)
        self.assertEqual(eval_res["soil_grade"], "Grade A (Highly Fertile)")

    def test_npk_adequacy(self):
        npk = calculate_npk_adequacy(n=180.0, p=22.0, k=250.0)
        self.assertEqual(npk["nitrogen"]["status"], "Deficient")
        self.assertEqual(npk["phosphorus"]["status"], "Optimal")
        self.assertEqual(npk["potassium"]["status"], "Optimal")

    def test_ph_correction(self):
        acidic_fix = calculate_ph_corrections(ph=5.2)
        self.assertEqual(acidic_fix["soil_reaction"], "Acidic")
        self.assertTrue(acidic_fix["quantity_kg_per_acre"] > 0)

        alkaline_fix = calculate_ph_corrections(ph=8.4)
        self.assertEqual(alkaline_fix["soil_reaction"], "Alkaline / Calcareous")
        self.assertTrue(alkaline_fix["quantity_kg_per_acre"] > 0)


class TestWeatherModule(unittest.TestCase):
    """Unit Tests for FAO-56 Penman-Monteith ET0 and Agro-Weather Alerts."""

    def test_fao56_et0(self):
        et0 = calculate_fao56_et0(
            temp_c=28.0, temp_min_c=22.0, temp_max_c=34.0,
            humidity_percent=65.0, wind_speed_kmh=12.0, solar_radiation_mj_m2=19.0
        )
        self.assertTrue(2.0 <= et0 <= 8.0)

    def test_weather_alerts(self):
        alerts_bundle = evaluate_weather_alerts(
            temp_c=41.0, temp_max_c=42.0, temp_min_c=28.0,
            humidity_percent=88.0, wind_speed_kmh=38.0, precipitation_mm=55.0
        )
        self.assertTrue(alerts_bundle["total_alerts_count"] >= 3)


class TestRecommendationAndPlotModules(unittest.TestCase):
    """Unit Tests for Fertilizer 4R Splits, Irrigation, and GeoJSON polygon calculations."""

    def test_fertilizer_split_prescription(self):
        fert = generate_fertilizer_prescription(crop="Rice", area_acres=5.0)
        self.assertIn("packaging_summary", fert)
        self.assertTrue(fert["packaging_summary"]["dap_50kg_bags"] > 0)
        self.assertEqual(len(fert["application_schedule"]), 3)

    def test_crop_irrigation_schedule(self):
        irrig = calculate_crop_irrigation_schedule(crop="Wheat", area_acres=2.0, et0_mm_per_day=4.2)
        self.assertTrue(irrig["schedule"]["irrigation_interval_days"] > 0)
        self.assertTrue(irrig["schedule"]["total_water_liters_this_cycle"] > 0)

    def test_polygon_area_and_centroid(self):
        # A rectangular field in Guntur (approx 0.002 deg x 0.002 deg ~ 200m x 200m ~ 10 acres)
        coords = [
            [16.300, 80.430],
            [16.302, 80.430],
            [16.302, 80.432],
            [16.300, 80.432],
            [16.300, 80.430]
        ]
        centroid = calculate_polygon_centroid(coords)
        self.assertAlmostEqual(centroid[0], 16.301, places=3)
        self.assertAlmostEqual(centroid[1], 80.431, places=3)
        area = calculate_polygon_area_acres(coords)
        self.assertTrue(area > 0.5)


class TestFastAPIEndToEndEndpoints(unittest.TestCase):
    """End-to-End Integration and API Route Verification."""

    @classmethod
    def setUpClass(cls):
        init_db()
        quantum_engine.load_models()

    def test_01_root_and_health(self):
        res = client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn("version", res.json())

        res = client.get("/health")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "healthy")

    def test_02_dashboard_aggregator(self):
        res = client.get("/dashboard?state=Andhra+Pradesh&district=Guntur")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertIn("kpi_cards", data)
        self.assertIn("satellite_health", data["kpi_cards"])
        self.assertIn("weather_alerts", data["kpi_cards"])

    def test_03_satellite_endpoints(self):
        res = client.get("/satellite?state=Andhra+Pradesh&district=Guntur")
        self.assertEqual(res.status_code, 200)
        sat = res.json()
        self.assertIn("ndvi", sat["indices"])
        self.assertIn("evi", sat["indices"])
        self.assertIn("vhi", sat["indices"])
        self.assertIn("spatial_raster", sat)

        res_ind = client.get("/satellite/indices?state=Gujarat&district=Amreli")
        self.assertEqual(res_ind.status_code, 200)

        res_ts = client.get("/satellite/timeseries?state=Punjab&district=Ludhiana")
        self.assertEqual(res_ts.status_code, 200)
        self.assertEqual(len(res_ts.json()["historical_timeseries"]), 12)

    def test_04_soil_endpoints(self):
        res = client.get("/soil?state=Andhra+Pradesh&district=Guntur")
        self.assertEqual(res.status_code, 200)
        self.assertIn("health_evaluation", res.json())

        soil_payload = {
            "state": "Maharashtra",
            "district": "Pune",
            "nitrogen": 210.0,
            "phosphorus": 14.0,
            "potassium": 260.0,
            "ph": 7.8,
            "organic_carbon": 0.52,
            "ec": 0.6,
            "moisture": 0.24,
            "zinc": 0.65,
            "iron": 4.5,
            "boron": 0.50,
            "sulphur": 10.0
        }
        res_analyze = client.post("/soil/analyze", json=soil_payload)
        self.assertEqual(res_analyze.status_code, 200)
        self.assertTrue(res_analyze.json()["success"])

        res_fert = client.post("/soil/recommend-fertilizer", json={"crop": "Cotton", "area_acres": 4.0})
        self.assertEqual(res_fert.status_code, 200)
        self.assertIn("commercial_fertilizers_total", res_fert.json())

    def test_05_weather_endpoints(self):
        res = client.get("/weather?state=Andhra+Pradesh&district=Guntur")
        self.assertEqual(res.status_code, 200)
        w = res.json()
        self.assertIn("current_weather", w)
        self.assertIn("forecast_7_day", w)
        self.assertEqual(len(w["forecast_7_day"]), 7)

        res_et0 = client.get("/weather/et0?temp_c=30.0&temp_min_c=24.0&temp_max_c=36.0&humidity_percent=60.0&wind_speed_kmh=10.0")
        self.assertEqual(res_et0.status_code, 200)
        self.assertTrue(res_et0.json()["evapotranspiration_et0_mm_per_day"] > 0)

    def test_06_recommendation_endpoints(self):
        payload = {
            "Crop": "Rice",
            "State": "Andhra Pradesh",
            "District": "Guntur",
            "Season": "Kharif",
            "Crop_Year": 2024,
            "Area": 5.0,
            "Grade": "FAQ"
        }
        res = client.post("/recommendation", json=payload)
        self.assertEqual(res.status_code, 200)
        rec = res.json()
        self.assertTrue(rec["success"])
        self.assertIn("quantum_predictions", rec)
        self.assertIn("economic_financial_outlook", rec)
        self.assertTrue(rec["economic_financial_outlook"]["net_expected_profit_inr"] != 0)

        res_suit = client.get("/recommendation/crop-suitability?state=Andhra+Pradesh&season=Kharif")
        self.assertEqual(res_suit.status_code, 200)
        self.assertTrue(len(res_suit.json()["ranked_crops"]) > 0)

    def test_07_plot_endpoints(self):
        # 1. Create a new plot
        plot_data = {
            "name": "Krishna Delta Farm Plot 1",
            "crop_type": "Rice",
            "area_acres": 8.5,
            "soil_type": "Clay Loam",
            "center_lat": 16.3067,
            "center_lon": 80.4365,
            "boundary_geojson": '{"type": "Polygon", "coordinates": [[[80.430, 16.300], [80.435, 16.300], [80.435, 16.305], [80.430, 16.305], [80.430, 16.300]]]}'
        }
        res_create = client.post("/plots", json=plot_data)
        self.assertEqual(res_create.status_code, 200)
        plot_obj = res_create.json()["plot"]
        plot_id = plot_obj["id"]

        # 2. List plots
        res_list = client.get("/plots")
        self.assertEqual(res_list.status_code, 200)
        self.assertTrue(res_list.json()["count"] >= 1)

        # 3. Analyze specific plot
        res_analyze = client.post(f"/plots/{plot_id}/analyze")
        self.assertEqual(res_analyze.status_code, 200)
        self.assertTrue(res_analyze.json()["success"])

        # 4. Direct plot analysis route (/plot-analysis)
        direct_payload = {
            "plot_name": "Direct Analysis Plot",
            "crop": "Cotton",
            "state": "Gujarat",
            "district": "Amreli",
            "area_acres": 12.0,
            "soil_type": "Black Soil"
        }
        res_direct = client.post("/plot-analysis", json=direct_payload)
        self.assertEqual(res_direct.status_code, 200)
        self.assertTrue(res_direct.json()["success"])

    def test_08_backward_compatibility_predictions(self):
        # Crop Yield Prediction
        yield_payload = {
            "Crop": "Rice",
            "Crop_Year": 2024,
            "Season": "Kharif",
            "State": "Andhra Pradesh",
            "District": "Guntur",
            "Area": 10.0,
            "Annual_Rainfall": None,
            "Fertilizer": 850.0,
            "Pesticide": 45.0
        }
        res_yield = client.post("/predict-yield", json=yield_payload)
        self.assertEqual(res_yield.status_code, 200)
        self.assertTrue(res_yield.json()["predicted_yield_per_acre"] > 0)

        # Commodity Price Forecast
        price_payload = {
            "State": "Gujarat",
            "District": "Amreli",
            "Market": "Damnagar",
            "Commodity": "Cotton",
            "Variety": "Other",
            "Grade": "FAQ",
            "Prediction_Date": "2026-08-22"
        }
        res_price = client.post("/predict-price", json=price_payload)
        self.assertEqual(res_price.status_code, 200)
        self.assertTrue(res_price.json()["predicted_price"] > 0)

    def test_09_quantum_circuit_and_options(self):
        res_circ = client.get("/quantum/circuit")
        self.assertEqual(res_circ.status_code, 200)
        self.assertIn("crop_yield_circuit", res_circ.json())

        res_opts = client.get("/yield-options")
        self.assertEqual(res_opts.status_code, 200)
        self.assertTrue(len(res_opts.json()["crops"]) > 0)

    def test_10_geocode_endpoint_districts(self):
        districts = [
            ("Andhra Pradesh", "Guntur"),
            ("Andhra Pradesh", "Prakasam"),
            ("Andhra Pradesh", "Krishna"),
            ("Andhra Pradesh", "Anakapalli"),
            ("Andhra Pradesh", "Visakhapatnam"),
            ("Telangana", "Hyderabad"),
            ("Karnataka", "Bengaluru"),
            ("Tamil Nadu", "Chennai")
        ]
        for state, dist in districts:
            res = client.get(f"/geocode?state={state}&district={dist}")
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertIn("latitude", data)
            self.assertIn("longitude", data)
            self.assertIsInstance(data["latitude"], (int, float))
            self.assertIsInstance(data["longitude"], (int, float))

        # Test invalid geocode 404
        res_inv = client.get("/geocode?state=InvalidStateXYZ&district=InvalidDist123")
        self.assertEqual(res_inv.status_code, 404)


class TestGeocodingModule(unittest.TestCase):
    """Unit Tests for Multi-tier Geocoding & Coordinate Resolution."""

    def test_resolve_curated_coordinates(self):
        from geocode_service import resolve_coordinates
        res = resolve_coordinates("Andhra Pradesh", "Prakasam")
        self.assertIsNotNone(res)
        lat, lon, source = res
        self.assertAlmostEqual(lat, 15.5057, places=2)
        self.assertAlmostEqual(lon, 80.0499, places=2)
        self.assertEqual(source, "curated_database")

    def test_resolve_anakapalli(self):
        from geocode_service import resolve_coordinates
        res = resolve_coordinates("Andhra Pradesh", "Anakapalli")
        self.assertIsNotNone(res)
        lat, lon, source = res
        self.assertAlmostEqual(lat, 17.6896, places=2)
        self.assertAlmostEqual(lon, 83.0033, places=2)

    def test_resolve_state_centroid(self):
        from geocode_service import resolve_coordinates
        res = resolve_coordinates("Kerala", None)
        self.assertIsNotNone(res)
        lat, lon, source = res
        self.assertAlmostEqual(lat, 10.8505, places=2)


def run_full_suite():
    print("=" * 80)
    print("RUNNING FULL TEST SUITE: QUANTUM PRECISION AGRICULTURE PLATFORM")
    print("=" * 80)
    suite = unittest.TestLoader().loadTestsFromNames([
        "test_suite.TestSatelliteModule",
        "test_suite.TestSoilModule",
        "test_suite.TestWeatherModule",
        "test_suite.TestRecommendationAndPlotModules",
        "test_suite.TestGeocodingModule",
        "test_suite.TestFastAPIEndToEndEndpoints",
    ])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    if result.wasSuccessful():
        print("\n" + "=" * 80)
        print("[SUCCESS] ALL TESTS PASSED! 100% PRODUCTION READY & COMPATIBLE.")
        print("=" * 80)
    else:
        print("\n" + "=" * 80)
        print("[FAIL] SOME TESTS FAILED")
        print("=" * 80)
        sys.exit(1)


if __name__ == "__main__":
    run_full_suite()
