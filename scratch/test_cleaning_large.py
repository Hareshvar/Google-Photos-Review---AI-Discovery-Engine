import os
import json
import csv
from typing import List, Dict, Any

from backend.models.schema import UnifiedPostRecord
from backend.ingest.cleaner import DataCleaner

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

raw_records: List[UnifiedPostRecord] = []

# 1. Help Community
if os.path.exists("help_community_V2.csv"):
    with open("help_community_V2.csv", mode="r", encoding="utf-8-sig", errors="replace") as f:
        reader = csv.DictReader(f)
        idx = 0
        for row in reader:
            idx += 1
            raw_text = row.get("text", "").strip()
            title = row.get("title", "").strip()
            url = row.get("url", "").strip()
            date_str = row.get("date", "").strip() or "2024-01-01"
            if not raw_text and not title:
                continue
            raw_records.append(UnifiedPostRecord(
                post_id=f"help_community_{idx}",
                source="help_community",
                url=url if url else None,
                created_at=date_str,
                title=title,
                raw_text=raw_text if raw_text else title,
                author_id=None,
                source_metadata={"kind": row.get("kind", "question")}
            ))

# 2. JSONL files
jsonl_files = [
    ("appstore.jsonl", "app_store"),
    ("reddit.jsonl", "reddit"),
    ("youtube.jsonl", "youtube"),
    ("playstore.jsonl", "play_store")
]

for filename, default_source in jsonl_files:
    filepath = os.path.join(PREVIOUS_DATA_DIR, filename)
    data = load_jsonl(filepath)
    for idx, item in enumerate(data):
        src = item.get("source") or default_source
        if src == "appstore":
            src = "app_store"
        elif src == "playstore":
            src = "play_store"
        elif src == "reddit":
            sub = item.get("subreddit")
            if sub == "GeminiAI":
                src = "reddit_geminiai"
            else:
                src = "reddit_googlephotos"
        
        post_id = item.get("post_id") or f"{src}_{idx}"
        title = item.get("title", "").strip() if item.get("title") else ""
        text = item.get("text", "").strip() if item.get("text") else ""
        date_str = item.get("date", "")[:10] if item.get("date") else "2024-01-01"
        url = item.get("url")

        if not title and not text:
            continue

        raw_records.append(UnifiedPostRecord(
            post_id=post_id,
            source=src,
            url=url,
            created_at=date_str,
            title=title,
            raw_text=text if text else title,
            author_id=None,
            source_metadata={
                "kind": item.get("kind"),
                "rating": item.get("rating"),
                "score": item.get("score"),
                "country": item.get("country"),
                "collector": item.get("collector")
            }
        ))

print(f"Total raw records loaded across all files: {len(raw_records)}")

cleaner = DataCleaner(near_dup_threshold=0.85, min_words=5)
cleaned_records, clean_summary = cleaner.clean_records(raw_records)

print(f"Total cleaned records kept: {len(cleaned_records)}")
for src, rep in clean_summary.per_source_report.items():
    print(f"Source {src}: {rep.total_cleaned} kept out of {rep.total_raw} raw (Exact dups: {rep.exact_duplicates}, Near dups: {rep.near_duplicates}, Prefilter excluded: {rep.prefilter_excluded})")
