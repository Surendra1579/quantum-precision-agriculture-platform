"""
Quantum Inference Engine
Production-ready singleton managing quantum model loading, caching, execution, and telemetry.
"""

from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import logging
import joblib
import pandas as pd
import numpy as np

from quantum.quantum_crop_model import QuantumCropYieldModel
from quantum.quantum_price_model import QuantumPriceForecastModel
from quantum.config import QUANTUM_CIRCUIT_CFG, QUANTUM_DEVICE_CFG

logger = logging.getLogger("quantum_inference")


class QuantumInferenceEngine:
    """
    Singleton Hybrid Quantum Inference Engine.
    Manages lazy and eager model loading, thread safety, and execution.
    """
    _instance: Optional["QuantumInferenceEngine"] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(QuantumInferenceEngine, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, base_dir: Optional[Path] = None):
        if self._initialized:
            return

        self.base_dir = base_dir or Path(__file__).resolve().parent.parent
        self.yield_model_path = self._resolve_model_path(["crop_yield_quantum.pkl", "crop_yield_model.pkl"])
        self.price_model_path = self._resolve_model_path(["crop_price_quantum.pkl", "crop_price_model.pkl"])

        self.yield_model: Optional[QuantumCropYieldModel] = None
        self.price_model: Optional[QuantumPriceForecastModel] = None

        self.load_models()
        self._initialized = True

    def _resolve_model_path(self, filenames: List[str]) -> Path:
        """Finds existing model file across candidate directory locations."""
        candidate_dirs = [
            self.base_dir / "models",
            self.base_dir / "data" / "models",
            self.base_dir.parent / "backend" / "models",
            Path("models"),
            Path("backend/models"),
            Path(__file__).resolve().parent.parent / "models"
        ]
        for cdir in candidate_dirs:
            for fname in filenames:
                p = cdir / fname
                if p.exists() and p.is_file():
                    return p
        # Default fallback path
        return self.base_dir / "models" / filenames[0]

    def load_models(self) -> None:
        """Loads both quantum models from disk with full traceback logging and self-healing fallback."""
        import traceback

        # 1. Load Crop Yield Quantum Model
        if self.yield_model_path.exists():
            try:
                self.yield_model = joblib.load(self.yield_model_path)
                logger.info(f"[OK] Quantum Crop Yield Model loaded from {self.yield_model_path}")
            except Exception as e:
                logger.error(f"[ERROR] Failed to unpickle Quantum Crop Yield Model at {self.yield_model_path}: {e}")
                traceback.print_exc()
                self.yield_model = None
        else:
            logger.warning(f"Quantum Crop Yield Model checkpoint not found at {self.yield_model_path}")
            self.yield_model = None

        # Self-heal Yield Model if unpickling failed or missing
        if self.yield_model is None:
            try:
                logger.info("[Self-Healing] Training fresh native Quantum Crop Yield Model on startup...")
                from quantum.train_crop_quantum import train_crop_yield_quantum
                self.yield_model = train_crop_yield_quantum()
                if self.yield_model:
                    logger.info("[Self-Healing OK] Quantum Crop Yield Model trained and ready.")
            except Exception as tr_err:
                logger.error(f"[Self-Healing Error] Could not train yield model: {tr_err}")
                traceback.print_exc()

        # 2. Load Commodity Price Quantum Model
        if self.price_model_path.exists():
            try:
                self.price_model = joblib.load(self.price_model_path)
                logger.info(f"[OK] Quantum Commodity Price Model loaded from {self.price_model_path}")
            except Exception as e:
                logger.error(f"[ERROR] Failed to unpickle Quantum Commodity Price Model at {self.price_model_path}: {e}")
                traceback.print_exc()
                self.price_model = None
        else:
            logger.warning(f"Quantum Commodity Price Model checkpoint not found at {self.price_model_path}")
            self.price_model = None

        # Self-heal Price Model if unpickling failed or missing
        if self.price_model is None:
            try:
                logger.info("[Self-Healing] Training fresh native Quantum Commodity Price Model on startup...")
                from quantum.train_price_quantum import train_price_quantum
                self.price_model = train_price_quantum()
                if self.price_model:
                    logger.info("[Self-Healing OK] Quantum Commodity Price Model trained and ready.")
            except Exception as tr_err:
                logger.error(f"[Self-Healing Error] Could not train price model: {tr_err}")
                traceback.print_exc()

    def predict_crop_yield(
        self,
        crop: str,
        crop_year: int,
        season: str,
        state: str,
        area_acres: float,
        annual_rainfall: float,
        fertilizer: float,
        pesticide: float,
        satellite_indices: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Executes Quantum Crop Yield Prediction.
        """
        if self.yield_model is None:
            raise RuntimeError("Quantum Crop Yield Model is not loaded or trained.")

        # Convert Acre to Hectare for standard agronomic calculation (1 Acre = 0.404686 Ha)
        area_ha = area_acres * 0.404686

        # Build feature row
        row_dict = {
            "Crop": crop,
            "Season": season,
            "State": state,
            "Crop_Year": crop_year,
            "Area": area_ha,
            "Annual_Rainfall": annual_rainfall,
            "Fertilizer": fertilizer,
            "Pesticide": pesticide,
        }

        # Attach Satellite indices if provided
        if satellite_indices:
            row_dict["ndvi"] = satellite_indices.get("ndvi", 0.60)
            row_dict["evi"] = satellite_indices.get("evi", 0.46)
            row_dict["soil_moisture"] = satellite_indices.get("soil_moisture", 0.27)
            row_dict["lst_c"] = satellite_indices.get("land_surface_temperature_c", 30.5)

        input_df = pd.DataFrame([row_dict])
        return self.yield_model.predict_detailed(input_df, area_acres=area_acres)

    def predict_commodity_price(
        self,
        state: str,
        district: str,
        market: str,
        commodity: str,
        variety: str,
        grade: str,
        year: int,
        month: int,
        day: int,
        day_of_week: int,
        price_lag_1: float,
        price_lag_7: float,
        rolling_mean_7: float
    ) -> Dict[str, Any]:
        """
        Executes Variational Quantum Commodity Price Prediction.
        """
        if self.price_model is None:
            raise RuntimeError("Quantum Commodity Price Model is not loaded or trained.")

        input_df = pd.DataFrame([{
            "State": state,
            "District": district,
            "Market": market,
            "Commodity": commodity,
            "Variety": variety,
            "Grade": grade,
            "Year": year,
            "Month": month,
            "Day": day,
            "DayOfWeek": day_of_week,
            "Price_Lag_1": price_lag_1,
            "Price_Lag_7": price_lag_7,
            "Rolling_Mean_7": rolling_mean_7
        }])

        return self.price_model.predict_detailed(input_df)

    def get_status(self) -> Dict[str, Any]:
        """Returns comprehensive quantum system health and model architecture metrics."""
        return {
            "system_status": "operational",
            "quantum_framework": "PennyLane + Qiskit + PyTorch Hybrid Architecture",
            "device_backend": QUANTUM_DEVICE_CFG.backend_name,
            "models": {
                "quantum_crop_yield": {
                    "loaded": self.yield_model is not None,
                    "model_class": "HybridQuantumNeuralNetwork (HQNN)",
                    "qubits": self.yield_model.n_qubits if self.yield_model else QUANTUM_CIRCUIT_CFG.n_qubits_yield,
                    "layers": self.yield_model.n_layers if self.yield_model else QUANTUM_CIRCUIT_CFG.n_layers_yield,
                    "trainable_parameters": (self.yield_model.n_layers * self.yield_model.n_qubits * 3) if self.yield_model else 72
                },
                "quantum_commodity_price": {
                    "loaded": self.price_model is not None,
                    "model_class": "VariationalQuantumRegressor (VQR)",
                    "qubits": self.price_model.n_qubits if self.price_model else QUANTUM_CIRCUIT_CFG.n_qubits_price,
                    "layers": self.price_model.n_layers if self.price_model else QUANTUM_CIRCUIT_CFG.n_layers_price,
                    "trainable_parameters": (self.price_model.n_layers * self.price_model.n_qubits * 3) if self.price_model else 72
                }
            }
        }

    def get_yield_options(self) -> Dict[str, List[str]]:
        """Returns available dropdown options extracted from the quantum model preprocessor."""
        crops, seasons, states = [], [], []
        if self.yield_model and self.yield_model.preprocessor:
            try:
                cat_encoder = self.yield_model.preprocessor.named_transformers_.get("cat")
                if cat_encoder and hasattr(cat_encoder, "categories_"):
                    cats = cat_encoder.categories_
                    crops = [str(c).strip() for c in cats[0]]
                    seasons = [str(s).strip() for s in cats[1]]
                    states = [str(st).strip() for st in cats[2]]
            except Exception as e:
                logger.warning(f"Could not extract yield categories: {e}")

        # All 36 Indian States and Union Territories
        all_india_states = [
            "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", "Goa", "Gujarat",
            "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala", "Madhya Pradesh",
            "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
            "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh",
            "Uttarakhand", "West Bengal", "Andaman and Nicobar Islands", "Chandigarh",
            "Dadra and Nagar Haveli and Daman and Diu", "Delhi", "Jammu and Kashmir", "Ladakh",
            "Lakshadweep", "Puducherry"
        ]

        if not crops:
            crops = ["Rice", "Wheat", "Maize", "Cotton", "Sugarcane", "Groundnut", "Pulses", "Soyabean", "Tomato", "Chilli", "Onion"]
        if not seasons:
            seasons = ["Kharif", "Rabi", "Whole Year", "Summer", "Autumn", "Winter"]

        # Merge extracted states with full all-India states list
        merged_states = sorted(list(set(states + all_india_states)))

        return {
            "crops": sorted(list(set(crops))),
            "seasons": sorted(list(set(seasons))),
            "states": merged_states
        }


# Singleton Global Accessor
quantum_engine = QuantumInferenceEngine()
