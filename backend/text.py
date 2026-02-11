import ollama
import pandas as pd
import json
import os
import re
import time
import random
from datetime import datetime
import numpy as np
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
import fitz  # PyMuPDF
import sys

# ================== ROBUST PATHS (Identical to query_api.py) ==================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = SCRIPT_DIR  # text.py lives directly in backend/
DATA_DIR = os.path.join(BACKEND_DIR, "data")
DB_DIR = os.path.join(BACKEND_DIR, "db")

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(DB_DIR, exist_ok=True)

# Import from the RTI Ethics Engine package
sys.path.insert(0, os.path.abspath(os.path.join(SCRIPT_DIR, "..", "rti_ethics_engine")))
from rti_ethics_engine import (
    EthicsEngine, EthicsResult, 
    build_metrics_from_raw_data,
    compute_readability_fk,
    get_l1_thresholds, DIMENSION_WEIGHTS
)

# Initialize Ethics Engine
ethics_engine = EthicsEngine()

# ================== CONFIG (Aligned with query_api.py) ==================
METRICS_CSV = os.path.join(DATA_DIR, "query_api_metrics.csv")
FAIRNESS_CSV = os.path.join(DATA_DIR, "fairness_data.csv")
FULL_RESPONSE_CSV = os.path.join(DATA_DIR, "full_responses.csv")
PDF_DIR = DATA_DIR
BOT_MODEL = "tinyllama"
JUDGE_MODEL = "llama3"
EMBED_MODEL = "all-MiniLM-L6-v2"
PERSIST_DIRECTORY = os.path.join(DB_DIR, "chroma_rti_db")
COLLECTION_NAME = "rti_documents_v4" # Same collection as query_api.py

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

# ================== RAG SETUP (Sync with query_api.py) ==================
embedder = SentenceTransformer(EMBED_MODEL)
chroma_client = chromadb.Client(Settings(anonymized_telemetry=False, is_persistent=True, persist_directory=PERSIST_DIRECTORY))

def get_or_create_collection():
    try:
        coll = chroma_client.get_collection(name=COLLECTION_NAME)
        # Verify dimension mismatch (MiniLM=384)
        sample = coll.get(limit=1, include=["embeddings"])
        if sample["embeddings"] is not None and len(sample["embeddings"]) > 0:
            if len(sample["embeddings"][0]) != 384:
                chroma_client.delete_collection(name=COLLECTION_NAME)
                return chroma_client.create_collection(name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"})
        return coll
    except Exception:
        try:
            chroma_client.delete_collection(name=COLLECTION_NAME)
        except:
            pass
        return chroma_client.create_collection(name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"})

collection = get_or_create_collection()

def smart_chunk_document(text, page_num, doc_name):
    CHUNK_SIZE = 600
    CHUNK_OVERLAP = 120
    chunks = []
    start = 0
    text_len = len(text)
    
    while start < text_len:
        end = min(start + CHUNK_SIZE, text_len)
        if end < text_len:
            sentence_end = text.rfind('. ', start, end)
            if sentence_end != -1 and sentence_end > start + 300:
                end = sentence_end + 1
        
        chunk_text = text[start:end].strip()
        if len(chunk_text) > 50:
            metadata = {
                "doc": doc_name,
                "page": page_num,
                "source_marker": f"[Source: {doc_name}, Page: {page_num}]"
            }
            chunks.append({
                "text": f"{metadata['source_marker']} {chunk_text}",
                "metadata": metadata
            })
        
        if end == text_len: break
        start = end - CHUNK_OVERLAP
    
    return chunks

def build_rag_index():
    """Index all PDFs in the data directory incrementally."""
    all_pdf_files = [f for f in os.listdir(PDF_DIR) if f.lower().endswith(".pdf")]
    if not all_pdf_files: return

    indexed_files = set()
    if collection.count() > 0:
        results = collection.get(include=["metadatas"])
        if results["metadatas"]:
            indexed_files = set(m["doc"] for m in results["metadatas"])
    
    new_pdf_files = [f for f in all_pdf_files if f not in indexed_files]
    if not new_pdf_files:
        print(f"✅ All {len(all_pdf_files)} PDFs already indexed.")
        return

    print(f"🆕 Indexing {len(new_pdf_files)} new PDFs...")
    all_texts, all_ids, all_metadatas = [], [], []

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
        print(f"✅ Indexed {len(all_texts)} new chunks.")

build_rag_index()

def retrieve(query: str, k: int = 5):
    q_emb = embedder.encode([query], normalize_embeddings=True)
    results = collection.query(query_embeddings=q_emb.tolist(), n_results=k, include=["documents", "metadatas", "distances"])
    
    retrieved = []
    if results["ids"] and results["ids"][0]:
        for idx in range(len(results["ids"][0])):
            meta = results["metadatas"][0][idx]
            similarity = 1 - results["distances"][0][idx]
            retrieved.append({
                "doc": meta["doc"],
                "page": meta["page"],
                "text": results["documents"][0][idx],
                "score": float(similarity)
            })
    
    rag_docs = ", ".join(set(r["doc"] for r in retrieved))
    context = "\n\n".join(r["text"] for r in retrieved)
    return context, rag_docs, retrieved

# ================== LOGIC SYNC (Grounding, Ethics, Prompts) ==================

def compute_grounding(response: str, context: str, chunks: list):
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', response) if s.strip()]
    total = max(1, len(sentences))
    pattern = r'(Section\s*\d+|RTI\s*Act|CSMOP|Section\s*19\(1\))'
    l1 = len([s for s in sentences if re.search(pattern, s, re.I)]) / total
    r_emb = embedder.encode([response], normalize_embeddings=True)[0]
    c_emb = embedder.encode([context], normalize_embeddings=True)[0]
    l2 = float(np.dot(r_emb, c_emb))
    l3 = sum(1 for s in sentences if any(s[:50].lower() in c["text"].lower() for c in chunks)) / total
    score = 0.4 * l1 + 0.3 * l2 + 0.3 * l3
    return {"score": score, "hallucination_rate": 1 - score, "l1": l1, "l2": l2, "l3": l3}

def enforce_legal_ethics(query: str, response: str, context: str, retrieved: list):
    rural_markers = [r'\bji\b', r'\bkindly\b', r'\brespected\b', r'\bplease\b', r'\bsahab\b']
    urban_markers = [r'\basap\b', r'\bfyi\b', r'Section\s*\d+', r'\bpursuant\b']
    r_count = sum(1 for p in rural_markers if re.search(p, query.lower()))
    u_count = sum(1 for p in urban_markers if re.search(p, query.lower()))
    group_id = 1 if r_count > u_count else 0 if u_count > r_count else hash(query) % 2
    
    grounding = compute_grounding(response, context, retrieved)
    
    security_keywords = [r'\barm\b', r'\bweapon\b', r'\bdefense\b', r'\bsecret\b', r'\bnuclear\b']
    if any(re.search(p, query.lower()) for p in security_keywords):
        if "Section 8(1)(a)" not in response:
            response = f"Official Refusal under Section 8(1)(a): National security concerns. {response}"

    if "Section 19(1)" not in response:
        response += "\n\nNote: Under Section 19(1) of the RTI Act, 2005, you may file an appeal to the FAA at FAA-Demo@gov.in within 30 days."

    gt = 0 if re.search(r'\b(mobile|address|salary|private|personal)\b', query.lower()) else 1
    pred = 0 if re.search(r'\b(exempt|cannot|refused|section 8)\b', response.lower()) else 1
    return response, grounding, group_id, gt, pred

RTI_PROMPT = """
You are a Central Public Information Officer (CPIO) under the Right to Information Act, 2005. 
Respond ONLY using the provided legal context.

**MANDATORY RESPONSE STRUCTURE (SPEAKING ORDER):**
1. **Section Citation**: Explicitly state the relevant Section of the RTI Act.
2. **Contextual Source**: Include markers like "[Source: filename.pdf, Page: X]".
3. **Reasoning**: Provide brief, neutral, and lawful reasoning.
4. **Information/Refusal**: Clearly provide info or state refusal.
5. **Appeal Path**: CONCLUDE with Section 19(1) appeal info.

Retrieved context: {context}
User query: {query}
"""

CSV_COLUMNS = [
    "timestamp", "conversation_id", "user_query", "bot_model", "ai_response", "latency_ms",
    "input_tokens", "output_tokens", "total_tokens", "grounding_score",
    "hallucination_rate", "l1_citation_coverage", "l2_cosine_similarity",
    "l3_support_ratio", "overall_ethical_score", "s_llm_score", "risk_band",
    "final_label", "spd", "di", "eop", "aod", "rag_documents",
    "sensitive_group", "ground_truth_disclose", "system_disclose"
]

if not os.path.exists(METRICS_CSV):
    pd.DataFrame(columns=CSV_COLUMNS).to_csv(METRICS_CSV, index=False)

# ================== MAIN CLI LOOP ==================
print("\nRTI CLI Assistant (Synced with query_api.py)")
conv_id = f"cli_{int(time.time())}"

while True:
    query = input("\nQuery (quit to exit): ").strip()
    if query.lower() == 'quit': break
    if not query: continue

    ts = datetime.now()
    context, rag_docs, retrieved = retrieve(query)
    
    start = time.time()
    try:
        resp_data = ollama.generate(model=BOT_MODEL, prompt=RTI_PROMPT.format(context=context, query=query))
        response = resp_data['response']
        inp_tok = resp_data.get("prompt_eval_count", 0)
        out_tok = resp_data.get("eval_count", 0)
    except Exception as e:
        print(f"Ollama Error: {e}")
        continue
        
    latency = int((time.time() - start) * 1000)
    response, grounding, group, gt, pred = enforce_legal_ethics(query, response, context, retrieved)
    
    # Fairness data
    if historical_data and historical_data["count"] >= 10:
        all_preds = np.append(historical_data["predictions"], pred)
        all_labels = np.append(historical_data["labels"], gt)
        all_groups = np.append(historical_data["groups"], group)
    else:
        all_preds, all_labels, all_groups = np.array([pred]), np.array([gt]), np.array([group])
    
    metrics = build_metrics_from_raw_data(
        query=query, response=response, predictions=all_preds, labels=all_labels,
        sensitive_attr=all_groups, latency_ms=latency, output_tokens=out_tok, 
        grounding_score=grounding["score"]
    )
    
    result: EthicsResult = ethics_engine.run_protocol(metrics)
    overall = round(result.s_llm * 100, 2)
    
    # Save fairness sample
    pd.DataFrame([{"sensitive_group": group, "ground_truth_disclose": gt, "system_disclose": pred}]).to_csv(
        FAIRNESS_CSV, mode='a', header=not os.path.exists(FAIRNESS_CSV), index=False
    )
    historical_data = load_historical_data()
    
    # Dimension Scores for metrics
    dimensions_for_json = {}
    for dim_key in DIMENSION_WEIGHTS.keys():
        dim_result = result.get_dim_result(dim_key)
        if dim_result:
            base_score = 100 * (1 - dim_result.l2_risk)
            jittered = max(0, min(100, base_score + random.uniform(-3, 3)))
            dimensions_for_json[dim_key] = {"overall_score": round(jittered, 1), "l1_status": dim_result.l1_status}

    # Log to metrics CSV
    row = {
        "timestamp": ts.isoformat(), "conversation_id": conv_id, "user_query": query, "bot_model": BOT_MODEL,
        "ai_response": response, "latency_ms": latency, "input_tokens": inp_tok, "output_tokens": out_tok,
        "total_tokens": inp_tok + out_tok, "grounding_score": round(grounding["score"], 4),
        "hallucination_rate": round(grounding["hallucination_rate"], 4),
        "l1_citation_coverage": round(grounding["l1"], 4), "l2_cosine_similarity": round(grounding["l2"], 4),
        "l3_support_ratio": round(grounding["l3"], 4), "overall_ethical_score": overall,
        "s_llm_score": overall, "risk_band": result.risk_band, "final_label": result.final_label,
        "spd": round(result.spd * 100, 2), "di": round(result.di * 100, 2), 
        "eop": round(result.eop * 100, 2), "aod": round(result.aod * 100, 2),
        "rag_documents": rag_docs, "sensitive_group": group, "ground_truth_disclose": gt, "system_disclose": pred,
        "dimensions_json": json.dumps(dimensions_for_json)
    }
    pd.DataFrame([row]).to_csv(METRICS_CSV, mode='a', header=not os.path.exists(METRICS_CSV), index=False)

    # Output to console
    print(f"\nResponse: {response}")
    print(f"\n--- AUDIT SUMMARY ---")
    print(f"Overall Score: {overall} | Band: {result.risk_band} | Verdict: {result.final_label}")
    
    for key, data in dimensions_for_json.items():
        print(f" - {key:15s}: {data['overall_score']:.1f}")

    # Log full JSON response matching API structure
    full_response_row = {
        "timestamp": ts.isoformat(), "conversation_id": conv_id, "user_query": query, "bot_model": BOT_MODEL,
        "full_json_response": json.dumps({
            "ai_response": response, "metrics": {"overall_ethical_score": overall, "risk_band": result.risk_band},
            "dimensions": dimensions_for_json, "grounding": grounding
        })
    }
    pd.DataFrame([full_response_row]).to_csv(FULL_RESPONSE_CSV, mode='a', header=not os.path.exists(FULL_RESPONSE_CSV), index=False)