import json

final_data = json.load(open('data/final_tagged_dataset.json', encoding='utf-8'))
cursor_old = [r for r in final_data if r.get('tag_source') == 'llm_cursor_earlier_run']

old_rel_other_cue = [r for r in cursor_old if r.get('taxonomy', {}).get('primary_cue') == 'other' and r.get('taxonomy', {}).get('relevant') is True]

print(f'Relevant posts in old_unique with primary_cue == "other": {len(old_rel_other_cue)}')
for idx, p in enumerate(old_rel_other_cue, 1):
    title = p.get('title', '')
    raw = p.get('raw_text', '')
    quote = p.get('taxonomy', {}).get('quote', '')
    print(f'\n--- Relevant Cue Sample {idx} (ID: {p["post_id"]}) ---')
    print(f'Title: {title}')
    print(f'Text: {raw[:250]}...')
    print(f'Quote: {quote}')
