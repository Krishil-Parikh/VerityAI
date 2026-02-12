"""
Backfill script: Generate full_responses.csv from query_api_metrics.csv
This creates the JSON response objects that the /history endpoint needs for graphs.
"""
import os
import json
import pandas as pd
import numpy as np

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "backend", "data")
METRICS_CSV = os.path.join(DATA_DIR, "query_api_metrics.csv")
FULL_RESPONSE_CSV = os.path.join(DATA_DIR, "full_responses.csv")

def backfill():
    if not os.path.exists(METRICS_CSV):
        print("❌ No query_api_metrics.csv found")
        return
    
    df = pd.read_csv(METRICS_CSV, engine='python', on_bad_lines='skip')
    df = df.replace({np.nan: None})
    print(f"📊 Found {len(df)} rows in query_api_metrics.csv")
    
    rows = []
    for idx, r in df.iterrows():
        dimensions = {}
        if r.get("dimensions_json"):
            try:
                dimensions = json.loads(r["dimensions_json"])
            except:
                pass
        
        full_response_obj = {
            "success": True,
            "ai_response": r.get("ai_response", ""),
            "bot_model": r.get("bot_model", "unknown"),
            "metrics": {
                "overall_ethical_score": r.get("overall_ethical_score", 0),
                "s_llm_score": r.get("s_llm_score", 0),
                "risk_band": r.get("risk_band", ""),
                "final_label": r.get("final_label", ""),
            },
            "tokens": {
                "input_tokens": r.get("input_tokens", 0),
                "output_tokens": r.get("output_tokens", 0),
                "total_tokens": r.get("total_tokens", 0),
                "latency_ms": r.get("latency_ms", 0)
            },
            "grounding": {
                "score": r.get("grounding_score", 0),
                "hallucination_rate": r.get("hallucination_rate", 0),
                "l1_citation_coverage": r.get("l1_citation_coverage", 0),
                "l2_cosine_similarity": r.get("l2_cosine_similarity", 0),
                "l3_support_ratio": r.get("l3_support_ratio", 0)
            },
            "dimensions": dimensions,
            "rag_sources": []
        }
        
        rows.append({
            "timestamp": r.get("timestamp", ""),
            "conversation_id": r.get("conversation_id", ""),
            "user_query": r.get("user_query", ""),
            "bot_model": r.get("bot_model", "unknown"),
            "full_json_response": json.dumps(full_response_obj)
        })
    
    pd.DataFrame(rows).to_csv(FULL_RESPONSE_CSV, index=False)
    print(f"✅ Backfilled {len(rows)} rows to {FULL_RESPONSE_CSV}")

if __name__ == "__main__":
    backfill()
