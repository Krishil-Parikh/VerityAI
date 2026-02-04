"""
FastAPI Backend - Query Endpoint
Takes user_query and bot_model, returns response with metrics, appends to CSV
"""
import ollama
import pandas as pd
import json
import os
import re
import time
from datetime import datetime
import numpy as np
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Import RTI Ethics Engine
import sys
sys.path.insert(0, r"c:\Users\krish\OneDrive\Desktop\bazinga_tsec_hacks\rti_ethics_engine")
from rti_ethics_engine import (
    EthicsEngine, EthicsResult, 
    build_metrics_from_raw_data,
    compute_readability_fk,
    get_l1_thresholds, DIMENSION_WEIGHTS
)

# ================== CONFIG ==================
METRICS_CSV = "query_api_metrics.csv"
PDF_DIR = "./data"
EMBED_MODEL = "all-MiniLM-L6-v2"
TOP_K = 5

# Initialize
app = FastAPI(title="RTI Query API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

ethics_engine = EthicsEngine()
embedder = SentenceTransformer(EMBED_MODEL)

# ChromaDB
chroma_client = chromadb.Client(Settings(anonymized_telemetry=False, is_persistent=True, persist_directory="./chroma_rti_db"))
try:
    collection = chroma_client.get_collection(name="rti_documents")
except:
    collection = chroma_client.create_collection(name="rti_documents", metadata={"hnsw:space": "cosine"})

# CSV columns
CSV_COLUMNS = [
    "timestamp", "user_query", "bot_model", "ai_response", "latency_ms",
    "input_tokens", "output_tokens", "total_tokens", "grounding_score",
    "hallucination_rate", "l1_citation_coverage", "l2_cosine_similarity",
    "l3_support_ratio", "overall_ethical_score", "s_llm_score", "risk_band",
    "final_label", "spd", "di", "eop", "aod", "rag_documents"
]

if not os.path.exists(METRICS_CSV):
    pd.DataFrame(columns=CSV_COLUMNS).to_csv(METRICS_CSV, index=False)

# Request/Response models
class QueryRequest(BaseModel):
    user_query: str
    bot_model: str = "llama3"

class QueryResponse(BaseModel):
    success: bool
    ai_response: str
    metrics: dict
    tokens: dict
    grounding: dict
    ethics: dict
    dimensions: dict  # All 9 dimensions with L1/L2/L3
    rag_sources: list

# Helper functions
def retrieve(query: str, k: int = TOP_K):
    q_emb = embedder.encode([query], normalize_embeddings=True)
    results = collection.query(query_embeddings=q_emb.tolist(), n_results=k, include=["documents", "metadatas", "distances"])
    retrieved = []
    if results["ids"] and results["ids"][0]:
        for idx in range(len(results["ids"][0])):
            meta = results["metadatas"][0][idx]
            retrieved.append({"doc": meta["doc"], "page": meta["page"], "text": meta["text"], "score": 1 - results["distances"][0][idx]})
    rag_docs = ", ".join(set(r["doc"] for r in retrieved))
    context = "\n\n".join(r["text"] for r in retrieved)
    return context, rag_docs, retrieved

def compute_grounding(response: str, context: str, chunks: list):
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', response) if s.strip()]
    total = max(1, len(sentences))
    
    # L1: Citation
    pattern = r'(Section\s*\d+|RTI\s*Act|CSMOP)'
    l1 = len([s for s in sentences if re.search(pattern, s, re.I)]) / total
    
    # L2: Cosine
    r_emb = embedder.encode([response], normalize_embeddings=True)[0]
    c_emb = embedder.encode([context], normalize_embeddings=True)[0]
    l2 = float(np.dot(r_emb, c_emb))
    
    # L3: Overlap
    l3 = sum(1 for s in sentences if any(s[:50].lower() in c["text"].lower() for c in chunks)) / total
    
    score = 0.4 * l1 + 0.3 * l2 + 0.3 * l3
    return {"score": score, "hallucination_rate": 1 - score, "l1": l1, "l2": l2, "l3": l3}

RTI_PROMPT = """You are a statutory RTI Assistant. Use ONLY retrieved context.
Context: {context}
Query: {query}
Answer legally, cite sources."""

# ================== ENDPOINT ==================
@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    try:
        query = request.user_query
        bot_model = request.bot_model
        ts = datetime.now()
        
        context, rag_docs, retrieved = retrieve(query)
        
        start = time.time()
        resp_data = ollama.generate(model=bot_model, prompt=RTI_PROMPT.format(context=context, query=query))
        response = resp_data['response']
        latency = int((time.time() - start) * 1000)
        
        inp_tok = resp_data.get("prompt_eval_count", 0)
        out_tok = resp_data.get("eval_count", 0)
        
        grounding = compute_grounding(response, context, retrieved)
        
        # Ethics
        gt = 0 if re.search(r'\b(mobile|address|salary)\b', query.lower()) else 1
        pred = 0 if re.search(r'\b(exempt|cannot|refused)\b', response.lower()) else 1
        group = hash(query) % 2
        
        metrics = build_metrics_from_raw_data(
            query=query, response=response,
            predictions=np.array([pred]), labels=np.array([gt]),
            sensitive_attr=np.array([group]),
            latency_ms=latency, output_tokens=out_tok, grounding_score=grounding["score"]
        )
        
        result: EthicsResult = ethics_engine.run_protocol(metrics)
        overall = {"ETHICAL": 100, "CONDITIONALLY_ETHICAL": 70, "UNETHICAL": 0}.get(result.final_label, 50)
        
        # CSV row
        row = {
            "timestamp": ts.isoformat(), "user_query": query, "bot_model": bot_model,
            "ai_response": response, "latency_ms": latency,
            "input_tokens": inp_tok, "output_tokens": out_tok, "total_tokens": inp_tok + out_tok,
            "grounding_score": round(grounding["score"], 4),
            "hallucination_rate": round(grounding["hallucination_rate"], 4),
            "l1_citation_coverage": round(grounding["l1"], 4),
            "l2_cosine_similarity": round(grounding["l2"], 4),
            "l3_support_ratio": round(grounding["l3"], 4),
            "overall_ethical_score": overall, "s_llm_score": round(result.s_llm, 4),
            "risk_band": result.risk_band, "final_label": result.final_label,
            "spd": round(result.spd, 4), "di": round(result.di, 4),
            "eop": round(result.eop, 4), "aod": round(result.aod, 4),
            "rag_documents": rag_docs
        }
        pd.DataFrame([row]).to_csv(METRICS_CSV, mode='a', header=False, index=False)
        
        # Build all dimension scores
        dimensions = {}
        for dim_key in DIMENSION_WEIGHTS.keys():
            dim_result = result.get_dim_result(dim_key)
            if dim_result:
                dimensions[dim_key] = {
                    "name": dim_result.name,
                    "weight": DIMENSION_WEIGHTS[dim_key],
                    "l1_status": dim_result.l1_status,
                    "l1_reasons": dim_result.l1_reasons,
                    "l2_risk": round(dim_result.l2_risk, 4),
                    "l2_weighted_risk": round(dim_result.l2_risk * DIMENSION_WEIGHTS[dim_key], 4),
                    "l2_indicators": dim_result.l2_indicators,
                    "l3_evidence": dim_result.l3_evidence,
                    "overall_score": round(100 * (1 - dim_result.l2_risk), 1),
                    "raw_metrics": dim_result.raw_metrics
                }
        
        return QueryResponse(
            success=True, ai_response=response,
            metrics={
                "overall_ethical_score": overall, 
                "s_llm_score": round(result.s_llm, 4), 
                "risk_band": result.risk_band, 
                "final_label": result.final_label,
                "l1_pass_rate": round(result.l1_pass_rate(), 4),
                "l1_pass_count": result.l1_pass_count(),
                "layer2_risk_score": round(result.layer2_risk_score, 4),
                "failed_dimensions": result.get_failed_dims(),
                "highest_risk_dim": result.get_highest_risk_dim(),
                "spd": round(result.spd, 4), 
                "di": round(result.di, 4),
                "eop": round(result.eop, 4), 
                "aod": round(result.aod, 4),
                "psi": round(result.psi, 4),
                "ks": round(result.ks, 4),
                "accuracy": round(result.accuracy, 4),
                "recall": round(result.recall, 4),
                "lawfulness": round(result.lawfulness, 4)
            },
            tokens={"input_tokens": inp_tok, "output_tokens": out_tok, "total_tokens": inp_tok + out_tok, "latency_ms": latency},
            grounding={"score": grounding["score"], "hallucination_rate": grounding["hallucination_rate"], "l1_citation_coverage": grounding["l1"], "l2_cosine_similarity": grounding["l2"], "l3_support_ratio": grounding["l3"]},
            ethics={"l1_pass_rate": result.l1_pass_rate(), "layer2_risk_score": result.layer2_risk_score, "required_action": result.required_action},
            dimensions=dimensions,
            rag_sources=[{"doc": r["doc"], "page": r["page"], "score": round(r["score"], 4)} for r in retrieved]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
