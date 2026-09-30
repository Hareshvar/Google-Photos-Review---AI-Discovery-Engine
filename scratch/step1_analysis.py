import json

tagged_posts = json.load(open('data/tagged_posts.json', 'r', encoding='utf-8'))
tagged_posts_map = {p['post_id']: p for p in tagged_posts}
tagged_posts_pids = set(tagged_posts_map.keys())

retag_v2 = json.load(open('data/retag_sample_v2.json', 'r', encoding='utf-8'))
retag_v2_pids = {r['post_id'] for r in retag_v2}

tags_jsonl = []
with open('data/tags.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip():
            tags_jsonl.append(json.loads(line.strip()))

non_demo = [r for r in tags_jsonl if r.get('tagger') != 'demo-labels']

in_corpus = [r for r in non_demo if r['post_id'] in tagged_posts_pids]
excluded_not_in_corpus = [r for r in non_demo if r['post_id'] not in tagged_posts_pids]
unique_excluded = set(r['post_id'] for r in excluded_not_in_corpus)

seen = set()
step1_candidates = []
for r in in_corpus:
    pid = r['post_id']
    if pid not in retag_v2_pids and pid not in seen:
        seen.add(pid)
        step1_candidates.append(r)

print(f"Total lines in tags.jsonl: {len(tags_jsonl)}")
print(f"Non-demo rows: {len(non_demo)}")
print(f"Unique PIDs in non-demo tags.jsonl: {len(set(r['post_id'] for r in non_demo))}")
print(f"Excluded (not in tagged_posts.json corpus): {len(excluded_not_in_corpus)} rows ({len(unique_excluded)} unique PIDs)")
print(f"Matching corpus: {len(in_corpus)} rows ({len(set(r['post_id'] for r in in_corpus))} unique PIDs)")
print(f"Step 1 usable-unique posts (not in retag_sample_v2.json): {len(step1_candidates)}")
