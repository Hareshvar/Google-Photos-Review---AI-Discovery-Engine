import logging
from backend.analysis.pipeline import AnalysisPipeline
from backend.exporter.bundle_builder import BundleBuilder

logging.basicConfig(level=logging.INFO)

print("--- REGENERATING PRECOMPUTED STATS AND BUNDLE ---")
pipeline = AnalysisPipeline(data_dir="./data")
result = pipeline.run()
print("Pipeline Result:", result)

builder = BundleBuilder(data_dir="./data")
bundle = builder.build_bundle()
print("Bundle generated with title:", bundle.get("title"))

# Audit the situations in precomputed_stats.json and retrieval_lens_analysis_bundle.json
import json
precomputed = json.load(open("data/precomputed_stats.json", "r", encoding="utf-8"))
situations = precomputed.get("situations", [])
tail = precomputed.get("situations_tail_aggregated")

print("\n--- REGENERATED SITUATION TITLES (precomputed_stats.json) ---")
all_titles = []
for s in situations:
    rank = s.get("rank")
    n = s.get("count")
    title = s.get("situation_title")
    all_titles.append(title)
    print(f"Rank #{rank:2d}: n={n:3d} | {title}")

if tail:
    tail_title = tail.get("situation_title")
    all_titles.append(tail_title)
    print(f"Tail Aggregated: n={tail.get('count'):3d} | {tail_title}")

print(f"\nTotal rows: {len(all_titles)}")
print(f"Unique titles: {len(set(all_titles))}")
assert len(all_titles) == len(set(all_titles)), "ERROR: Duplicate titles remain!"
print("SUCCESS: Every situation title is 100% unique!")
