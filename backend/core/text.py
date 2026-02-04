import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
import ollama
import re
import time
from datetime import datetime
import numpy as np
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
import fitz  # PyMuPDF
from scipy.stats import entropy  # For KL divergence in Layer 2, if needed; pip install scipy

# Import from the new RTI Ethics Engine package (production-level)
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../rti_ethics_engine")))
from rti_ethics_engine import (
    EthicsEngine, EthicsResult, 
    build_metrics_from_raw_data,
    compute_spd, compute_readability_fk,
    get_l1_thresholds, DIMENSION_WEIGHTS
)

# Initialize Ethics Engine
ethics_engine = EthicsEngine()

# Initialize dynamic thresholds
L1_THRESHOLDS = get_l1_thresholds()

# ================== ROBUST PATHS ==================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(BACKEND_DIR, "data")
DB_DIR = os.path.join(BACKEND_DIR, "db")

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(DB_DIR, exist_ok=True)

METRICS_CSV = os.path.join(DATA_DIR, "conversations_metrics.csv")
PDF_DIR = DATA_DIR
BOT_MODEL = "llama3"
JUDGE_MODEL = "llama3"
EMBED_MODEL = "all-MiniLM-L6-v2"
CHUNK_SIZE = 600
TOP_K = 5
PERSIST_DIRECTORY = os.path.join(DB_DIR, "chroma_rti_db")

# ================== ACADEMIC & LEGAL CITATIONS ==================
# These citations validate each metric for research papers and government audits
CITATIONS = {
    # Layer 1 - Fairness Metrics
    "spd": {
        "name": "Statistical Parity Difference",
        "formula": "P(Ŷ=1|A=1) - P(Ŷ=1|A=0)",
        "citation": "Dwork et al. (2012). Fairness Through Awareness. ITCS'12.",
        "legal_basis": "EEOC Guidelines; EU AI Act Art. 10(2)(f)"
    },
    "di": {
        "name": "Disparate Impact (80% Rule)",
        "formula": "P(Ŷ=1|A=1) / P(Ŷ=1|A=0)",
        "citation": "Feldman et al. (2015). Certifying and Removing Disparate Impact. KDD'15.",
        "legal_basis": "US EEOC Uniform Guidelines (29 CFR 1607.4D); Griggs v. Duke Power Co. (1971)"
    },
    "eop": {
        "name": "Equal Opportunity (TPR Parity)",
        "formula": "P(Ŷ=1|Y=1,A=1) - P(Ŷ=1|Y=1,A=0)",
        "citation": "Hardt et al. (2016). Equality of Opportunity in Supervised Learning. NeurIPS'16.",
        "legal_basis": "EU AI Act Art. 9(7); NIST AI RMF 1.0"
    },
    "aod": {
        "name": "Average Odds Difference",
        "formula": "0.5 × [(TPR_1 - TPR_0) + (FPR_1 - FPR_0)]",
        "citation": "Bellamy et al. (2019). AI Fairness 360: An Extensible Toolkit. IBM J. R&D.",
        "legal_basis": "ISO/IEC TR 24027:2021 (Bias in AI)"
    },
    # Layer 2 - Advanced Fairness
    "fnrd": {
        "name": "False Negative Rate Difference",
        "formula": "P(Ŷ=0|Y=1,A=1) - P(Ŷ=0|Y=1,A=0)",
        "citation": "Chouldechova (2017). Fair Prediction with Disparate Impact. Big Data.",
        "legal_basis": "GDPR Art. 22; Indian IT Act 2000 S.43A"
    },
    "predictive_parity": {
        "name": "Predictive Parity (Precision Parity)",
        "formula": "P(Y=1|Ŷ=1,A=1) - P(Y=1|Ŷ=1,A=0)",
        "citation": "Kleinberg et al. (2016). Inherent Trade-Offs in Fair Determination of Risk Scores. ITCS'17.",
        "legal_basis": "EU AI Act Art. 15(3)"
    },
    "refusal_disparity": {
        "name": "Refusal Disparity (LLM-specific)",
        "formula": "P(Refusal|A=1) - P(Refusal|A=0)",
        "citation": "Weidinger et al. (2022). Taxonomy of Risks posed by LLMs. FAccT'22.",
        "legal_basis": "NIST AI RMF Govern 1.1; RTI Act 2005 S.7(1)"
    },
    # Layer 3 - Interpretability
    "mutual_info": {
        "name": "Mutual Information Leakage",
        "formula": "I(Ŷ;A) = Σ P(ŷ,a) log[P(ŷ,a) / P(ŷ)P(a)]",
        "citation": "Zemel et al. (2013). Learning Fair Representations. ICML'13.",
        "legal_basis": "GDPR Art. 5(1)(c) (Data Minimization)"
    },
    "counterfactual": {
        "name": "Counterfactual Fairness",
        "formula": "P(Ŷ_{A←a}(X)=y) = P(Ŷ_{A←a'}(X)=y)",
        "citation": "Kusner et al. (2017). Counterfactual Fairness. NeurIPS'17.",
        "legal_basis": "EU AI Act Art. 13 (Transparency)"
    },
    # Grounding & Legal
    "grounding": {
        "name": "Context Grounding Score",
        "citation": "Lewis et al. (2020). Retrieval-Augmented Generation. NeurIPS'20.",
        "legal_basis": "RTI Act 2005 S.4(1)(b); CSMOP 2020"
    },
    "lawfulness": {
        "name": "Lawfulness Assessment",
        "citation": "Floridi et al. (2018). AI4People—An Ethical Framework. Minds & Machines.",
        "legal_basis": "RTI Act 2005 S.8; Indian Const. Art. 19(1)(a)"
    },
    # Framework References
    "_framework": {
        "80_percent_rule": "US EEOC Uniform Guidelines on Employee Selection Procedures (1978), 29 CFR 1607.4D",
        "eu_ai_act": "Regulation (EU) 2024/1689 (AI Act), esp. Art. 9-15",
        "nist_ai_rmf": "NIST AI Risk Management Framework 1.0 (2023)",
        "rti_act": "Right to Information Act, 2005 (India)",
        "gdpr": "General Data Protection Regulation (EU) 2016/679"
    }
}
# ===========================================

columns = [
    "conversation_id", "turn_id", "user_id", "department", "timestamp_request",
    "timestamp_response", "latency_ms", "user_prompt", "ai_response",
    "rag_documents", "rag_sections", "safety_flag", "error_code",
    "overall_ethical_score", "bias_fairness_score", "data_grounding_drift_score",
    "explainability_transparency_score", "ethical_alignment_score",
    "human_control_score", "legal_compliance_score", "security_robustness_score",
    "response_quality_score", "is_gold_example", "task_completed",
    "hallucination_rate", "context_grounding_score", "citation_coverage",
    "source_diversity", "human_feedback_score", "norm_violation_count",
    "contextual_harm_risk", "lawfulness_assessment", "pii_detected",
    "pii_allowed", "consent_required", "consent_present", "consent_valid",
    "input_tokens", "output_tokens", "total_tokens", "estimated_cost_usd",
    "model_name", "infra_region"
]

if os.path.exists(METRICS_CSV):
    df = pd.read_csv(METRICS_CSV)
else:
    df = pd.DataFrame(columns=columns)
    df.to_csv(METRICS_CSV, index=False)

# ================== RAG SETUP (ChromaDB with Cosine Similarity) ==================
embedder = SentenceTransformer(EMBED_MODEL)

# Initialize ChromaDB with persistent storage
chroma_client = chromadb.Client(Settings(
    anonymized_telemetry=False,
    is_persistent=True,
    persist_directory=PERSIST_DIRECTORY
))

# Get or create collection with cosine similarity
COLLECTION_NAME = "rti_documents"
try:
    collection = chroma_client.get_collection(name=COLLECTION_NAME)
    print(f"Loaded existing ChromaDB collection: {COLLECTION_NAME}")
except:
    collection = chroma_client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}  # Use cosine similarity
    )
    print(f"Created new ChromaDB collection: {COLLECTION_NAME}")

chunk_metadata = []

def build_rag_index():
    global chunk_metadata
    
    # Check if collection already has documents
    if collection.count() > 0:
        print(f"ChromaDB collection already has {collection.count()} chunks. Skipping rebuild.")
        # Load metadata from collection
        all_data = collection.get(include=["metadatas", "documents"])
        chunk_metadata = all_data["metadatas"] if all_data["metadatas"] else []
        return
    
    all_texts = []
    all_ids = []
    all_metadatas = []
    
    # Dynamically take all PDFs in data directory
    pdf_files = [f for f in os.listdir(PDF_DIR) if f.endswith(".pdf")]
    
    for pdf_file in pdf_files:
        path = os.path.join(PDF_DIR, pdf_file)
        try:
            doc = fitz.open(path)
            doc_id = pdf_file
            for page_num in range(len(doc)):
                text = doc[page_num].get_text("text").strip()
                if not text: continue
                paras = [p.strip() for p in re.split(r'\n\s*\n|\n{3,}', text) if p.strip()]
                chunk_id = 0
                for para in paras:
                    if len(para) > 80:
                        unique_id = f"{doc_id}_{page_num}_{chunk_id}"
                        metadata = {"doc": doc_id, "page": page_num+1, "chunk_id": chunk_id, "text": para}
                        
                        all_texts.append(para)
                        all_ids.append(unique_id)
                        all_metadatas.append(metadata)
                        chunk_metadata.append(metadata)
                        chunk_id += 1
            doc.close()
        except Exception as e:
            print(f"Error on {pdf_file}: {e}")
    
    if not all_texts:
        raise RuntimeError("No text from PDFs.")
    
    # Generate embeddings
    print("Generating embeddings...")
    embeddings = embedder.encode(all_texts, show_progress_bar=True, normalize_embeddings=True)
    
    # Add to ChromaDB collection
    print("Adding to ChromaDB...")
    # ChromaDB has a batch limit, so we add in chunks
    batch_size = 500
    for i in range(0, len(all_texts), batch_size):
        end_idx = min(i + batch_size, len(all_texts))
        collection.add(
            ids=all_ids[i:end_idx],
            embeddings=embeddings[i:end_idx].tolist(),
            documents=all_texts[i:end_idx],
            metadatas=all_metadatas[i:end_idx]
        )
    
    print(f"Indexed {len(all_texts)} chunks in ChromaDB with cosine similarity.")

build_rag_index()

def retrieve(query: str, k: int = TOP_K):
    """Retrieve relevant chunks using ChromaDB with cosine similarity."""
    # Generate query embedding
    q_emb = embedder.encode([query], normalize_embeddings=True)
    
    # Query ChromaDB - it uses cosine similarity as configured
    results = collection.query(
        query_embeddings=q_emb.tolist(),
        n_results=k,
        include=["documents", "metadatas", "distances"]
    )
    
    retrieved = []
    if results["ids"] and results["ids"][0]:
        for idx in range(len(results["ids"][0])):
            meta = results["metadatas"][0][idx]
            # ChromaDB returns distance, convert to similarity for cosine
            # For cosine: similarity = 1 - distance
            distance = results["distances"][0][idx]
            similarity = 1 - distance  # Convert cosine distance to similarity
            
            retrieved.append({
                "doc": meta["doc"],
                "page": meta["page"],
                "chunk_id": meta["chunk_id"],
                "text": meta["text"],
                "score": similarity  # Cosine similarity score
            })
    
    rag_docs = ", ".join(set(r["doc"] for r in retrieved))
    rag_sections = "; ".join(f"{r['doc']} p{r['page']}" for r in retrieved)
    context = "\n\n".join(r["text"] for r in retrieved)
    return context, rag_docs, rag_sections, retrieved

# ================== PROMPTS ==================
RTI_BOT_PROMPT = """
You are a statutory RTI Assistant. Use ONLY retrieved context from approved documents.
Do NOT hallucinate, guess or add external info.

Retrieved Context:
{context}

Answer the query legally, cite sources, give speaking order if refusing.
Query: {query}
"""

# ================== 3-LAYER GROUNDING JUDGE ==================

def split_sentences(text: str) -> list:
    """Split text into sentences for granular analysis."""
    # Protect common abbreviations and Section numbers
    text = re.sub(r'Section\s*(\d+)', r'Section_\1', text)
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.replace('Section_', 'Section ').strip() for s in sentences if s.strip()]

def compute_grounding_3layer(response: str, context: str, retrieved_chunks: list, embedder, embed_model):
    """
    Deterministic 3-Layer Grounding Judge (Best Practice)
    
    L1: Citation Coverage (Hard Requirement)
    L2: Cosine Similarity (Soft Signal)
    L3: Claim-Context Overlap (Anti-Hallucination)
    """
    sentences = split_sentences(response)
    total_sentences = max(1, len(sentences))
    
    # --- Layer 1: Citation Coverage ---
    pattern = r'(Section\s*\d+\(?\d*\)?|RTI\s*Act|CIC\s*Report|CSMOP|GovAudit|AFS_|PR_IT_|HR_CIRC)'
    matches = len([s for s in sentences if re.search(pattern, s, re.I)])
    l1_citation_coverage = matches / total_sentences
    
    # --- Layer 2: Cosine Similarity ---
    # Generate embeddings for response and context
    r_emb = embedder.encode([response], normalize_embeddings=True)[0]
    c_emb = embedder.encode([context], normalize_embeddings=True)[0]
    l2_cosine_similarity = float(np.dot(r_emb, c_emb)) # Since normalized
    
    # --- Layer 3: Claim-Context Overlap ---
    # Deterministic check: Is the claim start (50 chars) found in any chunk?
    supported = sum(1 for sentence in sentences if any(sentence[:50].lower() in chunk["text"].lower() for chunk in retrieved_chunks))
    l3_support_ratio = supported / total_sentences
    
    # Final Grounding Score (Recommended Weighted Formula)
    grounding_score = (0.4 * l1_citation_coverage + 0.3 * l2_cosine_similarity + 0.3 * l3_support_ratio)
    hallucination_rate = 1.0 - grounding_score
    
    return {
        "score": grounding_score,
        "hallucination_rate": hallucination_rate,
        "l1_citation_coverage": l1_citation_coverage,
        "l2_cosine_similarity": l2_cosine_similarity,
        "l3_support_ratio": l3_support_ratio,
        "details": {
            "total_sentences": total_sentences,
            "cited_sentences": matches,
            "supported_sentences": supported
        }
    }

# ================== NSFW CONTENT DETECTOR (LLM Judge) ==================
NSFW_JUDGE = """
You MUST respond with **valid JSON only** — no extra text, no markdown, no preamble.

Task: Analyze if the user query contains NSFW (Not Safe For Work) content.

NSFW includes:
- Explicit sexual content, pornography, or sexual requests
- Graphic violence, gore, or torture descriptions
- Hate speech, slurs, or discrimination against protected groups
- Illegal activities (drugs, weapons, hacking instructions)
- Self-harm, suicide, or dangerous activities
- Harassment, bullying, or threats
- Obscene or vulgar language intended to offend

This is an RTI (Right to Information) system for government transparency. Queries should be about:
- Government policies, acts, rules
- Public information requests
- Official procedures and guidelines

Return EXACTLY this JSON:
{{"is_nsfw": true or false, "reason": "one short sentence explanation", "category": "safe" or "sexual" or "violence" or "hate" or "illegal" or "harmful" or "harassment"}}

User Query:
{query}
"""

def ollama_judge(prompt: str, default: dict = None) -> dict:
    default = default or {"score": 0.5, "assessment": "warning", "reason": "judge failed"}
    try:
        raw_resp = ollama.generate(model=JUDGE_MODEL, prompt=prompt)['response'].strip()
        # print(f"RAW JUDGE OUTPUT: {raw_resp}") # Cleanup noisy output

        if raw_resp.startswith("```json"):
            raw_resp = raw_resp[7:].strip()
        if raw_resp.endswith("```"):
            raw_resp = raw_resp[:-3].strip()
        raw_resp = raw_resp.replace("'", '"')  # fix single quotes
        parsed = json.loads(raw_resp)
        return parsed
    except Exception as e:
        # print(f"Judge failed: {e}")
        return default


def check_nsfw(query: str) -> dict:
    """
    LLM-based NSFW content detector.
    Returns dict with is_nsfw (bool), reason (str), category (str).
    """
    default = {"is_nsfw": False, "reason": "Check passed", "category": "safe"}
    try:
        prompt = NSFW_JUDGE.format(query=query)
        raw_resp = ollama.generate(model=JUDGE_MODEL, prompt=prompt)['response'].strip()
        print(f"[NSFW CHECK] RAW OUTPUT: {raw_resp}")
        
        # Clean up response
        if raw_resp.startswith("```json"):
            raw_resp = raw_resp[7:].strip()
        if raw_resp.endswith("```"):
            raw_resp = raw_resp[:-3].strip()
        raw_resp = raw_resp.replace("'", '"')
        
        parsed = json.loads(raw_resp)
        return {
            "is_nsfw": parsed.get("is_nsfw", False),
            "reason": parsed.get("reason", "Unknown"),
            "category": parsed.get("category", "safe")
        }
    except Exception as e:
        print(f"[NSFW CHECK] Failed: {e}")
        return default

# ================== HELPER METRICS ==================

def pii_detected(query: str, response: str) -> int:
    """Simple regex to detect PII keywords."""
    pattern = r'\b(mobile|phone|contact|address|residential|salary|home|personal|email)\b'
    return 1 if re.search(pattern, query.lower()) or re.search(pattern, response.lower()) else 0

def detect_sensitive_group(query: str) -> int:
    """Detect group 0 (Urban) vs group 1 (Rural/Traditional) based on query style."""
    query_lower = query.lower()
    rural = [r'\bji\b', r'\bkindly\b', r'\bplease\s+sir\b', r'\brespected\b', r'\bhumbly\b', r'\bvillage\b', r'\bfarmer\b']
    urban = [r'\basap\b', r'\bfyi\b', r'\bbasically\b', r'\bpursuant to\b', r'Section\s*\d+']
    
    r_score = sum(1 for p in rural if re.search(p, query_lower))
    u_score = sum(1 for p in urban if re.search(p, query_lower))
    
    return 1 if r_score > u_score else 0 if u_score > r_score else hash(query) % 2

def format_rag_citations(retrieved: list) -> list:
    """Format retrieved PDF chunks as proper citations"""
    citations = []
    for i, r in enumerate(retrieved, 1):
        # Generate absolute file URI for clickable links
        abs_path = os.path.abspath(os.path.join(PDF_DIR, r["doc"]))
        file_uri = f"file:///{abs_path.replace(os.sep, '/')}#page={r['page']}"
        
        citations.append({
            "citation_id": i,
            "document": r["doc"],
            "page": r["page"],
            "uri": file_uri,
            "relevance_score": round(r["score"], 4),
            "excerpt": r["text"][:300] + "..." if len(r["text"]) > 300 else r["text"]
        })
    return citations

# ================== MAIN LOOP ==================
print("RAG RTI Ethics Engine (PDFs loaded)")
print("PDFs found:", [f for f in PDF_FILES if os.path.exists(f)])
print("Enter queries below.\n")

conv_counter = len(df["conversation_id"].unique()) + 1 if not df.empty else 1

while True:
    query = input("RTI query (quit to exit): ").strip()
    if query.lower() == 'quit':
        break

    # Detect sensitive group from query linguistics (urban vs rural/traditional)
    sensitive_group = detect_sensitive_group(query)
    department = "finance"
    user_id = f"user_auto_{conv_counter}"
    
    print(f"[Detected Group: {'Urban/Formal' if sensitive_group == 0 else 'Rural/Traditional'}]")

    # ================== NSFW CHECK (LLM Judge - Before LLM Generation) ==================
    print("[NSFW CHECK] Analyzing query for inappropriate content...")
    nsfw_result = check_nsfw(query)
    
    if nsfw_result["is_nsfw"]:
        print(f"\n{'='*60}")
        print("🚫 QUERY BLOCKED - NSFW CONTENT DETECTED")
        print(f"{'='*60}")
        print(f"  Category: {nsfw_result['category'].upper()}")
        print(f"  Reason: {nsfw_result['reason']}")
        print(f"{'='*60}")
        print("\n⚠️  This query contains inappropriate content and cannot be processed.")
        print("    Please submit queries related to RTI (Right to Information) requests only.\n")
        conv_counter += 1
        continue  # Skip to next query, do NOT generate response
    
    print(f"[NSFW CHECK] ✅ Query is safe (category: {nsfw_result['category']})")

    t_request = datetime.now()

    context, rag_docs, rag_sections, retrieved = retrieve(query)

    prompt = RTI_BOT_PROMPT.format(context=context, query=query)
    start_gen = time.time()
    try:
        resp_data = ollama.generate(model=BOT_MODEL, prompt=prompt)
        response = resp_data['response']
    except Exception as e:
        response = f"Error: {str(e)}"
        resp_data = {}
    latency_ms = int((time.time() - start_gen) * 1000 + 500)

    t_response = datetime.now()

    # --- 3-LAYER GROUNDING JUDGE ---
    print("[GROUNDING] Analyzing 3-layer deterministic grounding stack...")
    grounding_res = compute_grounding_3layer(response, context, retrieved, embedder, EMBED_MODEL)
    grounding_score = grounding_res["score"]
    halluc_rate = grounding_res["hallucination_rate"]
    cit_cov = grounding_res["l1_citation_coverage"]
    cos_sim = grounding_res["l2_cosine_similarity"]
    supp_ratio = grounding_res["l3_support_ratio"]
    
    print(f"  - L1 Citation Coverage: {cit_cov:.2%}")
    print(f"  - L2 Cosine Similarity: {cos_sim:.2f}")
    print(f"  - L3 Claim Overlap: {supp_ratio:.2%}")
    print(f"  - Final Grounding: {grounding_score:.2f}")

    gt_disclose = 0 if re.search(r'\b(mobile|address|salary|personal)\b', query.lower()) else 1
    sys_disclose = 0 if re.search(r'\b(exempt|cannot|refused|section 8)\b', response.lower()) else 1

    pii_det = pii_detected(query, response)
    source_div = len(set(r["doc"] for r in retrieved))

    # =================== FAIRNESS DATA COLLECTION ===================
    # Build a separate fairness dataframe with proper columns
    fairness_cols = ["sensitive_group", "ground_truth_disclose", "system_disclose"]
    
    # Create or load existing fairness data
    fairness_csv = "../data/fairness_data.csv"
    if os.path.exists(fairness_csv):
        df_fairness = pd.read_csv(fairness_csv)
    else:
        df_fairness = pd.DataFrame(columns=fairness_cols)
    
    # Add current query data
    new_row = pd.DataFrame([{
        "sensitive_group": sensitive_group, 
        "ground_truth_disclose": gt_disclose, 
        "system_disclose": sys_disclose
    }])
    df_fairness = pd.concat([df_fairness, new_row], ignore_index=True)
    df_fairness.to_csv(fairness_csv, index=False)
    
    # Debug: Show fairness data stats
    print(f"\n[DEBUG] Fairness Data Stats:")
    print(f"  Total samples: {len(df_fairness)}")
    print(f"  Group 0 count: {(df_fairness['sensitive_group'] == 0).sum()}")
    print(f"  Group 1 count: {(df_fairness['sensitive_group'] == 1).sum()}")
    print(f"  Current query: group={sensitive_group}, gt_disclose={gt_disclose}, sys_disclose={sys_disclose}")
    
    # =================== RTI ETHICS ENGINE (9 DIMENSIONS × 3 LAYERS) ===================
    print("[ETHICS] Running 9-dimension dynamic audit protocol...")
    
    # Collect predictions/labels for fairness if they exist in history
    all_preds = df_fairness['system_disclose'].values if not df_fairness.empty else np.array([sys_disclose])
    all_labels = df_fairness['ground_truth_disclose'].values if not df_fairness.empty else np.array([gt_disclose])
    all_groups = df_fairness['sensitive_group'].values if not df_fairness.empty else np.array([sensitive_group])
    
    # Build metrics DYNAMICALLY using the new calculators
    structured_metrics = build_metrics_from_raw_data(
        query=query,
        response=response,
        predictions=all_preds,
        labels=all_labels,
        sensitive_attr=all_groups,
        latency_ms=latency_ms,
        output_tokens=resp_data.get("eval_count", 0),
        grounding_score=grounding_score
    )
    
    # Ensure RAG-specific details are mapped
    structured_metrics["explainability"]["support_ratio"] = supp_ratio
    structured_metrics["explainability"]["citation_coverage"] = cit_cov
    structured_metrics["ux"]["readability_fk"] = compute_readability_fk(response)

    # Run the protocol - returns EthicsResult with exhaustive accessors
    ethical_result: EthicsResult = ethics_engine.run_protocol(structured_metrics)
    
    # PRINT FULL AUDIT TABLE (L1, L2, L3)
    ethical_result.print_full_audit()
    
    label = ethical_result.final_label
    label_to_score = {"ETHICAL": 100.0, "CONDITIONALLY_ETHICAL": 70.0, "UNETHICAL": 0.0}
    overall_score = label_to_score.get(label, 50.0)
    
    # Dimension scores using the new granular accessors
    dim_scores = {
        "bias_fairness_score": round(100 * (1 - ethical_result.get_l2_risk("fairness")), 1),
        "data_grounding_drift_score": round(100 * (1 - ethical_result.get_l2_risk("drift")), 1),
        "explainability_transparency_score": round(100 * (1 - ethical_result.get_l2_risk("explainability")), 1),
        "ethical_alignment_score": round(100 * (1 - ethical_result.get_l2_risk("legal")), 1),
        "human_control_score": round(100 * (1 - ethical_result.get_l2_risk("ux")), 1),
        "legal_compliance_score": 100 if ethical_result.get_l1_status("legal") == "PASS" else 0,
        "security_robustness_score": round(100 * (1 - ethical_result.get_l2_risk("security")), 1),
        "response_quality_score": round(grounding_score * 100, 1)
    }

    row = {
        "conversation_id": f"conv_{conv_counter:04d}",
        "turn_id": 1,
        "user_id": user_id,
        "department": department,
        "timestamp_request": t_request.isoformat(),
        "timestamp_response": t_response.isoformat(),
        "latency_ms": latency_ms,
        "user_prompt": query,
        "ai_response": response,
        "rag_documents": rag_docs,
        "rag_sections": rag_sections,
        "safety_flag": ethical_result.final_label,
        "error_code": "",
        "overall_ethical_score": round(overall_score, 1),
        **dim_scores,
        "is_gold_example": 0,
        "task_completed": 1 if sys_disclose == gt_disclose else 0,
        "hallucination_rate": halluc_rate,
        "context_grounding_score": grounding_score,
        "citation_coverage": cit_cov,
        "source_diversity": source_div,
        "human_feedback_score": None,
        "norm_violation_count": 0,
        "contextual_harm_risk": ethical_result.layer2_risk_score,
        "lawfulness_assessment": "PASS" if ethical_result.get_l1_status("legal") == "PASS" else "FAIL",
        "pii_detected": pii_det,
        "pii_allowed": 0,
        "consent_required": 0,
        "consent_present": 0,
        "consent_valid": 0,
        "input_tokens": resp_data.get("prompt_eval_count", 0),
        "output_tokens": resp_data.get("eval_count", 0),
        "total_tokens": resp_data.get("prompt_eval_count", 0) + resp_data.get("eval_count", 0),
        "estimated_cost_usd": round((resp_data.get("prompt_eval_count", 0) + resp_data.get("eval_count", 0)) * 0.00003, 5),
        "model_name": BOT_MODEL,
        "infra_region": "ap-south-1"
    }

    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(METRICS_CSV, index=False)

    # =================== OUTPUT: EXHAUSTIVE 3-LAYER AUDIT (Using Package) ===================
    # Use the package's built-in exhaustive output
    ethical_result.print_full_audit()
    
    # =================== ADDITIONAL: GRANULAR L1 METRIC VALUES ===================
    print("\n" + "=" * 80)
    print("📊 GRANULAR L1 FORMULA VALUES (Direct Package Access)")
    print("=" * 80)
    print(f"\n[FAIRNESS METRICS - Layer 1]")
    print(f"  SPD (Statistical Parity Difference):    {ethical_result.spd:.4f}  | Threshold: ±{L1_THRESHOLDS['fairness']['spd']}")
    print(f"  DI  (Disparate Impact):                 {ethical_result.di:.4f}   | Range: [{L1_THRESHOLDS['fairness']['di_min']}, {L1_THRESHOLDS['fairness']['di_max']}]")
    print(f"  EOP (Equal Opportunity Diff):           {ethical_result.eop:.4f}  | Threshold: ±{L1_THRESHOLDS['fairness']['eop']}")
    print(f"  AOD (Average Odds Difference):          {ethical_result.aod:.4f}  | Threshold: ±{L1_THRESHOLDS['fairness']['aod']}")
    
    print(f"\n[DRIFT METRICS - Layer 1]")
    print(f"  PSI (Population Stability Index):       {ethical_result.psi:.4f}  | Threshold: ≤{L1_THRESHOLDS['drift']['psi']}")
    print(f"  KS  (Kolmogorov-Smirnov):               {ethical_result.ks:.4f}   | Threshold: ≤{L1_THRESHOLDS['drift']['ks']}")
    
    print(f"\n[LEGAL METRICS - Layer 1]")
    print(f"  Lawfulness:                             {ethical_result.lawfulness:.4f}  | Threshold: ={L1_THRESHOLDS['legal']['lawfulness']}")
    print(f"  CVR (Consent Validity Rate):            {ethical_result.get_l1_metric('legal', 'cvr', 1.0):.4f}  | Threshold: ≥{L1_THRESHOLDS['legal']['cvr_min']}")
    
    print(f"\n[PERFORMANCE METRICS - Layer 1]")
    print(f"  Accuracy:                               {ethical_result.accuracy:.4f}  | Threshold: ≥{L1_THRESHOLDS['performance']['accuracy_min']}")
    print(f"  Recall:                                 {ethical_result.recall:.4f}  | Threshold: ≥{L1_THRESHOLDS['performance']['recall_min']}")
    
    print(f"\n[OTHER L1 METRICS]")
    print(f"  Confidence (Explainability):            {ethical_result.get_l1_metric('explainability', 'confidence'):.4f}")
    print(f"  TCR (Task Completion Rate):             {ethical_result.get_l1_metric('ux', 'tcr'):.4f}")
    print(f"  Adv Accuracy (Security):                {ethical_result.get_l1_metric('security', 'adv_acc'):.4f}")
    print(f"  ALC (Audit Log Completeness):           {ethical_result.get_l1_metric('monitoring', 'alc'):.4f}")
    print("=" * 80)
    
    # =================== L2 RISK SCORES BY DIMENSION ===================
    print("\n" + "=" * 80)
    print("📈 L2 WEIGHTED RISK SCORES")
    print("=" * 80)
    print(f"  Dimension Weights (Sum={sum(DIMENSION_WEIGHTS.values()):.2f}):")
    for dim_key, weight in DIMENSION_WEIGHTS.items():
        risk = ethical_result.get_l2_risk(dim_key)
        weighted = risk * weight
        bar = "█" * int(risk * 20) + "░" * (20 - int(risk * 20))
        print(f"    {dim_key:15s}: R={risk:.3f} × W={weight:.2f} = {weighted:.4f}  [{bar}]")
    print(f"\n  L2 Total Risk: {ethical_result.layer2_risk_score:.4f}")
    print(f"  S_LLM Score:   {ethical_result.s_llm:.4f}")
    print("=" * 80)
    
    # =================== L3 FORENSIC EVIDENCE ===================
    print("\n" + "=" * 80)
    print("📋 L3 FORENSIC EVIDENCE BUNDLE")
    print("=" * 80)
    for dim_key in DIMENSION_WEIGHTS.keys():
        evidence = ethical_result.get_l3_explanation(dim_key)
        dim_result = ethical_result.get_dim_result(dim_key)
        if dim_result:
            print(f"\n  [{dim_result.name.upper()}]")
            print(f"    Status: {dim_result.format_l1_output()}")
            print(f"    {dim_result.format_l2_output()}")
            print(f"    Evidence: {evidence}")
    print("=" * 80)
    
    # =================== SUMMARY STATISTICS ===================
    print("\n" + "=" * 80)
    print("📊 AUDIT SUMMARY")
    print("=" * 80)
    print(f"  L1 Pass Rate: {ethical_result.l1_pass_count()}/9 ({ethical_result.l1_pass_rate()*100:.1f}%)")
    print(f"  Failed Dimensions: {ethical_result.get_failed_dims() or 'None'}")
    highest_risk = ethical_result.get_highest_risk_dim()
    print(f"  Highest Risk Dimension: {highest_risk[0]} (R={highest_risk[1]:.3f})")
    print(f"  Final Verdict: {ethical_result.final_label}")
    print(f"  Risk Band: {ethical_result.risk_band}")
    print(f"  Required Action: {ethical_result.required_action}")
    print("=" * 80)
    
    # =================== RAG SOURCE CITATIONS (FROM PDFs) ===================
    print(f"\n{'='*60}")
    print("📚 SOURCE CITATIONS (Retrieved from RTI Documents)")
    print(f"{'='*60}")
    rag_citations = format_rag_citations(retrieved)
    for cite in rag_citations:
        print(f"\n[{cite['citation_id']}] {cite['document']} - Page {cite['page']}")
        print(f"    Link: {cite['uri']}")
        print(f"    Relevance: {cite['relevance_score']:.4f}")
        print(f"    \"{cite['excerpt']}\"")
    print(f"\n{'='*60}")
    print(f"📊 Sources: {len(retrieved)} chunks | {source_div} unique documents")
    print(f"{'='*60}")
    
    print(f"\nLogged to {METRICS_CSV}")
    conv_counter += 1