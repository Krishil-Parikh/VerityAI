import requests
import json

def test_rag_accuracy():
    url = "http://localhost:8000/query"
    payload = {
        "user_query": "List the nine important websites exactly as they appear under 'IMPORTANT WEBSITES' on page 2 of CSMOP_0_0.pdf (May 2015).",
        "bot_model": "llama3",
        "conversation_id": "precision_test_1"
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        
        print(f"Status: {data['success']}")
        print(f"AI Response Snippet: {data['ai_response'][:200]}...")
        print(f"Grounding Score: {data['grounding']['score']}")
        print(f"Citations (RAG Sources): {data['rag_sources']}")
        print(f"Retrieved Documents: {data.get('metrics', {}).get('rag_documents', 'Unknown')}")
        
        # Check if Page 2 CSMOP is in sources
        sources_str = str(data['rag_sources'])
        if "CSMOP_0_0.pdf" in sources_str and ("Page 2" in sources_str or "Page: 2" in sources_str):
             print("✅ Retrieval SUCCESS: Page 2 CSMOP found in sources")
        else:
             print("❌ Retrieval FAILURE: Page 2 CSMOP NOT found in sources")
        
        # Verify source marker presence
        if "[Source: CSMOP_0_0.pdf, Page: 2]" in data['ai_response']:
            print("✅ SUCCESS: Source marker found in response")
        else:
            print("❌ FAILURE: Source marker missing")
            
        # Verify content
        websites = ["india.gov.in", "darpg.gov.in", "pib.nic.in"]
        found = [w for w in websites if w in data['ai_response'].lower()]
        print(f"✅ Found {len(found)}/3 sample websites")
        
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    test_rag_accuracy()
