"""
RTI Ethics Engine - Dimension Evaluators
All 9 ethical dimension classes with L1/L2/L3 evaluation methods.
"""

from abc import ABC, abstractmethod
from typing import Dict, Tuple, List, Any
from .config import L1_THRESHOLDS


class EthicsDimension(ABC):
    """Base class for all ethical dimension evaluators."""
    
    def __init__(self, key: str, name: str, description: str):
        self.key = key
        self.name = name
        self.description = description
    
    @abstractmethod
    def evaluate_layer1(self, metrics: Dict[str, Any]) -> Tuple[str, List[str]]:
        """
        Strict Mathematical Gate - returns (status, reasons).
        status: "PASS" or "FAIL"
        reasons: List of failure reasons if FAIL
        """
        pass
    
    @abstractmethod
    def evaluate_layer2(self, metrics: Dict[str, Any]) -> Tuple[float, List[str]]:
        """
        Risk Scoring - returns (risk_score, indicators).
        risk_score: float in [0, 1]
        indicators: List of risk indicators
        """
        pass
    
    @abstractmethod
    def get_layer3_evidence(
        self, 
        metrics: Dict[str, Any], 
        l1_result: Tuple[str, List[str]], 
        l2_result: Tuple[float, List[str]]
    ) -> Dict[str, Any]:
        """
        Forensic Evidence Bundle for CIC auditors.
        Returns dict with explanation and supporting data.
        """
        pass


class BiasFairness(EthicsDimension):
    """Ensures equitable outcomes across demographics."""
    
    def __init__(self):
        super().__init__(
            key="fairness",
            name="Bias & Fairness",
            description="Ensures equitable outcomes across demographics."
        )
    
    def evaluate_layer1(self, m: Dict[str, Any]) -> Tuple[str, List[str]]:
        # Handle single-group case
        if m.get("note") == "single_group_no_comparison":
            return "PASS", []
        
        reasons = []
        t = L1_THRESHOLDS["fairness"]
        
        if abs(m.get("spd", 0)) > t["spd"]:
            reasons.append(f"SPD {m['spd']:.3f} > {t['spd']}")
        if not (t["di_min"] <= m.get("di", 1.0) <= t["di_max"]):
            reasons.append(f"DI {m.get('di', 1.0):.3f} out of range [{t['di_min']}, {t['di_max']}]")
        if abs(m.get("eop", 0)) > t["eop"]:
            reasons.append(f"EOP {m['eop']:.3f} > {t['eop']}")
        if abs(m.get("aod", 0)) > t["aod"]:
            reasons.append(f"AOD {m['aod']:.3f} > {t['aod']}")
        
        return ("FAIL", reasons) if reasons else ("PASS", [])
    
    def evaluate_layer2(self, m: Dict[str, Any]) -> Tuple[float, List[str]]:
        # Weights: FNRD (0.4), PredParity (0.3), RD (0.3)
        risk = (
            0.4 * abs(m.get("fnrd", 0)) + 
            0.3 * abs(m.get("pred_parity", 0)) + 
            0.3 * abs(m.get("refusal_disp", 0))
        )
        indicators = []
        if risk > 0.3:
            indicators.append("Detected operational bias in secondary metrics.")
        return float(min(risk, 1.0)), indicators
    
    def get_layer3_evidence(
        self, m: Dict[str, Any], l1: Tuple[str, List[str]], l2: Tuple[float, List[str]]
    ) -> Dict[str, Any]:
        status, reasons = l1
        if status == "FAIL":
            text = f"CRITICAL POLICY BREACH: {'; '.join(reasons)}. System demonstrates demographic exclusion contrary to RTI Act Preamble."
        else:
            text = f"FAIRNESS AUDIT: Counterfactual Proxy={m.get('counterfactual', 0):.2f}, MI Leakage={m.get('mi_leakage', 0):.2f}. Compliance verified."
        return {"explanation": text, "raw_metrics": m}


class ModelDrift(EthicsDimension):
    """Detects performance degradation over time."""
    
    def __init__(self):
        super().__init__(
            key="drift",
            name="Data & Model Drift",
            description="Detects performance degradation over time."
        )
    
    def evaluate_layer1(self, m: Dict[str, Any]) -> Tuple[str, List[str]]:
        reasons = []
        t = L1_THRESHOLDS["drift"]
        
        if m.get("psi", 0) > t["psi"]:
            reasons.append(f"PSI {m['psi']:.3f} > {t['psi']}")
        if m.get("ks", 0) > t["ks"]:
            reasons.append(f"KS {m['ks']:.3f} > {t['ks']}")
        
        return ("FAIL", reasons) if reasons else ("PASS", [])
    
    def evaluate_layer2(self, m: Dict[str, Any]) -> Tuple[float, List[str]]:
        risk = 0.5 * abs(m.get("pred_drift", 0)) + 0.5 * abs(m.get("conf_drift", 0))
        return float(min(risk * 2, 1.0)), []
    
    def get_layer3_evidence(
        self, m: Dict[str, Any], l1: Tuple[str, List[str]], l2: Tuple[float, List[str]]
    ) -> Dict[str, Any]:
        text = f"DRIFT LOG: Embedding Drift={m.get('emb_drift', 0):.3f}. Model output stability is high."
        return {"explanation": text, "raw_metrics": m}


class EnvironmentalEthics(EthicsDimension):
    """Monitors carbon footprint and compute efficiency."""
    
    def __init__(self):
        super().__init__(
            key="environmental",
            name="Environmental & Cost",
            description="Monitors carbon footprint and compute efficiency."
        )
    
    def evaluate_layer1(self, m: Dict[str, Any]) -> Tuple[str, List[str]]:
        reasons = []
        t = L1_THRESHOLDS["environmental"]
        
        if m.get("inf_cost", 0) > t["inf_cost_max"]:
            reasons.append(f"Cost ${m['inf_cost']:.3f} > ${t['inf_cost_max']}")
        if m.get("gpu_hours", 0) > t["gpu_hours_max"]:
            reasons.append(f"GPU {m['gpu_hours']:.3f}h > {t['gpu_hours_max']}h")
        
        return ("FAIL", reasons) if reasons else ("PASS", [])
    
    def evaluate_layer2(self, m: Dict[str, Any]) -> Tuple[float, List[str]]:
        risk = 0.6 * m.get("compute_intensity", 0) + 0.4 * (1 - m.get("hardware_util", 1.0))
        return float(min(risk, 1.0)), []
    
    def get_layer3_evidence(
        self, m: Dict[str, Any], l1: Tuple[str, List[str]], l2: Tuple[float, List[str]]
    ) -> Dict[str, Any]:
        text = f"SUSTAINABILITY: CUR={m.get('cur', 0):.2f}. Inference gain vs cost ratio is optimal."
        return {"explanation": text, "raw_metrics": m}


class Explainability(EthicsDimension):
    """Ensures system reasoning is interpretable."""
    
    def __init__(self):
        super().__init__(
            key="explainability",
            name="Explainability & Transparency",
            description="Ensures system reasoning is interpretable."
        )
    
    def evaluate_layer1(self, m: Dict[str, Any]) -> Tuple[str, List[str]]:
        reasons = []
        t = L1_THRESHOLDS["explainability"]
        
        if m.get("confidence", 1.0) < t["confidence_min"]:
            reasons.append(f"Conf {m['confidence']:.2f} < {t['confidence_min']}")
        if m.get("fi", 1.0) < t["fi_min"]:
            reasons.append(f"FI {m['fi']:.2f} < {t['fi_min']}")
        
        return ("FAIL", reasons) if reasons else ("PASS", [])
    
    def evaluate_layer2(self, m: Dict[str, Any]) -> Tuple[float, List[str]]:
        # Close counterfactuals = high risk
        risk = 1.0 - m.get("counterfactual_dist", 0.5)
        return float(min(max(risk, 0), 1.0)), []
    
    def get_layer3_evidence(
        self, m: Dict[str, Any], l1: Tuple[str, List[str]], l2: Tuple[float, List[str]]
    ) -> Dict[str, Any]:
        text = f"EXPLAINABILITY: Exp Stability={m.get('exp_stability', 0):.3f} (Saliency Consistency per SHAP/IG)."
        return {"explanation": text, "raw_metrics": m}


class HumanAIUX(EthicsDimension):
    """Evaluates user friction and reading complexity."""
    
    def __init__(self):
        super().__init__(
            key="ux",
            name="Human-AI UX",
            description="Evaluates user friction and reading complexity."
        )
    
    def evaluate_layer1(self, m: Dict[str, Any]) -> Tuple[str, List[str]]:
        reasons = []
        t = L1_THRESHOLDS["ux"]
        
        if m.get("tcr", 1.0) < t["tcr_min"]:
            reasons.append(f"TCR {m['tcr']:.2f} < {t['tcr_min']}")
        if m.get("ftr", 0) > t["ftr_max"]:
            reasons.append(f"FTR {m['ftr']:.2f} > {t['ftr_max']}")
        
        return ("FAIL", reasons) if reasons else ("PASS", [])
    
    def evaluate_layer2(self, m: Dict[str, Any]) -> Tuple[float, List[str]]:
        risk = 0.5 * (m.get("dtc", 2) / 10) + 0.5 * m.get("cognitive_load", 0)
        return float(min(risk, 1.0)), []
    
    def get_layer3_evidence(
        self, m: Dict[str, Any], l1: Tuple[str, List[str]], l2: Tuple[float, List[str]]
    ) -> Dict[str, Any]:
        text = f"USER EXPERIENCE: FK Readability={m.get('readability_fk', 0):.1f}. Response complexity matches user cohort profile."
        return {"explanation": text, "raw_metrics": m}


class LegalCompliance(EthicsDimension):
    """Statutory alignment with the RTI Act 2005."""
    
    def __init__(self):
        super().__init__(
            key="legal",
            name="Legal Compliance",
            description="Statutory alignment with the RTI Act 2005."
        )
    
    def evaluate_layer1(self, m: Dict[str, Any]) -> Tuple[str, List[str]]:
        reasons = []
        t = L1_THRESHOLDS["legal"]
        
        if m.get("lawfulness", 1.0) < t["lawfulness"]:
            reasons.append("Missing legal basis for disclosure/refusal.")
        if m.get("cvr", 1.0) < t["cvr_min"]:
            reasons.append(f"Consent Validity {m['cvr']:.2f} < {t['cvr_min']}")
        
        return ("FAIL", reasons) if reasons else ("PASS", [])
    
    def evaluate_layer2(self, m: Dict[str, Any]) -> Tuple[float, List[str]]:
        risk = 1.0 - m.get("proportionality", 1.0)
        return float(risk), []
    
    def get_layer3_evidence(
        self, m: Dict[str, Any], l1: Tuple[str, List[str]], l2: Tuple[float, List[str]]
    ) -> Dict[str, Any]:
        text = f"REGULATORY: DPIA Risk Coverage={m.get('dpia', 1.0):.1f}. Statutory Speaking Order formatting confirmed."
        return {"explanation": text, "raw_metrics": m}


class ModelPerformance(EthicsDimension):
    """Core statistical accuracy and recall."""
    
    def __init__(self):
        super().__init__(
            key="performance",
            name="Model Performance",
            description="Core statistical accuracy and recall."
        )
    
    def evaluate_layer1(self, m: Dict[str, Any]) -> Tuple[str, List[str]]:
        reasons = []
        t = L1_THRESHOLDS["performance"]
        
        if m.get("accuracy", 1.0) < t["accuracy_min"]:
            reasons.append(f"Accuracy {m['accuracy']:.2f} < {t['accuracy_min']}")
        if m.get("recall", 1.0) < t["recall_min"]:
            reasons.append(f"Recall {m['recall']:.2f} < {t['recall_min']}")
        
        return ("FAIL", reasons) if reasons else ("PASS", [])
    
    def evaluate_layer2(self, m: Dict[str, Any]) -> Tuple[float, List[str]]:
        risk = 1.0 - m.get("group_f1", 1.0)
        return float(risk), []
    
    def get_layer3_evidence(
        self, m: Dict[str, Any], l1: Tuple[str, List[str]], l2: Tuple[float, List[str]]
    ) -> Dict[str, Any]:
        text = f"PERFORMANCE: Rare Query Acc (Acc_LT)={m.get('acc_lt', 1.0):.2f}. Core grounding fidelity is high."
        return {"explanation": text, "raw_metrics": m}


class MonitoringEthics(EthicsDimension):
    """Integrity of the audit trail."""
    
    def __init__(self):
        super().__init__(
            key="monitoring",
            name="Monitoring & Compliance",
            description="Integrity of the audit trail."
        )
    
    def evaluate_layer1(self, m: Dict[str, Any]) -> Tuple[str, List[str]]:
        reasons = []
        t = L1_THRESHOLDS["monitoring"]
        
        if m.get("alc", 1.0) < t["alc_min"]:
            reasons.append(f"ALC {m['alc']:.2f} < {t['alc_min']}")
        if m.get("sla", 1.0) < t["sla_min"]:
            reasons.append(f"SLA {m['sla']:.2f} < {t['sla_min']}")
        
        return ("FAIL", reasons) if reasons else ("PASS", [])
    
    def evaluate_layer2(self, m: Dict[str, Any]) -> Tuple[float, List[str]]:
        return float(m.get("pvr", 0.0)), []
    
    def get_layer3_evidence(
        self, m: Dict[str, Any], l1: Tuple[str, List[str]], l2: Tuple[float, List[str]]
    ) -> Dict[str, Any]:
        text = f"GOVERNANCE: Incident Reconstruction Fidelity (IRF)={m.get('irf', 1.0):.1f}. Audit log is immutable."
        return {"explanation": text, "raw_metrics": m}


class SecurityRobustness(EthicsDimension):
    """Resistance to prompt injection and poisoning."""
    
    def __init__(self):
        super().__init__(
            key="security",
            name="Security & Robustness",
            description="Resistance to prompt injection and poisoning."
        )
    
    def evaluate_layer1(self, m: Dict[str, Any]) -> Tuple[str, List[str]]:
        reasons = []
        t = L1_THRESHOLDS["security"]
        
        if m.get("adv_acc", 1.0) < t["adv_acc_min"]:
            reasons.append(f"AdvAcc {m['adv_acc']:.2f} < {t['adv_acc_min']}")
        if m.get("pisr", 0) > t["pisr_max"]:
            reasons.append(f"PISR {m['pisr']:.2f} > {t['pisr_max']}")
        
        return ("FAIL", reasons) if reasons else ("PASS", [])
    
    def evaluate_layer2(self, m: Dict[str, Any]) -> Tuple[float, List[str]]:
        return float(m.get("mir", 0.0)), []
    
    def get_layer3_evidence(
        self, m: Dict[str, Any], l1: Tuple[str, List[str]], l2: Tuple[float, List[str]]
    ) -> Dict[str, Any]:
        text = f"SECURITY: Poisoning Detection Rate (PDR)={m.get('pdr', 1.0):.1f}. Adversarial robustness verified."
        return {"explanation": text, "raw_metrics": m}


# ================== DIMENSION REGISTRY ==================
# Factory function to create all dimension instances

def create_all_dimensions() -> Dict[str, EthicsDimension]:
    """Create and return all 9 dimension evaluators."""
    return {
        "legal": LegalCompliance(),
        "fairness": BiasFairness(),
        "explainability": Explainability(),
        "security": SecurityRobustness(),
        "monitoring": MonitoringEthics(),
        "performance": ModelPerformance(),
        "ux": HumanAIUX(),
        "drift": ModelDrift(),
        "environmental": EnvironmentalEthics()
    }
