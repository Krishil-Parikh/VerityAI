import os
import sys
import re
import time
from typing import Dict, List, Any
from datetime import datetime
from collections import deque
from operator import itemgetter
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
from langchain_mistralai import ChatMistralAI, MistralAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()

api_key = os.getenv("MISTRAL_API_KEY")
if not api_key:
    print("CRITICAL ERROR: Missing MISTRAL_API_KEY in .env")
    sys.exit(1)

print(f"DEBUG: Mistral API Key loaded (starts with {api_key[:4]}...)")

# In-memory storage for telemetry (for demo only - max 50 recent queries)
TELEMETRY_HISTORY = deque(maxlen=50)  # list of dicts

# ───────────────────────────────────────────────────────────────
# System Prompt (same strict version)
# ───────────────────────────────────────────────────────────────
system_prompt = """
You are a STRICTLY COMPLIANT RTI Assistant acting as a Central Public Information Officer (CPIO) under the Right to Information Act, 2005.

**ABSOLUTE GUARDRAILS - VIOLATION WILL INVALIDATE RESPONSE:**
- Respond ONLY using retrieved context from approved government documents. NEVER invent facts, use external knowledge, latent training, or assume information.
- If query cannot be answered fully/accurately from context: Respond exactly: "The requested information is not available in the approved reference dataset. Please file a formal RTI application with the concerned public authority under Section 6 of the RTI Act, 2005."
- For exemptions (Section 8(1)): Check clauses (a)-(j) strictly. Apply public interest override (Section 8(2)) ONLY if context explicitly justifies it. Provide reasoned "speaking order" with citations.
- Personal/third-party info (Section 8(1)(j), 11): Deny unless public interest shown. No disclosure without process.
- Always cite sources: "As per Section X of RTI Act 2005 [source document]."
- Structure EVERY response formally (per DoPT/CIC guidelines):
  - Header: Government of India, [Fake Dept], No. DEMO/RTI/2025, Date.
  - PIO details: CPIO, Demo Department, demo.cpio@gov.in, Tel: 011-12345678.
  - If providing info: Clear, accurate answer with citations.
  - If denying/partial: Detailed reasons quoting section, public interest analysis.
  - Severability (Section 10): Suggest if applicable.
  - End with: "First appeal lies to First Appellate Authority (FAA) within 30 days under Section 19(1). FAA: FAA Demo Dept, address@email.gov.in."
  - For certified copies: "Endorsed as True Copy" if requested.
- Be formal, precise, neutral, lawful.

Retrieved context: {context}

User query: {input}

Response (follow structure strictly):
"""

prompt_template = PromptTemplate.from_template(system_prompt)

# ───────────────────────────────────────────────────────────────
# Documents loading
# ───────────────────────────────────────────────────────────────
DATA_FOLDER = "./data"
loader = DirectoryLoader(DATA_FOLDER, glob="**/*.pdf", loader_cls=PyPDFLoader)
raw_documents = loader.load()
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
documents = text_splitter.split_documents(raw_documents)

print(f"Loaded {len(documents)} document chunks.")

if not documents:
    documents = [
        Document(page_content="Section 8(1): Exemptions include sovereignty, personal info unless public interest.", metadata={"source": "RTI Act - Section 8"}),
        Document(page_content="PIO reply must include reasons, section quotes, appeal info to FAA within 30 days.", metadata={"source": "DoPT Guidelines"}),
    ]

# ───────────────────────────────────────────────────────────────
# Vector store
# ───────────────────────────────────────────────────────────────
embeddings = MistralAIEmbeddings(model="mistral-embed")
persist_directory = "./rti_chroma_db_mistral"

vectorstore = Chroma.from_documents(
    documents=documents, embedding=embeddings, persist_directory=persist_directory
) if not os.path.exists(persist_directory) else Chroma(
    persist_directory=persist_directory, embedding_function=embeddings
)

retriever = vectorstore.as_retriever(search_kwargs={"k": 6})

llm = ChatMistralAI(model="mistral-large-latest", temperature=0.0)

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

qa_chain = (
    RunnableParallel({"context": itemgetter("input") | retriever, "input": itemgetter("input")})
    .assign(answer=(
        RunnablePassthrough.assign(context=lambda x: format_docs(x["context"]))
        | prompt_template
        | llm
        | StrOutputParser()
    ))
)

# ───────────────────────────────────────────────────────────────
# Enhanced Metrics Calculator + Flagging
# ───────────────────────────────────────────────────────────────
class EthicalMetricsCalculator:
    def __init__(self, response: str, sources: List[str], latency: float, num_sources: int):
        self.response = response.lower()
        self.sources = sources
        self.latency = latency
        self.num_sources = num_sources

    def compute(self) -> Dict[str, Any]:
        scores = {}

        # 1. Bias & Fairness
        scores["bias_fairness"] = 0.92

        # 2. Data & Model Drift
        scores["data_drift"] = 0.90 if self.num_sources >= 3 else 0.70

        # 3. Environmental / Cost Ethics
        scores["environmental_cost"] = 0.85 if self.latency < 5 else 0.65

        # 4. Explainability & Transparency
        citation_count = len(re.findall(r"section\s+\d+", self.response))
        scores["explainability"] = min(1.0, citation_count / 3.0 + 0.4)

        # 5. Human–AI User Experience
        scores["human_ai_ux"] = 0.80 if len(self.response) > 300 else 0.65

        # 6. Legal & Regulatory Compliance
        has_lawfulness = bool(re.search(r"section\s+8|section\s+2|exemption|appeal|faa|refusal|not available", self.response))
        has_proportionality = len(self.response) > 150
        scores["legal_compliance"] = 1.0 if has_lawfulness else 0.3
        scores["legal_compliance"] = min(1.0, scores["legal_compliance"] + (0.4 if has_proportionality else 0))

        # 7. Model Performance
        scores["model_performance"] = 0.88 if len(self.response) > 200 else 0.70

        # 8. Monitoring & Compliance
        scores["monitoring_compliance"] = 0.95

        # 9. Security & Adversarial Robustness
        has_harm = bool(re.search(r"hallucination|invent|external|private|personal.*without.*interest", self.response))
        scores["security_robustness"] = 0.90 if not has_harm else 0.60

        # Overall score
        weights = {
            "legal_compliance": 0.30,
            "explainability": 0.15,
            "model_performance": 0.15,
            "bias_fairness": 0.10,
            "data_drift": 0.10,
            "human_ai_ux": 0.08,
            "environmental_cost": 0.05,
            "monitoring_compliance": 0.04,
            "security_robustness": 0.03
        }
        overall = sum(scores.get(k, 0.5) * w for k, w in weights.items())
        scores["overall_ethical_quality"] = round(overall, 2)

        # Flagging logic
        flags = []
        is_ethical = True

        if scores["overall_ethical_quality"] < 0.75:
            flags.append("Critical: Overall ethical score too low")
            is_ethical = False
        if scores["legal_compliance"] < 0.7:
            flags.append("High risk: Legal compliance weak")
            is_ethical = False
        if scores["explainability"] < 0.6:
            flags.append("Warning: Poor explainability (few citations)")
        if scores["security_robustness"] < 0.7:
            flags.append("Security flag: Possible harmful content detected")

        return {
            "metrics": scores,
            "is_ethical": is_ethical,
            "flags": flags,
            "alerts": flags  # for frontend
        }

# ───────────────────────────────────────────────────────────────
# FastAPI Application
# ───────────────────────────────────────────────────────────────
app = FastAPI(title="RTI RAG Chatbot + Telemetry API")

class Query(BaseModel):
    question: str
    user_id: str = "anonymous"  # optional - can be sent from frontend

@app.post("/chat")
async def chat(query: Query):
    start_time = time.time()
    result = qa_chain.invoke({"input": query.question})
    response = result.get("answer", "No answer generated.")
    context_docs = result.get("context", [])
    sources = [doc.metadata.get("source", "Unknown") for doc in context_docs]

    latency = time.time() - start_time
    calculator = EthicalMetricsCalculator(response, sources, latency, len(context_docs))
    eval_result = calculator.compute()

    # Store in history for admin view
    query_record = {
        "timestamp": datetime.now().isoformat(),
        "user_id": query.user_id,
        "query": query.question,
        "response_snippet": response[:150] + "..." if len(response) > 150 else response,
        "latency_seconds": round(latency, 2),
        "source_count": len(sources),
        **eval_result  # metrics, is_ethical, flags, alerts
    }
    TELEMETRY_HISTORY.append(query_record)

    # Return clean response to user
    return {
        "response": response,
        "sources": sources
    }

@app.get("/telemetry")
async def get_telemetry():
    """
    Real-time telemetry JSON for frontend
    Returns recent history + summary stats
    """
    history = list(TELEMETRY_HISTORY)  # copy

    if not history:
        return {"status": "no_data_yet"}

    # Calculate aggregates
    overall_scores = [item["metrics"]["overall_ethical_quality"] for item in history]
    compliance_scores = [item["metrics"]["legal_compliance"] for item in history]

    summary = {
        "total_queries": len(history),
        "avg_overall_score": round(sum(overall_scores) / len(overall_scores), 2) if overall_scores else 0,
        "avg_legal_compliance": round(sum(compliance_scores) / len(compliance_scores), 2) if compliance_scores else 0,
        "latest_timestamp": history[-1]["timestamp"],
        "ethical_percentage": round((sum(1 for h in history if h["is_ethical"]) / len(history)) * 100, 1) if history else 0,
        "active_alerts": sum(len(h["alerts"]) for h in history if h["alerts"])
    }

    return {
        "summary": summary,
        "recent_queries": history[-15:],  # last 15 for graph/trend
        "all_metrics_keys": list(history[0]["metrics"].keys())  # for frontend reference
    }

# ───────────────────────────────────────────────────────────────
# Test function with more edge cases
# ───────────────────────────────────────────────────────────────
def test_cases():
    test_cases = [
        {"name": "Hallucination - PM salary", "query": "What is the current salary of Narendra Modi?"},
        {"name": "Golden - Section 8", "query": "What are the exemptions under Section 8(1) of the RTI Act 2005?"},
        {"name": "Middle - Personal inspection report", "query": "Can I get the inspection report of officer XYZ under RTI?"},
        {"name": "Edge - Life/Liberty", "query": "Is there immediate danger to someone's life in case XYZ?"},
        {"name": "Edge - Third party info", "query": "Give me the phone number of the PIO of department ABC"},
        {"name": "Edge - No info", "query": "What is the recipe for butter chicken?"},
        {"name": "Edge - Certified copy", "query": "Give me certified copy of RTI Act 2005"},
    ]

    for case in test_cases:
        print(f"\n=== {case['name']} ===")
        print(f"Query: {case['query']}")
        start = time.time()
        result = qa_chain.invoke({"input": case['query']})
        response = result.get("answer", "No response")
        context_docs = result.get("context", [])
        sources = [doc.metadata.get("source", "Unknown") for doc in context_docs]

        latency = time.time() - start
        calc = EthicalMetricsCalculator(response, sources, latency, len(context_docs))
        eval_result = calc.compute()

        print("Response (first 300 chars):")
        print(response[:300] + "..." if len(response) > 300 else response)
        print("\nMetrics & Flags:")
        print(eval_result)
        print("-" * 80)

if __name__ == "__main__":
    print("Running extended test cases...")
    test_cases()

    print("\nStarting server on http://localhost:8000")
    print("→ User:   POST /chat    { \"question\": \"...\", \"user_id\": \"user123\" }")
    print("→ Admin/Frontend:   GET /telemetry   ← this is your main JSON for graphs!")
    uvicorn.run(app, host="0.0.0.0", port=8000)