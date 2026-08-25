"""
Quantum Commodity Price Training Pipeline
Trains the Variational Quantum Regressor on historical mandi commodity arrival and price data.
Saves model checkpoint to models/crop_price_quantum.pkl.
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

from quantum.quantum_price_model import QuantumPriceForecastModel
from quantum.config import HYBRID_TRAIN_CFG, QUANTUM_CIRCUIT_CFG

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("train_price_quantum")


def load_and_engineer_price_data(csv_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Loads historical commodity prices and constructs temporal and lag time-series features.
    """
    if csv_path is None:
        csv_path = BASE_DIR / "data" / "commodity_price.csv"

    df = pd.read_csv(csv_path)

    # Standardize column naming
    rename_dict = {
        "District Name": "District",
        "Market Name": "Market",
        "Modal Price (Rs./Quintal)": "Modal_Price",
        "Modal_x0020_Price": "Modal_Price",
        "Min Price (Rs./Quintal)": "Min_Price",
        "Min_x0020_Price": "Min_Price",
        "Max Price (Rs./Quintal)": "Max_Price",
        "Max_x0020_Price": "Max_Price",
        "Price Date": "Arrival_Date"
    }
    df = df.rename(columns=rename_dict)
    df = df.drop(columns=["Sl no."], errors="ignore")

    # Date parsing and cleaning
    df["Arrival_Date"] = pd.to_datetime(df["Arrival_Date"], dayfirst=True, errors="coerce")
    df["Modal_Price"] = pd.to_numeric(df["Modal_Price"], errors="coerce")
    df = df.dropna(subset=["Arrival_Date", "Modal_Price"])
    df = df[df["Modal_Price"] > 0].copy()
    df = df.sort_values(["Commodity", "Market", "Arrival_Date"]).reset_index(drop=True)

    # Time & Calendar features
    df["Year"] = df["Arrival_Date"].dt.year
    df["Month"] = df["Arrival_Date"].dt.month
    df["Day"] = df["Arrival_Date"].dt.day
    df["DayOfWeek"] = df["Arrival_Date"].dt.dayofweek

    # Feature Engineering: Lag 1, Lag 7, and Rolling Mean 7
    df["Price_Lag_1"] = df.groupby(["Commodity", "Market"])["Modal_Price"].shift(1)
    df["Price_Lag_7"] = df.groupby(["Commodity", "Market"])["Modal_Price"].shift(7)
    df["Rolling_Mean_7"] = df.groupby(["Commodity", "Market"])["Modal_Price"].transform(lambda s: s.shift(1).rolling(7, min_periods=1).mean())

    # Impute missing lags with commodity-wide or row baseline
    df["Price_Lag_1"] = df["Price_Lag_1"].fillna(df["Modal_Price"])
    df["Price_Lag_7"] = df["Price_Lag_7"].fillna(df["Price_Lag_1"])
    df["Rolling_Mean_7"] = df["Rolling_Mean_7"].fillna(df["Price_Lag_1"])

    return df


def train_price_quantum(
    csv_path: Optional[Path] = None,
    save_path: Optional[str] = None,
    epochs: int = HYBRID_TRAIN_CFG.epochs,
    batch_size: int = HYBRID_TRAIN_CFG.batch_size,
    learning_rate: float = HYBRID_TRAIN_CFG.learning_rate
) -> Dict[str, Any]:
    """
    Executes training of the Variational Quantum Regressor for Commodity Price Prediction.
    """
    logger.info("Initializing Quantum Commodity Price Training Pipeline...")

    df = load_and_engineer_price_data(csv_path)
    logger.info(f"Loaded and engineered {len(df)} commodity market records.")

    # Target variable
    y = df["Modal_Price"].values

    # Feature dataframe
    features_df = df[[
        "State", "District", "Market", "Commodity", "Variety", "Grade",
        "Year", "Month", "Day", "DayOfWeek", "Price_Lag_1", "Price_Lag_7", "Rolling_Mean_7"
    ]].copy()

    # Instantiate Quantum Price Model
    model = QuantumPriceForecastModel(
        n_qubits=QUANTUM_CIRCUIT_CFG.n_qubits_price,
        n_layers=QUANTUM_CIRCUIT_CFG.n_layers_price
    )

    X_trans, y_trans = model.fit_preprocessing(features_df, y)

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

    criterion = nn.SmoothL1Loss()
    optimizer = torch.optim.Adam(model.qnn.parameters(), lr=learning_rate, weight_decay=HYBRID_TRAIN_CFG.weight_decay)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="min", factor=HYBRID_TRAIN_CFG.lr_scheduler_factor, patience=HYBRID_TRAIN_CFG.lr_scheduler_patience
    )

    best_val_loss = float("inf")
    best_weights = None
    patience_counter = 0

    history = {"train_loss": [], "val_loss": [], "val_mae": []}

    logger.info(f"Starting QNN optimization for {epochs} epochs on {len(X_train)} price records...")
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

        # Unscale for MAE calculation
        val_preds_flat = np.concatenate(val_preds_list).flatten()
        val_targets_flat = np.concatenate(val_targets_list).flatten()
        val_preds_orig = model.target_scaler.inverse_transform(val_preds_flat.reshape(-1, 1)).flatten()
        val_targets_orig = model.target_scaler.inverse_transform(val_targets_flat.reshape(-1, 1)).flatten()
        epoch_val_mae = float(mean_absolute_error(val_targets_orig, val_preds_orig))

        history["train_loss"].append(round(epoch_train_loss, 4))
        history["val_loss"].append(round(epoch_val_loss, 4))
        history["val_mae"].append(round(epoch_val_mae, 2))

        if epoch % 5 == 0 or epoch == 1:
            logger.info(f"Epoch [{epoch:02d}/{epochs}] - Train Loss: {epoch_train_loss:.4f} | Val Loss: {epoch_val_loss:.4f} | Val MAE: ₹{epoch_val_mae:.2f}/Qtl")

        # Early Stopping
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
    final_preds = model.predict(features_df)
    final_rmse = float(np.sqrt(mean_squared_error(y, final_preds)))
    final_mae = float(mean_absolute_error(y, final_preds))
    final_r2 = float(r2_score(y, final_preds))

    logger.info(f"[Training Complete] Final Quantum Price Model Metrics -> RMSE: ₹{final_rmse:.2f}, MAE: ₹{final_mae:.2f}, R²: {final_r2:.3f}")

    # Serialize Model
    if save_path is None:
        save_path = BASE_DIR / "models" / "crop_price_quantum.pkl"
    save_path = Path(save_path)
    save_path.parent.mkdir(parents=True, exist_ok=True)

    joblib.dump(model, save_path)
    logger.info(f"[SUCCESS] Quantum Commodity Price Model saved to: {save_path}")

    return {
        "status": "success",
        "model_type": "Variational Quantum Regressor (VQR)",
        "n_qubits": model.n_qubits,
        "n_layers": model.n_layers,
        "final_rmse": round(final_rmse, 2),
        "final_mae": round(final_mae, 2),
        "final_r2": round(final_r2, 3),
        "training_history": history,
        "saved_path": str(save_path)
    }


if __name__ == "__main__":
    train_price_quantum()
