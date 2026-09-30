import json
from backend.rag.rag_engine import RAGEngine

def test_three_questions():
    engine = RAGEngine()
    
    questions = [
        "Where in the search flow do users encounter errors?",
        "Which photo types fail search most frequently?",
        "What kind of old photos users struggle to retrieve?"
    ]
    
    results = []
    
    for idx, q in enumerate(questions, 1):
        print(f"\n========================================================")
        print(f"QUERY {idx}: '{q}'")
        print(f"========================================================")
        res = engine.ask(q, session_id=f"session_{idx}")
        
        answer_text = (res.get('answer') or "").encode("utf-8", errors="ignore").decode("ascii", errors="ignore")
        disclaimer = (res.get('sample_disclaimer') or "").encode("utf-8", errors="ignore").decode("ascii", errors="ignore")
        
        print(f"Status: {res.get('status')}")
        print(f"Is Refusal: {res.get('is_refusal', False)}")
        print(f"Answer Body:\n{answer_text}")
        print(f"Disclaimer: {disclaimer}")
        print(f"Citations ({len(res.get('citations', []))}):")
        for c in res.get("citations", []):
            quote = (c.get('quote') or "").encode("utf-8", errors="ignore").decode("ascii", errors="ignore")
            print(f"  - [{c.get('source')}] \"{quote[:75]}...\"")
            
        results.append({
            "query": q,
            "answer": answer_text,
            "status": res.get("status")
        })

    print("\n========================================================")
    print("DIVERSITY CHECK ACROSS THE 3 ANSWERS")
    print("========================================================")
    answers = [r["answer"] for r in results]
    is_all_same = len(set(answers)) == 1
    print(f"Are all 3 answers identical? {is_all_same}")

if __name__ == "__main__":
    test_three_questions()
