import json
from backend.rag.rag_engine import RAGEngine

def test_cues_query():
    query = "what information do people remember while searching a photo?"
    print(f"Testing RAGEngine with query: '{query}'")
    
    engine = RAGEngine()
    res = engine.ask(query)
    
    answer_text = (res.get('answer') or "").encode("utf-8", errors="ignore").decode("ascii", errors="ignore")
    disclaimer = (res.get('sample_disclaimer') or "").encode("utf-8", errors="ignore").decode("ascii", errors="ignore")
    
    print("\n=== RAG RESPONSE PAYLOAD ===")
    print(f"Status: {res.get('status')}")
    print(f"Answer:\n{answer_text}")
    print(f"\nBackend sample_disclaimer: '{disclaimer}'")
    print(f"Citations ({len(res.get('citations', []))}):")
    for cit in res.get("citations", []):
        q = (cit.get('quote') or "").encode("utf-8", errors="ignore").decode("ascii", errors="ignore")
        print(f"  - ({cit['source']}) \"{q[:80]}...\"")

if __name__ == "__main__":
    test_cues_query()
