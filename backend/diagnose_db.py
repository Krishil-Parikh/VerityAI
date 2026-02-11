import chromadb
from chromadb.config import Settings
import os

BACKEND_DIR = os.getcwd()
DB_DIR = os.path.join(BACKEND_DIR, 'db')
PERSIST_DIRECTORY = os.path.join(DB_DIR, 'chroma_rti_db')
COLLECTION_NAME = "rti_documents_v4"

def check_page_2():
    client = chromadb.PersistentClient(path=PERSIST_DIRECTORY)
    coll = client.get_collection(COLLECTION_NAME)
    
    # Query for Page 2 metadata AND specific doc
    results = coll.get(
        where={"$and": [{"page": 2}, {"doc": "CSMOP_0_0.pdf"}]},
        include=["metadatas", "documents"]
    )
    
    print(f"Found {len(results['ids'])} chunks for Page 2.")
    if len(results['ids']) > 0:
        print("Sample Chunk:", results['documents'][0][:150])
        print("Sample Metadata:", results['metadatas'][0])
        
        # Check for 'IMPORTANT WEBSITES'
        found = False
        for doc in results['documents']:
            if "IMPORTANT WEBSITES" in doc:
                found = True
                print("✅ Found 'IMPORTANT WEBSITES' in a Page 2 chunk!")
                break
        if not found:
            print("❌ 'IMPORTANT WEBSITES' keyword NOT found in any Page 2 chunk.")

if __name__ == "__main__":
    check_page_2()
