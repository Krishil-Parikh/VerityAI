import sys
import os
import pandas as pd
import numpy as np

# Add RTI Ethics Engine package path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
PACKAGE_PATH = os.path.join(PROJECT_ROOT, "rti_ethics_engine")
if PACKAGE_PATH not in sys.path:
    sys.path.append(PACKAGE_PATH)

import scoring_engine as se

def test_formulas():
    print("--- Testing Fairness ---")
    df = pd.DataFrame({
        'sensitive_group': [0, 0, 1, 1],
        'system_disclose': [1, 1, 0, 1],
        'ground_truth_disclose': [1, 1, 1, 1]
    })
    fairness = se.compute_fairness_metrics(df)
    print(f"SPD: {fairness.get('spd')}")
    print(f"DI: {fairness.get('di')}")
    print(f"EOP: {fairness.get('eop')}")

    print("\n--- Testing Drift ---")
    actual = [1, 0, 1, 0]
    expected = [1, 1, 0, 0]
    psi = se.compute_psi(actual, expected)
    ks = se.compute_ks_stat(actual, expected)
    print(f"PSI: {psi}")
    print(f"KS: {ks}")

    print("\n--- Testing UX ---")
    text = "The Right to Information Act 2005 is very helpful for citizens."
    ux = se.compute_ux_metrics(text)
    print(f"FK: {ux.get('fk')}")
    print(f"Load: {ux.get('load')}")

    print("\n--- Testing Performance ---")
    y_true = [1, 1, 0, 0]
    y_pred = [1, 0, 0, 1]
    perf = se.compute_performance_metrics(y_true, y_pred)
    print(f"Accuracy: {perf.get('accuracy')}")
    print(f"Recall: {perf.get('recall')}")
    print(f"F1: {perf.get('f1')}")

if __name__ == "__main__":
    test_formulas()
