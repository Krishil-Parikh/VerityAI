# RTI Ethics Engine (v2.0.0)

**India's first granular AI ethics framework for RTI applications** - A production-ready Python package implementing 36 metrics across 9 ethical dimensions with granular formula access and dynamic data computation.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🚀 Installation

```bash
pip install rti-ethics-engine
```

## ⚡ Quick Start (Dynamic Mode)

The recommended way to use the engine is to compute metrics directly from your application data:

```python
import numpy as np
from rti_ethics_engine import evaluate_from_raw

# 1. Prepare your data
query = "What is the budget for the Metro project?"
response = "The budget for the Metro project is 5000 Crores..."
predictions = np.array([1, 1, 0, 1])  # Model predictions
labels = np.array([1, 1, 1, 1])       # Ground truth
sensitive_attr = np.array([0, 1, 0, 1]) # Demographic group (e.g. Urban/Rural)

# 2. Evaluate with one call
result = evaluate_from_raw(
    query=query,
    response=response,
    predictions=predictions,
    labels=labels,
    sensitive_attr=sensitive_attr,
    latency_ms=450.0,
    grounding_score=0.92
)

# 3. Get results
print(f"Label: {result.final_label}")  # "ETHICAL"
print(f"S_LLM Score: {result.s_llm}")  # 0.942
print(f"Risk Band: {result.risk_band}") # "LOW"
```

## 📊 The 3-Layer Audit Protocol

The RTI Ethics Engine uses a rigorous 3-layer protocol for every dimension:

1.  **Layer 1: Hard Gates (L1)** - Pass/Fail compliance checks (e.g., Statistical Parity < 0.1).
2.  **Layer 2: Risk Scoring (L2)** - Normalized risk vectors weighted by policy importance.
3.  **Layer 3: Forensic Evidence (L3)** - Detailed context and reasoning for the scores.

### Granular Access

```python
# Check if a specific dimension passed its hard gates
if result.get_l1_status("fairness") == "FAIL":
    print(f"Fairness fail reasons: {result.get_l1_reasons('fairness')}")

# Get granular metric values (36 metrics available)
spd = result.get_l1_metric("fairness", "spd")
psi = result.get_l1_metric("drift", "psi")

# Export complete audit trail
audit_json = result.to_json()
```

## 🏗️ 9 Ethical Dimensions

| Dimension            | Description                          | Key Metrics                     |
| -------------------- | ------------------------------------ | ------------------------------- |
| **Legal Compliance** | RTI Act 2005 & Data Policy alignment | Lawfulness, Consent Validity    |
| **Bias & Fairness**  | Demographic equity across groups     | SPD, DI, EOP, AOD               |
| **Explainability**   | Transparency & Model Confidence      | FI Sum, Counterfactual Distance |
| **Security**         | Robustness against prompt injection  | PISR, Adversarial Accuracy      |
| **Monitoring**       | Audit trail & SLA integrity          | Audit Completeness, SLA rate    |
| **Performance**      | Statistical accuracy of responses    | Recall, Group-F1, Accuracy      |
| **Human-AI UX**      | User friction and frustration levels | TCR, Cognitive Load             |
| **Drift**            | Model/Data stability over time       | PSI, KS-Statistic               |
| **Environment**      | Carbon footprint & compute cost      | GPU Hours, Inference Cost       |

## 📖 Documentation

For detailed input/output schemas and advanced configuration, see:

- [API Reference (INPUTS_OUTPUTS.md)](https://github.com/Krishil-Parikh/bazinga_tsec_hacks/blob/krishil/rti_ethics_engine/INPUTS_OUTPUTS.md)
- [Mathematical Manifest (calculators.py)](https://github.com/Krishil-Parikh/bazinga_tsec_hacks/blob/krishil/rti_ethics_engine/rti_ethics_engine/calculators.py)

## 🧪 Testing

```bash
pytest tests/ -v
```

## 🇮🇳 Why RTI Ethics Engine?

Designed specifically for **Right to Information (RTI)** workflows, it ensures that AI systems responding to citizen queries are:

- **Legally Sound:** Compliant with Section 4/8 of the RTI Act.
- **Fair:** No bias between rural/urban or language variations.
- **Auditable:** Providing forensic evidence for Central Information Commission (CIC) audits.

---

**License:** MIT | **Support:** [github.com/rti-ethics/rti-ethics-engine](https://github.com/rti-ethics/rti-ethics-engine)
