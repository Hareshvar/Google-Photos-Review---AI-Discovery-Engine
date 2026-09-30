import json

precomputed = json.load(open("data/precomputed_stats.json", "r", encoding="utf-8"))

print("Keys in precomputed_stats.json:", list(precomputed.keys()))
print("Metadata in precomputed_stats.json:", precomputed.get("metadata"))

# Check if precomputed stats has failure_step or key_insights Q9 or overall breakdown
for k in precomputed.get("key_insights", []):
    print(f"Q{k.get('number')}: {k.get('question')} | n={k.get('n_sample')}")
    if k.get('number') == 9 or 'failure_step' in str(k):
        print("  Distribution:", k.get('distribution'))
