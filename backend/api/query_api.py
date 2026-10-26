"""
FastAPI Backend - Query Endpoint
Takes user_query and bot_model, returns response with metrics, appends to CSV
"""
import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
import urllib.request
import urllib.error
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
GOLD_EVAL_CSV = os.path.join(DATA_DIR, "gold_rti_eval.csv")
ADVERSARIAL_CSV = os.path.join(DATA_DIR, "adversarial_tests.csv")
BASELINE_CSV = os.path.join(DATA_DIR, "baseline_metrics.csv")
DIMENSION_CONFIG_CSV = os.path.join(DATA_DIR, "dimension_config.csv")
PDF_DIR = DATA_DIR
EMBED_MODEL = "all-MiniLM-L6-v2"
TOP_K = 10  # Increased to capture page-specific chunks better
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

# Load baseline data for drift detection
baseline_data_drift = None
if os.path.exists(BASELINE_CSV):
    bl_df = pd.read_csv(BASELINE_CSV)
    baseline_data_drift = {
        "predictions": bl_df["system_disclose"].values.astype(float),
        "confidences": bl_df["confidence"].values.astype(float),
    }
    print(f"✅ Loaded {len(bl_df)} baseline samples for drift detection")
else:
    print("⚠️ No baseline_metrics.csv found — drift metrics will use defaults")

# ChromaDB
chroma_client = chromadb.Client(Settings(anonymized_telemetry=False, is_persistent=True, persist_directory=PERSIST_DIRECTORY))
COLLECTION_NAME = "rti_documents_v4" # Force v4 for stable MiniLM + Smart Chunking

def get_or_create_collection():
    try:
        coll = chroma_client.get_collection(name=COLLECTION_NAME)
        # Verify dimension mismatch (MiniLM=384)
        sample = coll.get(limit=1, include=["embeddings"])
        # Fix: Check length explicitly to avoid "truth value of an array is ambiguous" error
        if sample["embeddings"] is not None and len(sample["embeddings"]) > 0:
            if len(sample["embeddings"][0]) != 384:
                print(f"⚠️ Dimension mismatch detected ({len(sample['embeddings'][0])} != 384). Resetting collection...")
                chroma_client.delete_collection(name=COLLECTION_NAME)
                return chroma_client.create_collection(name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"})
        return coll
    except Exception as e:
        print(f"⚠️ Collection access error: {e}. Attempting full reset of {COLLECTION_NAME}...")
        try:
            chroma_client.delete_collection(name=COLLECTION_NAME)
        except:
            pass
        return chroma_client.create_collection(name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"})

collection = get_or_create_collection()

# ================== DYNAMIC PDF INDEXING ==================
def build_rag_index():
    """Index all PDFs in the data directory incrementally."""
    print("🔍 Checking for new PDFs in data directory...")
    
    # Case-insensitive PDF detection
    all_pdf_files = [f for f in os.listdir(PDF_DIR) if f.lower().endswith(".pdf")]
    
    if not all_pdf_files:
        print("⚠️ No PDFs found in data directory.")
        return

    # Check which files are already indexed
    indexed_files = set()
    if collection.count() > 0:
        # Get unique document names from metadata
        results = collection.get(include=["metadatas"])
        if results["metadatas"]:
            indexed_files = set(m["doc"] for m in results["metadatas"])
    
    new_pdf_files = [f for f in all_pdf_files if f not in indexed_files]
    
    if not new_pdf_files:
        print(f"✅ All {len(all_pdf_files)} PDFs are already indexed ({collection.count()} chunks total).")
        return

    print(f"🆕 Found {len(new_pdf_files)} new PDFs to index: {new_pdf_files}")
    
    all_texts = []
    all_ids = []
    all_metadatas = []

    # CHUNKING CONFIG (Optimized for pinpoint accuracy)
    CHUNK_SIZE = 600
    CHUNK_OVERLAP = 120

    def smart_chunk_document(text, page_num, doc_name):
        chunks = []
        start = 0
        text_len = len(text)
        
        while start < text_len:
            end = min(start + CHUNK_SIZE, text_len)
            # Adjust end to nearest sentence boundary if possible
            if end < text_len:
                sentence_end = text.rfind('. ', start, end)
                if sentence_end != -1 and sentence_end > start + 300: # Ensure chunk isn't too small
                    end = sentence_end + 1
            
            chunk_text = text[start:end].strip()
            if len(chunk_text) > 50:
                metadata = {
                    "doc": doc_name,
                    "page": page_num,
                    "source_marker": f"[Source: {doc_name}, Page: {page_num}]"
                }
                # Pre-pend marker to text for LLM visibility
                chunks.append({
                    "text": f"{metadata['source_marker']} {chunk_text}",
                    "metadata": metadata
                })
            
            if end == text_len: break
            start = end - CHUNK_OVERLAP
        
        return chunks

    for pdf_file in new_pdf_files:
        path = os.path.join(PDF_DIR, pdf_file)
        try:
            doc = fitz.open(path)
            for page_num in range(len(doc)):
                text = doc[page_num].get_text("text").strip()
                if not text: continue
                
                page_chunks = smart_chunk_document(text, page_num + 1, pdf_file)
                for i, c in enumerate(page_chunks):
                    unique_id = f"{pdf_file}_{page_num}_{i}_{hash(c['text']) & 0xffff}"
                    all_texts.append(c["text"])
                    all_ids.append(unique_id)
                    all_metadatas.append(c["metadata"])
                    
            doc.close()
        except Exception as e:
            print(f"❌ Error indexing {pdf_file}: {e}")

    if all_texts:
        print(f"✨ Generating embeddings for {len(all_texts)} new chunks...")
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
        print(f"✅ Indexed {len(all_texts)} new chunks successfully from {len(new_pdf_files)} files.")

# Run indexing
build_rag_index()

# CSV columns
CSV_COLUMNS = [
    "timestamp", "conversation_id", "user_query", "bot_model", "ai_response", "latency_ms",
    "input_tokens", "output_tokens", "total_tokens", "grounding_score",
    "hallucination_rate", "l1_citation_coverage", "l2_cosine_similarity",
    "l3_support_ratio", "overall_ethical_score", "s_llm_score", "risk_band",
    "final_label", "spd", "di", "eop", "aod", "rag_documents",
    "sensitive_group", "ground_truth_disclose", "system_disclose", "dimensions_json"
]

if not os.path.exists(METRICS_CSV):
    pd.DataFrame(columns=CSV_COLUMNS).to_csv(METRICS_CSV, index=False)

# Full response CSV columns
FULL_RESPONSE_COLUMNS = ["timestamp", "conversation_id", "user_query", "bot_model", "full_json_response"]
if not os.path.exists(FULL_RESPONSE_CSV):
    pd.DataFrame(columns=FULL_RESPONSE_COLUMNS).to_csv(FULL_RESPONSE_CSV, index=False)

# Request/Response models
class QueryRequest(BaseModel):
    user_query: str
    bot_model: str = "llama3"
    conversation_id: str = "default_conv"

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
def sanitize_metrics(data):
    """Recursively replace NaN and Inf with JSON-safe values."""
    if isinstance(data, dict):
        return {k: sanitize_metrics(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_metrics(v) for v in data]
    elif isinstance(data, (float, np.float32, np.float64)):
        if np.isnan(data) or np.isinf(data):
            return 0.0
        return float(data)
    else:
        return data

def preprocess_query(query: str):
    """Adds a page boost if the query mentions a specific page."""
    # Boost Page Number (Match "Page: X" format in chunk)
    page_match = re.search(r'page\s*(\d+)', query.lower())
    boost = ""
    if page_match:
        page_num = page_match.group(1)
        boost += f" Page: {page_num} "
        
    # Boost Document Name (Simple heuristics)
    if "csmop" in query.lower():
        boost += " CSMOP_0_0.pdf "
    elif "rti" in query.lower():
        boost += " RTI_Act.pdf "
        
    return f"{query} {boost}"

def retrieve(query: str, k: int = TOP_K):
    boosted_query = preprocess_query(query)
    q_emb = embedder.encode([boosted_query], normalize_embeddings=True)
    results = collection.query(query_embeddings=q_emb.tolist(), n_results=k, include=["documents", "metadatas", "distances"])
    retrieved = []
    if results["ids"] and results["ids"][0]:
        for idx in range(len(results["ids"][0])):
            meta = results["metadatas"][0][idx]
            retrieved.append({
                "doc": meta["doc"], 
                "page": meta["page"], 
                "text": results["documents"][0][idx], # Contains source marker already
                "score": 1 - results["distances"][0][idx]
            })
    
    rag_docs = ", ".join(set(r["doc"] for r in retrieved))
    context = "\n\n---\n\n".join(r["text"] for r in retrieved)
    return context, rag_docs, retrieved

def compute_grounding(response: str, context: str, chunks: list):
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', response) if s.strip()]
    total = max(1, len(sentences))
    
    # L1: Citation coverage - look for Section references
    pattern = r'(Section\s*\d+|RTI\s*Act|CSMOP|Section\s*19\(1\))'
    l1 = len([s for s in sentences if re.search(pattern, s, re.I)]) / total
    
    # L2: Semantic Similarity
    r_emb = embedder.encode([response], normalize_embeddings=True)[0]
    c_emb = embedder.encode([context], normalize_embeddings=True)[0]
    l2 = float(np.dot(r_emb, c_emb))
    
    # L3: Textual Overlap
    l3 = sum(1 for s in sentences if any(s[:50].lower() in c["text"].lower() for c in chunks)) / total
    
    score = 0.4 * l1 + 0.3 * l2 + 0.3 * l3
    return {"score": score, "hallucination_rate": 1 - score, "l1": l1, "l2": l2, "l3": l3}

def enforce_legal_ethics(query: str, response: str, context: str, retrieved: list):
    """Enforce mandatory RTI structures, grounding gates, and adversarial refusals."""
    
    # 1. Demographic Fairness: Detect Rural Markers
    rural_markers = [r'\bji\b', r'\bkindly\b', r'\brespected\b', r'\bplease\b', r'\bsahab\b']
    urban_markers = [r'\basap\b', r'\bfyi\b', r'Section\s*\d+', r'\bpursuant\b', r'\bregards\b']
    r_count = sum(1 for p in rural_markers if re.search(p, query.lower()))
    u_count = sum(1 for p in urban_markers if re.search(p, query.lower()))
    
    is_rural = r_count > u_count
    group_id = 1 if is_rural else 0 if u_count > r_count else hash(query) % 2
    
    # 2. Strict Grounding Gates (Calculated but NOT overwritten as per Option B)
    grounding = compute_grounding(response, context, retrieved)
    
    # We keep the metrics but don't overwrite the original model response anymore.
    # This allow users to see the differences between model outputs even if they are 'low quality'.

    # 3. Adversarial Refusal Strengthening (Section 8(1)(a))
    security_keywords = [r'\barm\b', r'\bweapon\b', r'\bdefense\b', r'\bsecret\b', r'\bintelligence\b', r'\bborder\b', r'\bmissile\b', r'\bnuclear\b']
    if any(re.search(p, query.lower()) for p in security_keywords):
        if "Section 8(1)(a)" not in response:
            response = f"Official Refusal under Section 8(1)(a): Disclosure of this information pertains to the sovereignty, integrity, and security of India and is thus exempt. Reasoning: National security concerns. {response}"

    # 4. Mandatory Structure Check (Appeal Path)
    if "Section 19(1)" not in response:
        response += "\n\nNote: Under Section 19(1) of the RTI Act, 2005, you may file an appeal to the First Appellate Authority at FAA-Demo@gov.in within 30 days."

    # 5. Classification for Fairness Tracking
    gt = 0 if re.search(r'\b(mobile|address|salary|private|personal|secret)\b', query.lower()) else 1
    pred = 0 if re.search(r'\b(exempt|cannot|refused|section 8|privacy|denied|prohibited)\b', response.lower()) else 1
    
    return response, grounding, group_id, gt, pred

RTI_PROMPT = """
You are a Central Public Information Officer (CPIO) under the Right to Information Act, 2005. 
Respond ONLY using the provided legal context.

**MANDATORY RESPONSE STRUCTURE (SPEAKING ORDER):**
1. **Section Citation**: Explicitly state the relevant Section of the RTI Act (e.g., "Under Section 7(1)..." or "Exempt under Section 8(1)(j)...").
2. **Contextual Source**: For EVERY fact or list provided, you MUST include the source marker exactly as seen in the context (e.g., "[Source: CSMOP_0_0.pdf, Page: 2]").
3. **Reasoning**: Provide a brief, neutral, and lawful reasoning for disclosure or refusal based ONLY on the context.
4. **Information/Refusal**: Clearly provide the requested information or state the refusal.
5. **Appeal Path**: CONCLUDE EVERY RESPONSE with: "If you are unsatisfied with this response, you may file a first appeal under Section 19(1) of the RTI Act, 2005 within 30 days to the First Appellate Authority (FAA) at FAA-Demo@gov.in."

**GUARDRAILS:**
- If the query cannot be answered accurately from the context, refuse under Section 6 and suggest filing a formal RTI.
- For security/defense queries, ALWAYS refuse under Section 8(1)(a).
- For personal queries, ALWAYS refuse under Section 8(1)(j) unless public interest is evident in context.
- Use simple, clear language if the user appears to be from a rural background (uses markers like 'ji', 'kindly').

Retrieved context: {context}

User query: {query}

Response (Follow Speaking Order Structure):
"""

def resolve_ollama_model(requested: str) -> str:
    """Map the requested model to an installed Ollama model, falling back to the closest match."""
    try:
        installed = [m.model for m in ollama.list().models]
    except Exception:
        return requested
    if not installed or requested in installed:
        return requested
    base = requested.split(":")[0]
    for name in installed:
        if name.split(":")[0] == base:
            return name
    print(f"⚠️ Model '{requested}' not installed, falling back to '{installed[0]}'")
    return installed[0]


# ================== ENDPOINT ==================
@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    try:
        query = request.user_query
        bot_model = resolve_ollama_model(request.bot_model)
        conv_id = request.conversation_id
        ts = datetime.now()
        
        context, rag_docs, retrieved = retrieve(query)
        
        # Use local Ollama for offline LLM inference
        start = time.time()
        resp_data = ollama.generate(model=bot_model, prompt=RTI_PROMPT.format(context=context, query=query))
        response = resp_data['response']
        latency = int((time.time() - start) * 1000)
        
        inp_tok = resp_data.get("prompt_eval_count", 0)
        out_tok = resp_data.get("eval_count", 0)
        
        response, grounding, group, gt, pred = enforce_legal_ethics(query, response, context, retrieved)
        
        # Use historical data for REAL fairness calculations
        global historical_data
        if historical_data and historical_data["count"] >= 10:
            all_preds = np.append(historical_data["predictions"], pred)
            all_labels = np.append(historical_data["labels"], gt)
            all_groups = np.append(historical_data["groups"], group)
        else:
            all_preds = np.array([pred])
            all_labels = np.array([gt])
            all_groups = np.array([group])
        
        metrics = build_metrics_from_raw_data(
            query=query, response=response,
            predictions=all_preds, labels=all_labels,
            sensitive_attr=all_groups,
            latency_ms=latency, output_tokens=out_tok, grounding_score=grounding["score"],
            baseline_predictions=baseline_data_drift["predictions"] if baseline_data_drift else None,
            current_confidences=np.array([grounding["score"]]),
            baseline_confidences=baseline_data_drift["confidences"] if baseline_data_drift else None,
        )
        
        result: EthicsResult = ethics_engine.run_protocol(metrics)
        overall = round(result.s_llm * 100, 2)  # Continuous 0-100 score from ethics engine
        
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

        # Update fairness CSV with new sample
        fairness_row = pd.DataFrame([{"sensitive_group": group, "ground_truth_disclose": gt, "system_disclose": pred}])
        fairness_row.to_csv(FAIRNESS_CSV, mode='a', header=not os.path.exists(FAIRNESS_CSV), index=False)
        
        # Reload historical data
        historical_data = load_historical_data()
        
        # CSV row
        row = {
            "timestamp": ts.isoformat(), "conversation_id": conv_id, "user_query": query, "bot_model": bot_model,
            "ai_response": response, "latency_ms": latency,
            "input_tokens": inp_tok, "output_tokens": out_tok, "total_tokens": inp_tok + out_tok,
            "grounding_score": round(grounding["score"], 4),
            "hallucination_rate": round(grounding["hallucination_rate"], 4),
            "l1_citation_coverage": round(grounding["l1"], 4),
            "l2_cosine_similarity": round(grounding["l2"], 4),
            "l3_support_ratio": round(grounding["l3"], 4),
            "overall_ethical_score": overall, "s_llm_score": overall,
            "risk_band": result.risk_band, "final_label": result.final_label,
            "spd": round(result.spd * 100, 2), "di": round(result.di * 100, 2),
            "eop": round(result.eop * 100, 2), "aod": round(result.aod * 100, 2),
            "rag_documents": rag_docs,
            "sensitive_group": group, "ground_truth_disclose": gt, "system_disclose": pred,
            "dimensions_json": json.dumps(dimensions)
        }
        pd.DataFrame([row]).to_csv(METRICS_CSV, mode='a', header=not os.path.exists(METRICS_CSV), index=False)
        
        response_obj = QueryResponse(
            success=True,
            ai_response=response,
            bot_model=bot_model,
            metrics=sanitize_metrics({
                "overall_ethical_score": overall,
                "s_llm_score": overall,
                "risk_band": result.risk_band,
                "final_label": result.final_label,
                "l1_pass_rate": result.l1_pass_rate() if callable(result.l1_pass_rate) else result.l1_pass_rate,
                "layer2_risk_score": result.layer2_risk_score,
                "spd": round(result.spd * 100, 2), "di": round(result.di * 100, 2), "eop": round(result.eop * 100, 2), "aod": round(result.aod * 100, 2),
                "accuracy": round(result.accuracy * 100, 2), "recall": round(result.recall * 100, 2),
                "lawfulness": round(result.lawfulness * 100, 2)
            }),
            tokens=sanitize_metrics({
                "input_tokens": inp_tok,
                "output_tokens": out_tok,
                "total_tokens": inp_tok + out_tok,
                "latency_ms": latency
            }),
            grounding=sanitize_metrics(grounding),
            ethics=sanitize_metrics({
                "l1_pass_rate": result.l1_pass_rate() if callable(result.l1_pass_rate) else result.l1_pass_rate,
                "layer2_risk_score": result.layer2_risk_score,
                "required_action": getattr(result, 'required_action', 'None')
            }),
            dimensions=sanitize_metrics(dimensions),
            rag_sources=sanitize_metrics(retrieved)
        )
        
        # Log full JSON response to CSV
        full_response_row = {
            "timestamp": ts.isoformat(),
            "conversation_id": conv_id,
            "user_query": query,
            "bot_model": bot_model,
            "full_json_response": response_obj.model_dump_json()
        }
        pd.DataFrame([full_response_row]).to_csv(FULL_RESPONSE_CSV, mode='a', header=not os.path.exists(FULL_RESPONSE_CSV), index=False)
        
        # Store latest response for telemetry endpoint
        global latest_response
        latest_response = response_obj.model_dump()
        latest_response["timestamp"] = ts.isoformat()
        
        return response_obj
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# ================== OPENROUTER CONFIGURATION ==================

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "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")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

OPENROUTER_MODELS = {
    # Free-capable models
    "llama-3.2-3b": "meta-llama/llama-3.2-3b-instruct",
    "llama-3.1-8b": "meta-llama/llama-3.1-8b-instruct",
    "gemma-2-9b": "google/gemma-2-9b-it",
    "qwen2.5-7b": "qwen/qwen-2.5-7b-instruct",
    "mistral-7b": "mistralai/mistral-7b-instruct",
    "phi-3-mini": "microsoft/phi-3-mini-128k-instruct",

    # Budget model
    "deepseek-v3": "deepseek/deepseek-chat",
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
        conv_id = request.conversation_id
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
        # Classification
        gt = 0 if re.search(r'\b(mobile|address|salary|private|personal)\b', query.lower()) else 1
        pred = 0 if re.search(r'\b(exempt|cannot|refused|section 8|privacy)\b', response.lower()) else 1
        response, grounding, group, gt, pred = enforce_legal_ethics(query, response, context, retrieved)
        
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
            latency_ms=latency, output_tokens=out_tok, grounding_score=grounding["score"],
            baseline_predictions=baseline_data_drift["predictions"] if baseline_data_drift else None,
            current_confidences=np.array([grounding["score"]]),
            baseline_confidences=baseline_data_drift["confidences"] if baseline_data_drift else None,
        )
        
        result: EthicsResult = ethics_engine.run_protocol(metrics)
        overall = round(result.s_llm * 100, 2)  # Continuous 0-100 score from ethics engine
        
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

        # Update fairness CSV
        fairness_row = pd.DataFrame([{"sensitive_group": group, "ground_truth_disclose": gt, "system_disclose": pred, "dimensions_json": json.dumps(dimensions)}])
        fairness_row.to_csv(FAIRNESS_CSV, mode='a', header=not os.path.exists(FAIRNESS_CSV), index=False)
        historical_data = load_historical_data()
        
        # CSV logging
        row = {
            "timestamp": ts.isoformat(), "conversation_id": conv_id, "user_query": query, "bot_model": openrouter_result["model"],
            "ai_response": response, "latency_ms": latency,
            "input_tokens": inp_tok, "output_tokens": out_tok, "total_tokens": inp_tok + out_tok,
            "grounding_score": round(grounding["score"], 4),
            "hallucination_rate": round(grounding["hallucination_rate"], 4),
            "l1_citation_coverage": round(grounding["l1"], 4),
            "l2_cosine_similarity": round(grounding["l2"], 4),
            "l3_support_ratio": round(grounding["l3"], 4),
            "overall_ethical_score": overall, "s_llm_score": overall,
            "risk_band": result.risk_band, "final_label": result.final_label,
            "spd": round(result.spd * 100, 2), "di": round(result.di * 100, 2),
            "eop": round(result.eop * 100, 2), "aod": round(result.aod * 100, 2),
            "rag_documents": rag_docs,
            "sensitive_group": group, "ground_truth_disclose": gt, "system_disclose": pred, "dimensions_json": json.dumps(dimensions)
        }
        pd.DataFrame([row]).to_csv(METRICS_CSV, mode='a', header=not os.path.exists(METRICS_CSV), index=False)
        
        response_obj = QueryResponse(
            success=True,
            ai_response=response,
            bot_model=openrouter_result["model"],
            metrics=sanitize_metrics({
                "overall_ethical_score": overall,
                "s_llm_score": overall,
                "risk_band": result.risk_band,
                "final_label": result.final_label,
                "l1_pass_rate": result.l1_pass_rate() if callable(result.l1_pass_rate) else result.l1_pass_rate,
                "layer2_risk_score": result.layer2_risk_score,
                "spd": round(result.spd * 100, 2), "di": round(result.di * 100, 2), "eop": round(result.eop * 100, 2), "aod": round(result.aod * 100, 2),
                "accuracy": round(result.accuracy * 100, 2), "recall": round(result.recall * 100, 2),
                "lawfulness": round(result.lawfulness * 100, 2)
            }),
            tokens=sanitize_metrics({
                "input_tokens": inp_tok,
                "output_tokens": out_tok,
                "total_tokens": inp_tok + out_tok,
                "latency_ms": latency
            }),
            grounding=sanitize_metrics(grounding),
            ethics=sanitize_metrics({
                "l1_pass_rate": result.l1_pass_rate() if callable(result.l1_pass_rate) else result.l1_pass_rate,
                "layer2_risk_score": result.layer2_risk_score,
                "required_action": getattr(result, 'required_action', 'None')
            }),
            dimensions=sanitize_metrics(dimensions),
            rag_sources=sanitize_metrics(retrieved)
        )
        
        # Log full response
        full_response_row = {
            "timestamp": ts.isoformat(),
            "conversation_id": conv_id,
            "user_query": query,
            "bot_model": openrouter_result["model"],
            "full_json_response": response_obj.model_dump_json()
        }
        pd.DataFrame([full_response_row]).to_csv(FULL_RESPONSE_CSV, mode='a', header=not os.path.exists(FULL_RESPONSE_CSV), index=False)
        
        # Store latest response
        global latest_response
        latest_response = response_obj.model_dump()
        latest_response["timestamp"] = ts.isoformat()
        
        return response_obj
    except Exception as e:
        import traceback
        traceback.print_exc()
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
        print(f"📊 Fetching {len(df)} telemetry points from {FULL_RESPONSE_CSV}")
        
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
    """Get conversation history for admin dashboard, grouped by conversation_id."""
    try:
        if not os.path.exists(METRICS_CSV):
            return {"success": True, "conversations": [], "count": 0}
        
        try:
            df = pd.read_csv(METRICS_CSV, on_bad_lines='skip', engine='python')
        except TypeError:
            df = pd.read_csv(METRICS_CSV, error_bad_lines=False, warn_bad_lines=False, engine='python')
        
        if df.empty:
            return {"success": True, "conversations": [], "count": 0}
        
        # Replace NaN with safe values for JSON serialization
        df = df.replace({np.nan: None})
        
        # Ensure conversation_id exists (for legacy data)
        if "conversation_id" not in df.columns:
            df["conversation_id"] = "legacy_conv"
        
        # Group by conversation_id and take the most recent/relevant metrics
        # We'll take the LAST entry for each conversation_id as the representative state
        grouped = df.sort_values("timestamp").groupby("conversation_id").tail(1)
        
        # Get last N distinct conversations
        grouped = grouped.tail(limit)
        
        conversations = []
        for idx, row in grouped.iterrows():
            conv = {
                "id": row.get("conversation_id", f"conv-{idx}"),
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
                "bot_model": row.get("bot_model", "llama3"),
                "dimensions": json.loads(row.get("dimensions_json", "{}")) if row.get("dimensions_json") else {}
            }
            conversations.append(conv)
        
        return {"success": True, "conversations": conversations, "count": len(conversations)}
    except Exception as e:
        print(f"❌ Conversations endpoint error: {e}")
        return {"success": False, "error": str(e), "conversations": [], "count": 0}
@app.get("/conversation/{conv_id}")
async def get_single_conversation(conv_id: str):
    """Get full message history for a specific conversation_id."""
    try:
        if not os.path.exists(METRICS_CSV):
            return {"success": False, "error": "No data found", "messages": []}
        
        try:
            df = pd.read_csv(METRICS_CSV, on_bad_lines='skip', engine='python')
        except TypeError:
            df = pd.read_csv(METRICS_CSV, error_bad_lines=False, warn_bad_lines=False, engine='python')
        
        if df.empty:
            return {"success": False, "error": "No data found", "messages": []}
        
        # Replace NaN with safe values for JSON serialization
        df = df.replace({np.nan: None})
        
        if "conversation_id" not in df.columns:
            # Fallback for old data: match by index if conv_id looks like index
            if conv_id.startswith("conv-"):
                try:
                    idx = int(conv_id.split("-")[1])
                    df = df.iloc[[idx]]
                except:
                    return {"success": False, "error": "Conversation not found", "messages": []}
            else:
                return {"success": False, "error": "Conversation_id column missing", "messages": []}
        else:
            df = df[df["conversation_id"] == conv_id]
        
        if df.empty:
            return {"success": False, "error": "Conversation not found", "messages": []}
        
        # Sort by timestamp to get chronology right
        df = df.sort_values("timestamp")
        
        messages = []
        for _, row in df.iterrows():
            # Add user message
            messages.append({
                "id": f"msg-user-{row.name}",
                "role": "user",
                "content": row.get("user_query", ""),
                "timestamp": row.get("timestamp", ""),
            })
            # Add AI response
            messages.append({
                "id": f"msg-ai-{row.name}",
                "role": "assistant",
                "content": row.get("ai_response", ""),
                "timestamp": row.get("timestamp", ""),
                "ethicalScore": row.get("overall_ethical_score", 0),
                "dimensions": json.loads(row.get("dimensions_json", "{}")) if row.get("dimensions_json") else {}
            })
        
        # Return structured metadata from the LAST message
        last_row = df.iloc[-1]
        return {
            "success": True,
            "id": conv_id,
            "messages": messages,
            "overall_ethical_score": last_row.get("overall_ethical_score", 0),
            "bot_model": last_row.get("bot_model", "llama3"),
            "final_label": last_row.get("final_label", ""),
            "risk_band": last_row.get("risk_band", ""),
        }
    except Exception as e:
        return {"success": False, "error": str(e), "messages": []}

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

# ================== NEW CSV DATA ENDPOINTS ==================

@app.get("/gold-eval")
async def get_gold_eval(limit: int = 100):
    """Return gold_rti_eval.csv data."""
    try:
        if not os.path.exists(GOLD_EVAL_CSV):
            return {"success": False, "error": "gold_rti_eval.csv not found", "data": []}
        df = pd.read_csv(GOLD_EVAL_CSV, on_bad_lines='skip', engine='python')
        df = df.tail(limit).replace({np.nan: None})
        return {"success": True, "data": df.to_dict(orient="records"), "count": len(df)}
    except Exception as e:
        return {"success": False, "error": str(e), "data": []}

@app.get("/adversarial")
async def get_adversarial(limit: int = 60):
    """Return adversarial_tests.csv data."""
    try:
        if not os.path.exists(ADVERSARIAL_CSV):
            return {"success": False, "error": "adversarial_tests.csv not found", "data": []}
        df = pd.read_csv(ADVERSARIAL_CSV, on_bad_lines='skip', engine='python')
        df = df.tail(limit).replace({np.nan: None})
        return {"success": True, "data": df.to_dict(orient="records"), "count": len(df)}
    except Exception as e:
        return {"success": False, "error": str(e), "data": []}

@app.post("/reindex")
async def manual_reindex():
    """Manually trigger a complete re-indexing of all documents."""
    try:
        # Stop existing client connections if possible or just delete the collection
        try:
            chroma_client.delete_collection(COLLECTION_NAME)
        except:
            pass
        
        # Re-initialize collection
        new_coll = chroma_client.create_collection(name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"})
        
        # Re-run the indexing logic
        build_rag_index()
        
        return {"success": True, "message": f"Successfully re-indexed into {COLLECTION_NAME}", "count": new_coll.count()}
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
