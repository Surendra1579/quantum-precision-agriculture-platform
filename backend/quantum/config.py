"""
Quantum Machine Learning Configuration
Defines quantum device parameters, circuit hyperparameters, feature dimensions, and simulator backends.
"""

from dataclasses import dataclass, field
from typing import Optional, List
import os


@dataclass
class QuantumDeviceConfig:
    """Configuration for Quantum Devices and Backends."""
    backend_name: str = "default.qubit"  # Options: 'default.qubit', 'qiskit.aer', 'qiskit.basicaer', 'ibm_runtime'
    shots: Optional[int] = None  # None for analytic statevector, integer for shot-based sampling
    ibm_token: Optional[str] = field(default_factory=lambda: os.getenv("IBM_QUANTUM_TOKEN", None))
    ibm_hub: str = "ibm-q"
    ibm_group: str = "open"
    ibm_project: str = "main"
    ibm_backend: str = "ibmq_qasm_simulator"
    seed: int = 42


@dataclass
class QuantumCircuitConfig:
    """Configuration for Parameterized Quantum Circuits."""
    n_qubits_yield: int = 8  # 8 qubits for crop yield feature representation
    n_qubits_price: int = 8  # 8 qubits for price feature representation
    n_layers_yield: int = 3   # Depth of StronglyEntanglingLayers for Yield
    n_layers_price: int = 3   # Depth of StronglyEntanglingLayers for Price
    encoding_type: str = "angle"  # 'angle' (AngleEmbedding) or 'amplitude' (AmplitudeEmbedding)
    rotation_gate: str = "RY"     # 'RY', 'RX', or 'RZ'
    entanglement_type: str = "circular"  # 'circular', 'linear', or 'all-to-all'
    diff_method: str = "parameter-shift"  # 'parameter-shift', 'adjoint', or 'backprop'


@dataclass
class HybridTrainingConfig:
    """Hyperparameters for Hybrid Quantum-Classical Training."""
    batch_size: int = 32
    learning_rate: float = 0.008
    weight_decay: float = 1e-4
    epochs: int = 60
    early_stopping_patience: int = 12
    min_delta: float = 1e-4
    lr_scheduler_factor: float = 0.5
    lr_scheduler_patience: int = 5
    val_split: float = 0.15
    random_seed: int = 42


# Global Default Instances
QUANTUM_DEVICE_CFG = QuantumDeviceConfig()
QUANTUM_CIRCUIT_CFG = QuantumCircuitConfig()
HYBRID_TRAIN_CFG = HybridTrainingConfig()
