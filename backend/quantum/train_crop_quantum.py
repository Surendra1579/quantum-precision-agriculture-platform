"""
Quantum Crop Yield Training Pipeline
Trains the Hybrid Quantum-Classical Neural Network on agricultural and satellite features.
Saves model checkpoint to models/crop_yield_quantum.pkl.
"""

import sys
from pathlib import Path

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import os
from typing import Optional, List, Dict, Any, Tuple
import joblib
import logging
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

from quantum.quantum_crop_model import QuantumCropYieldModel
from quantum.config import HYBRID_TRAIN_CFG, QUANTUM_CIRCUIT_CFG
from satellite_service import AGRO_ECOLOGICAL_BASELINES

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("train_crop_quantum")


def generate_comprehensive_crop_data(n_samples: int = 1500) -> pd.DataFrame:
    """
    Generates a realistic multi-state, multi-crop agricultural dataset
    aligned with ICAR Indian Agricultural Statistics standards covering all Indian States.
    """
    np.random.seed(42)

    try:
        from main import ALL_STATE_DISTRICTS
        states_districts = ALL_STATE_DISTRICTS
    except ImportError:
        states_districts = {
            "Andhra Pradesh": ["Guntur", "Krishna", "Eluru", "East Godavari", "West Godavari", "Kurnool", "Anantapur"],
            "Telangana": ["Warangal", "Karimnagar", "Nizamabad", "Khammam", "Nalgonda"],
            "Tamil Nadu": ["Coimbatore", "Madurai", "Salem", "Erode", "Thanjavur"],
            "Karnataka": ["Belagavi", "Mysuru", "Mandya", "Dharwad", "Haveri"],
            "Maharashtra": ["Pune", "Nashik", "Nagpur", "Ahmednagar", "Kolhapur", "Solapur"],
            "Gujarat": ["Amreli", "Anand", "Rajkot", "Surat", "Bhavnagar"],
            "Punjab": ["Ludhiana", "Amritsar", "Jalandhar", "Patiala", "Bathinda"],
            "Uttar Pradesh": ["Lucknow", "Kanpur", "Varanasi", "Meerut", "Agra"],
            "Rajasthan": ["Jaipur", "Jodhpur", "Kota", "Bikaner", "Ajmer", "Udaipur"],
            "Madhya Pradesh": ["Indore", "Bhopal", "Jabalpur", "Gwalior", "Ujjain"],
            "West Bengal": ["Kolkata", "Hooghly", "Murshidabad", "Burdwan", "Nadia"],
            "Bihar": ["Patna", "Gaya", "Muzaffarpur", "Bhagalpur", "Darbhanga"],
            "Haryana": ["Karnal", "Hisar", "Ambala", "Rohtak", "Sirsa"],
            "Kerala": ["Palakkad", "Alappuzha", "Ernakulam", "Thrissur", "Wayanad"],
            "Odisha": ["Cuttack", "Sambalpur", "Puri", "Balasore", "Ganjam"],
            "Assam": ["Kamrup", "Dibrugarh", "Jorhat", "Nagaon", "Cachar"],
            "Uttarakhand": ["Dehradun", "Haridwar", "Nainital", "Udham Singh Nagar"]
        }

    crops = ["Rice", "Wheat", "Maize", "Cotton", "Sugarcane", "Groundnut", "Pulses", "Soyabean", "Tomato", "Chilli", "Onion"]
    seasons = ["Kharif", "Rabi", "Whole Year", "Summer", "Autumn", "Winter"]

    # Base yield rates (Tons per Hectare)
    crop_base_yield = {
        "Rice": 3.8, "Wheat": 3.4, "Maize": 3.2, "Cotton": 2.4,
        "Sugarcane": 72.0, "Groundnut": 2.1, "Pulses": 1.1,
        "Soyabean": 2.2, "Tomato": 24.5, "Chilli": 2.8, "Onion": 18.0
    }

    data = []
    for _ in range(n_samples):
        st = np.random.choice(list(states_districts.keys()))
        dist = np.random.choice(states_districts[st])
        crop = np.random.choice(crops)
        season = np.random.choice(seasons)
        year = int(np.random.randint(2015, 2025))

        area_ha = round(float(np.random.uniform(0.5, 45.0)), 2)
        base_rain = 950.0 if st in ["Andhra Pradesh", "Telangana", "Tamil Nadu", "Karnataka"] else (750.0 if st in ["Maharashtra", "Gujarat"] else 650.0)
        rainfall = round(float(np.random.normal(base_rain, 180.0)), 1)
        rainfall = max(250.0, min(2800.0, rainfall))

        fertilizer = round(float(area_ha * np.random.uniform(80.0, 160.0)), 1)
        pesticide = round(float(area_ha * np.random.uniform(2.5, 8.0)), 1)

        # Baseline satellite indices
        base_sat = AGRO_ECOLOGICAL_BASELINES.get(st.upper(), AGRO_ECOLOGICAL_BASELINES["DEFAULT"])
        ndvi = round(float(base_sat["ndvi"] + np.random.uniform(-0.08, 0.08)), 3)
        evi = round(float(base_sat["evi"] + np.random.uniform(-0.06, 0.06)), 3)
        soil_moist = round(float(base_sat["soil_moisture"] + np.random.uniform(-0.05, 0.05)), 3)
        lst_c = round(float(base_sat["lst_c"] + np.random.uniform(-2.0, 2.0)), 1)

        # Calculate ground truth yield with realistic agro-climatic non-linearities
        base = crop_base_yield.get(crop, 3.0)
        rain_factor = min(1.25, max(0.75, rainfall / base_rain))
        fert_factor = min(1.2, max(0.8, (fertilizer / (area_ha * 120.0))))
        ndvi_factor = min(1.25, max(0.8, ndvi / 0.60))
        noise = np.random.normal(0, 0.08 * base)

        yield_val = max(0.2, round((base * rain_factor * fert_factor * ndvi_factor) + noise, 3))

        data.append({
            "Crop": crop,
            "Season": season,
            "State": st,
            "District": dist,
            "Crop_Year": year,
            "Area": area_ha,
            "Annual_Rainfall": rainfall,
            "Fertilizer": fertilizer,
            "Pesticide": pesticide,
            "ndvi": ndvi,
            "evi": evi,
            "soil_moisture": soil_moist,
            "lst_c": lst_c,
            "Yield": yield_val
        })

    return pd.DataFrame(data)


def train_crop_yield_quantum(
    data_df: Optional[pd.DataFrame] = None,
    save_path: Optional[str] = None,
    epochs: int = HYBRID_TRAIN_CFG.epochs,
    batch_size: int = HYBRID_TRAIN_CFG.batch_size,
    learning_rate: float = HYBRID_TRAIN_CFG.learning_rate
) -> Dict[str, Any]:
    """
    Executes training of the Hybrid Quantum Crop Yield Model.
    """
    logger.info("Initializing Quantum Crop Yield Training Pipeline...")

    if data_df is None:
        logger.info("Generating synthetic agro-climatic dataset for Quantum Yield training...")
        data_df = generate_comprehensive_crop_data(n_samples=1000)

    # Instantiate Quantum Crop Model
    model = QuantumCropYieldModel(
        n_qubits=QUANTUM_CIRCUIT_CFG.n_qubits_yield,
        n_layers=QUANTUM_CIRCUIT_CFG.n_layers_yield
    )

    X_df = data_df.drop(columns=["Yield", "District"], errors="ignore")
    y = data_df["Yield"].values

    # Preprocessing and initial QNN construction
    X_trans, y_trans = model.fit_preprocessing(X_df, y)

    # Train / Validation Split
    X_train, X_val, y_train, y_val = train_test_split(
        X_trans, y_trans,
        test_size=HYBRID_TRAIN_CFG.val_split,
        random_state=HYBRID_TRAIN_CFG.random_seed
    )

    train_dataset = TensorDataset(torch.tensor(X_train, dtype=torch.float32), torch.tensor(y_train, dtype=torch.float32).unsqueeze(1))
    val_dataset = TensorDataset(torch.tensor(X_val, dtype=torch.float32), torch.tensor(y_val, dtype=torch.float32).unsqueeze(1))

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

    # Optimizer, Loss, and Scheduler
    criterion = nn.SmoothL1Loss()
    optimizer = torch.optim.Adam(model.qnn.parameters(), lr=learning_rate, weight_decay=HYBRID_TRAIN_CFG.weight_decay)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="min", factor=HYBRID_TRAIN_CFG.lr_scheduler_factor, patience=HYBRID_TRAIN_CFG.lr_scheduler_patience
    )

    best_val_loss = float("inf")
    best_weights = None
    patience_counter = 0

    history = {"train_loss": [], "val_loss": [], "val_mae": []}

    logger.info(f"Starting QNN optimization for {epochs} epochs on {len(X_train)} samples...")
    for epoch in range(1, epochs + 1):
        model.qnn.train()
        running_loss = 0.0

        for batch_x, batch_y in train_loader:
            optimizer.zero_grad()
            preds, _ = model.qnn(batch_x)
            loss = criterion(preds, batch_y)
            loss.backward()
            optimizer.step()
            running_loss += loss.item() * len(batch_x)

        epoch_train_loss = running_loss / len(X_train)

        # Validation
        model.qnn.eval()
        val_running_loss = 0.0
        val_preds_list, val_targets_list = [], []

        with torch.no_grad():
            for val_x, val_y in val_loader:
                v_preds, _ = model.qnn(val_x)
                v_loss = criterion(v_preds, val_y)
                val_running_loss += v_loss.item() * len(val_x)
                val_preds_list.append(v_preds.cpu().numpy())
                val_targets_list.append(val_y.cpu().numpy())

        epoch_val_loss = val_running_loss / len(X_val)
        scheduler.step(epoch_val_loss)

        # Unscale for true MAE metric
        val_preds_flat = np.concatenate(val_preds_list).flatten()
        val_targets_flat = np.concatenate(val_targets_list).flatten()
        val_preds_orig = model.target_scaler.inverse_transform(val_preds_flat.reshape(-1, 1)).flatten()
        val_targets_orig = model.target_scaler.inverse_transform(val_targets_flat.reshape(-1, 1)).flatten()
        epoch_val_mae = float(mean_absolute_error(val_targets_orig, val_preds_orig))

        history["train_loss"].append(round(epoch_train_loss, 4))
        history["val_loss"].append(round(epoch_val_loss, 4))
        history["val_mae"].append(round(epoch_val_mae, 4))

        if epoch % 5 == 0 or epoch == 1:
            logger.info(f"Epoch [{epoch:02d}/{epochs}] - Train Loss: {epoch_train_loss:.4f} | Val Loss: {epoch_val_loss:.4f} | Val MAE: {epoch_val_mae:.3f} t/ha")

        # Early Stopping check
        if epoch_val_loss < best_val_loss:
            best_val_loss = epoch_val_loss
            best_weights = model.qnn.state_dict()
            patience_counter = 0
        else:
            patience_counter += 1
            if patience_counter >= HYBRID_TRAIN_CFG.early_stopping_patience:
                logger.info(f"Early stopping triggered at epoch {epoch}.")
                break

    # Restore best weights
    if best_weights is not None:
        model.qnn.load_state_dict(best_weights)

    model.is_trained = True
    model.training_history = history

    # Evaluate final metrics
    final_preds = model.predict(X_df.iloc[:len(y)])
    final_rmse = float(np.sqrt(mean_squared_error(y, final_preds)))
    final_mae = float(mean_absolute_error(y, final_preds))
    final_r2 = float(r2_score(y, final_preds))

    logger.info(f"[Training Complete] Final Quantum Yield Model Metrics -> RMSE: {final_rmse:.3f}, MAE: {final_mae:.3f}, R²: {final_r2:.3f}")

    # Serialize Model
    if save_path is None:
        save_path = BASE_DIR / "models" / "crop_yield_quantum.pkl"
    save_path = Path(save_path)
    save_path.parent.mkdir(parents=True, exist_ok=True)

    joblib.dump(model, save_path)
    logger.info(f"[SUCCESS] Quantum Crop Yield Model saved to: {save_path}")

    return {
        "status": "success",
        "model_type": "Hybrid Quantum-Classical Neural Network (HQNN)",
        "n_qubits": model.n_qubits,
        "n_layers": model.n_layers,
        "final_rmse": round(final_rmse, 3),
        "final_mae": round(final_mae, 3),
        "final_r2": round(final_r2, 3),
        "training_history": history,
        "saved_path": str(save_path)
    }


if __name__ == "__main__":
    train_crop_yield_quantum()
