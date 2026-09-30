import json
from backend.rag.vector_store import VectorStore
from backend.rag.rag_engine import RAGEngine

def main():
    print("=== 1. CHROMADB LIVE COLLECTION COUNT ===")
    vs = VectorStore()
    count = vs.collection.count()
    print(f"ChromaDB Collection Name: '{vs.collection.name}'")
    print(f"ChromaDB Document Count (Live): {count}")
    
    print("\n=== 2. QUERY TRACE FOR 'what information do people remember while searching a photo?' ===")
    query = "what information do people remember while searching a photo?"
    
    engine = RAGEngine()
    matches = engine.vector_store.query_similar(query, n_results=10)
    print(f"Number of documents retrieved from ChromaDB: {len(matches)}")
    
    print("\n--- TOP 5 RETRIEVED DOCUMENTS FROM CHROMADB ---")
    for idx, m in enumerate(matches[:5], 1):
        print(f"[{idx}] Post ID: {m['post_id']} | Source: {m['source']} | Distance: {m['distance']:.4f}")
        print(f"    Quote: {m['quote']}")
        print(f"    Text Snippet: {m['matched_text'][:150]}...")
        
    print("\n--- PRECOMPUTED STATS PASSED TO LLM PROMPT ---")
    with open("data/precomputed_stats.json", "r", encoding="utf-8") as f:
        precomputed = json.load(f)
    print(f"total_relevant in precomputed_stats.json: {precomputed.get('metadata', {}).get('total_relevant')}")
    print("Themes overview passed to prompt:", [c.get("title") for c in precomputed.get("themes", {}).get("layer_b_emergent_clusters", [])])
    
    # Check if cues_remembered or Q2 distribution is present in precomputed_stats.json
    has_q2_in_precomputed = "insights" in precomputed and any("cues" in str(v).lower() for v in precomputed.get("insights", []))
    print(f"Is Q2 precomputed distribution in precomputed_stats.json? {'insights' in precomputed}")

    # Let's inspect precomputed keys
    print("Keys present in precomputed_stats.json:", list(precomputed.keys()))
    
    # Ask RAGEngine
    response = engine.ask(query)
    print("\n=== 3. RAG ENGINE API RESPONSE PAYLOAD ===")
    print(f"Status: {response.get('status')}")
    print(f"Answer Body: {response.get('answer')}")
    print(f"Backend sample_disclaimer: '{response.get('sample_disclaimer')}'")
    print(f"Citations count: {len(response.get('citations', []))}")

if __name__ == "__main__":
    main()
