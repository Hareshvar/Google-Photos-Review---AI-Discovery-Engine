import json

records = json.load(open('data/tag_data_old_unique.json', 'r', encoding='utf-8'))
total = len(records)

print(f"--- STEP 1 FIELD DISTRIBUTIONS (Total = {total}) ---")

# Relevant distribution
rel_counts = {}
for r in records:
    val = r['taxonomy'].get('relevant')
    rel_counts[val] = rel_counts.get(val, 0) + 1

print("\nRelevant:")
for val, count in sorted(rel_counts.items(), key=lambda x: str(x[0])):
    pct = (count / total) * 100
    print(f"  - {val}: {count} ({pct:.1f}%)")

# Job distribution
job_counts = {}
for r in records:
    val = r['taxonomy'].get('job')
    job_counts[val] = job_counts.get(val, 0) + 1

print("\nJob:")
for val, count in sorted(job_counts.items(), key=lambda x: x[1], reverse=True):
    pct = (count / total) * 100
    print(f"  - {val}: {count} ({pct:.1f}%)")

# Failure Step distribution
fs_counts = {}
for r in records:
    val = r['taxonomy'].get('failure_step')
    fs_counts[val] = fs_counts.get(val, 0) + 1

print("\nFailure Step:")
for val, count in sorted(fs_counts.items(), key=lambda x: x[1], reverse=True):
    pct = (count / total) * 100
    print(f"  - {val}: {count} ({pct:.1f}%)")
