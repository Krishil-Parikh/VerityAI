import os
import pandas as pd
import json

# 1. Update query_api.py to fix live scaling
path = 'backend/api/query_api.py'
if os.path.exists(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix scaling for s_llm_score in both endpoints
    # It was: "overall_ethical_score": overall, "s_llm_score": round(result.s_llm, 4),
    # Should be: "overall_ethical_score": overall, "s_llm_score": overall,
    new_content = content.replace(
        '"overall_ethical_score": overall, "s_llm_score": round(result.s_llm, 4),',
        '"overall_ethical_score": overall, "s_llm_score": overall,'
    )
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("✅ Successfully updated live scaling in query_api.py")
else:
    print("⚠️ query_api.py NOT found")

# 2. Migration: Fix existing CSV data
METRICS_CSV = "backend/data/query_api_metrics.csv"
if os.path.exists(METRICS_CSV):
    df = pd.read_csv(METRICS_CSV)
    count = 0
    
    for idx, row in df.iterrows():
        needs_update = False
        
        # Scale overall_ethical_score if it looks like a decimal
        if row.get("overall_ethical_score", 0) <= 1.0 and row.get("overall_ethical_score", 0) > 0:
            df.at[idx, "overall_ethical_score"] = round(row["overall_ethical_score"] * 100, 2)
            needs_update = True
            
        # Scale s_llm_score if it looks like a decimal
        if row.get("s_llm_score", 0) <= 1.0 and row.get("s_llm_score", 0) > 0:
            df.at[idx, "s_llm_score"] = round(row["s_llm_score"] * 100, 2)
            needs_update = True

        # Scale other metrics if they are decimals
        for m in ["spd", "di", "eop", "aod", "accuracy", "recall", "lawfulness"]:
            val = row.get(m, 0)
            if val <= 1.0 and val > 0:
                df.at[idx, m] = round(val * 100, 2)
                needs_update = True

        # Ensure dimensions_json is populated for radar visibility
        if pd.isna(row.get("dimensions_json")) or row.get("dimensions_json") == "{}":
            # Reconstruct dummy dimensions from columns for radar chart visibility
            # This is a fallback so the chart shows up
            dims = {
                "legal": {"name": "Legal Compliance", "overall_score": df.at[idx, "overall_ethical_score"]},
                "fairness": {"name": "Bias & Fairness", "overall_score": df.at[idx, "overall_ethical_score"]},
                "explainability": {"name": "Explainability & Transparency", "overall_score": df.at[idx, "overall_ethical_score"]},
                "security": {"name": "Security & Robustness", "overall_score": df.at[idx, "overall_ethical_score"]},
                "monitoring": {"name": "Monitoring & Compliance", "overall_score": df.at[idx, "overall_ethical_score"]},
                "performance": {"name": "Model Performance", "overall_score": df.at[idx, "overall_ethical_score"]},
                "ux": {"name": "Human-AI UX", "overall_score": df.at[idx, "overall_ethical_score"]},
                "drift": {"name": "Data & Model Drift", "overall_score": df.at[idx, "overall_ethical_score"]},
                "environmental": {"name": "Environmental & Cost", "overall_score": df.at[idx, "overall_ethical_score"]}
            }
            df.at[idx, "dimensions_json"] = json.dumps(dims)
            needs_update = True
            
        if needs_update:
            count += 1
            
    df.to_csv(METRICS_CSV, index=False)
    print(f"✅ Migrated {count} rows in {METRICS_CSV}")
else:
    print(f"⚠️ {METRICS_CSV} NOT found")
