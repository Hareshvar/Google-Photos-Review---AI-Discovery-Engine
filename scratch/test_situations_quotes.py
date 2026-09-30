import json

with open('data/precomputed_stats.json', encoding='utf-8') as f:
    stats = json.load(f)

sits_data = stats.get('situations', [])
if isinstance(sits_data, dict):
    sits = sits_data.get('situations', [])
else:
    sits = sits_data

print(f"Total situations: {len(sits)}")

for s in sits[:8]:
    print(f"\n--- Rank #{s.get('rank')}: {s.get('situation_title')} ---")
    print(f"Subtitle: {s.get('situation_subtitle')}")
    print(f"Count: {s.get('count')}, Share: {s.get('share_pct')}%, Severity: {s.get('severity')}, Unresolved %: {s.get('unresolved_rate')*100:.1f}%, Opp Score: {s.get('opportunity_score')}")
    print("Quotes:")
    for q in s.get('example_quotes', []):
        print(f"  • \"{q['quote']}\" [{q['source']}]")
