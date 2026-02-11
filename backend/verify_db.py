import chromadb
from chromadb.config import Settings
import os

BACKEND_DIR = os.getcwd()
DB_DIR = os.path.join(BACKEND_DIR, 'db')
PERSIST_DIRECTORY = os.path.join(DB_DIR, 'chroma_rti_db')

def verify():
    client = chromadb.PersistentClient(path=PERSIST_DIRECTORY)
    try:
        coll = client.get_collection('rti_documents_v3')
        print(f"Collection: rti_documents_v3")
        print(f"Count: {coll.count()}")
        if coll.count() > 0:
            sample = coll.get(limit=1, include=['documents', 'metadatas'])
            print(f"Sample Metadata: {sample['metadatas'][0]}")
            print(f"Sample Text: {sample['documents'][0][:100]}...")
    except Exception as e:
        print(f"Error accessing collection: {e}")
        # List all collections
        print(f"Available collections: {[c.name for c in client.list_collections()]}")

if __name__ == "__main__":
    verify()
