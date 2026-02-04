"""
RTI Ethics Engine - Production AI Ethics Framework for RTI Applications
India's first granular 9-dimension AI ethics evaluator (36 metrics)

ALL METRICS COMPUTED DYNAMICALLY FROM DATA - NO HARDCODED VALUES.

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

Dynamic Metrics (compute from raw data):
    from rti_ethics_engine import build_metrics_from_raw_data, MetricCalculator
    
    # Build metrics from actual data
    metrics = build_metrics_from_raw_data(
        query="What is Section 4?",
        response="Section 4 requires...",
        predictions=np.array([1, 0, 1]),
        labels=np.array([1, 1, 0]),
        sensitive_attr=np.array([0, 1, 1]),
        latency_ms=500.0
    )
    result = evaluate(metrics)
"""

from .core import EthicsEngine
from .results import EthicsResult, DimensionResult, RiskBand, FinalLabel
from .config import (
    # Backwards-compatible static exports
    L1_THRESHOLDS, 
    DIMENSION_WEIGHTS, 
    RISK_THRESHOLDS,
    DIMENSION_INFO,
    METRIC_CATALOG,
    # Dynamic config functions
    get_l1_thresholds,
    get_dimension_weights,
    get_risk_thresholds,
    get_config_from_data,
    get_similarity_function,
    generate_columns_from_formulas,
    reset_config,
    DynamicConfigLoader
)
from .metrics import (
    build_default_metrics,
    build_metrics_from_raw_data,
    compute_fairness_from_data,
    compute_drift_from_data,
    compute_environmental_from_data,
    compute_ux_from_text,
    compute_legal_from_response,
    compute_performance_from_data,
    compute_monitoring_from_data,
    compute_security_from_data,
    compute_explainability_from_data,
    test_dynamic_formulas
)
from .calculators import (
    # Individual metric calculators
    compute_spd, compute_di, compute_eop, compute_aod,
    compute_fnrd, compute_refusal_disparity, compute_mutual_info_leakage,
    compute_psi, compute_ks_statistic, compute_prediction_drift,
    compute_inference_cost, compute_gpu_hours,
    compute_readability_fk, compute_cognitive_load,
    compute_accuracy, compute_recall, compute_f1, compute_group_f1,
    # Master calculator class
    MetricCalculator
)

__version__ = "2.0.1"  # Major version bump for dynamic computation
__author__ = "RTI Ethics Engine Team"
__license__ = "MIT"

__all__ = [
    # Core classes
    "EthicsEngine",
    "EthicsResult", 
    "DimensionResult",
    "MetricCalculator",
    # Enums
    "RiskBand",
    "FinalLabel",
    # Config (static - backwards compatible)
    "L1_THRESHOLDS",
    "DIMENSION_WEIGHTS",
    "RISK_THRESHOLDS",
    "DIMENSION_INFO",
    "METRIC_CATALOG",
    # Config (dynamic)
    "get_l1_thresholds",
    "get_dimension_weights",
    "get_risk_thresholds",
    "get_config_from_data",
    "get_similarity_function",
    "generate_columns_from_formulas",
    "reset_config",
    "DynamicConfigLoader",
    # Metric builders
    "build_default_metrics",
    "build_metrics_from_raw_data",
    "compute_fairness_from_data",
    "compute_drift_from_data",
    "compute_environmental_from_data",
    "compute_ux_from_text",
    "compute_legal_from_response",
    "compute_performance_from_data",
    "compute_monitoring_from_data",
    "compute_security_from_data",
    "compute_explainability_from_data",
    # Individual calculators
    "compute_spd", "compute_di", "compute_eop", "compute_aod",
    "compute_fnrd", "compute_mutual_info_leakage",
    "compute_psi", "compute_ks_statistic",
    "compute_accuracy", "compute_recall", "compute_f1",
    "compute_readability_fk",
    # Helpers
    "evaluate",
    "test_dynamic_formulas",
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


def evaluate_from_raw(
    query: str,
    response: str,
    **kwargs
) -> EthicsResult:
    """
    Evaluate ethics directly from raw data (no pre-computed metrics needed).
    
    Args:
        query: User query text
        response: LLM response text
        **kwargs: Additional data (predictions, labels, sensitive_attr, latency_ms, etc.)
    
    Returns:
        EthicsResult with complete evaluation
    
    Example:
        result = evaluate_from_raw(
            query="What is Section 4 of RTI?",
            response="Section 4 mandates proactive disclosure...",
            latency_ms=500,
            grounding_score=0.9
        )
        print(result.final_label)
    """
    metrics = build_metrics_from_raw_data(query, response, **kwargs)
    return evaluate(metrics)
