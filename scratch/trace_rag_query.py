import json
from backend.rag.rag_engine import RAGEngine, RAG_PROMPT_TEMPLATE, clean_response_formatting

def trace_retrieval():
    query = "what information do people remember while searching a photo?"
    engine = RAGEngine()
    
    matches = engine.vector_store.query_similar(query, n_results=10)
    
    with open("data/precomputed_stats.json", "r", encoding="utf-8") as f:
        precomputed = json.load(f)
        
    total_relevant = precomputed.get("metadata", {}).get("total_relevant", 9774)

    themes_list = []
    for c in precomputed.get("themes", {}).get("layer_b_emergent_clusters", []):
        title = c.get("title") or c.get("theme_title")
        pct = c.get("share_pct") or c.get("percentage")
        count = c.get("count")
        if title:
            themes_list.append(f"{title} ({pct}% of posts, n={count:,})")
    themes_summary = "; ".join(themes_list) if themes_list else "None"

    situations_list = []
    for s in precomputed.get("situations", [])[:5]:
        title = s.get("situation") or s.get("situation_title")
        pct = s.get("pct") or s.get("share_pct")
        score = s.get("opportunity_score")
        if title:
            situations_list.append(f"{title} ({pct}%, Score: {score})")
    situations_summary = "; ".join(situations_list) if situations_list else "None"

    context_snippets = []
    for idx, m in enumerate(matches[:5], 1):
        q_clean = clean_response_formatting(m.get('quote') or '')
        context_snippets.append(f"[{idx}] Source: {m['source']} | Quote: \"{q_clean}\" | Text: {m['matched_text'][:200]}")
    retrieved_context_str = "\n".join(context_snippets)

    prompt_input = RAG_PROMPT_TEMPLATE.format(
        prompt=query,
        chat_history_context="None",
        retrieved_context=retrieved_context_str,
        total_relevant=total_relevant,
        themes_summary=themes_summary,
        situations_summary=situations_summary
    )
    
    print("=== EXACT RETRIEVED CONTEXT PASSED TO LLM ===")
    print(retrieved_context_str.encode("utf-8", errors="ignore").decode("ascii", errors="ignore"))
    
    print("\n=== SYSTEM STATISTICS PASSED TO LLM ===")
    print(f"total_relevant: {total_relevant}")
    print(f"themes_summary: {themes_summary}")
    print(f"situations_summary: {situations_summary}")

    # Check if cues_remembered or Q2 distribution is present anywhere in prompt_input
    has_q2_distribution = "cues_remembered" in prompt_input or "person / face" in prompt_input.lower() or "date / time" in prompt_input.lower()
    print(f"\nWas Q2 cues_remembered distribution or cue categories included in the prompt context? {has_q2_distribution}")

if __name__ == "__main__":
    trace_retrieval()
