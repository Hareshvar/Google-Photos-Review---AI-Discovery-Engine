import json

with open('data/tagged_posts.json', encoding='utf-8') as f:
    posts = json.load(f)

context_posts = []
for p in posts:
    cues = p.get('taxonomy', {}).get('cues_remembered', [])
    if 'context' in cues or 'event_context' in cues:
        context_posts.append(p)

print(f"Total posts with 'context' or 'event_context' in cues_remembered: {len(context_posts)}")

print("\nSample posts in 'context' bucket:")
for i, p in enumerate(context_posts[:15], 1):
    tax = p.get('taxonomy', {})
    quote = tax.get('quote') or p.get('title')
    print(f"{i}. [{p.get('source')}] \"{quote}\"")
    print(f"   Target: {tax.get('target_type')}, Cues: {tax.get('cues_remembered')}, Job: {tax.get('job')}\n")
