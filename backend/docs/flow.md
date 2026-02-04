This is the **last missing piece** — how values from **Layer 1, Layer 2, and Layer 3** actually turn into a **single final system output**.

I’ll give you a **crisp, deterministic decision protocol** that you can **directly implement**, explain to a government reviewer, and defend in a paper.

---

## Big Picture: What Each Layer Produces

Before combining anything, be clear about **outputs**, not metrics.

| Layer       | Produces                                | Type               |
| ----------- | --------------------------------------- | ------------------ |
| **Layer 1** | Pass / Fail flags per dimension         | Boolean            |
| **Layer 2** | Risk score per dimension + overall risk | Continuous ([0,1]) |
| **Layer 3** | Evidence bundle (logs, explanations)    | Structured record  |

⚠️ **You do NOT numerically combine all three layers.**

They are combined **procedurally**, not mathematically.

---

## Step-by-Step Final Output Logic (Authoritative)

### ✅ Step 1: Evaluate Layer 1 (Hard Gate)

For each ethical dimension (d):

[
L1_d =
\begin{cases}
1 & \text{if all Layer-1 metrics satisfy thresholds} \
0 & \text{otherwise}
\end{cases}
]

Define overall Layer 1 result:

[
L1 = \bigwedge_d L1_d
]

### 🔴 If (L1 = 0)

➡️ **FINAL OUTPUT = UNETHICAL**

Stop here.
Layer 2 is **not consulted**.
Layer 3 is invoked **only to explain** the failure.

---

### ✅ Step 2: Compute Layer 2 Risk (Only if Layer 1 Passed)

For each dimension (d):

[
R_d = \sum_{m \in d} w_{m|d} \cdot r_m
]

Aggregate across dimensions:

[
R_{\text{total}} = \sum_d \beta_d \cdot R_d
]

Where:

- (r_m \in [0,1]) = normalized risk of metric (m)
- (w\_{m|d}) = metric-level weights
- (\beta_d) = dimension-level weights

---

### 🔹 Step 3: Apply Risk Thresholds (Ternary Decision)

Define two policy thresholds:

- ( \tau_1 ) = low-risk boundary
- ( \tau_2 ) = high-risk boundary
  with ( 0 < \tau_1 < \tau_2 \le 1 )

Decision rule:

[
\text{Final Label} =
\begin{cases}
\textbf{ETHICAL} & R_{\text{total}} \le \tau_1 \
\textbf{CONDITIONALLY ETHICAL} & \tau_1 < R_{\text{total}} \le \tau_2 \
\textbf{UNETHICAL} & R_{\text{total}} > \tau_2
\end{cases}
]

📌 **This is where binary → 3-class happens.**

---

### 🧾 Step 4: Attach Layer 3 Evidence (Always)

Regardless of the label, attach:

- Which Layer 1 checks passed/failed
- Layer 2 risk breakdown by dimension
- Top-contributing metrics
- Counterfactuals (if relevant)
- Logs, timestamps, model version

Layer 3 **never changes** the label.

---

## Final Output Structure (What Your System Returns)

Your system should return a **structured object**, not just a label.

### Example (JSON-like)

```json
{
  "final_label": "CONDITIONALLY_ETHICAL",
  "layer1_status": "PASS",
  "layer2_risk_score": 0.42,
  "risk_band": "MEDIUM",
  "dimension_risks": {
    "fairness": 0.18,
    "legal_compliance": 0.11,
    "transparency": 0.07,
    "security": 0.04
  },
  "required_action": "HUMAN_REVIEW",
  "layer3_evidence": {
    "failed_metrics": [],
    "high_risk_metrics": ["Refusal Disparity"],
    "explanations": "Counterfactual available",
    "audit_id": "RTI-AI-2026-00192"
  }
}
```

This format is **auditor-friendly**.

---

## Why You Must NOT “Combine” Layer 3 Numerically

Because Layer 3 contains:

- qualitative explanations,
- causal traces,
- legal justifications.

Averaging these would be meaningless and legally indefensible.

---

## Common Mistakes to Avoid (Important)

❌ “Final score = L1 + L2 + L3”
❌ “Weighted sum of all layers”
❌ “Layer 3 overrides Layer 1”
❌ “Single scalar ethics score only”

Government reviewers _hate_ these.

---

## One-Line Decision Algorithm (Put This in Your Paper)

> _The system first enforces a hard ethical gate (Layer 1). If passed, it computes a risk-weighted ethical score (Layer 2) to assign a ternary classification. Layer 3 then attaches non-decisional forensic evidence to support auditability, appeals, and governance._

That’s it. That sentence is **gold-standard**.

---

## If You Want Next

I can:

- write **pseudo-code** for the entire pipeline,
- help you **define τ₁ and τ₂ from data or policy**, or
- simulate **real RTI examples end-to-end**.

You’ve now fully closed the loop from metrics → decision → governance.
