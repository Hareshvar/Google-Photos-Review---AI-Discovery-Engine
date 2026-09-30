import json

tags_jsonl = []
with open('data/tags.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip():
            tags_jsonl.append(json.loads(line.strip()))

non_demo = [r for r in tags_jsonl if r.get('tagger') != 'demo-labels']

tagged_posts = json.load(open('data/tagged_posts.json', 'r', encoding='utf-8'))
tagged_posts_map = {p['post_id']: p for p in tagged_posts}

retag_v2 = json.load(open('data/retag_sample_v2.json', 'r', encoding='utf-8'))
retag_v2_pids = {r['post_id'] for r in retag_v2}

seen = set()
step1_candidates = []
for r in non_demo:
    pid = r['post_id']
    if pid in tagged_posts_map and pid not in retag_v2_pids and pid not in seen:
        seen.add(pid)
        step1_candidates.append(r)

# 1. Inspect job values
job_values = set()
for r in step1_candidates:
    tags = r.get('tags', {})
    job_values.add(tags.get('job'))
print(f"Distinct 'job' values in 1,364 candidates: {job_values}")

# 2. Inspect search_tool values
st_values = set()
gemini_st_posts = []
for r in step1_candidates:
    tags = r.get('tags', {})
    st = tags.get('search_tool')
    st_values.add(st)
    if st == 'gemini':
        p = tagged_posts_map.get(r['post_id'], {})
        gemini_st_posts.append((r['post_id'], p.get('title',''), p.get('raw_text','')))

print(f"Distinct 'search_tool' values in 1,364 candidates: {st_values}")
print(f"Count of search_tool == 'gemini': {len(gemini_st_posts)}")
for pid, title, text in gemini_st_posts[:10]:
    print(f"\n--- Gemini search_tool post: {pid} ---")
    print(f"Title: {title}")
    print(f"Text: {text[:200]}...")

# 3. Inspect all taxonomy keys present in tags.jsonl candidates
all_keys = set()
for r in step1_candidates:
    tags = r.get('tags', {})
    all_keys.update(tags.keys())

print(f"\nTaxonomy keys in tags.jsonl: {all_keys}")

# Let's inspect values of failure_step, memory_break, outcome, severity, vague_memory, target_type, primary_cue
check_fields = ['relevant', 'vague_memory', 'target_type', 'primary_cue', 'failure_step', 'memory_break', 'outcome', 'severity']
for fld in check_fields:
    vals = set()
    for r in step1_candidates:
        tags = r.get('tags', {})
        vals.add(str(tags.get(fld)))
    print(f"Values for field '{fld}': {vals}")
