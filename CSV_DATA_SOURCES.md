# CSV Data Sources — Significance & Column Reference

> Complete reference for every CSV file in `backend/data/`, explaining **why it exists**, **who writes to it**, and **what each column means** in the context of the RTI Ethics Engine's 9-dimension evaluation.

---

## File Overview

| #   | File                        | Rows | Written By                           | Read By                              | Purpose                                                                     |
| --- | --------------------------- | ---: | ------------------------------------ | ------------------------------------ | --------------------------------------------------------------------------- |
| 1   | `query_api_metrics.csv`     |  250 | `batch_simulator.py`, `query_api.py` | Frontend dashboard, `/history` API   | **Primary evaluation log** — one row per query, full ethics audit trail     |
| 2   | `fairness_data.csv`         |   48 | `query_api.py`, `tp.py`              | `query_api.py` (reload at startup)   | **Fairness ground truth** — paired demographic samples for bias measurement |
| 3   | `baseline_metrics.csv`      |    4 | Manual / historical snapshot         | `batch_simulator.py`, `query_api.py` | **Drift baseline** — reference distribution for detecting model degradation |
| 4   | `adversarial_tests.csv`     |   60 | Manual curation                      | Security dimension evaluation        | **Attack test suite** — adversarial prompts to measure robustness           |
| 5   | `dimension_config.csv`      |   30 | Manual configuration                 | `DynamicConfigLoader`                | **Threshold config** — per-metric weights, bounds, and layer assignments    |
| 6   | `gold_rti_eval.csv`         |  100 | Manual curation                      | Performance benchmarking             | **Gold standard Q&A** — expert-labeled RTI answers for accuracy validation  |
| 7   | `conversations_metrics.csv` |  239 | `query_api.py`                       | Frontend Conversations page          | **Conversation-level log** — structured format for admin conversation view  |
| 8   | `full_responses.csv`        |   57 | `batch_simulator.py`                 | `/history` API endpoint              | **Raw JSON log** — full API response objects for debugging / replay         |

---

## 1. `query_api_metrics.csv` — Primary Evaluation Log

**Why it exists**: This is the **single source of truth** for every query processed by the system. Each row captures the complete ethics evaluation pipeline output — from raw LLM response to final ethical verdict. The frontend Admin Dashboard reads this file to render model-comparison graphs, score distributions, and conversation histories.

**Written by**: `batch_simulator.py` (bulk simulation) and `query_api.py` (live API queries).

### Columns

| Column                  | Type          | Why We Need It                                                                                                                                                                                      |
| ----------------------- | ------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------ | -------------------------------------------------------- | --------- | --------------------------------------------- |
| `timestamp`             | ISO datetime  | **Temporal ordering** — enables time-series graphs on the dashboard and drift detection over time windows                                                                                           |
| `conversation_id`       | String        | **Session grouping** — links multiple turns within one user session; used by `/conversations` API to aggregate turns                                                                                |
| `user_query`            | String        | **Input text** — the actual RTI question asked; used for legal compliance regex analysis (lawfulness check) and security pattern scanning                                                           |
| `bot_model`             | String        | **Model identifier** — enables model-wise comparison charts; the dashboard filters and groups all metrics by this field                                                                             |
| `ai_response`           | String        | **Output text** — the LLM-generated answer; analyzed for readability (UX dimension), legal citation coverage, PII leakage (security), and grounding overlap (explainability)                        |
| `latency_ms`            | Integer       | **Response time** — feeds Environmental dimension (`inf_cost`, `gpu_hours`) and UX quality signals; also drives SLA compliance in Monitoring                                                        |
| `input_tokens`          | Integer       | **Prompt size** — used with `output_tokens` to estimate compute cost (`inf_cost = latency_sec × $0.00003`) and compute intensity (FLOPs ≈ tokens × 1e6)                                             |
| `output_tokens`         | Integer       | **Generation size** — directly proportional to inference cost and environmental impact; large outputs increase carbon footprint score                                                               |
| `total_tokens`          | Integer       | **Total token budget** — `input_tokens + output_tokens`; used for cost estimation normalization                                                                                                     |
| `grounding_score`       | Float (0–1)   | **RAG fidelity** — measures word overlap between AI response and retrieved context chunks; proxied as model `confidence` for Explainability L1 gate and as `current_confidence` for drift detection |
| `hallucination_rate`    | Float (0–1)   | **Inverse of grounding** — `1 - grounding_score`; appears on dashboard as a quick quality indicator                                                                                                 |
| `l1_citation_coverage`  | Float (0–1)   | **Legal citation overlap** — fraction of retrieved legal sections cited in the response; feeds `feature_importance` metric in Explainability                                                        |
| `l2_cosine_similarity`  | Float (0–1)   | **Semantic similarity** — cosine similarity between query embedding and response embedding; stored for dashboard display                                                                            |
| `l3_support_ratio`      | Float (0–1)   | **Evidence support** — ratio of response claims supported by retrieved documents; used in L3 evidence generation                                                                                    |
| `overall_ethical_score` | Float (0–100) | **Final composite score** — `s_llm × 100`; the headline number shown on every dashboard card and graph                                                                                              |
| `s_llm_score`           | Float (0–100) | **Same as above** — duplicate for backwards compatibility with older frontend components                                                                                                            |
| `risk_band`             | String        | **Risk classification** — `LOW` / `MEDIUM` / `HIGH` / `CRITICAL`; determined by `tau1=0.3` and `tau2=0.7` thresholds on aggregate L2 risk                                                           |
| `final_label`           | String        | **Ethical verdict** — `ETHICAL` / `CONDITIONALLY_ETHICAL` / `UNETHICAL`; the primary output of the 3-layer protocol                                                                                 |
| `spd`                   | Float         | **Statistical Parity Difference** — `                                                                                                                                                               | P(Ŷ=1        | G=0) - P(Ŷ=1                                             | G=1)      | `; stored as percentage for dashboard display |
| `di`                    | Float         | **Disparate Impact** — `P(Ŷ=1                                                                                                                                                                       | G=0) / P(Ŷ=1 | G=1)`; ratio of positive prediction rates across groups  |
| `eop`                   | Float         | **Equal Opportunity Difference** — `                                                                                                                                                                | TPR₀ - TPR₁  | `; gap in true positive rates between demographic groups |
| `aod`                   | Float         | **Average Odds Difference** — `(                                                                                                                                                                    | TPR₀-TPR₁    | +                                                        | FPR₀-FPR₁ | ) / 2`; average gap across both TPR and FPR   |
| `rag_documents`         | String        | **Retrieved sources** — comma-separated list of PDF filenames and page numbers used for grounding; enables citation click-through in frontend                                                       |
| `sensitive_group`       | Integer (0/1) | **Demographic flag** — `1` if query contains deferential language ("ji", "respected", "sir"), `0` otherwise; used as the protected attribute for all fairness metrics                               |
| `ground_truth_disclose` | Integer (0/1) | **Expert label** — `1` = information should be disclosed, `0` = should be refused (Section 8 exemption); the ground truth for accuracy/recall computation                                           |
| `system_disclose`       | Integer (0/1) | **Model prediction** — `1` = model disclosed information, `0` = model refused; determined by refusal keyword detection in the AI response                                                           |
| `dimensions_json`       | JSON String   | **Per-dimension breakdown** — JSON object with all 9 dimension scores and L1 statuses; parsed by frontend to render the dimension radar chart                                                       |

---

## 2. `fairness_data.csv` — Fairness Ground Truth

**Why it exists**: The Fairness dimension requires **group-level comparison** across demographic segments. A single query can't measure bias — you need a population of predictions across protected groups. This file accumulates paired predictions so that SPD, DI, EOP, and AOD can be computed meaningfully instead of defaulting to neutral values.

**Written by**: `query_api.py` (appends one row per live query) and `tp.py` (initial population script).

### Columns

| Column                  | Type          | Why We Need It                                                                                                                                           |
| ----------------------- | ------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `sensitive_group`       | Integer (0/1) | **Protected attribute** — splits the population into two groups for bias comparison; `1` = deferential/formal language detected, `0` = neutral           |
| `ground_truth_disclose` | Integer (0/1) | **True label** — expert judgment on whether information should be disclosed; needed for EOP (requires TPR per group) and AOD (requires both TPR and FPR) |
| `system_disclose`       | Integer (0/1) | **Model's prediction** — what the system actually decided (disclose vs refuse); core input to SPD and DI formulas                                        |
| `paired_test_id`        | String        | **Pairing identifier** — links paired queries that test the same question with different demographic styles; ensures we compare like-for-like            |
| `demographic_style`     | String        | **Style descriptor** — "formal_hindi", "neutral_english", etc.; enables fine-grained analysis of which linguistic styles trigger bias                    |
| `query_hash`            | String        | **Deduplication key** — hash of the normalized query text; prevents the same query from being counted twice in fairness calculations                     |
| `tp`                    | Integer       | **True Positives** — correctly disclosed information; component of precision, recall, F1, and group-level metrics                                        |
| `fp`                    | Integer       | **False Positives** — incorrectly disclosed (should have refused); component of FPR, needed for AOD calculation                                          |
| `fn`                    | Integer       | **False Negatives** — incorrectly refused (should have disclosed); component of FNR, needed for FNRD (False Negative Rate Difference)                    |
| `tn`                    | Integer       | **True Negatives** — correctly refused; completes the confusion matrix for each sample                                                                   |

---

## 3. `baseline_metrics.csv` — Drift Baseline Reference

**Why it exists**: The Drift dimension detects **performance degradation over time** by comparing current model behavior against a historical reference distribution. Without a baseline, PSI and KS statistics have nothing to compare against and default to 0.0 (no drift). This file provides that reference snapshot.

**Written by**: Generated from an initial calibration run or historical data snapshot.
**Read by**: `batch_simulator.py` and `query_api.py` at startup — columns `system_disclose` and `confidence` are loaded as `baseline_predictions` and `baseline_confidences`.

### Columns

| Column               | Type            | Why We Need It                                                                                                                                                                 |
| -------------------- | --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `grounding_score`    | Float (0–1)     | **Historical grounding** — reference distribution of RAG fidelity scores for embedding-based drift comparison                                                                  |
| `system_disclose`    | Integer (0/1)   | **Baseline predictions** — the reference prediction distribution; used by `compute_psi()` and `compute_ks_statistic()` to detect if the model's disclosure pattern has shifted |
| `confidence`         | Float (0–1)     | **Baseline confidences** — the reference confidence distribution; used by `compute_confidence_drift()` to detect if model certainty has degraded                               |
| `query_embedding`    | String (vector) | **Baseline embeddings** — serialized embedding vectors; would feed `compute_embedding_drift()` (L2 distance between mean embeddings), currently unused                         |
| `pred_drift_bucket`  | String          | **Prediction drift category** — pre-computed drift classification ("stable", "moderate", "severe") for historical reference                                                    |
| `conf_drift_bucket`  | String          | **Confidence drift category** — pre-computed confidence drift classification for historical reference                                                                          |
| `psi_score`          | Float           | **Pre-computed PSI** — historical Population Stability Index value at the time this baseline was captured                                                                      |
| `ks_score`           | Float           | **Pre-computed KS** — historical Kolmogorov-Smirnov statistic at baseline capture time                                                                                         |
| `embedding_drift_l2` | Float           | **Pre-computed embedding drift** — historical L2 distance between embedding centroids                                                                                          |
| `timestamp`          | ISO datetime    | **Capture time** — when this baseline snapshot was taken; useful for knowing how stale the baseline is                                                                         |

---

## 4. `adversarial_tests.csv` — Security Attack Suite

**Why it exists**: The Security dimension needs a **curated set of adversarial attacks** to validate system robustness. This test suite covers prompt injection, jailbreaking, PII extraction, and other attack categories so the system can be evaluated against known threat vectors.

**Written by**: Manually curated by the team — each row is a crafted attack prompt with expected behavior.

### Columns

| Column              | Type    | Why We Need It                                                                                                                                                                 |
| ------------------- | ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `test_id`           | String  | **Unique identifier** — references specific test cases in security audit reports                                                                                               |
| `attack_category`   | String  | **Attack taxonomy** — classifies the type of attack: "prompt_injection", "jailbreak", "pii_extraction", "context_manipulation", etc.; enables per-category pass/fail reporting |
| `attack_query`      | String  | **Attack payload** — the actual adversarial prompt to be submitted; used to test `adv_acc` (adversarial accuracy) and `pisr` (prompt injection success rate) metrics           |
| `expected_behavior` | String  | **Gold response** — what the system should ideally do (refuse, flag, safe response); compared against actual behavior for scoring                                              |
| `actual_response`   | String  | **System output** — what the model actually returned when given the attack; analyzed for safety violations                                                                     |
| `safe`              | Boolean | **Safety verdict** — `True` if the system safely handled the attack, `False` if it was compromised; feeds `adv_acc = safe_count / total_count`                                 |
| `attack_success`    | Boolean | **Attack outcome** — `True` if the attack succeeded in eliciting undesired behavior; inverse of `safe`; feeds `pisr = success_count / injection_count`                         |
| `severity`          | String  | **Risk level** — "low", "medium", "high", "critical"; weights the impact of each attack in risk scoring                                                                        |
| `target_dimension`  | String  | **Affected dimension** — which ethical dimension this attack primarily targets (security, legal, fairness); used for cross-dimensional impact analysis                         |

---

## 5. `dimension_config.csv` — Threshold & Weight Configuration

**Why it exists**: Instead of hardcoding all 36 metric thresholds and 9 dimension weights in Python code, this file provides a **declarative configuration** that can be adjusted without code changes. The `DynamicConfigLoader` in `config.py` can read this to override default thresholds.

**Written by**: Manual configuration by the team.

### Columns

| Column                | Type            | Why We Need It                                                                                                                                     |
| --------------------- | --------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| `dimension_name`      | String          | **Parent dimension** — one of the 9 dimensions (fairness, drift, legal, etc.); groups metrics under their dimension                                |
| `metric_name`         | String          | **Metric identifier** — e.g., "spd", "psi", "lawfulness"; must match the key names used in `METRIC_CATALOG` from `config.py`                       |
| `weight`              | Float (0–1)     | **Dimension weight** — how much this dimension contributes to the final `s_llm` score; e.g., legal=0.20, drift=0.08, environmental=0.04            |
| `direction`           | String          | **Scoring direction** — "higher_better" or "lower_better"; determines whether exceeding the threshold is a pass or fail                            |
| `min_value`           | Float           | **Floor value** — minimum possible value for this metric (used for normalization)                                                                  |
| `max_value`           | Float           | **Ceiling value** — maximum possible value (used for normalization and chart scaling)                                                              |
| `threshold_low`       | Float           | **L1 lower bound** — the minimum acceptable value (for "higher_better" metrics, below this = FAIL)                                                 |
| `threshold_high`      | Float           | **L1 upper bound** — the maximum acceptable value (for "lower_better" metrics, above this = FAIL)                                                  |
| `layer`               | Integer (1/2/3) | **Protocol layer** — which of the 3 layers this metric belongs to: L1 (hard gate), L2 (risk score), or L3 (evidence)                               |
| `confidence_interval` | Float           | **Statistical confidence** — the CI width used when computing thresholds from historical data distributions                                        |
| `department_override` | String          | **Department-specific rules** — allows different thresholds for different government departments (e.g., MHA may have stricter security thresholds) |
| `description`         | String          | **Human-readable explanation** — what this metric measures and why it matters; displayed in admin dashboard tooltips                               |

---

## 6. `gold_rti_eval.csv` — Gold Standard Evaluation Set

**Why it exists**: To measure **absolute model quality**, you need expert-labeled ground truth answers. This file contains 100 curated RTI queries with gold-standard answers, legal section references, and correctness labels. It enables systematic benchmarking of model accuracy, recall, and legal compliance.

**Written by**: Manually curated by domain experts with knowledge of the RTI Act 2005.

### Columns

| Column                  | Type        | Why We Need It                                                                                                                                      |
| ----------------------- | ----------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| `example_id`            | String      | **Unique identifier** — references specific evaluation examples in reports                                                                          |
| `department`            | String      | **Government department** — e.g., "DARPG", "MHA", "PMO"; enables department-wise accuracy analysis                                                  |
| `user_prompt`           | String      | **RTI query** — the question being asked; covers all query categories (proactive disclosure, exemptions, personal info, etc.)                       |
| `gold_answer`           | String      | **Expert answer** — the correct response as written by a domain expert; used for F1 token overlap calculation                                       |
| `gold_legal_sections`   | String      | **Required citations** — which sections of the RTI Act should be cited (e.g., "Section 4(1)(b)", "Section 8(1)(j)"); feeds legal compliance scoring |
| `ai_response`           | String      | **Model output** — what the AI actually generated for this prompt; compared against gold answer                                                     |
| `label_correct`         | String      | **Correctness verdict** — "correct", "partially_correct", "incorrect"; feeds the Performance dimension's accuracy metric                            |
| `comment`               | String      | **Expert notes** — qualitative feedback on what the model got right or wrong                                                                        |
| `f1_token_overlap`      | Float (0–1) | **Token-level F1** — precision-recall harmonic mean between gold answer tokens and AI response tokens; proxy for content quality                    |
| `legal_compliance_gold` | Float (0–1) | **Legal citation accuracy** — fraction of required legal sections that the AI correctly cited; feeds Legal dimension validation                     |
| `exemption_section`     | String      | **Applicable exemption** — which Section 8 exemption applies (if any); enables testing whether the model correctly identifies exemption grounds     |
| `difficulty`            | String      | **Query difficulty** — "easy", "medium", "hard"; enables difficulty-stratified performance analysis                                                 |

---

## 7. `conversations_metrics.csv` — Conversation-Level Log

**Why it exists**: While `query_api_metrics.csv` is the primary log, this file uses a **structured schema** aligned with the `generate_columns_from_formulas()` function in `config.py`. It's the source for the Admin Dashboard's Conversations page — each row represents a complete conversation turn with standardized columns.

**Written by**: `query_api.py` (appends on each live query).

### Columns

| Column                  | Type          | Why We Need It                                                                                                                                    |
| ----------------------- | ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| `conversation_id`       | String        | Session grouping — same as in `query_api_metrics.csv`                                                                                             |
| `turn_id`               | Integer       | **Turn number** — position within a multi-turn conversation; enables turn-level analysis                                                          |
| `user_id`               | String        | **User identifier** — tracks which user initiated the query; enables per-user analytics                                                           |
| `department`            | String        | **Government department** — categorizes queries by department for department-wise dashboards                                                      |
| `timestamp_request`     | ISO datetime  | **Request time** — when the query was received                                                                                                    |
| `timestamp_response`    | ISO datetime  | **Response time** — when the response was sent; difference = server-side latency                                                                  |
| `latency_ms`            | Integer       | Response time — same purpose as in primary log                                                                                                    |
| `user_prompt`           | String        | Input text                                                                                                                                        |
| `ai_response`           | String        | Output text                                                                                                                                       |
| `model_name`            | String        | Model identifier                                                                                                                                  |
| `infra_region`          | String        | **Deployment region** — which infrastructure region served this request; relevant for Environmental dimension (carbon intensity varies by region) |
| `sensitive_group`       | Integer (0/1) | Demographic flag                                                                                                                                  |
| `ground_truth_disclose` | Integer (0/1) | Expert label                                                                                                                                      |
| `system_disclose`       | Integer (0/1) | Model prediction                                                                                                                                  |

> This file also includes per-dimension metric columns (e.g., `fairness_spd`, `drift_psi`, `legal_lawfulness`) and aggregate columns (`s_llm`, `final_label`, `risk_band`) generated dynamically by `generate_columns_from_formulas()` in `config.py`.

---

## 8. `full_responses.csv` — Raw JSON Response Log

**Why it exists**: For **debugging and replay** capability. This file stores the complete JSON response object returned by the ethics engine, including all intermediate computations. When a query produces unexpected results, developers can load this file to inspect the exact state of every metric.

**Written by**: `batch_simulator.py` during bulk simulation runs.

### Columns

| Column               | Type         | Why We Need It                                                                                                                                              |
| -------------------- | ------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `timestamp`          | ISO datetime | When this response was generated                                                                                                                            |
| `conversation_id`    | String       | Links back to the corresponding row in `query_api_metrics.csv`                                                                                              |
| `user_query`         | String       | The original query text                                                                                                                                     |
| `bot_model`          | String       | Which model generated this response                                                                                                                         |
| `full_json_response` | JSON String  | **Complete response payload** — includes `metrics{}`, `result{}`, `dimensions_json{}`, and all intermediate values; enables full audit trail reconstruction |

---

## How CSVs Map to the 9 Dimensions

```
┌─────────────────────────┐     ┌──────────────────────────┐
│  query_api_metrics.csv  │────▶│  ALL 9 Dimensions        │
│  (primary log)          │     │  (final scores stored)   │
└─────────────────────────┘     └──────────────────────────┘

┌─────────────────────────┐     ┌──────────────────────────┐
│  fairness_data.csv      │────▶│  Dim 1: Bias & Fairness  │
│  (group predictions)    │     │  SPD, DI, EOP, AOD       │
└─────────────────────────┘     └──────────────────────────┘

┌─────────────────────────┐     ┌──────────────────────────┐
│  baseline_metrics.csv   │────▶│  Dim 2: Data & Model     │
│  (reference snapshot)   │     │  Drift (PSI, KS, drift)  │
└─────────────────────────┘     └──────────────────────────┘

┌─────────────────────────┐     ┌──────────────────────────┐
│  adversarial_tests.csv  │────▶│  Dim 9: Security &       │
│  (attack test suite)    │     │  Robustness              │
└─────────────────────────┘     └──────────────────────────┘

┌─────────────────────────┐     ┌──────────────────────────┐
│  gold_rti_eval.csv      │────▶│  Dim 7: Performance      │
│  (expert answers)       │     │  (accuracy, recall, F1)  │
└─────────────────────────┘     └──────────────────────────┘

┌─────────────────────────┐     ┌──────────────────────────┐
│  dimension_config.csv   │────▶│  ALL 9 Dimensions        │
│  (thresholds/weights)   │     │  (L1 gates, weights)     │
└─────────────────────────┘     └──────────────────────────┘
```

> **Dimensions 3–6 and 8** (Environmental, Explainability, UX, Legal, Monitoring) derive their inputs from **runtime computation** — latency timing, response text analysis, regex pattern matching — rather than from dedicated CSV files. Their results are logged to `query_api_metrics.csv` after computation.
