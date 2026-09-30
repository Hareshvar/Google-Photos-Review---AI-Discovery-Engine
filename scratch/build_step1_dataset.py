import json

tagged_posts = json.load(open('data/tagged_posts.json', 'r', encoding='utf-8'))
tagged_posts_map = {p['post_id']: p for p in tagged_posts}

retag_v2 = json.load(open('data/retag_sample_v2.json', 'r', encoding='utf-8'))
retag_v2_pids = {r['post_id'] for r in retag_v2}

tags_jsonl = []
with open('data/tags.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip():
            tags_jsonl.append(json.loads(line.strip()))

non_demo = [r for r in tags_jsonl if r.get('tagger') != 'demo-labels']

# 1. Filter usable-unique candidates
seen = set()
step1_records = []

# Mappings specified by user for job & search_tool
JOB_MAP = {
    "reuse_information": "practical_utility",
    "reminisce": "reminiscing",
    "prove_or_reference": "proof_documentation",
    "share": "sharing_social",
    "create": "create",
    "unspecified": "unknown"
}

SEARCH_TOOL_MAP = {
    "classic": "classic_search",
    "other_app": "other_app",
    "unspecified": "search_tab"
}

# Ambiguous Gemini search_tool post: reddit_1lqf8wd (General Gemini prompt, not photo search)
GEMINI_PHOTO_SEARCH_PIDS = {
    "reddit_1w55t8o",
    "appstore_us_14416246518",
    "playstore_a063c498-e373-40ef-8576-598daab29f0d",
    "playstore_56b98d58-f989-4991-bfeb-3e25738a4b89"
}

flagged_ambiguous = []

for item in non_demo:
    pid = item['post_id']
    if pid in tagged_posts_map and pid not in retag_v2_pids and pid not in seen:
        seen.add(pid)
        p = tagged_posts_map[pid]
        orig_tags = dict(item.get('tags', {}))
        
        # Apply job mapping
        orig_job = orig_tags.get('job', 'unspecified')
        mapped_job = JOB_MAP.get(orig_job, orig_job)
        orig_tags['job'] = mapped_job

        # Apply search_tool mapping
        orig_st = orig_tags.get('search_tool', 'unspecified')
        if orig_st == 'gemini':
            if pid in GEMINI_PHOTO_SEARCH_PIDS:
                mapped_st = 'ask_photos'
            else:
                mapped_st = 'search_tab' # Flagged as general Gemini chat
                flagged_ambiguous.append((pid, p.get('title',''), p.get('raw_text','')))
        else:
            mapped_st = SEARCH_TOOL_MAP.get(orig_st, orig_st)
        orig_tags['search_tool'] = mapped_st

        record = {
            "post_id": p["post_id"],
            "source": p["source"],
            "url": p.get("url"),
            "created_at": p.get("created_at"),
            "title": p.get("title", ""),
            "raw_text": p.get("raw_text", ""),
            "author_id": p.get("author_id"),
            "source_metadata": p.get("source_metadata"),
            "priority_score": 0, # Not sample prioritized
            "sample_bucket": "cursor_import",
            "tag_source": "cursor_reused",
            "fallback_reason": None,
            "taxonomy": orig_tags
        }
        step1_records.append(record)

print(f"Total Step 1 usable-unique records prepared: {len(step1_records)}")
print(f"Flagged ambiguous search_tool=='gemini' posts: {len(flagged_ambiguous)}")

output_path = "data/tag_data_old_unique.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(step1_records, f, indent=2, ensure_ascii=False)

print(f"Successfully wrote {len(step1_records)} records to {output_path}")
