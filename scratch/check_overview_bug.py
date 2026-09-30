import os
import json

DATA_DIR = "./data"
precomputed_file = os.path.join(DATA_DIR, "precomputed_stats.json")
mapped_tagged_path = os.path.join(DATA_DIR, "final_tagged_dataset_mapped.json")

precomputed = json.load(open(precomputed_file, "r", encoding="utf-8")) if os.path.exists(precomputed_file) else {}
metadata = precomputed.get("metadata", {})
total_relevant = metadata.get("total_relevant")
print("precomputed metadata total_relevant:", total_relevant)

if os.path.exists(mapped_tagged_path):
    tagged_posts = json.load(open(mapped_tagged_path, "r", encoding="utf-8"))
    print("len(final_tagged_dataset_mapped.json):", len(tagged_posts))
    if tagged_posts:
        print("Sample post keys:", list(tagged_posts[0].keys()))
        print("Sample post taxonomy:", tagged_posts[0].get("taxonomy"))
        
        # Check counts
        vague_memory_count_root = sum(1 for p in tagged_posts if p.get("vague_memory") in ("vague", "partial"))
        vague_memory_count_tax = sum(1 for p in tagged_posts if p.get("taxonomy", {}).get("vague_memory") in ("vague", "partial"))
        print("vague_memory count root:", vague_memory_count_root, "| taxonomy dict:", vague_memory_count_tax)

        fail_count_root = sum(1 for p in tagged_posts if p.get("failure_step") not in ("no_failure", None, ""))
        fail_count_tax = sum(1 for p in tagged_posts if p.get("taxonomy", {}).get("failure_step") not in ("no_failure", None, ""))
        print("fail count root:", fail_count_root, "| taxonomy dict:", fail_count_tax)
