import json

def dump_exact_key_insights():
    with open("data/precomputed_stats.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        
    key_insights = data.get("key_insights", [])
    print(f"Total Key Insights found: {len(key_insights)}")
    
    for item in key_insights:
        num = item.get("number")
        q_id = f"Q{num}"
        q_text = item.get("question")
        n_val = item.get("n_sample") or item.get("evidence_n")
        dist = item.get("distribution", [])
        
        print(f"\n[{q_id}] {q_text} (n={n_val})")
        for d in dist:
            label = d.get("label") or d.get("category")
            count = d.get("count")
            pct = d.get("share_pct") or d.get("pct")
            print(f"   - {label}: {pct}% (n={count})")

if __name__ == "__main__":
    dump_exact_key_insights()
