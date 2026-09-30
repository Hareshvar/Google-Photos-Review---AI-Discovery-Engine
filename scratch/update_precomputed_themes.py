import json
import logging
from backend.analysis.pipeline import AnalysisPipeline

logging.basicConfig(level=logging.INFO)

def main():
    print("Running AnalysisPipeline to update precomputed_stats.json...")
    pipeline = AnalysisPipeline(data_dir="./data")
    stats = pipeline.run()
    print("Precomputed stats updated successfully!")
    
    # Audit precomputed_stats.json themes output
    with open("data/precomputed_stats.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        
    themes_b = data.get("themes", {}).get("layer_b_emergent_clusters", [])
    residual = data.get("themes", {}).get("residual_disclosure", {})
    
    print("\n=== UPDATED LAYER B THEME CLUSTERS ===")
    all_quotes = []
    for c in themes_b:
        print(f"[{c['cluster_id']}] {c['title']} | Count: {c['count']} ({c['share_pct']}%)")
        quotes = c.get("example_quotes", [])
        print(f"  Quotes count: {len(quotes)}")
        for q in quotes:
            all_quotes.append(q["quote"])
            print(f"    - ({q['source']}) \"{q['quote'][:75]}...\"")
            
    dup_quotes = len(all_quotes) - len(set(all_quotes))
    print(f"\nTotal Quotes across all clusters: {len(all_quotes)}")
    print(f"Duplicate quotes count across clusters: {dup_quotes} (Target: 0)")
    print(f"Residual disclosure: {residual}")

if __name__ == "__main__":
    main()
