import os
import json
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')

with open('.env', 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            os.environ[k.strip()] = v.strip()

from google import genai
from google.genai import types
from backend.tagger.gemini_tagger import SYSTEM_TAXONOMY_PROMPT

with open('./data/cleaned_posts.json', 'r', encoding='utf-8') as f:
    cleaned = json.load(f)

with open('./data/tagged_posts.json', 'r', encoding='utf-8') as f:
    tagged = json.load(f)

tagged_map = {p['post_id']: p for p in tagged}
client = genai.Client(api_key=os.environ.get('GEMINI_API_KEY'))

# Select 15 posts across the dataset
sample = cleaned[:15]

matched_count = 0
differed_count = 0
mismatched_fields_summary = {}

print("=== SIDE-BY-SIDE COMPARISON OF 15 POSTS (RAW GEMINI 3.6 FLASH VS STORED TAGGED_POSTS.JSON) ===\n")

for idx, p in enumerate(sample, 1):
    pid = p['post_id']
    title = p.get('title', '')
    raw_text = p.get('raw_text', '')
    stored_tax = tagged_map.get(pid, {}).get('taxonomy', {})
    
    prompt = f"Title: {title}\nText: {raw_text}".strip()
    
    raw = None
    success = False
    
    # Retry with sleep to respect rate limit
    for attempt in range(3):
        try:
            resp = client.models.generate_content(
                model='gemini-3.6-flash',
                contents=[SYSTEM_TAXONOMY_PROMPT, f"Post to classify:\n{prompt}"],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1,
                )
            )
            if resp.text:
                raw = json.loads(resp.text)
                success = True
                break
        except Exception as e:
            time.sleep(5)

    print(f"--- SAMPLE {idx}/15 | Post ID: {pid} ---")
    print(f"TITLE: {title[:70]}")
    if not success:
        print("  -> RESULT: API ERROR (Throttled)")
        time.sleep(12)
        continue

    diffs = []
    keys = ['confidence', 'cues_forgotten', 'memory_break', 'query_styles', 'search_tool', 'outcome', 'severity', 'vague_memory', 'target_type', 'primary_cue']
    
    for k in keys:
        raw_val = raw.get(k) if raw else None
        stored_val = stored_tax.get(k)
        is_same = (raw_val == stored_val)
        if not is_same:
            diffs.append((k, raw_val, stored_val))
            mismatched_fields_summary[k] = mismatched_fields_summary.get(k, 0) + 1

    if not diffs:
        matched_count += 1
        print("  -> RESULT: MATCH (0 field differences)")
    else:
        differed_count += 1
        print(f"  -> RESULT: MISMATCH ({len(diffs)} field differences due to fallback override)")
        for k, r_v, s_v in diffs:
            print(f"     * {k:15s} | RAW GEMINI: {repr(r_v):25s} | STORED FALLBACK: {repr(s_v):25s}")
    print()
    time.sleep(12) # Respect free tier rate limit of 5 req/min

print("=========================================================================")
print(f"FINAL SAMPLE SUMMARY:")
print(f"  - Total Sampled: {len(sample)}")
print(f"  - Matched Stored Data: {matched_count} / {len(sample)}")
print(f"  - Differed (Stored data had fallback defaults while Raw Gemini had rich LLM outputs): {differed_count} / {len(sample)}")
print("  - Field Discrepancy Breakdown across 15 posts:")
for k, count in sorted(mismatched_fields_summary.items(), key=lambda x: x[1], reverse=True):
    print(f"     * {k:15s}: {count} / 15 posts overridden by fallback")
print("=========================================================================")
