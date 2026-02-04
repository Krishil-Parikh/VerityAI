# RTI Ethics Engine: Input & Output Specification

Detailed API reference for the package components.

## 1. Input: Metrics Dictionary Shape

The primary input to `evaluate(metrics)` is a nested dictionary structured by logical dimensions.

### Dimensions & Metric Keys

| Dimension          | Key              | L1 Metrics (Gates)        | L2 Metrics (Risk)      | L3 Metrics (Forensic) |
| ------------------ | ---------------- | ------------------------- | ---------------------- | --------------------- |
| **Fairness**       | `fairness`       | `spd`, `di`, `eop`, `aod` | `fnrd`, `refusal_disp` | `mutual_info`         |
| **Drift**          | `drift`          | `psi`, `ks`               | `pred_drift`           | `embed_drift`         |
| **Explainability** | `explainability` | `confidence`              | `support_ratio`        | `stability`           |
| **Legal**          | `legal`          | `lawfulness`, `cvr`       | `proportionality`      | `explanation`         |
| **Performance**    | `performance`    | `accuracy`, `recall`      | `f1`                   | `group_f1`            |
| **UX**             | `ux`             | `tcr`, `sla`              | `cognitive_load`       | `dtc`                 |
| **Security**       | `security`       | `adv_acc`                 | `pisr`                 | `mir`                 |
| **Monitoring**     | `monitoring`     | `alc`                     | `pvr`                  | `irf`                 |
| **Environment**    | `environmental`  | `inf_cost`                | `gpu_hours`            | `compute_intensity`   |

---

## 2. Dynamic Computation: `build_metrics_from_raw_data`

Used to convert raw arrays and runtime data into the metrics dictionary above.

### Parameters

| Name                   | Type         | Description                                 |
| ---------------------- | ------------ | ------------------------------------------- |
| `query`                | `str`        | User input string                           |
| `response`             | `str`        | AI response string                          |
| `predictions`          | `np.ndarray` | Binary classification array (0/1)           |
| `labels`               | `np.ndarray` | Ground truth array (0/1)                    |
| `sensitive_attr`       | `np.ndarray` | Sensitive group indicator (0/1)             |
| `latency_ms`           | `float`      | Response time in milliseconds               |
| `output_tokens`        | `int`        | Token count of AI response                  |
| `grounding_score`      | `float`      | Score from grounding judge (0-1)            |
| `baseline_predictions` | `np.ndarray` | (Optional) Predictions for drift comparison |

---

## 3. Output: `EthicsResult` Schema

The object returned by evaluation gives detailed access to the 3-layer audit results.

### Summary Fields

- `final_label`: `ETHICAL` (Pass), `CONDITIONALLY_ETHICAL` (Review), `UNETHICAL` (Block)
- `s_llm`: Balanced audit score [0 to 1]
- `risk_band`: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`
- `layer1_status`: `PASS` (All gates green) or `FAIL`

### Accessor Methods

- `get_l1_metric(dim, key)`: Returns raw float value (e.g., `0.021`)
- `get_l2_risk(dim)`: Returns normalized risk [0 to 1]
- `get_l3_evidence(dim)`: Returns forensic explanation string or dictionary
- `get_failed_dims()`: List of dimension names that failed L1 gates
- `to_json()`: Serializes the entire audit trail to JSON
