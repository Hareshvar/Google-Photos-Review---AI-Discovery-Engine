import json

retag_v2 = json.load(open('data/retag_sample_v2.json', 'r', encoding='utf-8'))
v2_taxonomy_sample = retag_v2[0]['taxonomy']
print(f"Taxonomy keys in retag_sample_v2.json: {list(v2_taxonomy_sample.keys())}")

tags_jsonl = []
with open('data/tags.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip():
            tags_jsonl.append(json.loads(line.strip()))

non_demo = [r for r in tags_jsonl if r.get('tagger') != 'demo-labels']
tagged_posts = json.load(open('data/tagged_posts.json', 'r', encoding='utf-8'))
tagged_posts_map = {p['post_id']: p for p in tagged_posts}
retag_v2_pids = {r['post_id'] for r in retag_v2}

seen = set()
candidates = []
for r in non_demo:
    pid = r['post_id']
    if pid in tagged_posts_map and pid not in retag_v2_pids and pid not in seen:
        seen.add(pid)
        candidates.append(r)

# Check all fields in candidates vs retag_v2
# Collect all unique values per field in retag_v2 vs candidates
fields_to_check = ['relevant', 'vague_memory', 'target_type', 'primary_cue', 'failure_step', 'memory_break', 'job', 'search_tool', 'outcome', 'severity']

for fld in fields_to_check:
    v2_vals = set(str(r['taxonomy'].get(fld)) for r in retag_v2)
    cand_vals = set(str(r['tags'].get(fld)) for r in candidates)
    print(f"\n--- Field: {fld} ---")
    print(f"  v2 values:   {sorted(list(v2_vals))}")
    print(f"  cand values: {sorted(list(cand_vals))}")
    diff = cand_vals - v2_vals
    if diff:
        print(f"  --> MISMATCH / Extra in candidates: {diff}")

# Check query_styles, workarounds, system_issues lists
for list_fld in ['query_styles', 'workarounds', 'system_issues']:
    v2_items = set()
    for r in retag_v2:
        for item in r['taxonomy'].get(list_fld, []):
            v2_items.add(item)
    cand_items = set()
    for r in candidates:
        for item in r['tags'].get(list_fld, []):
            cand_items.add(item)
    print(f"\n--- List Field: {list_fld} ---")
    print(f"  v2 items:   {sorted(list(v2_items))}")
    print(f"  cand items: {sorted(list(cand_items))}")
    diff = cand_items - v2_items
    if diff:
        print(f"  --> MISMATCH / Extra in candidates: {diff}")
