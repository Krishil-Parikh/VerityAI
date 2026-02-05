"""
FastAPI Backend - Query Endpoint
Takes user_query and bot_model, returns response with metrics, appends to CSV
"""
import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
import ollama
import pandas as pd
import json
import re
import time
import random
from datetime import datetime
import numpy as np
from sentence_transformers import SentenceTransformer
import chromadb
import fitz  # PyMuPDF
from chromadb.config import Settings
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Import RTI Ethics Engine
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../rti_ethics_engine")))
from rti_ethics_engine import (
    EthicsEngine, EthicsResult, 
    build_metrics_from_raw_data,
    compute_readability_fk,
    get_l1_thresholds, DIMENSION_WEIGHTS
)

# ================== ROBUST PATHS ==================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(BACKEND_DIR, "data")
DB_DIR = os.path.join(BACKEND_DIR, "db")

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(DB_DIR, exist_ok=True)

METRICS_CSV = os.path.join(DATA_DIR, "query_api_metrics.csv")
FAIRNESS_CSV = os.path.join(DATA_DIR, "fairness_data.csv")
FULL_RESPONSE_CSV = os.path.join(DATA_DIR, "full_responses.csv")
PDF_DIR = DATA_DIR
EMBED_MODEL = "all-MiniLM-L6-v2"
TOP_K = 5
PERSIST_DIRECTORY = os.path.join(DB_DIR, "chroma_rti_db")

# Initialize
app = FastAPI(title="RTI Query API", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

ethics_engine = EthicsEngine()
embedder = SentenceTransformer(EMBED_MODEL)

# ================== LOAD HISTORICAL DATA ==================
def load_historical_data():
    """Load historical fairness data for real calculations."""
    if os.path.exists(FAIRNESS_CSV):
        df = pd.read_csv(FAIRNESS_CSV)
        if len(df) >= 10:  # Need at least 10 samples
            return {
                "predictions": df["system_disclose"].values.astype(int),
                "labels": df["ground_truth_disclose"].values.astype(int),
                "groups": df["sensitive_group"].values.astype(int),
                "count": len(df)
            }
    return None

historical_data = load_historical_data()
if historical_data:
    print(f"✅ Loaded {historical_data['count']} historical samples for real fairness calculations")
else:
    print("⚠️ No historical data found. Run tp.py first to generate fairness_data.csv")

# ChromaDB
chroma_client = chromadb.Client(Settings(anonymized_telemetry=False, is_persistent=True, persist_directory=PERSIST_DIRECTORY))
try:
    collection = chroma_client.get_collection(name="rti_documents")
except:
    collection = chroma_client.create_collection(name="rti_documents", metadata={"hnsw:space": "cosine"})

# ================== DYNAMIC PDF INDEXING ==================
def build_rag_index():
    """Index all PDFs in the data directory if the collection is empty."""
    if collection.count() > 0:
        print(f"✅ ChromaDB has {collection.count()} chunks. Ready.")
        return

    print("🔍 Indexing PDFs from data directory...")
    pdf_files = [f for f in os.listdir(PDF_DIR) if f.endswith(".pdf")]
    
    if not pdf_files:
        print("⚠️ No PDFs found in data directory. RAG will be empty.")
        return

    all_texts = []
    all_ids = []
    all_metadatas = []

    for pdf_file in pdf_files:
        path = os.path.join(PDF_DIR, pdf_file)
        try:
            doc = fitz.open(path)
            for page_num in range(len(doc)):
                text = doc[page_num].get_text("text").strip()
                if not text: continue
                paras = [p.strip() for p in re.split(r'\n\s*\n|\n{3,}', text) if p.strip()]
                for i, para in enumerate(paras):
                    if len(para) > 50:
                        unique_id = f"{pdf_file}_{page_num}_{i}"
                        all_texts.append(para)
                        all_ids.append(unique_id)
                        all_metadatas.append({"doc": pdf_file, "page": page_num + 1, "text": para})
            doc.close()
        except Exception as e:
            print(f"❌ Error indexing {pdf_file}: {e}")

    if all_texts:
        print(f"✨ Generating embeddings for {len(all_texts)} chunks...")
        embeddings = embedder.encode(all_texts, show_progress_bar=True, normalize_embeddings=True)
        
        batch_size = 500
        for i in range(0, len(all_texts), batch_size):
            end_idx = min(i + batch_size, len(all_texts))
            collection.add(
                ids=all_ids[i:end_idx],
                embeddings=embeddings[i:end_idx].tolist(),
                documents=all_texts[i:end_idx],
                metadatas=all_metadatas[i:end_idx]
            )
        print(f"✅ Indexed {len(all_texts)} chunks successfully.")

# Run indexing
build_rag_index()

# CSV columns
CSV_COLUMNS = [
    "timestamp", "user_query", "bot_model", "ai_response", "latency_ms",
    "input_tokens", "output_tokens", "total_tokens", "grounding_score",
    "hallucination_rate", "l1_citation_coverage", "l2_cosine_similarity",
    "l3_support_ratio", "overall_ethical_score", "s_llm_score", "risk_band",
    "final_label", "spd", "di", "eop", "aod", "rag_documents",
    "sensitive_group", "ground_truth_disclose", "system_disclose"
]

if not os.path.exists(METRICS_CSV):
    pd.DataFrame(columns=CSV_COLUMNS).to_csv(METRICS_CSV, index=False)

# Full response CSV columns
FULL_RESPONSE_COLUMNS = ["timestamp", "user_query", "bot_model", "full_json_response"]
if not os.path.exists(FULL_RESPONSE_CSV):
    pd.DataFrame(columns=FULL_RESPONSE_COLUMNS).to_csv(FULL_RESPONSE_CSV, index=False)

# Request/Response models
class QueryRequest(BaseModel):
    user_query: str
    bot_model: str = "llama3"

class QueryResponse(BaseModel):
    success: bool
    ai_response: str
    bot_model: str
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
        
        # Detect group from query style
        def detect_group(q):
            rural = [r'\bji\b', r'\bkindly\b', r'\brespected\b', r'\bplease\s+sir\b']
            urban = [r'\basap\b', r'\bfyi\b', r'Section\s*\d+', r'\bpursuant\b']
            r = sum(1 for p in rural if re.search(p, q.lower()))
            u = sum(1 for p in urban if re.search(p, q.lower()))
            return 1 if r > u else 0 if u > r else hash(q) % 2
        
        # Current query classification
        gt = 0 if re.search(r'\b(mobile|address|salary|private|personal)\b', query.lower()) else 1
        pred = 0 if re.search(r'\b(exempt|cannot|refused|section 8|privacy)\b', response.lower()) else 1
        group = detect_group(query)
        
        # Use historical data for REAL fairness calculations
        global historical_data
        if historical_data and historical_data["count"] >= 10:
            # Append current to historical for calculation
            all_preds = np.append(historical_data["predictions"], pred)
            all_labels = np.append(historical_data["labels"], gt)
            all_groups = np.append(historical_data["groups"], group)
        else:
            # Fallback to single sample
            all_preds = np.array([pred])
            all_labels = np.array([gt])
            all_groups = np.array([group])
        
        metrics = build_metrics_from_raw_data(
            query=query, response=response,
            predictions=all_preds, labels=all_labels,
            sensitive_attr=all_groups,
            latency_ms=latency, output_tokens=out_tok, grounding_score=grounding["score"]
        )
        
        result: EthicsResult = ethics_engine.run_protocol(metrics)
        overall = {"ETHICAL": 100, "CONDITIONALLY_ETHICAL": 70, "UNETHICAL": 0}.get(result.final_label, 50)
        
        # Update fairness CSV with new sample
        fairness_row = pd.DataFrame([{"sensitive_group": group, "ground_truth_disclose": gt, "system_disclose": pred}])
        fairness_row.to_csv(FAIRNESS_CSV, mode='a', header=not os.path.exists(FAIRNESS_CSV), index=False)
        
        # Reload historical data
        historical_data = load_historical_data()
        
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
            "rag_documents": rag_docs,
            "sensitive_group": group, "ground_truth_disclose": gt, "system_disclose": pred
        }
        pd.DataFrame([row]).to_csv(METRICS_CSV, mode='a', header=False, index=False)
        
        # Build all dimension scores with small jitter for visual variance as requested
        dimensions = {}
        for dim_key in DIMENSION_WEIGHTS.keys():
            dim_result = result.get_dim_result(dim_key)
            if dim_result:
                # Add small jitter to make scores more dynamic (±2-5 points)
                # Dimensions: Legal, Fairness, Explainability, Security, Monitoring, Performance, Drift, Environmental
                base_score = 100 * (1 - dim_result.l2_risk)
                jitter = random.uniform(-3, 3) 
                jittered_score = max(0, min(100, base_score + jitter))
                
                dimensions[dim_key] = {
                    "name": dim_result.name,
                    "weight": DIMENSION_WEIGHTS[dim_key],
                    "l1_status": dim_result.l1_status,
                    "l1_reasons": dim_result.l1_reasons,
                    "l2_risk": round(dim_result.l2_risk, 4),
                    "l2_weighted_risk": round(dim_result.l2_risk * DIMENSION_WEIGHTS[dim_key], 4),
                    "l2_indicators": dim_result.l2_indicators,
                    "l3_evidence": dim_result.l3_evidence,
                    "overall_score": round(jittered_score, 1),
                    "raw_metrics": dim_result.raw_metrics
                }
        
        response_obj = QueryResponse(
            success=True, ai_response=response,
            bot_model=bot_model,
            metrics={
                "overall_ethical_score": overall, 
                "s_llm_score": round(result.s_llm * 100, 2),  # Scale to 0-100
                "risk_band": result.risk_band, 
                "final_label": result.final_label,
                "l1_pass_rate": round(result.l1_pass_rate() * 100, 2),  # Scale to 0-100
                "l1_pass_count": result.l1_pass_count(),
                "layer2_risk_score": round(result.layer2_risk_score * 100, 2),  # Scale to 0-100
                "failed_dimensions": result.get_failed_dims(),
                "highest_risk_dim": result.get_highest_risk_dim(),
                "spd": round(abs(result.spd) * 100, 2),  # Scale to 0-100 (abs for parity)
                "di": round(result.di * 100, 2),  # Scale to 0-100
                "eop": round(result.eop * 100, 2),  # Scale to 0-100
                "aod": round(abs(result.aod) * 100, 2),  # Scale to 0-100 (abs for disparity)
                "psi": round(result.psi * 100, 2),  # Scale to 0-100
                "ks": round(result.ks * 100, 2),  # Scale to 0-100
                "accuracy": round(result.accuracy * 100, 2),  # Scale to 0-100
                "recall": round(result.recall * 100, 2),  # Scale to 0-100
                "lawfulness": round(result.lawfulness * 100, 2)  # Scale to 0-100
            },
            tokens={"input_tokens": inp_tok, "output_tokens": out_tok, "total_tokens": inp_tok + out_tok, "latency_ms": latency},
            grounding={
                "score": round(grounding["score"] * 100, 2),  # Scale to 0-100
                "hallucination_rate": round(grounding["hallucination_rate"] * 100, 2),  # Scale to 0-100
                "l1_citation_coverage": round(grounding["l1"] * 100, 2),  # Scale to 0-100
                "l2_cosine_similarity": round(grounding["l2"] * 100, 2),  # Scale to 0-100
                "l3_support_ratio": round(grounding["l3"] * 100, 2)  # Scale to 0-100
            },
            ethics={"l1_pass_rate": round(result.l1_pass_rate() * 100, 2), "layer2_risk_score": round(result.layer2_risk_score * 100, 2), "required_action": result.required_action},
            dimensions=dimensions,
            rag_sources=[{"doc": r["doc"], "page": r["page"], "score": round(r["score"] * 100, 2)} for r in retrieved]  # Scale to 0-100
        )
        
        # Log full JSON response to CSV
        full_response_row = {
            "timestamp": ts.isoformat(),
            "user_query": query,
            "bot_model": bot_model,
            "full_json_response": response_obj.model_dump_json()
        }
        pd.DataFrame([full_response_row]).to_csv(FULL_RESPONSE_CSV, mode='a', header=False, index=False)
        
        # Store latest response for telemetry endpoint
        global latest_response
        latest_response = response_obj.model_dump()
        latest_response["timestamp"] = ts.isoformat()
        
        return response_obj
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ================== OPENROUTER CONFIGURATION ==================
import urllib.request
import urllib.error

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "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")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

OPENROUTER_MODELS = {
    "gpt-4o": "openai/gpt-4o",
    "claude-3.5-sonnet": "anthropic/claude-3.5-sonnet",
    "gemini-2.0-flash": "google/gemini-2.0-flash-exp",
    "llama-3.3-70b": "meta-llama/llama-3.3-70b-instruct",
    "deepseek-r1": "deepseek/deepseek-r1",
}

def call_openrouter(query: str, model: str, context: str = "") -> dict:
    """Call OpenRouter API for online LLM inference."""
    model_id = OPENROUTER_MODELS.get(model, "meta-llama/llama-3.3-70b-instruct")
    
    user_content = f"""Context: {context if context else 'No context provided'}

User Query: {query}

Please provide a helpful, accurate response based on RTI guidelines and Indian law. Cite relevant sections when applicable."""
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://rti-assistant.gov.in",
        "X-Title": "RTI Ethics Assistant"
    }
    
    payload = {
        "model": model_id,
        "messages": [
            {"role": "system", "content": RTI_PROMPT.replace("{context}", "").replace("{query}", "")},
            {"role": "user", "content": user_content}
        ],
        "temperature": 0.7,
        "max_tokens": 2048
    }
    
    start_time = time.time()
    
    try:
        req = urllib.request.Request(
            OPENROUTER_BASE_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST"
        )
        
        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))
            
        latency_ms = int((time.time() - start_time) * 1000)
        
        ai_response = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        usage = result.get("usage", {})
        
        return {
            "response": ai_response,
            "model": model_id,
            "latency_ms": latency_ms,
            "input_tokens": usage.get("prompt_tokens", 0),
            "output_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
            "success": True
        }
        
    except Exception as e:
        return {
            "response": f"Error calling OpenRouter: {str(e)}",
            "model": model_id,
            "latency_ms": int((time.time() - start_time) * 1000),
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "success": False,
            "error": str(e)
        }

# ================== ONLINE ENDPOINT (OpenRouter) ==================
@app.post("/query-online", response_model=QueryResponse)
async def process_query_online(request: QueryRequest):
    """
    Process query using OpenRouter (online mode) with full ethics engine calculations.
    Uses the same rti_ethics_engine as the Ollama endpoint - no hardcoded values.
    """
    try:
        query = request.user_query
        bot_model = request.bot_model
        ts = datetime.now()
        
        # RAG retrieval (same as offline mode)
        context, rag_docs, retrieved = retrieve(query)
        
        # Call OpenRouter instead of Ollama
        openrouter_result = call_openrouter(query, bot_model, context)
        
        if not openrouter_result["success"]:
            raise HTTPException(status_code=500, detail=openrouter_result.get("error", "OpenRouter call failed"))
        
        response = openrouter_result["response"]
        latency = openrouter_result["latency_ms"]
        inp_tok = openrouter_result["input_tokens"]
        out_tok = openrouter_result["output_tokens"]
        
        # Compute grounding (same as offline)
        grounding = compute_grounding(response, context, retrieved)
        
        # Detect group from query style
        def detect_group(q):
            rural = [r'\bji\b', r'\bkindly\b', r'\brespected\b', r'\bplease\s+sir\b']
            urban = [r'\basap\b', r'\bfyi\b', r'Section\s*\d+', r'\bpursuant\b']
            r = sum(1 for p in rural if re.search(p, q.lower()))
            u = sum(1 for p in urban if re.search(p, q.lower()))
            return 1 if r > u else 0 if u > r else hash(q) % 2
        
        # Classification
        gt = 0 if re.search(r'\b(mobile|address|salary|private|personal)\b', query.lower()) else 1
        pred = 0 if re.search(r'\b(exempt|cannot|refused|section 8|privacy)\b', response.lower()) else 1
        group = detect_group(query)
        
        # Use historical data for fairness calculations
        global historical_data
        if historical_data and historical_data["count"] >= 10:
            all_preds = np.append(historical_data["predictions"], pred)
            all_labels = np.append(historical_data["labels"], gt)
            all_groups = np.append(historical_data["groups"], group)
        else:
            all_preds = np.array([pred])
            all_labels = np.array([gt])
            all_groups = np.array([group])
        
        # USE RTI ETHICS ENGINE FOR ALL CALCULATIONS
        metrics = build_metrics_from_raw_data(
            query=query, response=response,
            predictions=all_preds, labels=all_labels,
            sensitive_attr=all_groups,
            latency_ms=latency, output_tokens=out_tok, grounding_score=grounding["score"]
        )
        
        result: EthicsResult = ethics_engine.run_protocol(metrics)
        overall = {"ETHICAL": 100, "CONDITIONALLY_ETHICAL": 70, "UNETHICAL": 0}.get(result.final_label, 50)
        
        # Update fairness CSV
        fairness_row = pd.DataFrame([{"sensitive_group": group, "ground_truth_disclose": gt, "system_disclose": pred}])
        fairness_row.to_csv(FAIRNESS_CSV, mode='a', header=not os.path.exists(FAIRNESS_CSV), index=False)
        historical_data = load_historical_data()
        
        # Build dimensions from ethics engine
        dimensions = {}
        for dim_key in DIMENSION_WEIGHTS.keys():
            dim_result = result.get_dim_result(dim_key)
            if dim_result:
                base_score = 100 * (1 - dim_result.l2_risk)
                jitter = random.uniform(-3, 3)
                jittered_score = max(0, min(100, base_score + jitter))
                
                dimensions[dim_key] = {
                    "name": dim_result.name,
                    "weight": DIMENSION_WEIGHTS[dim_key],
                    "l1_status": dim_result.l1_status,
                    "l1_reasons": dim_result.l1_reasons,
                    "l2_risk": round(dim_result.l2_risk, 4),
                    "l2_weighted_risk": round(dim_result.l2_risk * DIMENSION_WEIGHTS[dim_key], 4),
                    "l2_indicators": dim_result.l2_indicators,
                    "l3_evidence": dim_result.l3_evidence,
                    "overall_score": round(jittered_score, 1),
                    "raw_metrics": dim_result.raw_metrics
                }
        
        # CSV logging
        row = {
            "timestamp": ts.isoformat(), "user_query": query, "bot_model": openrouter_result["model"],
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
            "rag_documents": rag_docs,
            "sensitive_group": group, "ground_truth_disclose": gt, "system_disclose": pred
        }
        pd.DataFrame([row]).to_csv(METRICS_CSV, mode='a', header=False, index=False)
        
        response_obj = QueryResponse(
            success=True, ai_response=response,
            bot_model=openrouter_result["model"],
            metrics={
                "overall_ethical_score": overall,
                "s_llm_score": round(result.s_llm * 100, 2),
                "risk_band": result.risk_band,
                "final_label": result.final_label,
                "l1_pass_rate": round(result.l1_pass_rate() * 100, 2),
                "l1_pass_count": result.l1_pass_count(),
                "layer2_risk_score": round(result.layer2_risk_score * 100, 2),
                "failed_dimensions": result.get_failed_dims(),
                "highest_risk_dim": result.get_highest_risk_dim(),
                "spd": round(abs(result.spd) * 100, 2),
                "di": round(result.di * 100, 2),
                "eop": round(result.eop * 100, 2),
                "aod": round(abs(result.aod) * 100, 2),
                "psi": round(result.psi * 100, 2),
                "ks": round(result.ks * 100, 2),
                "accuracy": round(result.accuracy * 100, 2),
                "recall": round(result.recall * 100, 2),
                "lawfulness": round(result.lawfulness * 100, 2)
            },
            tokens={"input_tokens": inp_tok, "output_tokens": out_tok, "total_tokens": inp_tok + out_tok, "latency_ms": latency},
            grounding={
                "score": round(grounding["score"] * 100, 2),
                "hallucination_rate": round(grounding["hallucination_rate"] * 100, 2),
                "l1_citation_coverage": round(grounding["l1"] * 100, 2),
                "l2_cosine_similarity": round(grounding["l2"] * 100, 2),
                "l3_support_ratio": round(grounding["l3"] * 100, 2)
            },
            ethics={"l1_pass_rate": round(result.l1_pass_rate() * 100, 2), "layer2_risk_score": round(result.layer2_risk_score * 100, 2), "required_action": result.required_action},
            dimensions=dimensions,
            rag_sources=[{"doc": r["doc"], "page": r["page"], "score": round(r["score"] * 100, 2)} for r in retrieved]
        )
        
        # Log full response
        full_response_row = {
            "timestamp": ts.isoformat(),
            "user_query": query,
            "bot_model": openrouter_result["model"],
            "full_json_response": response_obj.model_dump_json()
        }
        pd.DataFrame([full_response_row]).to_csv(FULL_RESPONSE_CSV, mode='a', header=False, index=False)
        
        # Store latest response
        global latest_response
        latest_response = response_obj.model_dump()
        latest_response["timestamp"] = ts.isoformat()
        
        return response_obj
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Store latest response for admin graphs
latest_response = None

@app.get("/latest")
async def get_latest():
    """Get the latest response for admin telemetry graphs."""
    if latest_response:
        return latest_response
    return {"error": "No responses yet", "status": "waiting"}

@app.get("/history")
async def get_history(limit: int = 100):
    """Get historical responses from CSV for graphs."""
    try:
        if not os.path.exists(FULL_RESPONSE_CSV):
            return {"success": True, "history": [], "count": 0}
        
        try:
            df = pd.read_csv(FULL_RESPONSE_CSV, on_bad_lines='skip', engine='python')
        except TypeError:
            df = pd.read_csv(FULL_RESPONSE_CSV, error_bad_lines=False, warn_bad_lines=False, engine='python')
        
        if df.empty:
            return {"success": True, "history": [], "count": 0}
        
        # Get last N rows
        df = df.tail(limit)
        
        history = []
        for idx, row in df.iterrows():
            try:
                # Parse stored JSON response
                full_json = row.get("full_json_response", "{}")
                if pd.isna(full_json):
                    continue
                    
                response_data = json.loads(full_json)
                
                # Add metadata
                response_data["timestamp"] = row.get("timestamp", datetime.now().isoformat())
                response_data["bot_model"] = row.get("bot_model", "llama3")
                response_data["id"] = f"resp-{idx}-{hash(str(row.get('timestamp', '')))}"
                
                history.append(response_data)
            except (json.JSONDecodeError, Exception) as e:
                print(f"⚠️ Error parsing row {idx}: {e}")
                continue
        
        return {"success": True, "history": history, "count": len(history)}
    except Exception as e:
        print(f"❌ History endpoint error: {e}")
        return {"success": False, "error": str(e), "history": [], "count": 0}

@app.get("/conversations")
async def get_conversations_history(limit: int = 50):
    """Get conversation history for admin dashboard."""
    try:
        if not os.path.exists(METRICS_CSV):
            return {"success": True, "conversations": [], "count": 0}
        
        # Robust CSV reading: engine='python' is slower but better at handling bad lines
        # error_bad_lines=False is for older pandas versions, on_bad_lines='skip' for newer
        try:
            df = pd.read_csv(METRICS_CSV, on_bad_lines='skip', engine='python')
        except TypeError:
            # Fallback for older pandas versions
            df = pd.read_csv(METRICS_CSV, error_bad_lines=False, warn_bad_lines=False, engine='python')
        
        if df.empty:
            return {"success": True, "conversations": [], "count": 0}
        
        # Get last N rows
        df = df.tail(limit)
        
        conversations = []
        for idx, row in df.iterrows():
            conv = {
                "id": f"conv-{idx}-{hash(str(row.get('timestamp', '')))}",
                "timestamp": row.get("timestamp", ""),
                "user_query": row.get("user_query", ""),
                "ai_response": row.get("ai_response", ""),
                "overall_ethical_score": row.get("overall_ethical_score", 0),
                "s_llm_score": row.get("s_llm_score", 0),
                "risk_band": row.get("risk_band", ""),
                "final_label": row.get("final_label", ""),
                "latency_ms": row.get("latency_ms", 0),
                "total_tokens": row.get("total_tokens", 0),
                "grounding_score": row.get("grounding_score", 0),
                "spd": row.get("spd", 0),
                "di": row.get("di", 0),
                "eop": row.get("eop", 0),
                "aod": row.get("aod", 0),
                "rag_documents": row.get("rag_documents", ""),
            }
            conversations.append(conv)
        
        return {"success": True, "conversations": conversations, "count": len(conversations)}
    except Exception as e:
        print(f"❌ Conversations endpoint error: {e}")
        return {"success": False, "error": str(e), "conversations": [], "count": 0}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/pdf/{filename}")
async def serve_pdf(filename: str):
    """Serve PDF files from the data directory."""
    from fastapi.responses import FileResponse
    
    # Sanitize filename to prevent directory traversal
    safe_filename = os.path.basename(filename)
    pdf_path = os.path.join(DATA_DIR, safe_filename)
    
    print(f"📄 PDF Request: {safe_filename}")
    print(f"📁 Looking in: {DATA_DIR}")
    print(f"📍 Full path: {pdf_path}")
    print(f"✅ Exists: {os.path.exists(pdf_path)}")
    
    if not os.path.exists(pdf_path):
        # List available PDFs to help debug
        available = [f for f in os.listdir(DATA_DIR) if f.lower().endswith('.pdf')]
        print(f"❌ Not found! Available PDFs: {available}")
        raise HTTPException(status_code=404, detail=f"PDF not found: {safe_filename}. Available: {available}")
    
    if not safe_filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=safe_filename,
        headers={"Content-Disposition": f"inline; filename={safe_filename}"}
    )

@app.get("/pdfs")
async def list_pdfs():
    """List all available PDFs in the data directory."""
    pdf_files = [f for f in os.listdir(DATA_DIR) if f.lower().endswith('.pdf')]
    return {"pdfs": pdf_files, "data_dir": DATA_DIR}

@app.get("/debug")
async def debug_paths():
    """Debug endpoint to check paths."""
    return {
        "script_dir": SCRIPT_DIR,
        "backend_dir": BACKEND_DIR,
        "data_dir": DATA_DIR,
        "data_dir_exists": os.path.exists(DATA_DIR),
        "pdfs": [f for f in os.listdir(DATA_DIR) if f.lower().endswith('.pdf')] if os.path.exists(DATA_DIR) else []
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
