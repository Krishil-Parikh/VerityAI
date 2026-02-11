import os
import sys
import pandas as pd
import json

# Add rti_ethics_engine to path
sys.path.insert(0, os.path.abspath("rti_ethics_engine"))
try:
    from rti_ethics_engine import DIMENSION_WEIGHTS
    print(f"DIMENSION_WEIGHTS ({len(DIMENSION_WEIGHTS)} dimensions):")
    for k, v in DIMENSION_WEIGHTS.items():
        print(f"  {k}: {v}")
except Exception as e:
    print(f"Error importing DIMENSION_WEIGHTS: {e}")

METRICS_CSV = "backend/data/query_api_metrics.csv"
if os.path.exists(METRICS_CSV):
    df = pd.read_csv(METRICS_CSV)
    print(f"\nLast 5 rows of {METRICS_CSV}:")
    cols = ["timestamp", "overall_ethical_score", "s_llm_score", "spd", "di", "eop", "aod", "accuracy", "recall", "lawfulness"]
    available_cols = [c for c in cols if c in df.columns]
    print(df[available_cols].tail(5).to_string())
    
    # Check if dimensions_json is populated
    has_dims = df["dimensions_json"].apply(lambda x: pd.notna(x) and x != "{}").all()
    print(f"\nAll rows have valid dimensions_json: {has_dims}")
else:
    print(f"\n{METRICS_CSV} not found.")
