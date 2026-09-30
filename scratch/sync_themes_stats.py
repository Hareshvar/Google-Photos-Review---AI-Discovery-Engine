import json
from backend.models.taxonomy import TaggedPostRecord
from backend.analysis.cluster_engine import ClusterEngine

def update_stats_themes():
    with open("data/final_tagged_dataset_mapped.json", "r", encoding="utf-8") as f:
        raw_data = json.load(f)
    posts = [TaggedPostRecord(**p) for p in raw_data if p.get("taxonomy", {}).get("relevant", False)]
    
    engine = ClusterEngine(n_clusters=5)
    clusters, residual = engine.build_emergent_themes(posts)
    
    with open("data/precomputed_stats.json", "r", encoding="utf-8") as f:
        stats = json.load(f)
        
    stats["themes"]["layer_b_emergent_clusters"] = clusters
    stats["themes"]["residual_disclosure"] = residual
    
    with open("data/precomputed_stats.json", "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)
        
    print("Updated precomputed_stats.json themes section successfully!")

if __name__ == "__main__":
    update_stats_themes()
