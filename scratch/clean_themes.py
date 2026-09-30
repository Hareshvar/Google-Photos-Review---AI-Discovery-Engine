import json

def clean_text(t):
    if not t:
        return ""
    replacements = {
        "â€œ": '"',
        "â€": '"',
        "â€™": "'",
        "â€˜": "'",
        "â€”": "—",
        "â€“": "–",
        "â€¦": "...",
        "â€¢": "•",
        "âpets and peopleâ": '"pets and people"',
        "âpets": '"pets',
        "peopleâ": 'people"',
        "doesnât": "doesn't",
        "â": "",
        "Ã©": "é",
    }
    for bad, good in replacements.items():
        t = t.replace(bad, good)
    return t.strip()

with open('./data/precomputed_stats.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

clusters = data.get('themes', {}).get('layer_b_emergent_clusters', [])
print(f"Loaded {len(clusters)} clusters")

for idx, c in enumerate(clusters, 1):
    print(f"\nCluster {idx}: {c.get('title')} (Count: {c.get('count')})")
    for q in c.get('example_quotes', []):
        old_q = q.get('quote', '')
        new_q = clean_text(old_q)
        q['quote'] = new_q
        print(f"  [{q.get('source')}] {repr(new_q)}")
    for q in c.get('top_quotes', []):
        old_q = q.get('quote', '')
        new_q = clean_text(old_q)
        q['quote'] = new_q

with open('./data/precomputed_stats.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2)

print("\nSuccessfully cleaned precomputed_stats.json!")
