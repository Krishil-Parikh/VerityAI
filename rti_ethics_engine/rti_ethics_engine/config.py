"""
RTI Ethics Engine - Configuration Module (Dynamic)
Centralized thresholds and weights with dynamic loading capability.

All thresholds can be loaded from:
1. Hardcoded defaults (for cold start)
2. Historical data percentiles
3. Environment variables
4. External config files
"""

import os
import json
import numpy as np
from typing import Dict, Any, Optional
from pathlib import Path


# ================== DEFAULT THRESHOLDS (Fallback) ==================
# These are used when no historical data is available

DEFAULT_L1_THRESHOLDS: Dict[str, Dict[str, float]] = {
    "fairness": {
        "spd": 0.5,          # Statistical Parity Difference: |SPD| <= 0.5
        "di_min": 0.5,       # Disparate Impact: 0.5 <= DI <= 2.0
        "di_max": 2.0,
        "eop": 0.5,          # Equal Opportunity Difference: |EOP| <= 0.5
        "aod": 0.5           # Average Odds Difference: |AOD| <= 0.5
    },
    "drift": {
        "psi": 0.5,          # Population Stability Index: PSI <= 0.5
        "ks": 0.5            # Kolmogorov-Smirnov statistic: KS <= 0.5
    },
    "environmental": {
        "inf_cost_max": 0.5,    # Max inference cost (USD)
        "gpu_hours_max": 0.5    # Max GPU hours per query
    },
    "explainability": {
        "confidence_min": 0.5,  # Minimum model confidence
        "fi_min": 0.5           # Minimum feature importance coverage
    },
    "ux": {
        "tcr_min": 0.5,      # Task Completion Rate: TCR >= 0.5
        "ftr_max": 0.5       # Frustration Rate: FTR <= 0.5
    },
    "legal": {
        "lawfulness": 0.5,   # Minimum lawfulness score (binary/scalar)
        "cvr_min": 0.5       # Consent Validity Rate: CVR >= 0.5
    },
    "performance": {
        "accuracy_min": 0.5,  # Minimum accuracy
        "recall_min": 0.5    # Minimum recall
    },
    "monitoring": {
        "alc_min": 0.5,      # Audit Log Completeness: ALC >= 0.5
        "sla_min": 0.5       # SLA Compliance: SLA >= 0.5
    },
    "security": {
        "adv_acc_min": 0.5,  # Adversarial Accuracy: AdvAcc >= 0.5
        "pisr_max": 0.5      # Prompt Injection Success Rate: PISR <= 0.5
    }
}

DEFAULT_DIMENSION_WEIGHTS: Dict[str, float] = {
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

DEFAULT_RISK_THRESHOLDS: Dict[str, float] = {
    "tau1": 0.3,  # Below this: LOW risk
    "tau2": 0.7   # Above this: HIGH risk (0.3-0.7 = MEDIUM)
}


# ================== DYNAMIC THRESHOLD LOADER ==================

class DynamicConfigLoader:
    """
    Loads and computes thresholds dynamically from:
    - Historical data (percentiles)
    - Environment variables
    - External config files
    """
    
    def __init__(self, data_path: Optional[str] = None):
        self.data_path = data_path
        self._l1_thresholds = None
        self._dimension_weights = None
        self._risk_thresholds = None
    
    def load_from_env(self) -> Dict[str, Any]:
        """Load thresholds from environment variables."""
        config = {}
        
        # Example env vars: RTI_FAIRNESS_SPD_THRESHOLD, RTI_LEGAL_WEIGHT
        for dim in DEFAULT_L1_THRESHOLDS.keys():
            for metric, default_val in DEFAULT_L1_THRESHOLDS[dim].items():
                env_key = f"RTI_{dim.upper()}_{metric.upper()}_THRESHOLD"
                if env_key in os.environ:
                    try:
                        config.setdefault(dim, {})[metric] = float(os.environ[env_key])
                    except ValueError:
                        pass
        
        # Load weights
        for dim, default_weight in DEFAULT_DIMENSION_WEIGHTS.items():
            env_key = f"RTI_{dim.upper()}_WEIGHT"
            if env_key in os.environ:
                try:
                    config.setdefault('weights', {})[dim] = float(os.environ[env_key])
                except ValueError:
                    pass
        
        return config
    
    def load_from_file(self, filepath: str) -> Dict[str, Any]:
        """Load thresholds from JSON config file."""
        path = Path(filepath)
        if path.exists() and path.suffix == '.json':
            with open(path, 'r') as f:
                return json.load(f)
        return {}
    
    def compute_from_data(
        self, 
        historical_metrics: Dict[str, np.ndarray],
        percentile: float = 90
    ) -> Dict[str, Dict[str, float]]:
        """
        Compute thresholds from historical data distribution.
        
        Args:
            historical_metrics: Dict of metric_name -> array of historical values
            percentile: Percentile to use for threshold (default: 90th)
        
        Returns:
            Computed thresholds based on data distribution
        """
        computed = {}
        
        # Fairness thresholds from historical SPD distribution
        if 'spd' in historical_metrics:
            spd_values = np.abs(historical_metrics['spd'])
            computed.setdefault('fairness', {})['spd'] = float(np.percentile(spd_values, percentile))
        
        if 'di' in historical_metrics:
            di_values = historical_metrics['di']
            computed.setdefault('fairness', {})['di_min'] = float(np.percentile(di_values, 100 - percentile))
            computed.setdefault('fairness', {})['di_max'] = float(np.percentile(di_values, percentile))
        
        # Drift thresholds
        if 'psi' in historical_metrics:
            psi_values = historical_metrics['psi']
            computed.setdefault('drift', {})['psi'] = float(np.percentile(psi_values, percentile))
        
        # Performance thresholds
        if 'accuracy' in historical_metrics:
            acc_values = historical_metrics['accuracy']
            computed.setdefault('performance', {})['accuracy_min'] = float(np.percentile(acc_values, 100 - percentile))
        
        if 'recall' in historical_metrics:
            recall_values = historical_metrics['recall']
            computed.setdefault('performance', {})['recall_min'] = float(np.percentile(recall_values, 100 - percentile))
        
        # Environmental thresholds
        if 'inf_cost' in historical_metrics:
            cost_values = historical_metrics['inf_cost']
            computed.setdefault('environmental', {})['inf_cost_max'] = float(np.percentile(cost_values, percentile))
        
        return computed
    
    def get_thresholds(
        self, 
        historical_data: Dict[str, np.ndarray] = None,
        config_file: str = None
    ) -> Dict[str, Dict[str, float]]:
        """
        Get L1 thresholds with priority:
        1. Computed from historical data (if provided)
        2. From config file (if exists)
        3. From environment variables
        4. Fallback to defaults
        """
        if self._l1_thresholds is not None:
            return self._l1_thresholds
        
        # Start with defaults
        thresholds = {k: v.copy() for k, v in DEFAULT_L1_THRESHOLDS.items()}
        
        # Override with env vars
        env_config = self.load_from_env()
        for dim, metrics in env_config.items():
            if dim in thresholds and isinstance(metrics, dict):
                thresholds[dim].update(metrics)
        
        # Override with config file
        if config_file:
            file_config = self.load_from_file(config_file)
            if 'l1_thresholds' in file_config:
                for dim, metrics in file_config['l1_thresholds'].items():
                    if dim in thresholds:
                        thresholds[dim].update(metrics)
        
        # Override with computed values (highest priority)
        if historical_data:
            computed = self.compute_from_data(historical_data)
            for dim, metrics in computed.items():
                if dim in thresholds:
                    thresholds[dim].update(metrics)
        
        self._l1_thresholds = thresholds
        return thresholds
    
    def get_weights(
        self, 
        config_file: str = None
    ) -> Dict[str, float]:
        """Get dimension weights with priority: file > env > defaults."""
        if self._dimension_weights is not None:
            return self._dimension_weights
        
        weights = DEFAULT_DIMENSION_WEIGHTS.copy()
        
        # Override with env
        env_config = self.load_from_env()
        if 'weights' in env_config:
            weights.update(env_config['weights'])
        
        # Override with file
        if config_file:
            file_config = self.load_from_file(config_file)
            if 'dimension_weights' in file_config:
                weights.update(file_config['dimension_weights'])
        
        self._dimension_weights = weights
        return weights
    
    def get_risk_thresholds(
        self, 
        config_file: str = None
    ) -> Dict[str, float]:
        """Get risk band thresholds."""
        if self._risk_thresholds is not None:
            return self._risk_thresholds
        
        thresholds = DEFAULT_RISK_THRESHOLDS.copy()
        
        # Override with env
        if 'RTI_TAU1' in os.environ:
            try:
                thresholds['tau1'] = float(os.environ['RTI_TAU1'])
            except ValueError:
                pass
        if 'RTI_TAU2' in os.environ:
            try:
                thresholds['tau2'] = float(os.environ['RTI_TAU2'])
            except ValueError:
                pass
        
        # Override with file
        if config_file:
            file_config = self.load_from_file(config_file)
            if 'risk_thresholds' in file_config:
                thresholds.update(file_config['risk_thresholds'])
        
        self._risk_thresholds = thresholds
        return thresholds
    
    def reset(self):
        """Reset cached config for reloading."""
        self._l1_thresholds = None
        self._dimension_weights = None
        self._risk_thresholds = None


# ================== GLOBAL CONFIG LOADER ==================

_config_loader = DynamicConfigLoader()

def get_l1_thresholds(
    historical_data: Dict[str, np.ndarray] = None,
    config_file: str = None
) -> Dict[str, Dict[str, float]]:
    """Get L1 thresholds (dynamic or default)."""
    return _config_loader.get_thresholds(historical_data, config_file)

def get_dimension_weights(config_file: str = None) -> Dict[str, float]:
    """Get dimension weights (dynamic or default)."""
    return _config_loader.get_weights(config_file)

def get_risk_thresholds(config_file: str = None) -> Dict[str, float]:
    """Get risk band thresholds."""
    return _config_loader.get_risk_thresholds(config_file)

def reset_config():
    """Reset config loader cache."""
    _config_loader.reset()


# ================== BACKWARDS COMPATIBLE EXPORTS ==================
# These use defaults for backwards compatibility

L1_THRESHOLDS = DEFAULT_L1_THRESHOLDS.copy()
DIMENSION_WEIGHTS = DEFAULT_DIMENSION_WEIGHTS.copy()
RISK_THRESHOLDS = DEFAULT_RISK_THRESHOLDS.copy()


# ================== DIMENSION METADATA ==================

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


# ================== COLUMN GENERATOR ==================

def generate_columns_from_formulas() -> list:
    """
    Generate CSV columns dynamically from the 9-dimension formulas.
    No hardcoded column list.
    """
    base_cols = [
        "conversation_id", "turn_id", "user_id", "department",
        "timestamp_request", "timestamp_response", "latency_ms",
        "user_prompt", "ai_response", "model_name", "infra_region"
    ]
    
    # RAG columns
    rag_cols = ["rag_documents", "rag_sections"]
    
    # Dynamic metric columns from catalog
    metric_cols = []
    for dim, layers in METRIC_CATALOG.items():
        # Add L1 metrics
        for metric in layers.get("l1", []):
            metric_cols.append(f"{dim}_{metric}")
        # Add L2 metrics  
        for metric in layers.get("l2", []):
            metric_cols.append(f"{dim}_{metric}")
        # Add L3 metrics
        for metric in layers.get("l3", []):
            metric_cols.append(f"{dim}_{metric}")
        
        # Add layer aggregate scores
        metric_cols.extend([
            f"{dim}_l1_status",
            f"{dim}_l2_risk",
        ])
    
    # Aggregate columns
    aggregate_cols = [
        "overall_ethical_score", "final_label", "risk_band",
        "s_llm", "layer1_status", "layer2_risk_score",
        "required_action", "audit_id"
    ]
    
    # Additional operational columns
    operational_cols = [
        "safety_flag", "error_code", "is_gold_example", "task_completed",
        "hallucination_rate", "human_feedback_score", "sensitive_group"
    ]
    
    # Token columns
    token_cols = [
        "input_tokens", "output_tokens", "total_tokens", "estimated_cost_usd"
    ]
    
    return base_cols + rag_cols + metric_cols + aggregate_cols + operational_cols + token_cols


# ================== DYNAMIC CONFIG GETTER ==================

def get_config_from_data(
    df=None, 
    chunk_metadata: list = None,
    env_vars: Dict[str, str] = None
) -> Dict[str, Any]:
    """
    Derive configuration from actual data/environment.
    
    Args:
        df: Pandas DataFrame with conversation history
        chunk_metadata: List of RAG chunk metadata
        env_vars: Environment variables dict
    
    Returns:
        Dynamic configuration dict
    """
    config = {}
    
    # CHUNK_SIZE from data
    if df is not None and not df.empty and 'user_prompt' in df.columns:
        avg_query_len = df['user_prompt'].str.len().mean()
        config['chunk_size'] = max(400, int(avg_query_len * 1.2))
    else:
        config['chunk_size'] = int(os.environ.get('RTI_CHUNK_SIZE', 600))
    
    # TOP_K from index size
    if chunk_metadata:
        config['top_k'] = min(10, max(3, len(chunk_metadata) // 10))
    else:
        config['top_k'] = int(os.environ.get('RTI_TOP_K', 5))
    
    # Minimum chunk length from data
    if chunk_metadata and len(chunk_metadata) > 0:
        text_lengths = [len(m.get('text', '')) for m in chunk_metadata if 'text' in m]
        if text_lengths:
            config['min_chunk_len'] = max(50, int(np.mean(text_lengths) * 0.1))
    else:
        config['min_chunk_len'] = int(os.environ.get('RTI_MIN_CHUNK_LEN', 80))
    
    return config


# ================== SIMILARITY METRIC FACTORY ==================

def get_similarity_function(metric_type: str = "cosine"):
    """
    Get distance-to-similarity conversion function based on metric type.
    
    Args:
        metric_type: "cosine", "euclidean", "dot_product"
    
    Returns:
        Function that converts distance to similarity
    """
    if metric_type == "cosine":
        return lambda d: 1.0 - d  # Cosine distance to similarity
    elif metric_type == "euclidean":
        return lambda d: 1.0 / (1.0 + d)  # Euclidean to similarity
    elif metric_type == "dot_product":
        return lambda d: d  # Dot product is already similarity
    else:
        return lambda d: 1.0 - d  # Default to cosine
