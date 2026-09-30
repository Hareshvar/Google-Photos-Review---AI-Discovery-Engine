import json
from backend.rag.rag_engine import RAGEngine

def check_q3_grounding():
    engine = RAGEngine()
    query = "What kind of old photos users struggle to retrieve?"
    
    matches = engine.vector_store.query_similar(query, n_results=10)
    
    print("=== TOP 10 RETRIEVED DOCUMENTS FOR QUERY 3 ===")
    for idx, m in enumerate(matches, 1):
        print(f"\n[{idx}] Post ID: {m['post_id']} | Source: {m['source']}")
        print(f"    Quote: {m.get('quote')}")
        print(f"    Text: {m['matched_text'][:250]}")
        
    res = engine.ask(query, session_id="check_q3")
    
    print("\n=== CITED QUOTES IN RESPONSE ===")
    for idx, c in enumerate(res.get("citations", []), 1):
        print(f"[{idx}] Source: {c['source']} | Quote: \"{c['quote']}\" | Post ID: {c['post_id']}")
        
    print("\n=== FULL ANSWER TEXT ===")
    print(res.get("answer"))

if __name__ == "__main__":
    check_q3_grounding()
