import time
from backend.rag.rag_engine import RAGEngine

def test_live_rag():
    print("Waiting 3 seconds for rate limit reset...")
    time.sleep(3)
    
    query = "what information do people remember while searching a photo?"
    print(f"Querying: '{query}'")
    
    engine = RAGEngine()
    res = engine.ask(query)
    
    answer_text = (res.get('answer') or "").encode("utf-8", errors="ignore").decode("ascii", errors="ignore")
    disclaimer = (res.get('sample_disclaimer') or "").encode("utf-8", errors="ignore").decode("ascii", errors="ignore")
    
    print("\n=== GENERATED RAG ANSWER ===")
    print(answer_text)
    print(f"\nFooter Disclaimer: '{disclaimer}'")

if __name__ == "__main__":
    test_live_rag()
