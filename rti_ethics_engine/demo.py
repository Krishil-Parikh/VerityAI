"""
RTI Ethics Engine - Exhaustive Demo
Shows ALL L1, L2, L3 outputs with granular formula access.
"""
from rti_ethics_engine import (
    evaluate, 
    EthicsEngine,
    build_default_metrics, 
    L1_THRESHOLDS, 
    DIMENSION_WEIGHTS
)

print("=" * 80)
print("RTI ETHICS ENGINE - EXHAUSTIVE PACKAGE DEMO")
print("=" * 80)

# Create test metrics
metrics = build_default_metrics()
print("\n[1] Running evaluation with default (all-passing) metrics...")
result = evaluate(metrics)

# EXHAUSTIVE OUTPUT
result.print_full_audit()

# GRANULAR L1 ACCESS
print("\n" + "=" * 80)
print("GRANULAR L1 FORMULA ACCESS (Shortcut Properties)")
print("=" * 80)
print(f"  result.spd       = {result.spd:.4f}     # Statistical Parity Difference")
print(f"  result.di        = {result.di:.4f}     # Disparate Impact")
print(f"  result.eop       = {result.eop:.4f}     # Equal Opportunity Diff")
print(f"  result.aod       = {result.aod:.4f}     # Average Odds Diff")
print(f"  result.psi       = {result.psi:.4f}     # Population Stability Index")
print(f"  result.ks        = {result.ks:.4f}     # Kolmogorov-Smirnov")
print(f"  result.lawfulness= {result.lawfulness:.4f}     # Legal basis score")
print(f"  result.accuracy  = {result.accuracy:.4f}     # Model accuracy")
print(f"  result.recall    = {result.recall:.4f}     # Model recall")

# GRANULAR METHOD ACCESS
print("\n" + "=" * 80)
print("GRANULAR METHOD ACCESS")
print("=" * 80)
print(f"  get_l1_metric('fairness', 'spd')     = {result.get_l1_metric('fairness', 'spd'):.4f}")
print(f"  get_l1_metric('legal', 'cvr')        = {result.get_l1_metric('legal', 'cvr'):.4f}")
print(f"  get_l2_risk('fairness')              = {result.get_l2_risk('fairness'):.4f}")
print(f"  get_l2_risk('security')              = {result.get_l2_risk('security'):.4f}")
print(f"  get_l1_status('legal')               = {result.get_l1_status('legal')}")
print(f"  get_l3_explanation('legal')          = {result.get_l3_explanation('legal')[:60]}...")

# AGGREGATION HELPERS
print("\n" + "=" * 80)
print("AGGREGATION HELPERS")
print("=" * 80)
print(f"  get_failed_dims()       = {result.get_failed_dims()}")
print(f"  get_passed_dims()       = {result.get_passed_dims()}")
print(f"  l1_pass_rate()          = {result.l1_pass_rate():.2%}")
print(f"  l1_pass_count()         = {result.l1_pass_count()}/9")
print(f"  get_highest_risk_dim()  = {result.get_highest_risk_dim()}")

# NOW TEST WITH A FAILING DIMENSION
print("\n" + "=" * 80)
print("[2] Testing with LEGAL DIMENSION FAIL (lawfulness=0.9)")
print("=" * 80)

metrics["legal"]["lawfulness"] = 0.9  # Below 1.0 threshold
result2 = evaluate(metrics)

print(f"\n  Final Label: {result2.final_label}")
print(f"  Risk Band:   {result2.risk_band}")
print(f"  S_LLM Score: {result2.s_llm:.4f}")
print(f"  Failed Dims: {result2.get_failed_dims()}")
print(f"  L1 Pass Rate: {result2.l1_pass_rate():.2%}")

# L2 VISUALIZATION
print("\n  L2 Risk Breakdown:")
for dim_key, weight in DIMENSION_WEIGHTS.items():
    risk = result2.get_l2_risk(dim_key)
    bar = "█" * int(risk * 20) + "░" * (20 - int(risk * 20))
    print(f"    {dim_key:15s}: {risk:.3f} [{bar}]")

# JSON EXPORT
print("\n" + "=" * 80)
print("JSON EXPORT (for logging/APIs)")
print("=" * 80)
print(result2.to_json()[:500] + "...")

print("\n✅ Package demo complete!")
