"""
Hybrid Quantum-Classical Neural Network (HQNN) Architecture
Combines PyTorch classical feature encoders, Parameterized Variational Quantum Circuits (TorchLayer),
and classical post-processing heads with residual connections.
"""

from typing import Tuple, Dict, Any, Optional
import torch
import torch.nn as nn
import numpy as np

from quantum.feature_encoding import ClassicalToQuantumProjector
from quantum.quantum_layers import QuantumVariationalLayer


class HybridQuantumNeuralNetwork(nn.Module):
    """
    Hybrid Quantum-Classical Neural Network for Regression.

    Architecture:
    Classical Input (D_in) -> Classical Projector -> Quantum Encoding Angles (N_qubits, [0, pi])
                           -> Variational Quantum Circuit (Strongly Entangling Layers)
                           -> Quantum Readout: Pauli-Z Expectation Values (N_qubits, [-1, 1])
                           -> Post-Processing Dense Network + Residual Skip -> Output Prediction
    """

    def __init__(
        self,
        input_dim: int,
        n_qubits: int = 8,
        n_layers: int = 3,
        hidden_dim: int = 64,
        dropout: float = 0.1,
        dev_name: str = "default.qubit"
    ):
        super().__init__()
        self.input_dim = input_dim
        self.n_qubits = n_qubits
        self.n_layers = n_layers

        # 1. Classical Input Projection to Quantum Angles
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.BatchNorm1d(hidden_dim),
            nn.LeakyReLU(0.1),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, n_qubits),
            nn.Sigmoid()  # Maps to [0, 1]
        )

        # 2. Variational Quantum Layer (PennyLane + PyTorch)
        self.quantum_layer = QuantumVariationalLayer(
            n_qubits=n_qubits,
            n_layers=n_layers,
            dev_name=dev_name
        )

        # 3. Post-Quantum Classical Processing Head
        self.quantum_norm = nn.LayerNorm(n_qubits)
        self.head = nn.Sequential(
            nn.Linear(n_qubits * 2, hidden_dim),  # Fuses quantum readout + encoded angles
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 32),
            nn.GELU(),
            nn.Linear(32, 1)
        )

        # Residual skip connection from classical input
        self.skip = nn.Linear(input_dim, 1, bias=False)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """
        Forward pass through Hybrid QNN.
        Returns:
            prediction: (Batch, 1)
            telemetry: Dictionary of quantum metrics (angles, expectation values, entropy)
        """
        # Ensure 2D tensor
        if x.dim() == 1:
            x = x.unsqueeze(0)

        # Step 1: Classical encoding to [0, pi] angles
        angles = self.encoder(x) * np.pi  # Shape: (Batch, n_qubits)

        # Step 2: Variational Quantum Circuit Execution
        # Returns Pauli-Z expectation values in range [-1, 1]
        q_expvals = self.quantum_layer(angles)  # Shape: (Batch, n_qubits)
        q_norm = self.quantum_norm(q_expvals)

        # Step 3: Classical Fusion (Quantum Readout + Encoded Angles)
        fused = torch.cat([q_norm, angles / np.pi], dim=-1)
        q_out = self.head(fused)

        # Step 4: Residual connection
        residual = self.skip(x)
        prediction = q_out + residual

        # Calculate Quantum State Telemetry (State variance & confidence proxy)
        with torch.no_grad():
            expval_var = torch.var(q_expvals, dim=-1, unbiased=False)
            expval_mean = torch.mean(torch.abs(q_expvals), dim=-1)
            # Quantum Confidence Score: higher polarization and consistent variance -> higher score
            confidence = torch.clamp(
                (0.65 + 0.30 * expval_mean - 0.10 * expval_var) * 100.0,
                min=50.0,
                max=99.2
            )

        telemetry = {
            "quantum_angles": angles.detach().cpu().numpy().tolist(),
            "pauli_z_expectations": q_expvals.detach().cpu().numpy().tolist(),
            "quantum_confidence": confidence.detach().cpu().numpy().tolist(),
            "n_qubits": self.n_qubits,
            "n_layers": self.n_layers
        }

        return prediction, telemetry
