"""
Quantum Circuit Layers and Parameterized Ansatz Module
Defines Variational Quantum Circuits (VQC), strongly entangling layers,
and Pauli-Z measurement operations using PennyLane and Qiskit.
"""

from typing import Dict, Any, List, Optional
import pennylane as qml
import numpy as np
import torch
import torch.nn as nn

try:
    from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
    from qiskit.circuit.library import RealAmplitudes, EfficientSU2
    QISKIT_AVAILABLE = True
except ImportError:
    QISKIT_AVAILABLE = False


def create_variational_qnode(n_qubits: int, n_layers: int, dev_name: str = "default.qubit", diff_method: str = "backprop"):
    """
    Creates a PennyLane QNode for a Parameterized Variational Quantum Circuit (VQC).

    Architecture:
    1. Angle Embedding on N qubits (using RY gates).
    2. N_layers of StronglyEntanglingLayers (each layer applies rot(alpha, beta, gamma) on each qubit + CNOT entangling ring).
    3. Additional RX and RZ fine-tuning rotations.
    4. Multi-qubit Pauli-Z expectation value measurements [ <Z_0>, <Z_1>, ..., <Z_{N-1}> ].
    """
    dev = qml.device(dev_name, wires=n_qubits)

    @qml.qnode(dev, interface="torch", diff_method=diff_method)
    def quantum_circuit(inputs, weights):
        """
        inputs: shape (n_qubits,) - classical angles
        weights: shape (n_layers, n_qubits, 3) - variational parameters
        """
        # Step 1: Quantum Feature Encoding via AngleEmbedding
        qml.AngleEmbedding(inputs, wires=range(n_qubits), rotation="Y")

        # Step 2: Variational Quantum Layers with Entanglement
        qml.StronglyEntanglingLayers(weights, wires=range(n_qubits))

        # Step 3: Layer of Local Single-Qubit RX/RZ rotations
        for i in range(n_qubits):
            qml.RZ(0.1, wires=i)

        # Step 4: Multi-qubit Pauli-Z Expectation Value Readout
        return [qml.expval(qml.PauliZ(i)) for i in range(n_qubits)]

    return quantum_circuit, dev


def build_qiskit_vqc_circuit(n_qubits: int = 8, n_layers: int = 3, feature_values: Optional[List[float]] = None) -> Any:
    """
    Constructs a pure Qiskit QuantumCircuit representing the hybrid VQC
    for visualization, gate decomposition, and Qiskit Aer / IBM Quantum execution.
    """
    if not QISKIT_AVAILABLE:
        return None

    qr = QuantumRegister(n_qubits, name="q")
    cr = ClassicalRegister(n_qubits, name="c")
    qc = QuantumCircuit(qr, cr, name="CropPrice_VQC")

    # Feature encoding layer
    qc.barrier(label="Encoding")
    if feature_values is None:
        feature_values = [0.5 * np.pi] * n_qubits

    for i in range(n_qubits):
        val = feature_values[i] if i < len(feature_values) else 0.0
        qc.ry(val, qr[i])

    # Strongly Entangling Layers
    for layer in range(n_layers):
        qc.barrier(label=f"Layer_{layer+1}")
        # Single qubit rotations
        for i in range(n_qubits):
            qc.rx(0.25 * (layer + 1), qr[i])
            qc.ry(0.35 * (layer + 1), qr[i])
            qc.rz(0.45 * (layer + 1), qr[i])
        
        # Entanglement (Circular CNOT ring)
        for i in range(n_qubits):
            target = (i + 1) % n_qubits
            qc.cx(qr[i], qr[target])

    # Measurement layer
    qc.barrier(label="Measurement")
    for i in range(n_qubits):
        qc.measure(qr[i], cr[i])

    return qc


class QuantumVariationalLayer(nn.Module):
    """
    PyTorch Module wrapper for Parameterized Quantum Circuit using PennyLane TorchLayer.
    """

    def __init__(self, n_qubits: int = 8, n_layers: int = 3, dev_name: str = "default.qubit"):
        super().__init__()
        self.n_qubits = n_qubits
        self.n_layers = n_layers

        qnode, self.dev = create_variational_qnode(
            n_qubits=n_qubits,
            n_layers=n_layers,
            dev_name=dev_name,
            diff_method="backprop" if dev_name == "default.qubit" else "best"
        )

        weight_shapes = {"weights": (n_layers, n_qubits, 3)}
        self.q_layer = qml.qnn.TorchLayer(qnode, weight_shapes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        x: (Batch, n_qubits)
        returns: (Batch, n_qubits) Pauli-Z expectation values in [-1, 1]
        """
        return self.q_layer(x)
