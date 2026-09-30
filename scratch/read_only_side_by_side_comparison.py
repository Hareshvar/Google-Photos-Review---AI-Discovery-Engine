import os
import json
from google import genai
from google.genai import types

# Load environment variables
with open('.env', 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            os.environ[k.strip()] = v.strip()

# Load cleaned posts and tagged posts
with open('./data/cleaned_posts.json', 'r', encoding='utf-8') as f:
    cleaned = json.load(f)

with open('./data/tagged_posts.json', 'r', encoding='utf-8') as f:
    tagged = json.load(f)

tagged_map = {p['post_id']: p for p in tagged}

client = genai.Client(api_key=os.environ.get('GEMINI_API_KEY'))

from backend.tagger.gemini_tagger import SYSTEM_TAXONOMY_PROMPT

# Pick 15 diverse sample posts from cleaned_posts.json
sample_posts = cleaned[:15]

print("=== SIDE-BY-SIDE DIAGNOSTIC: 15 RAW GEMINI 3.6 FLASH RESPONSES VS STORED TAGS ===\n")

raw_matches_stored_count = 0
raw_differed_count = 0

diff_reasons = []

for idx, p in enumerate(sample_posts, 1):
    pid = p['post_id']
    title = p.get('title', '')
    raw_text = p.get('raw_text', '')
    stored = tagged_map.get(pid, {}).get('taxonomy', {})
    
    prompt = f"Title: {title}\nText: {raw_text}".strip()
    
    raw_response = None
    err_str = None
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
            raw_response = json.loads(resp.text)
    except Exception as e:
        err_str = str(e)
    
    print(f"--- SAMPLE {idx}/{len(sample_posts)} (post_id: {pid}) ---")
    print(f"TITLE: {title[:60]}")
    print(f"TEXT: {raw_text[:100]}...")
    
    if err_str:
        print(f"[API ERROR]: {err_str}")
        diff_reasons.append(f"Post {pid}: Gemini API error ({err_str[:60]})")
        continue

    # Compare key fields side-by-side
    keys_to_compare = ['vague_memory', 'target_type', 'primary_cue', 'cues_forgotten', 'memory_break', 'query_styles', 'queries_quoted', 'search_tool', 'outcome', 'severity', 'confidence']
    
    differences = []
    print("\n  FIELD COMPARISON (RAW Gemini 3.6 Flash vs STORED tagged_posts.json):")
    for k in keys_to_compare:
        raw_val = raw_response.get(k) if raw_response else None
        stored_val = stored.get(k)
        match = (raw_val == stored_val)
        status_icon = "MATCH" if match else "DIFFERENT (FALLBACK OVERRODE RAW)"
        if not match:
            differences.append(f"{k}: RAW='{raw_val}' vs STORED='{stored_val}'")
        print(f"    - {k:15s} | RAW GEMINI: {repr(raw_val):30s} | STORED: {repr(stored_val):30s} => {status_icon}")
    
    if len(differences) == 0:
        raw_matches_stored_count += 1
    else:
        raw_differed_count += 1
        diff_reasons.append(f"Post {pid}: {len(differences)} fields differed due to fallback override (e.g. {differences[0]})")

print("\n========================================================")
print(f"SUMMARY OF 15-SAMPLE COMPARISON:")
print(f"  - Total Sampled: {len(sample_posts)}")
print(f"  - Raw Gemini output matched stored output: {raw_matches_stored_count} / {len(sample_posts)}")
print(f"  - Raw Gemini output differed from stored output: {raw_differed_count} / {len(sample_posts)}")
print("========================================================")
