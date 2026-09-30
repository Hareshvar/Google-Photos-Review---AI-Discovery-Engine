import os
import json
from dotenv import load_dotenv
load_dotenv()
from backend.rag.rag_engine import RAGEngine

def test_live_rag_now():
    engine = RAGEngine()
    query = "what information do people remember while searching a photo?"
    print(f"Querying live RAGEngine: '{query}'...")
    res = engine.ask(query)
    
    print("\n=== LIVE RAG ENGINE RESPONSE ===")
    print("Status:", res.get("status"))
    print("Answer:\n", res.get("answer"))
    print("\nSample Disclaimer:", res.get("sample_disclaimer"))
    print("\nCitations count:", len(res.get("citations", [])))
    for c in res.get("citations", []):
        print(f"  - [{c.get('source')}] {c.get('quote')}")

if __name__ == "__main__":
    test_live_rag_now()
