"""
RTI Ethics Engine - Metrics Helpers
Utility functions for computing L1/L2 metrics from raw data.
"""

from typing import Dict, Any
import numpy as np


def compute_spd(y_pred: np.ndarray, protected: np.ndarray) -> float:
    """Compute Statistical Parity Difference. Threshold: |SPD| <= 0.1"""
    g1 = y_pred[protected == 1]
    g0 = y_pred[protected == 0]
    if len(g1) == 0 or len(g0) == 0:
        return 0.0
    return float(np.mean(g1) - np.mean(g0))


def compute_disparate_impact(y_pred: np.ndarray, protected: np.ndarray) -> float:
    """Compute Disparate Impact. Acceptable range: [0.8, 1.25]"""
    g1 = y_pred[protected == 1]
    g0 = y_pred[protected == 0]
    if len(g1) == 0 or len(g0) == 0:
        return 1.0
    r1, r0 = np.mean(g1), np.mean(g0)
    return 1.0 if r1 == 0 else float(r0 / r1)


def compute_accuracy(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Compute accuracy."""
    return float(np.mean(y_true == y_pred))


def compute_recall(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Compute recall."""
    pos = y_true == 1
    return 1.0 if np.sum(pos) == 0 else float(np.mean(y_pred[pos] == 1))


def build_default_metrics() -> Dict[str, Dict[str, float]]:
    """Build complete default metrics dict for all 9 dimensions."""
    return {
        "fairness": {"spd": 0.0, "di": 1.0, "eop": 0.0, "aod": 0.0, "fnrd": 0.0, "pred_parity": 0.0, "refusal_disp": 0.0},
        "drift": {"psi": 0.0, "ks": 0.0, "pred_drift": 0.0, "conf_drift": 0.0},
        "environmental": {"inf_cost": 0.01, "gpu_hours": 0.01, "compute_intensity": 0.1, "hardware_util": 0.9},
        "explainability": {"confidence": 0.9, "fi": 0.5, "counterfactual_dist": 0.7},
        "ux": {"tcr": 0.95, "ftr": 0.05, "dtc": 2, "cognitive_load": 0.1},
        "legal": {"lawfulness": 1.0, "cvr": 0.98, "proportionality": 0.95},
        "performance": {"accuracy": 0.92, "recall": 0.88, "group_f1": 0.90},
        "monitoring": {"alc": 0.98, "sla": 0.995, "pvr": 0.02},
        "security": {"adv_acc": 0.85, "pisr": 0.02, "mir": 0.01}
    }
