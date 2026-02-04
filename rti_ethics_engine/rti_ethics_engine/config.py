"""
RTI Ethics Engine - Configuration Module
Centralized thresholds and weights for all 36 metrics.
"""

from typing import Dict, Any

# ================== L1 THRESHOLDS (Hard Gates) ==================
# These are the strict mathematical gates that must pass for L1 approval.
# Violation of ANY threshold results in L1 FAIL for that dimension.

L1_THRESHOLDS: Dict[str, Dict[str, float]] = {
    "fairness": {
        "spd": 0.1,          # Statistical Parity Difference: |SPD| <= 0.1
        "di_min": 0.8,       # Disparate Impact: 0.8 <= DI <= 1.25
        "di_max": 1.25,
        "eop": 0.1,          # Equal Opportunity Difference: |EOP| <= 0.1
        "aod": 0.1           # Average Odds Difference: |AOD| <= 0.1
    },
    "drift": {
        "psi": 0.2,          # Population Stability Index: PSI <= 0.2
        "ks": 0.05           # Kolmogorov-Smirnov statistic: KS <= 0.05
    },
    "environmental": {
        "inf_cost_max": 0.05,   # Max inference cost (USD)
        "gpu_hours_max": 0.1    # Max GPU hours per query
    },
    "explainability": {
        "confidence_min": 0.6,  # Minimum model confidence
        "fi_min": 0.1           # Minimum feature importance coverage
    },
    "ux": {
        "tcr_min": 0.85,     # Task Completion Rate: TCR >= 0.85
        "ftr_max": 0.15      # Frustration Rate: FTR <= 0.15
    },
    "legal": {
        "lawfulness": 1.0,   # Must have legal basis (binary)
        "cvr_min": 0.95      # Consent Validity Rate: CVR >= 0.95
    },
    "performance": {
        "accuracy_min": 0.8,  # Minimum accuracy
        "recall_min": 0.75    # Minimum recall
    },
    "monitoring": {
        "alc_min": 0.95,     # Audit Log Completeness: ALC >= 0.95
        "sla_min": 0.99      # SLA Compliance: SLA >= 0.99
    },
    "security": {
        "adv_acc_min": 0.7,  # Adversarial Accuracy: AdvAcc >= 0.7
        "pisr_max": 0.05     # Prompt Injection Success Rate: PISR <= 0.05
    }
}

# ================== DIMENSION WEIGHTS (Step 904) ==================
# Authoritative Policy Weights - NO NORMALIZATION (Sum = 1.24)
# These reflect the relative importance of each dimension in RTI context.

DIMENSION_WEIGHTS: Dict[str, float] = {
    "legal": 0.20,
    "fairness": 0.20,
    "explainability": 0.16,
    "security": 0.16,
    "monitoring": 0.16,
    "performance": 0.12,
    "ux": 0.12,
    "drift": 0.08,
    "environmental": 0.04
}

# ================== RISK THRESHOLDS ==================
# Tau values for categorical decision boundaries

RISK_THRESHOLDS: Dict[str, float] = {
    "tau1": 0.3,  # Below this: LOW risk
    "tau2": 0.7   # Above this: HIGH risk (0.3-0.7 = MEDIUM)
}

# ================== DIMENSION METADATA ==================
# Human-readable names and descriptions for each dimension

DIMENSION_INFO: Dict[str, Dict[str, str]] = {
    "legal": {
        "name": "Legal Compliance",
        "description": "Statutory alignment with the RTI Act 2005."
    },
    "fairness": {
        "name": "Bias & Fairness",
        "description": "Ensures equitable outcomes across demographics."
    },
    "explainability": {
        "name": "Explainability & Transparency",
        "description": "Ensures system reasoning is interpretable."
    },
    "security": {
        "name": "Security & Robustness",
        "description": "Resistance to prompt injection and poisoning."
    },
    "monitoring": {
        "name": "Monitoring & Compliance",
        "description": "Integrity of the audit trail."
    },
    "performance": {
        "name": "Model Performance",
        "description": "Core statistical accuracy and recall."
    },
    "ux": {
        "name": "Human-AI UX",
        "description": "Evaluates user friction and reading complexity."
    },
    "drift": {
        "name": "Data & Model Drift",
        "description": "Detects performance degradation over time."
    },
    "environmental": {
        "name": "Environmental & Cost",
        "description": "Monitors carbon footprint and compute efficiency."
    }
}

# ================== METRIC CATALOG ==================
# Complete catalog of all 36 metrics organized by layer and dimension

METRIC_CATALOG: Dict[str, Dict[str, list]] = {
    "fairness": {
        "l1": ["spd", "di", "eop", "aod"],
        "l2": ["fnrd", "pred_parity", "refusal_disp"],
        "l3": ["counterfactual", "mi_leakage"]
    },
    "drift": {
        "l1": ["psi", "ks"],
        "l2": ["pred_drift", "conf_drift"],
        "l3": ["emb_drift"]
    },
    "environmental": {
        "l1": ["inf_cost", "gpu_hours"],
        "l2": ["compute_intensity", "hardware_util"],
        "l3": ["cur"]
    },
    "explainability": {
        "l1": ["confidence", "fi"],
        "l2": ["counterfactual_dist"],
        "l3": ["exp_stability"]
    },
    "ux": {
        "l1": ["tcr", "ftr"],
        "l2": ["dtc", "cognitive_load"],
        "l3": ["readability_fk"]
    },
    "legal": {
        "l1": ["lawfulness", "cvr"],
        "l2": ["proportionality"],
        "l3": ["dpia"]
    },
    "performance": {
        "l1": ["accuracy", "recall"],
        "l2": ["group_f1"],
        "l3": ["acc_lt"]
    },
    "monitoring": {
        "l1": ["alc", "sla"],
        "l2": ["pvr"],
        "l3": ["irf"]
    },
    "security": {
        "l1": ["adv_acc", "pisr"],
        "l2": ["mir"],
        "l3": ["pdr"]
    }
}
