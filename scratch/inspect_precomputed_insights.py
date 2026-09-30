import json

def inspect_precomputed_structure():
    with open("data/precomputed_stats.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        
    print("Top-level keys in precomputed_stats.json:", list(data.keys()))
    
    key_insights = data.get("key_insights", [])
    print(f"\nNumber of items in 'key_insights': {len(key_insights)}")
    
    total_tokens_approx = 0
    
    for idx, item in enumerate(key_insights, 1):
        q_id = item.get("id") or item.get("question_id") or f"Q{item.get('number', idx)}"
        q_text = item.get("question", "")
        n_sample = item.get("n_sample") or item.get("evidence_n")
        dist = item.get("distribution", [])
        dist_summary = ", ".join([f"{d.get('label') or d.get('category')}: {d.get('share_pct') or d.get('pct')}% (n={d.get('count')})" for d in dist[:3]])
        
        # Calculate compact representation token size
        compact_str = f"Q{item.get('number', idx)} ({q_text}): n={n_sample} sample. Distribution: " + "; ".join([f"{d.get('label') or d.get('category')}: {d.get('share_pct') or d.get('pct')}% (n={d.get('count')})" for d in dist])
        approx_tokens = len(compact_str.split()) * 1.3
        total_tokens_approx += approx_tokens
        
        print(f"  [{q_id}] {q_text[:55]}... | n={n_sample} | Top dist: {dist_summary}")
        print(f"      Compact summary: {compact_str[:120]}... (~{int(approx_tokens)} tokens)")

    print(f"\nApproximate Total Token Size of ALL 9 Key Insights compact distributions combined: ~{int(total_tokens_approx)} tokens")

if __name__ == "__main__":
    inspect_precomputed_structure()
