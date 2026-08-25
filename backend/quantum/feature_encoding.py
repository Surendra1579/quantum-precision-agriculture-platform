"""
Quantum Feature Encoding Module
Provides AngleEmbedding, AmplitudeEmbedding, scaling, and feature-to-qubit projection.
"""

from typing import Union, List, Optional, Tuple
import numpy as np
import torch
import torch.nn as nn
import pennylane as qml
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from sklearn.decomposition import PCA


class AngleEncoder:
    """
    Angle Embedding: Encodes classical feature vector x into rotation angles
    of single-qubit rotation gates (RY, RX, or RZ).
    Features are mapped into [0, pi] or [0, 2*pi].
    """

    def __init__(self, n_qubits: int, rotation: str = "Y", scale_range: Tuple[float, float] = (0.0, np.pi)):
        self.n_qubits = n_qubits
        self.rotation = rotation.upper()
        self.scale_range = scale_range

    def encode(self, features: np.ndarray, wires: Optional[List[int]] = None) -> None:
        """
        PennyLane quantum circuit operations for AngleEmbedding.
        Must be called within a PennyLane QNode context.
        """
        if wires is None:
            wires = list(range(self.n_qubits))

        qml.AngleEmbedding(features=features, wires=wires, rotation=self.rotation)


class AmplitudeEncoder:
    """
    Amplitude Embedding: Encodes a 2^N dimensional normalized classical vector
    into the amplitudes of an N-qubit quantum state |psi> = sum(c_i |i>).
    """

    def __init__(self, n_qubits: int, normalize: bool = True, pad_with: float = 0.0):
        self.n_qubits = n_qubits
        self.normalize = normalize
        self.pad_with = pad_with
        self.required_dim = 2 ** n_qubits

    def encode(self, features: np.ndarray, wires: Optional[List[int]] = None) -> None:
        """
        PennyLane quantum circuit operations for AmplitudeEmbedding.
        Must be called within a PennyLane QNode context.
        """
        if wires is None:
            wires = list(range(self.n_qubits))

        qml.AmplitudeEmbedding(
            features=features,
            wires=wires,
            pad_with=self.pad_with,
            normalize=self.normalize
        )


class ClassicalToQuantumProjector(nn.Module):
    """
    Trainable Classical PyTorch layer that compresses/expands arbitrary classical
    input feature dimension D_in into exactly N_qubits angles normalized for the quantum register.
    """

    def __init__(self, input_dim: int, n_qubits: int, activation_scale: float = np.pi):
        super().__init__()
        self.input_dim = input_dim
        self.n_qubits = n_qubits
        self.activation_scale = activation_scale

        self.dense_proj = nn.Sequential(
            nn.Linear(input_dim, 32),
            nn.LeakyReLU(0.1),
            nn.Linear(32, n_qubits),
            nn.Tanh()  # Produces [-1, 1]
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Maps (Batch, input_dim) -> (Batch, n_qubits) in range [-pi, pi] or [0, pi].
        """
        scaled = self.dense_proj(x) * (self.activation_scale / 2.0) + (self.activation_scale / 2.0)
        return scaled


class QuantumFeaturePreprocessor(BaseEstimator, TransformerMixin):
    """
    Scikit-Learn compatible transformer that scales numerical features to [0, pi]
    and applies PCA if classical dimensions exceed the quantum register size.
    """

    def __init__(self, n_qubits: int = 8, use_pca: bool = False):
        self.n_qubits = n_qubits
        self.use_pca = use_pca
        self.scaler = MinMaxScaler(feature_range=(0.0, np.pi))
        self.pca = PCA(n_components=n_qubits) if use_pca else None

    def fit(self, X: np.ndarray, y=None):
        X_arr = np.asarray(X)
        if self.use_pca and X_arr.shape[1] > self.n_qubits:
            self.pca.fit(X_arr)
            X_reduced = self.pca.transform(X_arr)
            self.scaler.fit(X_reduced)
        else:
            self.scaler.fit(X_arr)
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        X_arr = np.asarray(X)
        if self.use_pca and self.pca is not None and X_arr.shape[1] > self.n_qubits:
            X_reduced = self.pca.transform(X_arr)
            return self.scaler.transform(X_reduced)
        return self.scaler.transform(X_arr)
