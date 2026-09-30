"""
Situations Matrix and Opportunity Score Calculation Engine
Groups posts by target_type x primary_cue x job, assigns human scenario titles,
computes Opportunity Scores, and handles small-sample n < 10 tail aggregation.
"""

import logging
from collections import Counter
from typing import List, Dict, Any, Tuple
from backend.models.taxonomy import TaggedPostRecord

logger = logging.getLogger(__name__)

# Human readable dictionaries for target_type, primary_cue, and job
HUMAN_TARGETS = {
    "document_info": "Document / Receipt",
    "specific_event": "Specific Event",
    "person_pet": "Person / Pet Photo",
    "place_trip": "Place / Trip Photo",
    "object_item": "Specific Object / Item",
    "date_time": "Timed Photo",
    "general_old_photo": "General Old Memory",
    "other": "General Media"
}

HUMAN_CUES = {
    "date_time": "Remembered Date/Time",
    "location_place": "Remembered Location",
    "person_face": "Remembered Person/Face",
    "text_ocr": "Remembered Text in Photo",
    "visual_object": "Remembered Visual Object",
    "album_folder": "Remembered Album Name",
    "event_context": "Remembered Event Context",
    "file_metadata": "Remembered File Details",
    "none": "No Specific Clue"
}

HUMAN_JOBS = {
    "proof_documentation": "Proof / Documentation",
    "reminiscing": "Reminiscing",
    "sharing_social": "Sharing with Others",
    "practical_utility": "Practical Utility",
    "unknown": "General Need"
}

# Dedicated Human Product Scenario Titles for specific (target, cue, job) composite tuples
SITUATION_TITLE_MAP: Dict[Tuple[str, str, str], str] = {
    ("other", "none", "reminiscing"): "Browsing General Media to Reminisce",
    ("document_info", "none", "proof_documentation"): "Locating Utility Receipts & Documents for Proof",
    ("document_info", "date_time", "proof_documentation"): "Retrieving Dated Invoices & Financial Proof",
    ("person_pet", "person_face", "reminiscing"): "Finding Family & Pet Photos by Face Recognition",
    ("document_info", "person_face", "proof_documentation"): "Finding ID Cards & Documents Tagged with Faces",
    ("date_time", "date_time", "reminiscing"): "Navigating Past Memories by Specific Date & Year",
    ("document_info", "location_place", "proof_documentation"): "Locating Location-Specific Receipts & Contracts",
    ("person_pet", "none", "reminiscing"): "Searching Untagged People & Pet Memories",
    ("document_info", "text_ocr", "proof_documentation"): "Extracting Embedded Text from Screenshots & Bills",
    ("person_pet", "date_time", "reminiscing"): "Locating Photos of Loved Ones by Specific Year",
    ("place_trip", "location_place", "reminiscing"): "Searching Vacation & Travel Photos by Location",
    ("specific_event", "event_context", "sharing_social"): "Retrieving Celebration & Event Photos for Sharing",
    ("object_item", "text_ocr", "practical_utility"): "Finding Product Labels & serial Numbers by Text",
    ("general_old_photo", "date_time", "reminiscing"): "Retrieving Legacy Family Memories by Date",
    ("place_trip", "none", "reminiscing"): "Browsing Travel Memories Without Location Pins",
    ("object_item", "visual_object", "practical_utility"): "Locating Physical Belongings by Visual Appearance",
    ("document_info", "album_folder", "proof_documentation"): "Searching Document Scans Inside Albums",
    ("specific_event", "date_time", "sharing_social"): "Finding Anniversary & Holiday Photos by Year",
}

SEVERITY_WEIGHTS = {"low": 1.0, "medium": 2.0, "high": 3.0}


import re

TARGET_KEYWORDS = {
    "document_info": ["receipt", "document", "invoice", "bill", "pdf", "tax", "proof", "bank", "ticket", "statement", "screenshot", "ocr", "text", "scan", "id", "card", "passport", "utility", "record", "paper", "w2", "license", "form"],
    "person_pet": ["face", "person", "people", "baby", "kid", "son", "daughter", "mom", "dad", "wife", "husband", "friend", "dog", "cat", "pet", "facial", "tag", "family", "selfie", "child", "brother", "sister", "who", "girl", "boy"],
    "place_trip": ["trip", "travel", "vacation", "beach", "city", "hotel", "place", "location", "map", "country", "flight", "park", "tour", "visit", "mountain", "lake", "paris", "rome", "japan", "spain", "hawaii"],
    "object_item": ["car", "bike", "shoe", "watch", "serial", "label", "object", "item", "product", "plant", "flower", "device", "model", "wine", "book", "shirt"],
    "date_time": ["date", "year", "month", "timeline", "2020", "2021", "2022", "2023", "2024", "2025", "2019", "2018", "ago", "old", "calendar", "day", "chronological", "timestamp", "years"],
    "specific_event": ["wedding", "party", "birthday", "concert", "christmas", "event", "graduation", "holiday", "anniversary", "festival", "ceremony"],
    "general_old_photo": ["old photo", "memory", "nostalgic", "throwback", "old picture", "years ago", "legacy", "childhood", "growing up"],
    "other": ["photo", "image", "picture", "media", "video", "gallery", "album", "search", "find", "looking for"]
}

JOB_KEYWORDS = {
    "proof_documentation": ["receipt", "document", "proof", "bill", "invoice", "tax", "show", "claim", "check", "reference", "verify", "court", "lawyer", "police"],
    "reminiscing": ["memory", "reminisce", "old", "look back", "nostalgic", "remember", "memory lane", "scroll back", "miss", "past", "feeling nostalgic"],
    "sharing_social": ["share", "send", "post", "social", "family", "friend", "export", "forward", "group"],
    "practical_utility": ["find", "utility", "practical", "copy", "text", "serial", "link", "info", "use", "work"],
    "unknown": []
}

CUE_KEYWORDS = {
    "date_time": ["date", "year", "month", "timestamp", "202", "201", "ago", "day", "time"],
    "location_place": ["location", "place", "city", "map", "where", "gps", "spot"],
    "person_face": ["face", "person", "who", "people", "name", "tag", "facial"],
    "text_ocr": ["text", "ocr", "word", "written", "read", "sign", "label"],
    "visual_object": ["object", "color", "red", "blue", "looking like", "thing"],
    "album_folder": ["album", "folder", "directory"],
    "event_context": ["event", "wedding", "party", "trip", "holiday"],
    "file_metadata": ["file", "name", "format", "png", "jpg", "size"],
    "none": []
}

SPAM_OR_UNRELATED_PENALTY_TERMS = [
    "perplexity ai pro", "subscription", "warranty", "limited time offer", "discount", "coupon",
    "threatened me", "whatsapp", "battery drain", "screen burn", "app crash", "update broke",
    "storage full", "pay for storage", "uninstall", "default app", "three finger screenshot"
]

def score_quote_relevance(quote_text: str, title_text: str, target_type: str, primary_cue: str, job: str) -> float:
    text = (quote_text + " " + (title_text or "")).lower()
    score = 0.0

    for term in SPAM_OR_UNRELATED_PENALTY_TERMS:
        if term in text:
            score -= 10.0

    target_kw = TARGET_KEYWORDS.get(target_type, [])
    for kw in target_kw:
        if re.search(r'\b' + re.escape(kw) + r'\b', text):
            score += 3.5

    job_kw = JOB_KEYWORDS.get(job, [])
    for kw in job_kw:
        if re.search(r'\b' + re.escape(kw) + r'\b', text):
            score += 2.5

    cue_kw = CUE_KEYWORDS.get(primary_cue, [])
    for kw in cue_kw:
        if re.search(r'\b' + re.escape(kw) + r'\b', text):
            score += 2.0

    query_phrases = ["find", "search", "looking for", "cant find", "can't find", "how to get", "trying to get", "where is", "show me"]
    for qp in query_phrases:
        if qp in text:
            score += 1.5

    if 25 <= len(quote_text) <= 180:
        score += 1.0

    return score

def select_best_quotes(posts: List[TaggedPostRecord], target_type: str, primary_cue: str, job: str, max_quotes: int = 3) -> List[Dict[str, Any]]:
    candidates = []
    for p in posts:
        tax = p.taxonomy
        quote = tax.quote
        if quote and tax.quote_verified:
            quote_clean = quote.strip()
            title = p.title or ''
            rel_score = score_quote_relevance(quote_clean, title, target_type, primary_cue, job)
            candidates.append({
                "quote": quote_clean,
                "source": p.source or 'unknown',
                "url": p.url or '',
                "post_id": p.post_id,
                "score": rel_score
            })
            
    candidates.sort(key=lambda x: x['score'], reverse=True)

    selected = []
    used_sources = set()

    for c in candidates:
        if c['score'] > 0 and c['source'] not in used_sources:
            selected.append(c)
            used_sources.add(c['source'])
            if len(selected) >= max_quotes:
                break

    if len(selected) < max_quotes:
        selected_ids = {s['post_id'] for s in selected}
        for c in candidates:
            if c['score'] > 0 and c['post_id'] not in selected_ids:
                selected.append(c)
                if len(selected) >= max_quotes:
                    break

    if len(selected) < max_quotes:
        selected_ids = {s['post_id'] for s in selected}
        for c in candidates:
            if c['post_id'] not in selected_ids:
                selected.append(c)
                if len(selected) >= max_quotes:
                    break

    return [{
        "quote": item["quote"],
        "source": item["source"],
        "url": item["url"],
        "post_id": item["post_id"]
    } for item in selected[:max_quotes]]


class SituationsEngine:
    """Computes ranked Situations table with Opportunity Scores."""

    @staticmethod
    def build_situations_matrix(relevant_posts: List[TaggedPostRecord]) -> Dict[str, Any]:
        if not relevant_posts:
            return {"situations": [], "tail_aggregated": None}

        total_relevant = len(relevant_posts)
        groups: Dict[Tuple[str, str, str], List[TaggedPostRecord]] = {}

        for p in relevant_posts:
            key = (p.taxonomy.target_type, p.taxonomy.primary_cue, p.taxonomy.job)
            if key not in groups:
                groups[key] = []
            groups[key].append(p)

        raw_situations: List[Dict[str, Any]] = []
        tail_posts: List[TaggedPostRecord] = []

        for (target_type, primary_cue, job), posts in groups.items():
            count = len(posts)
            if count < 10:  # Aggregate small sample groups into tail row
                tail_posts.extend(posts)
                continue

            share_pct = round((count / total_relevant) * 100, 2)
            
            # Average Severity
            avg_severity = sum(SEVERITY_WEIGHTS.get(p.taxonomy.severity, 1.0) for p in posts) / count
            
            # Unresolved Rate
            unresolved_count = sum(
                1 for p in posts 
                if p.taxonomy.outcome == "not_found" or "gave_up" in p.taxonomy.workarounds
            )
            unresolved_rate = round(unresolved_count / count, 2)

            # Most common failure step
            failure_counts = Counter(p.taxonomy.failure_step for p in posts)
            most_common_failure = failure_counts.most_common(1)[0][0] if failure_counts else "no_or_wrong_results"

            # Human readable composition components
            target_h = HUMAN_TARGETS.get(target_type, target_type)
            cue_h = HUMAN_CUES.get(primary_cue, primary_cue)
            job_h = HUMAN_JOBS.get(job, job)

            # Assign Human Situation Title
            key_tuple = (target_type, primary_cue, job)
            title = SITUATION_TITLE_MAP.get(
                key_tuple, 
                f"Retrieving {target_h}, {cue_h} ({job_h})"
            )

            # Human readable composition subtitle
            subtitle = f"Target: {target_h} · Cue: {cue_h} · Job: {job_h}"

            # High Relevance P0 quote selection with P1 Source Diversity tie-breaker
            example_quotes = select_best_quotes(posts, target_type, primary_cue, job)

            raw_score = (share_pct / 100.0) * avg_severity * unresolved_rate

            raw_situations.append({
                "target_type": target_type,
                "primary_cue": primary_cue,
                "job": job,
                "situation_name": title,
                "situation_title": title,
                "situation_label": title,
                "situation_subtitle": subtitle,
                "count": count,
                "share_pct": share_pct,
                "severity": round(avg_severity, 2),
                "unresolved_rate": unresolved_rate,
                "most_common_failure": most_common_failure,
                "example_quotes": example_quotes,
                "raw_score": raw_score
            })

        # Calculate max raw score for 0-100 scaling
        max_raw_score = max((s["raw_score"] for s in raw_situations), default=1.0)
        if max_raw_score == 0:
            max_raw_score = 1.0

        # Assign Opportunity Score (0-100) and Ranks
        for s in raw_situations:
            opp_score = min(100, round((s["raw_score"] / max_raw_score) * 100))
            s["opportunity_score"] = opp_score

        # Sort by opportunity score descending
        raw_situations.sort(key=lambda item: item["opportunity_score"], reverse=True)

        for rank, s in enumerate(raw_situations, 1):
            s["rank"] = rank

        # Tail aggregation row (n < 10)
        tail_aggregated = None
        if tail_posts:
            tail_count = len(tail_posts)
            tail_share = round((tail_count / total_relevant) * 100, 2)
            tail_aggregated = {
                "label": "Other (fewer than 10 posts)",
                "situation_title": "Other (fewer than 10 posts)",
                "situation_subtitle": "Aggregated small sample retrieval situations",
                "count": tail_count,
                "share_pct": tail_share
            }

        logger.info(f"Built Situations matrix with {len(raw_situations)} distinct situations (n>=10) and tail aggregated count: {len(tail_posts)} posts.")
        return {
            "situations": raw_situations,
            "tail_aggregated": tail_aggregated
        }
