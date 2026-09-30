import os
import json
from backend.models.taxonomy import TaggedPostRecord
from backend.analysis.situations_engine import SituationsEngine, HUMAN_TARGETS, HUMAN_CUES, HUMAN_JOBS, SITUATION_TITLE_MAP

# Load dataset
mapped_tagged_path = "./data/final_tagged_dataset_mapped.json"
posts_data = json.load(open(mapped_tagged_path, "r", encoding="utf-8"))

rel_posts = [
    TaggedPostRecord(**p) for p in posts_data
    if (p.get("taxonomy", {}).get("relevant") is True or p.get("relevant") is True)
]

print(f"Loaded {len(rel_posts)} relevant posts.")

res = SituationsEngine.build_situations_matrix(rel_posts)
situations = res["situations"]

print("\n--- CURRENT SITUATION TITLES (RANK 1..N) ---")
current_titles = []
for s in situations:
    title = s["situation_title"]
    current_titles.append(title)
    print(f"Rank #{s['rank']}: n={s['count']} | {title} | Subtitle: {s['situation_subtitle']}")

print("\nDuplicate current titles:")
from collections import Counter
counts = Counter(current_titles)
for t, c in counts.items():
    if c > 1:
        print(f"  '{t}': {c} occurrences")
