import json

with open('data/precomputed_stats.json', encoding='utf-8') as f:
    stats = json.load(f)

cards = stats.get('key_insights', [])
output_lines = [f"Total Key Insight Cards: {len(cards)}"]

for c in cards:
    output_lines.append(f"\n==========================================")
    output_lines.append(f"Q{c.get('number')}: {c.get('question')}")
    output_lines.append(f"SUMMARY: {c.get('summary')}")
    output_lines.append("QUOTES:")
    for q in c.get('example_quotes', []):
        output_lines.append(f"  • [{q.get('source')}] \"{q.get('quote')}\"")

with open('scratch/inspected_insights_output.txt', 'w', encoding='utf-8') as f:
    f.write("\n".join(output_lines))

print("Successfully wrote scratch/inspected_insights_output.txt")
