import json
from backend.analysis.cluster_engine import ClusterEngine, THEME_DEFINITIONS
from backend.models.taxonomy import TaggedPostRecord

def main():
    with open("data/final_tagged_dataset_mapped.json", "r", encoding="utf-8") as f:
        raw_data = json.load(f)
    
    posts = [TaggedPostRecord(**p) for p in raw_data]
    relevant = [p for p in posts if p.taxonomy.relevant]
    total_relevant = len(relevant)
    print(f"Total dataset: {len(posts)}, Total relevant: {total_relevant}")
    
    engine = ClusterEngine(n_clusters=5)
    clusters, residual = engine.build_emergent_themes(relevant)
    
    print("\n--- CLUSTER BREAKDOWN ---")
    total_assignments = 0
    for c in clusters:
        print(f"ID: {c['cluster_id']} | Title: '{c['title']}' | Count: {c['count']} ({c['share_pct']}%)")
        total_assignments += c['count']
        
    sum_pct = sum(c['share_pct'] for c in clusters)
    print(f"\nSum of cluster counts: {total_assignments}")
    print(f"Sum of percentages relative to {total_relevant}: {sum_pct:.2f}%")
    
    # Calculate distinct assigned posts and overlap
    all_assigned_ids = set()
    post_cluster_counts = {}
    
    for theme in THEME_DEFINITIONS:
        for p in relevant:
            text_combined = f"{p.title} {p.raw_text}".lower()
            tax = p.taxonomy
            is_match = (
                theme["system_issue_match"] in (tax.system_issues or []) or
                tax.primary_cue == theme["primary_cue_match"] or
                any(term in text_combined for term in theme["terms"])
            )
            if is_match:
                all_assigned_ids.add(p.post_id)
                post_cluster_counts[p.post_id] = post_cluster_counts.get(p.post_id, 0) + 1

    distinct_assigned_count = len(all_assigned_ids)
    unclassified_count = total_relevant - distinct_assigned_count
    
    print("\n--- DISTINCT POST MEMBERSHIP STATS ---")
    print(f"Total Relevant Posts (N): {total_relevant}")
    print(f"Distinct Posts Assigned to >= 1 Cluster: {distinct_assigned_count} / {total_relevant} ({distinct_assigned_count / total_relevant * 100:.2f}%)")
    print(f"Residual / Unclassified Posts (Assigned to NO Cluster): {unclassified_count} / {total_relevant} ({unclassified_count / total_relevant * 100:.2f}%)")
    
    # Distribution of cluster memberships per post
    counts_hist = {}
    for pid, ccount in post_cluster_counts.items():
        counts_hist[ccount] = counts_hist.get(ccount, 0) + 1
    
    print("\n--- BREAKDOWN OF CLUSTERS PER POST ---")
    print(f"0 clusters (unclassified): {unclassified_count}")
    for k in sorted(counts_hist.keys()):
        print(f"{k} cluster(s): {counts_hist[k]} posts")

if __name__ == "__main__":
    main()
