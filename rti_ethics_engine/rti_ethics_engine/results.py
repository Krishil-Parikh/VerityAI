"""
RTI Ethics Engine - Results Module
EthicsResult dataclass with EXHAUSTIVE granular metric accessors and formatted output.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
import json


class RiskBand(Enum):
    """Risk classification bands."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class FinalLabel(Enum):
    """Final ethics decision labels."""
    ETHICAL = "ETHICAL"
    CONDITIONALLY_ETHICAL = "CONDITIONALLY_ETHICAL"
    UNETHICAL = "UNETHICAL"


# Dimension display names mapping
DIMENSION_NAMES = {
    "legal": "Legal Compliance",
    "fairness": "Bias & Fairness", 
    "explainability": "Explainability & Transparency",
    "security": "Security & Robustness",
    "monitoring": "Monitoring & Compliance",
    "performance": "Model Performance",
    "ux": "Human-AI UX",
    "drift": "Data & Model Drift",
    "environmental": "Environmental & Cost"
}


@dataclass
class DimensionResult:
    """Result for a single ethical dimension with FULL metric access."""
    key: str
    name: str
    l1_status: str
    l1_reasons: List[str]
    l2_risk: float
    l2_indicators: List[str]
    l3_evidence: Dict[str, Any]
    raw_metrics: Dict[str, Any]
    
    @property
    def passed_l1(self) -> bool:
        return self.l1_status == "PASS"
    
    @property
    def failed_l1(self) -> bool:
        return self.l1_status == "FAIL"
    
    def get_metric(self, metric_name: str, default: Any = None) -> Any:
        """Get a specific raw metric value."""
        return self.raw_metrics.get(metric_name, default)
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all raw metrics for this dimension."""
        return self.raw_metrics.copy()
    
    def format_l1_output(self) -> str:
        """Format L1 gate result for display."""
        icon = "✅" if self.passed_l1 else "❌"
        status_text = f"{icon} L1 {self.l1_status}"
        if self.l1_reasons:
            reasons = "; ".join(self.l1_reasons)
            return f"{status_text} | Violations: {reasons}"
        return status_text
    
    def format_l2_output(self) -> str:
        """Format L2 risk score for display."""
        risk_pct = self.l2_risk * 100
        if self.l2_risk < 0.3:
            icon = "🟢"
        elif self.l2_risk < 0.7:
            icon = "🟡"
        else:
            icon = "🔴"
        return f"{icon} L2 Risk: {risk_pct:.1f}%"
    
    def format_l3_output(self) -> str:
        """Format L3 evidence for display."""
        explanation = self.l3_evidence.get("explanation", "No evidence.")
        return f"📋 L3: {explanation}"
    
    def format_metrics_table(self) -> str:
        """Format all raw metrics as a table."""
        lines = []
        for k, v in self.raw_metrics.items():
            if isinstance(v, float):
                lines.append(f"    {k}: {v:.4f}")
            else:
                lines.append(f"    {k}: {v}")
        return "\n".join(lines)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "name": self.name,
            "l1_status": self.l1_status,
            "l1_reasons": self.l1_reasons,
            "l2_risk": self.l2_risk,
            "l2_indicators": self.l2_indicators,
            "l3_evidence": self.l3_evidence,
            "raw_metrics": self.raw_metrics
        }


@dataclass
class EthicsResult:
    """
    Complete ethics evaluation result with EXHAUSTIVE accessors.
    
    Access patterns:
    - result.final_label                         # "ETHICAL"
    - result.s_llm                               # 0.92
    - result.get_l1_metric("fairness", "spd")   # 0.02
    - result.get_l2_risk("legal")               # 0.0
    - result.get_l3_evidence("security")        # {"explanation": "..."}
    - result.print_full_audit()                 # Prints everything
    """
    
    final_label: str
    layer1_status: str
    layer2_risk_score: float
    s_llm: float
    risk_band: str
    required_action: str
    audit_id: str
    risk_vector: Dict[str, float]
    dimension_results: Dict[str, DimensionResult]
    layer3_evidence: Dict[str, Any]
    
    # ================== L1 METRIC ACCESS (GRANULAR) ==================
    
    def get_l1_metric(self, dimension: str, metric: str, default: float = 0.0) -> float:
        """Get raw L1 metric value. E.g. get_l1_metric('fairness', 'spd')"""
        dim = self.dimension_results.get(dimension)
        return dim.get_metric(metric, default) if dim else default
    
    def get_l1_status(self, dimension: str) -> str:
        """Get L1 status for dimension. Returns 'PASS' or 'FAIL'."""
        dim = self.dimension_results.get(dimension)
        return dim.l1_status if dim else "UNKNOWN"
    
    def get_l1_reasons(self, dimension: str) -> List[str]:
        """Get L1 failure reasons."""
        dim = self.dimension_results.get(dimension)
        return dim.l1_reasons if dim else []
    
    def get_all_l1_metrics(self, dimension: str) -> Dict[str, Any]:
        """Get ALL raw metrics for a dimension."""
        dim = self.dimension_results.get(dimension)
        return dim.get_all_metrics() if dim else {}
    
    # Individual L1 metric shortcuts
    @property
    def spd(self) -> float:
        """Statistical Parity Difference (Fairness L1)"""
        return self.get_l1_metric("fairness", "spd")
    
    @property
    def di(self) -> float:
        """Disparate Impact ratio (Fairness L1)"""
        return self.get_l1_metric("fairness", "di", 1.0)
    
    @property
    def eop(self) -> float:
        """Equal Opportunity Difference (Fairness L1)"""
        return self.get_l1_metric("fairness", "eop")
    
    @property
    def aod(self) -> float:
        """Average Odds Difference (Fairness L1)"""
        return self.get_l1_metric("fairness", "aod")
    
    @property
    def psi(self) -> float:
        """Population Stability Index (Drift L1)"""
        return self.get_l1_metric("drift", "psi")
    
    @property
    def ks(self) -> float:
        """Kolmogorov-Smirnov statistic (Drift L1)"""
        return self.get_l1_metric("drift", "ks")
    
    @property
    def lawfulness(self) -> float:
        """Lawfulness score (Legal L1)"""
        return self.get_l1_metric("legal", "lawfulness", 1.0)
    
    @property
    def accuracy(self) -> float:
        """Model accuracy (Performance L1)"""
        return self.get_l1_metric("performance", "accuracy")
    
    @property
    def recall(self) -> float:
        """Model recall (Performance L1)"""
        return self.get_l1_metric("performance", "recall")
    
    # ================== L2 RISK ACCESS ==================
    
    def get_l2_risk(self, dimension: str, default: float = 0.0) -> float:
        """Get L2 risk score for dimension [0, 1]."""
        dim = self.dimension_results.get(dimension)
        return dim.l2_risk if dim else default
    
    def get_l2_indicators(self, dimension: str) -> List[str]:
        """Get L2 risk indicators."""
        dim = self.dimension_results.get(dimension)
        return dim.l2_indicators if dim else []
    
    # ================== L3 EVIDENCE ACCESS ==================
    
    def get_l3_evidence(self, dimension: str) -> Dict[str, Any]:
        """Get L3 forensic evidence for dimension."""
        dim = self.dimension_results.get(dimension)
        return dim.l3_evidence if dim else {"explanation": "Not found."}
    
    def get_l3_explanation(self, dimension: str) -> str:
        """Get L3 explanation text."""
        return self.get_l3_evidence(dimension).get("explanation", "No explanation.")
    
    # ================== AGGREGATION HELPERS ==================
    
    def get_failed_dims(self) -> List[str]:
        """Get human-readable names of failed dimensions."""
        return [d.name for d in self.dimension_results.values() if d.failed_l1]
    
    def get_failed_dim_keys(self) -> List[str]:
        """Get keys of failed dimensions."""
        return [k for k, d in self.dimension_results.items() if d.failed_l1]
    
    def get_passed_dims(self) -> List[str]:
        """Get human-readable names of passed dimensions."""
        return [d.name for d in self.dimension_results.values() if d.passed_l1]
    
    def l1_pass_rate(self) -> float:
        """Fraction of L1 passes (e.g. 8/9 = 0.889)."""
        if not self.dimension_results:
            return 0.0
        return sum(1 for d in self.dimension_results.values() if d.passed_l1) / len(self.dimension_results)
    
    def l1_fail_count(self) -> int:
        return sum(1 for d in self.dimension_results.values() if d.failed_l1)
    
    def l1_pass_count(self) -> int:
        return sum(1 for d in self.dimension_results.values() if d.passed_l1)
    
    def get_highest_risk_dim(self) -> Tuple[str, float]:
        """Get (dimension_key, risk_score) of highest risk dimension."""
        if not self.risk_vector:
            return ("", 0.0)
        key = max(self.risk_vector, key=self.risk_vector.get)
        return (key, self.risk_vector[key])
    
    def get_dim_result(self, dimension: str) -> Optional[DimensionResult]:
        """Get full DimensionResult object."""
        return self.dimension_results.get(dimension)
    
    # ================== FORMATTED OUTPUT ==================
    
    def format_header(self) -> str:
        """Format audit header."""
        return f"{self.audit_id} | {self.final_label} | S_LLM={self.s_llm:.4f} | Risk={self.risk_band}"
    
    def format_l1_summary(self) -> str:
        """Format L1 summary table."""
        lines = ["LAYER 1 - HARD GATES (Pass/Fail Thresholds):"]
        for key, dim in self.dimension_results.items():
            icon = "✅" if dim.passed_l1 else "❌"
            reasons = f" [{'; '.join(dim.l1_reasons)}]" if dim.l1_reasons else ""
            lines.append(f"  {icon} {dim.name}: {dim.l1_status}{reasons}")
        lines.append(f"\n  L1 Pass Rate: {self.l1_pass_count()}/9 ({self.l1_pass_rate()*100:.1f}%)")
        return "\n".join(lines)
    
    def format_l2_summary(self) -> str:
        """Format L2 risk summary."""
        lines = ["LAYER 2 - WEIGHTED RISK SCORES:"]
        for key, dim in self.dimension_results.items():
            pct = dim.l2_risk * 100
            bar = "█" * int(pct / 10) + "░" * (10 - int(pct / 10))
            icon = "🟢" if dim.l2_risk < 0.3 else "🟡" if dim.l2_risk < 0.7 else "🔴"
            lines.append(f"  {icon} {dim.name}: {pct:5.1f}% [{bar}]")
        lines.append(f"\n  Total L2 Risk: {self.layer2_risk_score:.4f}")
        lines.append(f"  S_LLM Score: {self.s_llm:.4f}")
        return "\n".join(lines)
    
    def format_l3_summary(self) -> str:
        """Format L3 forensic evidence."""
        lines = ["LAYER 3 - FORENSIC EVIDENCE BUNDLE:"]
        for key, dim in self.dimension_results.items():
            explanation = dim.l3_evidence.get("explanation", "Forensic data available.")
            lines.append(f"  📋 {dim.name}:")
            lines.append(f"     └─ {explanation}")
        return "\n".join(lines)
    
    def format_risk_vector(self) -> str:
        """Format risk vector as JSON."""
        return json.dumps(self.risk_vector, indent=2)
    
    def format_metrics_details(self) -> str:
        """Format ALL raw metrics for ALL dimensions."""
        lines = ["RAW METRICS (All 36 Formulas):"]
        for key, dim in self.dimension_results.items():
            lines.append(f"\n  [{dim.name.upper()}]")
            for m, v in dim.raw_metrics.items():
                if isinstance(v, float):
                    lines.append(f"    • {m}: {v:.4f}")
                elif v is not None:
                    lines.append(f"    • {m}: {v}")
        return "\n".join(lines)
    
    def to_audit_table(self) -> str:
        """Compact audit table."""
        lines = [self.format_header()]
        for dim in self.dimension_results.values():
            icon = "✅" if dim.passed_l1 else "❌"
            lines.append(f"{icon} {dim.name}: L2={dim.l2_risk:.2f}")
        return "\n".join(lines)
    
    def print_audit_table(self) -> None:
        """Print compact audit table."""
        print(self.to_audit_table())
    
    def print_full_audit(self) -> None:
        """Print EXHAUSTIVE audit output with L1, L2, L3 details."""
        print("\n" + "=" * 80)
        print("⚖️  RTI ETHICS ENGINE - FULL AUDIT REPORT")
        print("=" * 80)
        print(f"\n📌 {self.format_header()}")
        print(f"📌 Action Required: {self.required_action}")
        print("\n" + "-" * 80)
        print(self.format_l1_summary())
        print("\n" + "-" * 80)
        print(self.format_l2_summary())
        print("\n" + "-" * 80)
        print(self.format_l3_summary())
        print("\n" + "-" * 80)
        print("RISK VECTOR [R_1...R_9]:")
        print(self.format_risk_vector())
        print("\n" + "=" * 80)
        
        # Final verdict
        if self.final_label == "UNETHICAL":
            print("🚨 [CRITICAL] PROTOCOL BREACHED - OUTPUT BLOCKED 🚨")
        elif self.final_label == "CONDITIONALLY_ETHICAL":
            print("⚠️  [WARNING] PARTIAL COMPLIANCE - HUMAN REVIEW REQUIRED ⚠️")
        else:
            print("✅ [PASS] ETHICAL COMPLIANCE VERIFIED")
        print("=" * 80 + "\n")
    
    def print_metrics_details(self) -> None:
        """Print all 36 raw metric values."""
        print(self.format_metrics_details())
    
    # ================== SERIALIZATION ==================
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "final_label": self.final_label,
            "layer1_status": self.layer1_status,
            "layer2_risk_score": self.layer2_risk_score,
            "s_llm": self.s_llm,
            "risk_band": self.risk_band,
            "required_action": self.required_action,
            "audit_id": self.audit_id,
            "risk_vector": self.risk_vector,
            "dimension_results": {k: v.to_dict() for k, v in self.dimension_results.items()},
            "layer3_evidence": self.layer3_evidence
        }
    
    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)
    
    def __repr__(self) -> str:
        return f"EthicsResult(label={self.final_label}, s_llm={self.s_llm:.3f}, band={self.risk_band})"
