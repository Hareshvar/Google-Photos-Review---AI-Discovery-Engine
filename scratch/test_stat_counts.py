import json

tagged_posts = json.load(open("data/final_tagged_dataset_mapped.json", "r", encoding="utf-8"))

print("Total posts in file:", len(tagged_posts))

# All posts in final_tagged_dataset_mapped
rel_posts = [p for p in tagged_posts if p.get("taxonomy", {}).get("relevant") is True or p.get("relevant") is True]
print("Posts with relevant == True:", len(rel_posts))

# If we filter relevant posts
vague_rel = sum(1 for p in rel_posts if p.get("taxonomy", {}).get("vague_memory") in ("vague", "partial") or p.get("vague_memory") in ("vague", "partial"))
fail_rel = sum(1 for p in rel_posts if p.get("taxonomy", {}).get("failure_step") not in ("no_failure", None, "") or p.get("failure_step") not in ("no_failure", None, ""))

print(f"Relevant posts count: {len(rel_posts)}")
print(f"Vague memory count (among relevant): {vague_rel} ({vague_rel / max(1, len(rel_posts))*100:.1f}%)")
print(f"Search failures count (among relevant): {fail_rel} ({fail_rel / max(1, len(rel_posts))*100:.1f}%)")

# What if relevant is 916 from precomputed_stats.json?
precomputed = json.load(open("data/precomputed_stats.json", "r", encoding="utf-8"))
q9_dist = next((k["distribution"] for k in precomputed.get("key_insights", []) if k.get("number") == 9), [])
no_fail_count = next((d["count"] for d in q9_dist if d.get("key") == "no_failure"), 0)
fail_count_q9 = 916 - no_fail_count
print(f"\nFrom precomputed Q9 (n=916):")
print(f"No failure count: {no_fail_count}")
print(f"Search failures count (n=916): {fail_count_q9} ({fail_count_q9 / 916 * 100:.1f}%)")
