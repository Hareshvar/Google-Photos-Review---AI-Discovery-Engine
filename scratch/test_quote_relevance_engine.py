import json
import re
from typing import List, Dict, Any

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

    # Penalize spam / off-topic complaints
    for term in SPAM_OR_UNRELATED_PENALTY_TERMS:
        if term in text:
            score -= 10.0

    # Target keywords match
    target_kw = TARGET_KEYWORDS.get(target_type, [])
    for kw in target_kw:
        if re.search(r'\b' + re.escape(kw) + r'\b', text):
            score += 3.5

    # Job keywords match
    job_kw = JOB_KEYWORDS.get(job, [])
    for kw in job_kw:
        if re.search(r'\b' + re.escape(kw) + r'\b', text):
            score += 2.5

    # Cue keywords match
    cue_kw = CUE_KEYWORDS.get(primary_cue, [])
    for kw in cue_kw:
        if re.search(r'\b' + re.escape(kw) + r'\b', text):
            score += 2.0

    # User query phrasing bonus
    query_phrases = ["find", "search", "looking for", "cant find", "can't find", "how to get", "trying to get", "where is", "show me"]
    for qp in query_phrases:
        if qp in text:
            score += 1.5

    # Optimal quote length
    if 25 <= len(quote_text) <= 180:
        score += 1.0

    return score

def select_best_quotes(posts: List[Dict[str, Any]], target_type: str, primary_cue: str, job: str, max_quotes: int = 3) -> List[Dict[str, Any]]:
    candidates = []
    for p in posts:
        tax = p.get('taxonomy', {})
        quote = tax.get('quote')
        if quote and tax.get('quote_verified'):
            quote_clean = quote.strip()
            title = p.get('title', '')
            rel_score = score_quote_relevance(quote_clean, title, target_type, primary_cue, job)
            candidates.append({
                "quote": quote_clean,
                "source": p.get('source', 'unknown'),
                "url": p.get('url', ''),
                "post_id": p.get('post_id'),
                "score": rel_score
            })
            
    candidates.sort(key=lambda x: x['score'], reverse=True)

    selected = []
    used_sources = set()

    # Pass 1: candidates with positive score & distinct source
    for c in candidates:
        if c['score'] > 0 and c['source'] not in used_sources:
            selected.append(c)
            used_sources.add(c['source'])
            if len(selected) >= max_quotes:
                break

    # Pass 2: candidates with positive score even if duplicate source
    if len(selected) < max_quotes:
        selected_ids = {s['post_id'] for s in selected}
        for c in candidates:
            if c['score'] > 0 and c['post_id'] not in selected_ids:
                selected.append(c)
                if len(selected) >= max_quotes:
                    break

    # Pass 3: fallback candidates with highest score if < max_quotes
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
