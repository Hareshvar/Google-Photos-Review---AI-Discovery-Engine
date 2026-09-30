import os
import json
from backend.models.taxonomy import TaggedPostRecord
from backend.analysis.situations_engine import SituationsEngine, HUMAN_TARGETS, HUMAN_CUES, HUMAN_JOBS, SITUATION_TITLE_MAP

# Load dataset
mapped_tagged_path = "./data/final_tagged_dataset_mapped.json"
posts_data = json.load(open(mapped_tagged_path, "r", encoding="utf-8"))

rel_posts = [
    TaggedPostRecord(**p) for p in posts_data
    if (p.get("taxonomy", {}).get("relevant") is True or p.get("relevant") is True)
]

# Simulate updated SituationsEngine fallback title formula
groups = {}
for p in rel_posts:
    key = (p.taxonomy.target_type, p.taxonomy.primary_cue, p.taxonomy.job)
    if key not in groups:
        groups[key] = []
    groups[key].append(p)

raw_situations = []
tail_posts = []

for (target_type, primary_cue, job), posts in groups.items():
    count = len(posts)
    if count < 10:
        tail_posts.extend(posts)
        continue

    target_h = HUMAN_TARGETS.get(target_type, target_type)
    cue_h = HUMAN_CUES.get(primary_cue, primary_cue)
    job_h = HUMAN_JOBS.get(job, job)

    key_tuple = (target_type, primary_cue, job)
    title = SITUATION_TITLE_MAP.get(
        key_tuple, 
        f"Retrieving {target_h}, {cue_h} ({job_h})"
    )

    share_pct = round((count / len(rel_posts)) * 100, 2)
    avg_severity = sum(1.0 if p.taxonomy.severity == "low" else (2.0 if p.taxonomy.severity == "medium" else 3.0) for p in posts) / count
    unresolved_count = sum(1 for p in posts if p.taxonomy.outcome == "not_found" or "gave_up" in p.taxonomy.workarounds)
    unresolved_rate = round(unresolved_count / count, 2)
    raw_score = (share_pct / 100.0) * avg_severity * unresolved_rate

    raw_situations.append({
        "target_type": target_type,
        "primary_cue": primary_cue,
        "job": job,
        "situation_title": title,
        "count": count,
        "raw_score": raw_score
    })

max_raw_score = max(s["raw_score"] for s in raw_situations)
for s in raw_situations:
    s["opportunity_score"] = min(100, round((s["raw_score"] / max_raw_score) * 100))

raw_situations.sort(key=lambda item: item["opportunity_score"], reverse=True)

print("--- PROPOSED SITUATION TITLES (RANK 1..N) ---")
all_titles = []
for rank, s in enumerate(raw_situations, 1):
    all_titles.append(s["situation_title"])
    print(f"Rank #{rank:2d}: n={s['count']:3d} | {s['situation_title']}")

tail_title = "Other (fewer than 10 posts)"
all_titles.append(tail_title)
print(f"Tail Aggregated: n={len(tail_posts):3d} | {tail_title}")

print("\n--- UNIQUE CHECK ---")
print(f"Total rows: {len(all_titles)}")
print(f"Unique titles: {len(set(all_titles))}")
if len(all_titles) == len(set(all_titles)):
    print("SUCCESS! Every title is 100% unique!")
else:
    print("WARNING: Duplicates remain!")
