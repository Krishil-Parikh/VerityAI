"""
RTI Ethics Engine - Production AI Ethics Framework for RTI Applications
India's first granular 9-dimension AI ethics evaluator (36 metrics)

Quick Start:
    from rti_ethics_engine import evaluate
    
    metrics = {
        "fairness": {"spd": 0.02, "di": 1.0, "eop": 0.05, "aod": 0.03},
        "legal": {"lawfulness": 1.0, "cvr": 0.98},
        # ... other dimensions
    }
    
    result = evaluate(metrics)
    print(result.final_label)        # "ETHICAL"
    print(result.s_llm)              # 0.92
    
    # Granular access
    print(result.get_l1_metric("fairness", "spd"))  # 0.02
    print(result.get_failed_dims())                  # []
"""

from .core import EthicsEngine
from .results import EthicsResult, DimensionResult, RiskBand, FinalLabel
from .config import (
    L1_THRESHOLDS, 
    DIMENSION_WEIGHTS, 
    RISK_THRESHOLDS,
    DIMENSION_INFO,
    METRIC_CATALOG
)
from .metrics import build_default_metrics

__version__ = "1.0.0"
__author__ = "RTI Ethics Engine Team"
__license__ = "MIT"

__all__ = [
    # Core classes
    "EthicsEngine",
    "EthicsResult", 
    "DimensionResult",
    # Enums
    "RiskBand",
    "FinalLabel",
    # Config
    "L1_THRESHOLDS",
    "DIMENSION_WEIGHTS",
    "RISK_THRESHOLDS",
    "DIMENSION_INFO",
    "METRIC_CATALOG",
    # Helpers
    "evaluate",
    "build_default_metrics",
]


def evaluate(metrics: dict) -> EthicsResult:
    """
    Quick evaluation entrypoint.
    
    Args:
        metrics: Dict of dimension -> metrics mapping.
    
    Returns:
        EthicsResult with complete evaluation and granular accessors.
    
    Example:
        result = evaluate({"fairness": {"spd": 0.02}, "legal": {"lawfulness": 1.0}})
        print(result.final_label)  # "ETHICAL"
    """
    engine = EthicsEngine()
    return engine.run_protocol(metrics)
