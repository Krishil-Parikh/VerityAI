import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"
import re
import fitz
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

# Paths
CORE_DIR = os.getcwd() # Should be backend
DATA_DIR = os.path.join(CORE_DIR, "data")
DB_DIR = os.path.join(CORE_DIR, "db")
PERSIST_DIRECTORY = os.path.join(DB_DIR, "chroma_rti_db")
EMBED_MODEL = "all-MiniLM-L6-v2"
COLLECTION_NAME = "rti_documents_v4"

embedder = SentenceTransformer(EMBED_MODEL)
client = chromadb.PersistentClient(path=PERSIST_DIRECTORY)

def smart_chunk_document(text, page_num, doc_name, chunk_size=600, overlap=120):
    chunks = []
    start = 0
    text_len = len(text)
    
    while start < text_len:
        end = min(start + chunk_size, text_len)
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
        start = end - overlap
    
    return chunks

def force_index():
    print(f"🚀 Forcing Index for {COLLECTION_NAME}...")
    try:
        client.delete_collection(COLLECTION_NAME)
    except:
        pass
        
    coll = client.create_collection(name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"})
    
    all_pdf_files = [f for f in os.listdir(DATA_DIR) if f.lower().endswith(".pdf")]
    
    all_texts = []
    all_ids = []
    all_metadatas = []
    
    for pdf_file in all_pdf_files:
        print(f"Indexing {pdf_file}...")
        path = os.path.join(DATA_DIR, pdf_file)
        doc = fitz.open(path)
        for page_num in range(len(doc)):
            text = doc[page_num].get_text("text").strip()
            if not text: continue
            
            chunks = smart_chunk_document(text, page_num + 1, pdf_file)
            for i, c in enumerate(chunks):
                uid = f"{pdf_file}_{page_num}_{i}"
                all_texts.append(c["text"])
                all_metadatas.append(c["metadata"])
                all_ids.append(uid)
        doc.close()

    if all_texts:
        print(f"✨ Generating {len(all_texts)} embeddings...")
        embeddings = embedder.encode(all_texts, show_progress_bar=True, normalize_embeddings=True)
        
        batch_size = 100
        for i in range(0, len(all_texts), batch_size):
            end = i + batch_size
            coll.add(
                ids=all_ids[i:end],
                embeddings=embeddings[i:end].tolist(),
                documents=all_texts[i:end],
                metadatas=all_metadatas[i:end]
            )
        print(f"✅ Success! {coll.count()} chunks indexed.")

if __name__ == "__main__":
    force_index()
