"""
Quantum Crop Yield Prediction Model
Implements a Hybrid Quantum-Classical Neural Network (HQNN) for agricultural crop yield regression.
"""

from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer

from quantum.hybrid_qnn import HybridQuantumNeuralNetwork
from quantum.quantum_utils import compute_quantum_confidence, compute_quantum_explainability, get_circuit_metadata
from quantum.config import QUANTUM_CIRCUIT_CFG, HYBRID_TRAIN_CFG


class QuantumCropYieldModel:
    """
    Production Hybrid Quantum Machine Learning Model for Crop Yield Prediction.
    
    Inputs:
    - Categorical: Crop, Season, State
    - Numerical: Crop_Year, Area, Annual_Rainfall, Fertilizer, Pesticide, [NDVI, EVI, Soil_Moisture, LST]
    - Output: Predicted Yield (Metric Tons per Hectare / Acre)
    """

    CATEGORICAL_FEATURES = ["Crop", "Season", "State"]
    NUMERICAL_FEATURES = ["Crop_Year", "Area", "Annual_Rainfall", "Fertilizer", "Pesticide"]
    SATELLITE_FEATURES = ["ndvi", "evi", "soil_moisture", "lst_c"]

    def __init__(
        self,
        n_qubits: int = QUANTUM_CIRCUIT_CFG.n_qubits_yield,
        n_layers: int = QUANTUM_CIRCUIT_CFG.n_layers_yield,
        dev_name: str = "default.qubit"
    ):
        self.n_qubits = n_qubits
        self.n_layers = n_layers
        self.dev_name = dev_name

        self.preprocessor: Optional[ColumnTransformer] = None
        self.target_scaler = StandardScaler()
        self.qnn: Optional[HybridQuantumNeuralNetwork] = None
        self.feature_names: List[str] = []
        self.is_trained: bool = False
        self.training_history: Dict[str, List[float]] = {"train_loss": [], "val_loss": [], "val_mae": []}

    def _build_preprocessor(self, df: pd.DataFrame) -> ColumnTransformer:
        """Constructs Scikit-learn ColumnTransformer for categorical and numerical features."""
        # Detect which features are present in the dataframe
        cat_cols = [c for c in self.CATEGORICAL_FEATURES if c in df.columns]
        num_cols = [c for c in self.NUMERICAL_FEATURES if c in df.columns]
        sat_cols = [c for c in self.SATELLITE_FEATURES if c in df.columns]
        all_num = num_cols + sat_cols

        transformers = []
        if cat_cols:
            transformers.append(
                ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cat_cols)
            )
        if all_num:
            transformers.append(
                ("num", StandardScaler(), all_num)
            )

        return ColumnTransformer(transformers=transformers, remainder="drop")

    def fit_preprocessing(self, df: pd.DataFrame, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Fits preprocessor and target scaler, returning transformed tensors."""
        self.preprocessor = self._build_preprocessor(df)
        X_trans = self.preprocessor.fit_transform(df)
        
        # Fit target scaler
        y_arr = np.asarray(y, dtype=np.float32).reshape(-1, 1)
        y_trans = self.target_scaler.fit_transform(y_arr).flatten()

        # Extract feature names
        cat_names = []
        if "cat" in self.preprocessor.named_transformers_:
            encoder = self.preprocessor.named_transformers_["cat"]
            cat_names = list(encoder.get_feature_names_out(self.CATEGORICAL_FEATURES))
        num_names = [c for c in self.NUMERICAL_FEATURES if c in df.columns] + [c for c in self.SATELLITE_FEATURES if c in df.columns]
        self.feature_names = cat_names + num_names

        # Initialize QNN with correct input dimension
        input_dim = X_trans.shape[1]
        self.qnn = HybridQuantumNeuralNetwork(
            input_dim=input_dim,
            n_qubits=self.n_qubits,
            n_layers=self.n_layers,
            dev_name=self.dev_name
        )

        return X_trans, y_trans

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        """
        Standard Scikit-learn style predict method returning yields in Tons/Hectare.
        """
        if self.qnn is None or self.preprocessor is None:
            raise ValueError("QuantumCropYieldModel is not initialized or trained.")

        self.qnn.eval()
        with torch.no_grad():
            X_trans = self.preprocessor.transform(df)
            X_tensor = torch.tensor(X_trans, dtype=torch.float32)
            preds_scaled, _ = self.qnn(X_tensor)
            preds = self.target_scaler.inverse_transform(preds_scaled.cpu().numpy()).flatten()
            return np.maximum(0.05, preds)

    def predict_detailed(self, df: pd.DataFrame, area_acres: float = 1.0) -> Dict[str, Any]:
        """
        Full quantum prediction pipeline with confidence, satellite telemetry, and explainability.
        """
        if self.qnn is None or self.preprocessor is None:
            raise ValueError("QuantumCropYieldModel is not trained.")

        self.qnn.eval()
        X_trans = self.preprocessor.transform(df)
        X_tensor = torch.tensor(X_trans, dtype=torch.float32)

        with torch.no_grad():
            pred_scaled, telemetry = self.qnn(X_tensor)
            pred_ha = float(self.target_scaler.inverse_transform(pred_scaled.cpu().numpy())[0][0])
            pred_ha = max(0.05, round(pred_ha, 3))

        # Acre conversion (1 Acre = 0.404686 Hectare)
        yield_per_acre = round(pred_ha * 0.404686, 2)
        total_production = round(yield_per_acre * area_acres, 2)

        # Quantum Confidence Score
        expvals = telemetry.get("pauli_z_expectations", [[]])[0]
        confidence_score = compute_quantum_confidence(expvals)

        # Quantum Feature Attribution Explainability
        explanations = compute_quantum_explainability(
            model=self.qnn,
            input_tensor=X_tensor,
            feature_names=self.feature_names
        )[:6]  # Top 6 features

        return {
            "success": True,
            "predicted_yield_per_ha": pred_ha,
            "predicted_yield_per_acre": yield_per_acre,
            "total_production_tons": total_production,
            "area_acres": area_acres,
            "quantum_confidence_score": confidence_score,
            "quantum_telemetry": {
                "n_qubits": self.n_qubits,
                "n_layers": self.n_layers,
                "pauli_z_expectations": [round(float(v), 3) for v in expvals],
                "circuit_depth": 1 + (self.n_layers * 2) + 1
            },
            "explainability": explanations
        }

    def get_circuit_info(self) -> Dict[str, Any]:
        """Returns quantum circuit properties and diagram."""
        return get_circuit_metadata(self.n_qubits, self.n_layers)

    def __getstate__(self) -> Dict[str, Any]:
        """Custom serialization to cleanly pickle state without QNode closure objects."""
        return {
            "n_qubits": self.n_qubits,
            "n_layers": self.n_layers,
            "dev_name": self.dev_name,
            "preprocessor": self.preprocessor,
            "target_scaler": self.target_scaler,
            "feature_names": self.feature_names,
            "is_trained": self.is_trained,
            "training_history": self.training_history,
            "input_dim": self.qnn.input_dim if self.qnn else None,
            "qnn_state_dict": self.qnn.state_dict() if self.qnn else None
        }

    def __setstate__(self, state: Dict[str, Any]) -> None:
        """Custom deserialization restoring QNN architecture and trained weights."""
        self.n_qubits = state["n_qubits"]
        self.n_layers = state["n_layers"]
        self.dev_name = state["dev_name"]
        self.preprocessor = state["preprocessor"]
        self.target_scaler = state["target_scaler"]
        self.feature_names = state["feature_names"]
        self.is_trained = state["is_trained"]
        self.training_history = state["training_history"]

        if state.get("input_dim") is not None and state.get("qnn_state_dict") is not None:
            self.qnn = HybridQuantumNeuralNetwork(
                input_dim=state["input_dim"],
                n_qubits=self.n_qubits,
                n_layers=self.n_layers,
                dev_name=self.dev_name
            )
            self.qnn.load_state_dict(state["qnn_state_dict"])
        else:
            self.qnn = None

    def save(self, filepath: str) -> None:
        """Saves model instance to file."""
        import joblib
        joblib.dump(self, filepath)

    @classmethod
    def load(cls, filepath: str) -> "QuantumCropYieldModel":
        """Loads model instance from file."""
        import joblib
        return joblib.load(filepath)
