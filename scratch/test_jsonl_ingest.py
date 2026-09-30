import os
import json
import csv
from typing import List, Dict, Any

PREVIOUS_DATA_DIR = "Previous data"

def load_jsonl(filepath: str) -> List[Dict[str, Any]]:
    records = []
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
    return records

appstore_data = load_jsonl(os.path.join(PREVIOUS_DATA_DIR, "appstore.jsonl"))
reddit_data = load_jsonl(os.path.join(PREVIOUS_DATA_DIR, "reddit.jsonl"))
youtube_data = load_jsonl(os.path.join(PREVIOUS_DATA_DIR, "youtube.jsonl"))
playstore_data = load_jsonl(os.path.join(PREVIOUS_DATA_DIR, "playstore.jsonl"))

print(f"App Store records in JSONL: {len(appstore_data)}")
print(f"Reddit records in JSONL: {len(reddit_data)}")
print(f"YouTube records in JSONL: {len(youtube_data)}")
print(f"Play Store records in JSONL: {len(playstore_data)}")

# Subreddit breakdown in reddit_data
subreddits = {}
for r in reddit_data:
    sub = r.get("subreddit") or "other"
    subreddits[sub] = subreddits.get(sub, 0) + 1
print("Reddit subreddits breakdown:", subreddits)
