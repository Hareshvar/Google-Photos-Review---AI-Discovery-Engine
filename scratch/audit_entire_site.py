import json

with open('./data/precomputed_stats.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("=== ENTIRE SITE DATA INTEGRITY AUDIT ===")

# 1. Metadata check
meta = data.get('metadata', {})
print("\n[1] METADATA & DATASET OVERVIEW CHECK:")
print(f"  Total Tagged Records: {meta.get('total_tagged')}")
print(f"  Total Relevant Records: {meta.get('total_relevant')}")

# 2. Themes check
themes = data.get('themes', {})
layer_a = themes.get('layer_a_struggle_matrix', [])
layer_b = themes.get('layer_b_emergent_clusters', [])
print(f"\n[2] THEMES DATA CHECK:")
print(f"  Layer A Struggle Matrix Cells: {len(layer_a)}")
print(f"  Layer B Emergent Intent Clusters: {len(layer_b)}")

encoding_errors = 0
for idx, cluster in enumerate(layer_b, 1):
    title = cluster.get('title') or cluster.get('theme_title')
    count = cluster.get('count')
    pct = cluster.get('share_pct')
    quotes = cluster.get('example_quotes') or cluster.get('top_quotes') or []
    print(f"  Theme #{idx}: {title} | Count: {count} ({pct}%) | Quotes: {len(quotes)}")
    for q in quotes:
        q_str = q.get('quote', '') if isinstance(q, dict) else str(q)
        if 'â' in q_str:
            encoding_errors += 1
            print(f"    [WARNING] Garbled encoding in quote: {q_str}")

# 3. Situations check
situations = data.get('situations', [])
print(f"\n[3] SITUATIONS DATA CHECK:")
print(f"  Total Ranked Situations: {len(situations)}")
for sit in situations[:6]:
    rank = sit.get('rank')
    title = sit.get('situation') or sit.get('situation_title')
    count = sit.get('count') or sit.get('post_count')
    pct = sit.get('pct') or sit.get('share_pct')
    score = sit.get('opportunity_score')
    print(f"  Rank {rank}: {title} | Count: {count} ({pct}%) | Opp Score: {score}")

# 4. Key Insights check
key_insights = data.get('key_insights', [])
print(f"\n[4] KEY INSIGHTS DATA CHECK (Q1 to Q9):")
print(f"  Total Key Insights items: {len(key_insights)}")
zero_pct_count = 0
empty_quotes_count = 0
missing_title_count = 0

for item in key_insights:
    q_id = item.get('id') or item.get('question_id')
    title = item.get('question_title') or item.get('question_text')
    dist = item.get('distribution', [])
    quotes = item.get('quotes', [])
    
    if not title:
        missing_title_count += 1
    if not quotes:
        empty_quotes_count += 1
    for cat in dist:
        if cat.get('pct') == 0.0:
            zero_pct_count += 1

print(f"  Questions evaluated: {len(key_insights)} / 9")
print(f"  Missing titles count: {missing_title_count}")
print(f"  Empty quotes count: {empty_quotes_count}")
print(f"  Zero percentage categories count: {zero_pct_count}")
print(f"  Garbled encoding errors in themes: {encoding_errors}")

if missing_title_count == 0 and empty_quotes_count == 0 and zero_pct_count == 0 and encoding_errors == 0:
    print("\n>>> ALL DATA CHECKS PASSED PERFECTLY WITH ZERO ISSUES! <<<")
else:
    print("\n>>> DATA AUDIT FOUND ISSUES TO ATTEND TO! <<<")
