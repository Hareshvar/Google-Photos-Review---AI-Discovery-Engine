import json
import random

final_data = json.load(open('data/final_tagged_dataset.json', encoding='utf-8'))

gemini_groq = [r for r in final_data if r.get('tag_source') == 'llm_gemini_groq']
cursor_old = [r for r in final_data if r.get('tag_source') == 'llm_cursor_earlier_run']

gg_rel = sum(1 for r in gemini_groq if r.get('taxonomy', {}).get('relevant') is True)
co_rel = sum(1 for r in cursor_old if r.get('taxonomy', {}).get('relevant') is True)

print('=== STEP 1.1 RELEVANCE CALIBRATION RATES ===')
print(f'llm_gemini_groq total: {len(gemini_groq)}')
print(f'  - Relevant=true: {gg_rel} ({gg_rel / len(gemini_groq) * 100:.2f}%)')
print(f'llm_cursor_earlier_run total: {len(cursor_old)}')
print(f'  - Relevant=true: {co_rel} ({co_rel / len(cursor_old) * 100:.2f}%)')

# 15 random relevant=true, target_type='other' from llm_gemini_groq
gg_rel_other = [r for r in gemini_groq if r.get('taxonomy', {}).get('relevant') is True and r.get('taxonomy', {}).get('target_type') == 'other']
print(f'\nTotal relevant=true, target_type="other" in llm_gemini_groq: {len(gg_rel_other)}')

rng = random.Random(42)
sampled_15 = rng.sample(gg_rel_other, min(15, len(gg_rel_other)))

print('\n=== STEP 1.2 15 SAMPLE POSTS (llm_gemini_groq, relevant=true, target_type="other") ===')
for idx, p in enumerate(sampled_15, 1):
    title = p.get('title', '')
    raw = p.get('raw_text', '')
    quote = p.get('taxonomy', {}).get('quote', 'N/A')
    print(f'\n--- Sample {idx} (ID: {p["post_id"]}, Source: {p.get("source")}) ---')
    print(f'Title: {title}')
    print(f'Text: {raw[:300]}...')
    print(f'Quote: {quote}')

# STEP 2 Investigation: 10 sample raw_text + quote pairs from old_unique where primary_cue == "other"
old_other_cue = [r for r in cursor_old if r.get('taxonomy', {}).get('primary_cue') == 'other']
print(f'\n=== STEP 2.3 INVESTIGATION: primary_cue="other" in old_unique (Total: {len(old_other_cue)}) ===')
sampled_10_cue = rng.sample(old_other_cue, min(10, len(old_other_cue)))
for idx, p in enumerate(sampled_10_cue, 1):
    title = p.get('title', '')
    raw = p.get('raw_text', '')
    quote = p.get('taxonomy', {}).get('quote', 'N/A')
    rel = p.get('taxonomy', {}).get('relevant')
    print(f'\n--- Cue Sample {idx} (ID: {p["post_id"]}, Relevant: {rel}) ---')
    print(f'Title: {title}')
    print(f'Text: {raw[:250]}...')
    print(f'Quote: {quote}')
