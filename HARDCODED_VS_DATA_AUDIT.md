# RTI Ethics Engine — Hardcoded vs Data-Driven Audit

> Per-metric audit of all **9 dimensions × 3 layers** showing which values come from real data and which are hardcoded.

---

## Summary Legend

| Symbol                     | Meaning                                              |
| -------------------------- | ---------------------------------------------------- |
| ✅ **Data-Driven**         | Computed from actual inputs / CSV data at runtime    |
| ⚠️ **Partially Hardcoded** | Some sub-values or fallbacks are hardcoded constants |
| ❌ **Hardcoded**           | Static constant — never changes regardless of input  |

---

## Overall Status

| #   | Dimension            | Status         | Data-Driven Metrics | Hardcoded Metrics | Notes                                                                              |
| --- | -------------------- | -------------- | ------------------: | ----------------: | ---------------------------------------------------------------------------------- |
| 1   | Bias & Fairness      | ⚠️ Partial     |              8 of 9 |            1 of 9 | `counterfactual` is hardcoded 0.02                                                 |
| 2   | Data & Model Drift   | ✅ Data-Driven |              5 of 5 |            0 of 5 | Now wired to `baseline_metrics.csv` — PSI, KS, pred_drift, conf_drift all computed |
| 3   | Environmental / Cost | ⚠️ Partial     |              4 of 5 |            1 of 5 | `hardware_util` hardcoded 0.95                                                     |
| 4   | Explainability       | ⚠️ Partial     |              2 of 4 |            2 of 4 | `counterfactual_dist` = 0.8, `exp_stability` = 0.95                                |
| 5   | User Experience (UX) | ✅ Mostly      |              4 of 5 |            1 of 5 | `ftr` uses simple boolean fallback                                                 |
| 6   | Legal Compliance     | ⚠️ Partial     |              2 of 4 |            2 of 4 | `proportionality` = 1.0, `dpia` = 1.0                                              |
| 7   | Performance          | ⚠️ Partial     |              3 of 4 |            1 of 4 | `acc_lt` is just a copy of accuracy (no long-tail data)                            |
| 8   | Monitoring           | ✅ Data-Driven |              4 of 4 |            0 of 4 | All computed — but caller often passes defaults (1,1,1,0)                          |
| 9   | Security             | ⚠️ Partial     |              3 of 4 |            1 of 4 | `pdr` hardcoded 1.0 (needs training data audit)                                    |

---

## Detailed Per-Metric Breakdown

### 1. Bias & Fairness

| Layer | Metric           | Status | Source / Comment                                                                     |
| ----- | ---------------- | ------ | ------------------------------------------------------------------------------------ |
| L1    | `spd`            | ✅     | `compute_spd()` from `predictions[]` + `sensitive_attr[]` — uses `fairness_data.csv` |
| L1    | `di`             | ✅     | `compute_di()` from same arrays                                                      |
| L1    | `eop`            | ✅     | `compute_eop()` — requires `labels[]` (ground truth) too                             |
| L1    | `aod`            | ✅     | `compute_aod()` — same triple input                                                  |
| L2    | `fnrd`           | ✅     | `compute_fnrd()` — FNR difference between groups                                     |
| L2    | `pred_parity`    | ✅     | `compute_predictive_parity()` — PPV difference                                       |
| L2    | `refusal_disp`   | ✅     | `compute_refusal_disparity()` — refusal rate gap                                     |
| L3    | `counterfactual` | ❌     | **Hardcoded `0.02`** — comment says "Needs causal model"                             |
| L3    | `mi_leakage`     | ✅     | `compute_mutual_info_leakage()` from predictions+groups                              |

**Data source**: `fairness_data.csv` columns `sensitive_group`, `ground_truth_disclose`, `system_disclose`, `tp`, `fp`, `fn`, `tn`. In `batch_simulator.py`, `sensitive_attr` is derived from query text keywords (`"ji"`, `"respected"`, `"sir"`).

---

### 2. Data & Model Drift

| Layer | Metric       | Status | Source / Comment                                                             |
| ----- | ------------ | ------ | ---------------------------------------------------------------------------- |
| L1    | `psi`        | ✅     | `compute_psi()` — needs `baseline_predictions` from `baseline_metrics.csv`   |
| L1    | `ks`         | ✅     | `compute_ks_statistic()` — same baseline comparison                          |
| L2    | `pred_drift` | ✅     | `compute_prediction_drift()` — mean shift current vs baseline                |
| L2    | `conf_drift` | ✅     | `compute_confidence_drift()` — now passed via `current_confidences` kwarg    |
| L3    | `emb_drift`  | ⚠️     | Falls back to **`0.0`** when `current_embeddings` not passed (rarely passed) |

**Data source**: `baseline_metrics.csv` columns `system_disclose`, `confidence`. Now connected — `batch_simulator.py` and `query_api.py` both load baseline data at startup and pass it to `build_metrics_from_raw_data()`.

---

### 3. Environmental / Cost Ethics

| Layer | Metric                     | Status | Source / Comment                                                              |
| ----- | -------------------------- | ------ | ----------------------------------------------------------------------------- |
| L1    | `inf_cost`                 | ✅     | `compute_inference_cost(latency_sec, cost_per_second)` — latency is real      |
| L1    | `gpu_hours`                | ✅     | `compute_gpu_hours(latency_sec)` — derived from latency                       |
| L2    | `compute_intensity`        | ⚠️     | FLOPs estimated as `output_tokens × 1e6` (rough constant multiplier)          |
| L2    | `hardware_util`            | ❌     | **Hardcoded `0.95`** — comment: "Would need system monitoring for real value" |
| L3    | `cur` (Cost-Utility Ratio) | ⚠️     | `compute_cost_utility_ratio(inf_cost, 1.0)` — info gain fixed at **1.0**      |

**Data source**: `query_api_metrics.csv` columns `latency_ms`, `output_tokens`, `input_tokens`. Real latency comes from timing the LLM call.

---

### 4. Explainability & Transparency

| Layer | Metric                    | Status | Source / Comment                                                                                     |
| ----- | ------------------------- | ------ | ---------------------------------------------------------------------------------------------------- |
| L1    | `confidence`              | ✅     | Proxied from `grounding_score` (real, from RAG overlap analysis)                                     |
| L1    | `fi` (Feature Importance) | ⚠️     | `min(1.0, citation_coverage + 0.5)` — `citation_coverage` defaults to 0.0 → fi = **0.5** in practice |
| L2    | `counterfactual_dist`     | ❌     | **Hardcoded `0.8`** — comment: "Would need actual counterfactual generation"                         |
| L3    | `exp_stability`           | ❌     | **Hardcoded `0.95`** — comment: "Would need perturbation analysis"                                   |

**Data source**: `query_api_metrics.csv` columns `grounding_score`, `l1_citation_coverage`. Grounding is computed via word overlap between response and retrieved context.

---

### 5. User Experience (UX)

| Layer | Metric                       | Status | Source / Comment                                                                      |
| ----- | ---------------------------- | ------ | ------------------------------------------------------------------------------------- |
| L1    | `tcr` (Task Completion Rate) | ✅     | `compute_task_completion_rate(completed, total)` — derived from `task_completed` bool |
| L1    | `ftr` (Frustration Rate)     | ⚠️     | Simple `0.0 if task_completed else 0.5` — no real frustration signal                  |
| L2    | `dtc` (Dialogue Turn Count)  | ✅     | Passed as `turn_count` parameter (default 1)                                          |
| L2    | `cognitive_load`             | ✅     | `compute_cognitive_load()` from FK readability score                                  |
| L3    | `readability_fk`             | ✅     | `compute_readability_fk(response_text)` — real text analysis                          |

**Data source**: Response text is analyzed live. `task_completed` defaults to `True` in practice. `turn_count` defaults to `1`.

---

### 6. Legal Compliance

| Layer | Metric                          | Status | Source / Comment                                                                   |
| ----- | ------------------------------- | ------ | ---------------------------------------------------------------------------------- |
| L1    | `lawfulness`                    | ✅     | Regex pattern matching on response for "Section X", "RTI Act", exemption citations |
| L1    | `cvr` (Consent Validity Rate)   | ⚠️     | `1.0 if has_consent else 0.0` — `has_consent` defaults to `True`                   |
| L2    | `proportionality`               | ❌     | **Hardcoded `1.0`** — comment: "Would need request analysis"                       |
| L3    | `dpia` (Data Protection Impact) | ❌     | **Hardcoded `1.0`** — comment: "Would need risk assessment"                        |

**Data source**: Query text + response text analyzed via regex for legal patterns. No dedicated legal CSV.

---

### 7. Performance

| Layer | Metric                        | Status | Source / Comment                                                      |
| ----- | ----------------------------- | ------ | --------------------------------------------------------------------- |
| L1    | `accuracy`                    | ✅     | `compute_accuracy(labels, predictions)` from ground truth             |
| L1    | `recall`                      | ✅     | `compute_recall(labels, predictions)` from ground truth               |
| L2    | `group_f1`                    | ✅     | `compute_group_f1()` with sensitive groups, or `compute_f1()` without |
| L3    | `acc_lt` (Long-tail Accuracy) | ⚠️     | Just copies `accuracy` — no actual long-tail frequency data           |

**Data source**: `fairness_data.csv` columns `tp`, `fp`, `fn`, `tn`; `query_api_metrics.csv` column `grounding_score` used as fallback proxy. In `batch_simulator.py`, labels and predictions are derived from query ground truth + refusal keyword detection.

---

### 8. Monitoring & Accountability

| Layer | Metric                           | Status | Source / Comment                                   |
| ----- | -------------------------------- | ------ | -------------------------------------------------- |
| L1    | `alc` (Audit Log Completeness)   | ✅     | `compute_audit_log_completeness(logged, total)`    |
| L1    | `sla` (SLA Compliance)           | ✅     | `compute_sla_compliance(within_sla, total)`        |
| L2    | `pvr` (Policy Violation Rate)    | ✅     | `compute_policy_violation_rate(violations, total)` |
| L3    | `irf` (Incident Replay Fidelity) | ✅     | `replayable / total` ratio                         |

**Data source**: Operational counters passed as kwargs. In practice, `batch_simulator.py` does NOT pass these explicitly, so defaults apply: `total_requests=1, logged_requests=1, within_sla=1, policy_violations=0` → all metrics show perfect scores.

> ⚠️ While formulas are data-driven, the **callers always pass perfect defaults**, making this dimension effectively **always-passing** in current deployment.

---

### 9. Security & Robustness

| Layer | Metric                                 | Status | Source / Comment                                                |
| ----- | -------------------------------------- | ------ | --------------------------------------------------------------- |
| L1    | `adv_acc` (Adversarial Accuracy)       | ✅     | Regex checks for injection patterns in query text               |
| L1    | `pisr` (Prompt Injection Success Rate) | ✅     | Based on `injection_blocked` flag + injection detection         |
| L2    | `mir` (Membership Inference Risk)      | ✅     | Regex checks for PII patterns (phone, PAN, Aadhaar) in response |
| L3    | `pdr` (Prompt Defense Rate)            | ❌     | **Hardcoded `1.0`** — comment: "Would need training data audit" |

**Data source**: `adversarial_tests.csv` (61 test cases with `attack_category`, `safe`, `attack_success`). In runtime, query/response text is analyzed via regex. `injection_blocked` defaults to `True`.

---

## CSV Data Files Summary

| CSV File                    | Rows | Used By Dimensions          | Key Columns                                                                                    |
| --------------------------- | ---: | --------------------------- | ---------------------------------------------------------------------------------------------- |
| `query_api_metrics.csv`     | 1142 | All (primary log)           | `grounding_score`, `latency_ms`, `output_tokens`, `spd`, `di`, `eop`, `aod`, `dimensions_json` |
| `fairness_data.csv`         |   49 | Fairness, Performance       | `sensitive_group`, `ground_truth_disclose`, `system_disclose`, `tp`, `fp`, `fn`, `tn`          |
| `baseline_metrics.csv`      |    5 | Drift                       | `grounding_score`, `confidence`, `psi_score`, `ks_score`, `embedding_drift_l2`                 |
| `adversarial_tests.csv`     |   61 | Security                    | `attack_category`, `safe`, `attack_success`, `severity`                                        |
| `dimension_config.csv`      |   31 | Config (thresholds/weights) | `dimension_name`, `metric_name`, `weight`, `threshold_low`, `threshold_high`                   |
| `gold_rti_eval.csv`         |  101 | Performance (gold standard) | `gold_answer`, `label_correct`, `f1_token_overlap`, `legal_compliance_gold`                    |
| `conversations_metrics.csv` |  758 | Dashboard display           | Same schema as `query_api_metrics.csv`                                                         |

---

## Key Findings

### Fully Hardcoded Constants (Never Change)

1. **`fairness.counterfactual`** = 0.02 (needs causal inference model)
2. **`environmental.hardware_util`** = 0.95 (needs GPU monitoring)
3. **`explainability.counterfactual_dist`** = 0.8 (needs counterfactual generation)
4. **`explainability.exp_stability`** = 0.95 (needs perturbation testing)
5. **`legal.proportionality`** = 1.0 (needs proportionality analysis)
6. **`legal.dpia`** = 1.0 (needs DPIA framework)
7. **`security.pdr`** = 1.0 (needs training data audit)

### Partially Hardcoded (Default Fallbacks Used)

1. **`drift.emb_drift`** — fallback 0.0 (embeddings rarely passed)
2. **`environmental.compute_intensity`** — FLOPs approximated via `tokens × 1e6`
3. **`environmental.cur`** — information_gain fixed at 1.0
4. **`explainability.fi`** — `citation_coverage + 0.5`, coverage often 0.0 → fi = 0.5
5. **`ux.ftr`** — binary 0.0 / 0.5, no real frustration signal
6. **`legal.cvr`** — `has_consent` defaults True
7. **`performance.acc_lt`** — just copies accuracy, no long-tail data
8. **`monitoring.*`** — formulas exist but caller always sends `(1,1,1,0)` defaults

### Fully Data-Driven (Working Correctly)

1. **`fairness.spd/di/eop/aod`** — computed from predictions+labels+groups
2. **`drift.psi/ks`** — when baseline data is actually passed
3. **`environmental.inf_cost/gpu_hours`** — from real latency
4. **`explainability.confidence`** — from grounding score
5. **`ux.tcr/cognitive_load/readability_fk`** — from response text analysis
6. **`legal.lawfulness`** — regex analysis of response citations
7. **`performance.accuracy/recall/group_f1`** — from labels+predictions
8. **`security.adv_acc/pisr/mir`** — from query/response regex analysis
