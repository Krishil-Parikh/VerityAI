# RTI Ethics Engine

**India's first granular AI ethics framework for RTI applications** - A production-ready Python package implementing 36 metrics across 9 ethical dimensions with granular formula access.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🚀 Installation

```bash
pip install rti-ethics-engine
```

Or install from source:

```bash
git clone https://github.com/rti-ethics/rti-ethics-engine.git
cd rti-ethics-engine
pip install -e .
```

## ⚡ Quick Start

```python
from rti_ethics_engine import evaluate

# Define your metrics
metrics = {
    "fairness": {"spd": 0.02, "di": 1.0, "eop": 0.05, "aod": 0.03},
    "drift": {"psi": 0.1, "ks": 0.02},
    "legal": {"lawfulness": 1.0, "cvr": 0.98},
    "performance": {"accuracy": 0.92, "recall": 0.88},
    "explainability": {"confidence": 0.85, "fi": 0.3},
    "security": {"adv_acc": 0.8, "pisr": 0.02},
    "monitoring": {"alc": 0.98, "sla": 0.995},
    "ux": {"tcr": 0.92, "ftr": 0.08},
    "environmental": {"inf_cost": 0.02, "gpu_hours": 0.05}
}

# Evaluate
result = evaluate(metrics)

# Get the decision
print(result.final_label)    # "ETHICAL"
print(result.s_llm)          # 0.9234 (LLM Ethics Score)
print(result.risk_band)      # "LOW"
```

## 🎯 Granular Metric Access

The killer feature - access ANY formula value at ANY layer:

```python
# Access specific L1 formula values
spd = result.get_l1_metric("fairness", "spd")      # 0.02
psi = result.get_l1_metric("drift", "psi")         # 0.1
accuracy = result.get_l1_metric("performance", "accuracy")  # 0.92

# Access L2 risk scores
fairness_risk = result.get_l2_risk("fairness")     # 0.12
legal_risk = result.get_l2_risk("legal")           # 0.00

# Access L3 forensic evidence
explanation = result.get_l3_evidence("legal")["explanation"]

# Aggregation helpers
failed_dims = result.get_failed_dims()   # ["Legal Compliance"]
pass_rate = result.l1_pass_rate()        # 0.889 (8/9 passed)

# Audit table for CIC compliance
result.print_audit_table()
# RTI-2026035174555 | ETHICAL | S_LLM=0.92
# ✅ Legal Compliance: L2=0.02
# ✅ Bias & Fairness: L2=0.05
# ...
```

## 📊 9 Ethical Dimensions

| Dimension            | L1 Metrics          | Description            |
| -------------------- | ------------------- | ---------------------- |
| **Legal Compliance** | lawfulness, cvr     | RTI Act 2005 alignment |
| **Bias & Fairness**  | spd, di, eop, aod   | Demographic equity     |
| **Explainability**   | confidence, fi      | Model interpretability |
| **Security**         | adv_acc, pisr       | Adversarial robustness |
| **Monitoring**       | alc, sla            | Audit trail integrity  |
| **Performance**      | accuracy, recall    | Statistical accuracy   |
| **Human-AI UX**      | tcr, ftr            | User friction          |
| **Drift**            | psi, ks             | Model stability        |
| **Environmental**    | inf_cost, gpu_hours | Carbon footprint       |

## 🏗️ Architecture

```
rti_ethics_engine/
├── __init__.py      # Public API
├── config.py        # Thresholds & weights
├── dimensions.py    # 9 dimension evaluators
├── core.py          # EthicsEngine orchestrator
├── results.py       # EthicsResult with accessors
└── metrics.py       # Computation helpers
```

## 📖 API Reference

### `evaluate(metrics: dict) -> EthicsResult`

Quick evaluation entrypoint.

### `EthicsEngine`

Full engine with `run_protocol()` method.

### `EthicsResult`

Result object with:

- `final_label`: "ETHICAL" / "CONDITIONALLY_ETHICAL" / "UNETHICAL"
- `s_llm`: LLM Ethics Score [0, 1]
- `risk_band`: "LOW" / "MEDIUM" / "HIGH" / "CRITICAL"
- `get_l1_metric(dim, metric)`: Access any L1 formula value
- `get_l2_risk(dim)`: Get dimension risk score
- `get_l3_evidence(dim)`: Get forensic evidence
- `get_failed_dims()`: List failed dimensions
- `l1_pass_rate()`: Fraction of L1 passes
- `to_json()`: Export as JSON

## 🧪 Testing

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

## 📄 License

MIT License - See [LICENSE](LICENSE) for details.

## 🇮🇳 Made for India

Designed specifically for RTI Act 2005 compliance and CIC audit requirements.
