import json
from collections import Counter

with open('./data/tagged_posts.json', 'r', encoding='utf-8') as f:
    tagged_posts = json.load(f)

with open('./data/precomputed_stats.json', 'r', encoding='utf-8') as f:
    precomputed = json.load(f)

total_posts = len(tagged_posts)
print(f"=== AUDIT OF DATASET (Total Posts: {total_posts}) ===")

# 1. Themes Layer A Audit
print("\n--- 1. THEMES SECTION A (Layer A Struggle Matrix) ---")
crosstab = Counter()
for p in tagged_posts:
    step = p.get('taxonomy', {}).get('failure_step', 'no_failure')
    issues = p.get('taxonomy', {}).get('system_issues') or ['missing_results']
    for sys_issue in issues:
        crosstab[(step, sys_issue)] += 1

print(f"Top 5 Layer A Matrix Cells (out of {len(crosstab)}):")
for (step, issue), cnt in crosstab.most_common(5):
    pct = round((cnt / total_posts) * 100, 2)
    print(f"  Step: {step:<25} | Issue: {issue:<25} | Count: {cnt:<5} | Share: {pct}%")

# 2. Themes Layer B Audit
print("\n--- 2. THEMES SECTION B (Layer B Emergent Intent Clusters) ---")
layer_b = precomputed.get('themes', {}).get('layer_b_emergent_clusters', [])
for idx, c in enumerate(layer_b, 1):
    print(f"  Rank {idx}: {c.get('title')} | Count: {c.get('count')} | Share: {c.get('share_pct')}%")
    for q in c.get('example_quotes', []):
        quote_text = q.get('quote') if isinstance(q, dict) else q
        source = q.get('source') if isinstance(q, dict) else 'unknown'
        print(f"     - [{source}] {quote_text[:90]}")

# 3. Situations Audit
print("\n--- 3. SITUATIONS & OPPORTUNITY SCORES ---")
situations = precomputed.get('situations', [])
print(f"Total Ranked Situations: {len(situations)}")
for idx, s in enumerate(situations[:6], 1):
    sit_id = s.get('situation_id', f'sit_{idx}')
    t_text = str(s.get('title') or s.get('context_name') or 'Situation')
    count = s.get('count', 0)
    pct = s.get('share_pct', 0.0)
    sev = s.get('avg_severity', 0.0)
    unres = s.get('unresolved_rate', 0.0)
    opp = s.get('opportunity_score', 0.0)
    print(f"  Rank {idx}: [{sit_id}] {t_text[:35]:<35} | Count: {count:<4} | Share: {pct}% | Sev: {sev} | Unres: {unres} | Opp: {opp}")

# 4. Key Insights Audit (Q1 to Q9)
print("\n--- 4. KEY INSIGHTS (9 Questions Audit) ---")
insights = precomputed.get('key_insights', [])
print(f"Total Key Insights Questions: {len(insights)}")
for q in insights:
    q_id = q.get('question_id')
    q_text = q.get('question_text')
    dist = q.get('distribution', [])
    quotes = q.get('quotes', [])
    summary = q.get('summary', '')
    print(f"\n  [{q_id}] {q_text}")
    print(f"      Distribution items: {len(dist)}")
    for d in dist[:3]:
        lbl = d.get('category') or d.get('label') or d.get('name') or 'Item'
        cnt_val = d.get('count', 0)
        pct_val = d.get('pct', 0.0)
        print(f"        - {lbl}: {cnt_val} ({pct_val}%)")
    print(f"      Quotes count: {len(quotes)}")
    for q_item in quotes[:2]:
        q_str = q_item.get('quote') if isinstance(q_item, dict) else q_item
        print(f"        * {str(q_str)[:80]}")
    print(f"      Summary snippet: {str(summary)[:100]}...")
