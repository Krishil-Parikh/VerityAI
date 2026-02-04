"""
RTI Ethics Engine - Core Tests
Tests for EthicsEngine and evaluation protocol.
"""

import pytest
from rti_ethics_engine import (
    EthicsEngine, 
    EthicsResult, 
    evaluate,
    L1_THRESHOLDS,
    DIMENSION_WEIGHTS,
    build_default_metrics
)


class TestEthicsEngine:
    """Test suite for EthicsEngine."""
    
    def test_engine_initialization(self):
        """Test engine initializes with all 9 dimensions."""
        engine = EthicsEngine()
        assert len(engine.dimensions) == 9
        assert len(engine.weights) == 9
    
    def test_all_pass_returns_ethical(self):
        """Test that passing all L1 gates with low risk returns ETHICAL."""
        metrics = build_default_metrics()
        result = evaluate(metrics)
        
        assert result.final_label == "ETHICAL"
        assert result.risk_band == "LOW"
        assert result.layer1_status == "PASS"
        assert result.l1_pass_rate() == 1.0
    
    def test_legal_fail_returns_conditionally_ethical(self):
        """Test that failing legal L1 returns CONDITIONALLY_ETHICAL."""
        metrics = build_default_metrics()
        metrics["legal"]["lawfulness"] = 0.9  # Below threshold of 1.0
        
        result = evaluate(metrics)
        
        assert result.final_label == "CONDITIONALLY_ETHICAL"
        assert result.risk_band == "MEDIUM"
        assert "Legal Compliance" in result.get_failed_dims()
    
    def test_fairness_spd_fail(self):
        """Test that failing fairness SPD triggers L1 FAIL."""
        metrics = build_default_metrics()
        metrics["fairness"]["spd"] = 0.15  # Above threshold of 0.1
        
        result = evaluate(metrics)
        
        assert result.get_l1_status("fairness") == "FAIL"
        assert "Bias & Fairness" in result.get_failed_dims()
    
    def test_high_risk_returns_unethical(self):
        """Test that high aggregate risk returns UNETHICAL."""
        metrics = {}
        for key in ["legal", "fairness", "explainability", "security", 
                    "monitoring", "performance", "ux", "drift", "environmental"]:
            metrics[key] = {}  # All empty = all L1 PASS with default behavior
        
        # Force high L2 risk by failing multiple L1 gates
        metrics["legal"]["lawfulness"] = 0.5
        metrics["fairness"]["spd"] = 0.5
        metrics["security"]["adv_acc"] = 0.3
        metrics["performance"]["accuracy"] = 0.3
        
        result = evaluate(metrics)
        
        assert result.layer2_risk_score > 0.7
        assert result.final_label == "UNETHICAL"
        assert result.risk_band in ["HIGH", "CRITICAL"]
    
    def test_audit_id_format(self):
        """Test audit ID has correct format."""
        result = evaluate(build_default_metrics())
        assert result.audit_id.startswith("RTI-")
        assert len(result.audit_id) > 10


class TestGranularAccess:
    """Test suite for granular metric access."""
    
    def test_get_l1_metric(self):
        """Test granular L1 metric access."""
        metrics = build_default_metrics()
        metrics["fairness"]["spd"] = 0.023
        metrics["drift"]["psi"] = 0.15
        
        result = evaluate(metrics)
        
        assert result.get_l1_metric("fairness", "spd") == 0.023
        assert result.get_l1_metric("drift", "psi") == 0.15
    
    def test_get_l1_metric_default(self):
        """Test L1 metric access with default value."""
        result = evaluate(build_default_metrics())
        
        # Non-existent metric
        assert result.get_l1_metric("fairness", "nonexistent", 999) == 999
        # Non-existent dimension
        assert result.get_l1_metric("nonexistent", "spd", 999) == 999
    
    def test_get_l2_risk(self):
        """Test L2 risk score access."""
        result = evaluate(build_default_metrics())
        
        assert 0 <= result.get_l2_risk("fairness") <= 1
        assert 0 <= result.get_l2_risk("legal") <= 1
    
    def test_get_l3_evidence(self):
        """Test L3 evidence access."""
        result = evaluate(build_default_metrics())
        
        evidence = result.get_l3_evidence("legal")
        assert "explanation" in evidence
    
    def test_get_failed_dims(self):
        """Test failed dimensions helper."""
        metrics = build_default_metrics()
        metrics["legal"]["lawfulness"] = 0.9
        
        result = evaluate(metrics)
        
        failed = result.get_failed_dims()
        assert isinstance(failed, list)
        assert "Legal Compliance" in failed
    
    def test_l1_pass_rate(self):
        """Test L1 pass rate calculation."""
        metrics = build_default_metrics()
        metrics["legal"]["lawfulness"] = 0.9  # FAIL
        
        result = evaluate(metrics)
        
        # 8/9 = 0.888...
        assert 0.88 < result.l1_pass_rate() < 0.90
    
    def test_dimension_result_properties(self):
        """Test DimensionResult object properties."""
        result = evaluate(build_default_metrics())
        
        dim = result.get_dim_result("fairness")
        assert dim is not None
        assert dim.key == "fairness"
        assert dim.name == "Bias & Fairness"
        assert dim.passed_l1 == True


class TestOutputFormatters:
    """Test suite for output formatters."""
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        result = evaluate(build_default_metrics())
        d = result.to_dict()
        
        assert "final_label" in d
        assert "s_llm" in d
        assert "dimension_results" in d
    
    def test_to_json(self):
        """Test JSON export."""
        result = evaluate(build_default_metrics())
        json_str = result.to_json()
        
        assert isinstance(json_str, str)
        assert "final_label" in json_str
    
    def test_to_audit_table(self):
        """Test audit table generation."""
        result = evaluate(build_default_metrics())
        table = result.to_audit_table()
        
        assert result.audit_id in table
        assert result.final_label in table
        assert "✅" in table or "❌" in table


class TestThresholds:
    """Test L1 threshold validation."""
    
    def test_fairness_thresholds(self):
        """Test fairness L1 thresholds."""
        t = L1_THRESHOLDS["fairness"]
        assert t["spd"] == 0.1
        assert t["di_min"] == 0.8
        assert t["di_max"] == 1.25
    
    def test_legal_thresholds(self):
        """Test legal L1 thresholds."""
        t = L1_THRESHOLDS["legal"]
        assert t["lawfulness"] == 1.0
        assert t["cvr_min"] == 0.95
    
    def test_dimension_weights_sum(self):
        """Test dimension weights (should sum to ~1.24)."""
        total = sum(DIMENSION_WEIGHTS.values())
        assert 1.2 < total < 1.3  # Raw weights, no normalization


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
