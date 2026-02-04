# RTI AI Ethics Protocol: Formal Mathematical Manifest (9 Dimensions)

This document contains the authoritative mathematical definitions for the 3-layer ethical protocol across all 9 dimensions.

## Global Notation

- $A$ → Sensitive attribute (e.g., demographic group)
- $X$ → Input query
- $Y \in \{0,1\}$ → Ground truth
- $\hat{Y} \in \{0,1\}$ → System decision
- $\hat{P} \in [0,1]$ → Confidence/Probability
- $n$ → Sample count

---

## 1. Bias & Fairness

**Layer 1 (Hard Gate):**

- **SPD**: $P(\hat{Y}=1|A=1) - P(\hat{Y}=1|A=0)$
- **DI**: $\frac{P(\hat{Y}=1|A=1)}{P(\hat{Y}=1|A=0)}$
- **EOP**: $P(\hat{Y}=1|Y=1,A=1) - P(\hat{Y}=1|Y=1,A=0)$
- **AOD**: $\frac{1}{2}[(TPR_{A=1}-TPR_{A=0}) + (FPR_{A=1}-FPR_{A=0})]$

**Layer 2 (Risk):**

- **FNRD**: $P(\hat{Y}=0|Y=1,A=1) - P(\hat{Y}=0|Y=1,A=0)$
- **Refusal Disparity**: $P(\text{Refusal}|A=1) - P(\text{Refusal}|A=0)$

**Layer 3 (Evidence):**

- **MI Leakage**: $I(\hat{Y};A) = \sum P(\hat{y},a) \log \frac{P(\hat{y},a)}{P(\hat{y})P(a)}$

---

## 2. Data & Model Drift

**Layer 1 (Hard Gate):**

- **PSI**: $\sum (p_i - q_i) \ln(p_i/q_i)$
- **Feature Drift (KS)**: $D_{KS} = \sup_x |F_t(x) - F_{t-1}(x)|$

**Layer 2 (Risk):**

- **Prediction Drift**: $\mathbb{E}[\hat{Y}_t] - \mathbb{E}[\hat{Y}_{t-1}]$

**Layer 3 (Evidence):**

- **Embedding Drift**: $||\mu_t - \mu_{t-1}||_2$

---

## 3. Environmental / Cost Ethics

**Layer 1 (Hard Gate):**

- **Inference Cost**: $C_{inf} = \text{cost\_per\_sec} \times \text{latency}$

**Layer 2 (Risk):**

- **Compute Intensity**: $\frac{\text{FLOPs}}{\text{output\_tokens}}$

**Layer 3 (Evidence):**

- **Cost-Utility Ratio**: $\frac{C_{inf}}{\text{Information Gain}}$

---

## 4. Explainability & Transparency

**Layer 1 (Hard Gate):**

- **Confidence Score**: $\hat{P} = \max P(Y|X)$
- **Feature Importance (FI)**: $\sum |\phi_i|$ (SHAP/IG)

**Layer 2 (Risk):**

- **Counterfactual Distance**: $d(x, x') = \min ||x-x'||$ s.t. $\hat{Y}(x') \neq \hat{Y}(x)$

**Layer 3 (Evidence):**

- **Explanation Stability**: $\mathbb{E}[||\phi(X) - \phi(X+\epsilon)||]$

---

## 5. Human–AI User Experience

**Layer 1 (Hard Gate):**

- **Task Completion Rate (TCR)**: $\frac{\text{completed}}{\text{total}}$

**Layer 2 (Risk):**

- **Cognitive Load Index**: $\alpha \cdot \text{TurnCount} + \beta \cdot \text{Complexity}$

**Layer 3 (Evidence):**

- **Readability (FK)**: $206.835 - 1.015(\text{W/S}) - 84.6(\text{Sy/W})$

---

## 6. Legal & Regulatory Compliance

**Layer 1 (Hard Gate):**

- **Lawfulness ($L$)**: $\mathbf{1}(\text{legal basis exists})$

**Layer 2 (Risk):**

- **Proportionality Score**: $\frac{\text{disclosed}}{\text{requested}}$

**Layer 3 (Evidence):**

- **DPIA Coverage**: $\frac{\text{assessed\_risks}}{\text{total\_risks}}$

---

## 7. Model Performance

**Layer 1 (Hard Gate):**

- **Accuracy**: $\frac{TP+TN}{\text{Total}}$
- **Recall**: $\frac{TP}{TP+FN}$

**Layer 2 (Risk):**

- **Group-wise F1**: $2 \frac{P \cdot R}{P+R}$

**Layer 3 (Evidence):**

- **Long-Tail Accuracy**: Performance on rare query distributions.

---

## 8. Monitoring & Compliance

**Layer 1 (Hard Gate):**

- **Audit Log Completeness (ALC)**: $\frac{\text{logged}}{\text{expected}}$

**Layer 2 (Risk):**

- **Policy Violation Rate (PVR)**: $\frac{\text{violations}}{\text{requests}}$

**Layer 3 (Evidence):**

- **Incident Reconstruction Fidelity (IRF)**: $\frac{\text{replayable}}{\text{total}}$

---

## 9. Security & Adversarial Robustness

**Layer 1 (Hard Gate):**

- **Adversarial Accuracy**: Accuracy under perturbation.
- **Prompt Injection SR**: Attack success rate.

**Layer 2 (Risk):**

- **Membership Inference Risk**: Privacy leakage probability.

**Layer 3 (Evidence):**

- **Poisoning Detection Rate**: Audit of training data integrity.
