"""
Hybrid Quantum Machine Learning Package for Agricultural Intelligence
"""

from quantum.config import QUANTUM_DEVICE_CFG, QUANTUM_CIRCUIT_CFG, HYBRID_TRAIN_CFG
from quantum.feature_encoding import AngleEncoder, AmplitudeEncoder, QuantumFeaturePreprocessor
from quantum.quantum_layers import create_variational_qnode, QuantumVariationalLayer
from quantum.hybrid_qnn import HybridQuantumNeuralNetwork
from quantum.quantum_crop_model import QuantumCropYieldModel
from quantum.quantum_price_model import QuantumPriceForecastModel
from quantum.inference import quantum_engine, QuantumInferenceEngine
from quantum.quantum_utils import get_circuit_metadata, compute_quantum_confidence, compute_quantum_explainability
