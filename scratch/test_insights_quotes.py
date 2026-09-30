import json
import re
from typing import List, Dict, Any

def clean_mojibake(text: str) -> str:
    if not text:
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
        "â": "",
        "Ã©": "é",
    }
    for bad, good in replacements.items():
        text = text.replace(bad, good)
    return re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text).strip()

QUESTION_KEYWORDS = {
    "q1": ["receipt", "document", "invoice", "bill", "pdf", "tax", "ticket", "passport", "license", "screenshot", "face", "person", "baby", "pet", "dog", "cat", "trip", "travel", "vacation", "beach", "car", "bike", "event", "wedding", "party", "old photo", "memory"],
    "q2": ["remember", "remembered", "date", "year", "month", "location", "place", "city", "where", "face", "person", "who", "text", "ocr", "word", "album", "folder", "event", "wedding", "trip"],
    "q3": ["forgot", "forget", "forgotten", "don't know", "don't remember", "can't remember", "no date", "no location", "missing date", "exact date", "timestamp", "year", "when", "where", "who", "exif", "time"],
    "q4": ["search", "typed", "searched for", "query", "trying to search", "looking for", "natural language", "keywords", "exact quote", "quotes", "ask photos"],
    "q5": ["words", "describe", "how to search", "express", "put into words", "can't explain", "how to find", "search for"],
    "q6": ["search not working", "wrong results", "no results", "ocr failed", "face recognition", "face search", "date index", "hallucinated", "incorrect", "returns nothing", "cant find"],
    "q7": ["thumbnail", "preview", "recognize", "small", "blur", "can't tell", "difficult to see", "which photo", "wrong photo opened", "bounce", "opened"],
    "q8": ["scroll", "scrolling", "timeline", "manual", "gave up", "switched", "gallery", "other app", "drive", "takeout", "folder", "browse"],
    "q9": ["did not search", "search bar", "no results", "wrong results", "scroll timeline", "gave up", "bounce", "ctr", "photo opened"]
}

def extract_insights_quotes(posts: List[Dict[str, Any]], q_id: str, max_quotes: int = 3) -> List[Dict[str, str]]:
    keywords = QUESTION_KEYWORDS.get(q_id, [])
    candidates = []

    for p in posts:
        tax = p.get('taxonomy', {})
        quote = tax.get('quote') or p.get('title')
        if not quote or not tax.get('quote_verified', True):
            continue

        clean_q = clean_mojibake(quote)
        if len(clean_q) < 15 or len(clean_q) > 220:
            continue

        text_lower = (clean_q + " " + (p.get('title') or '')).lower()
        
        # Calculate relevance score
        score = 0.0
        for kw in keywords:
            if re.search(r'\b' + re.escape(kw) + r'\b', text_lower):
                score += 3.0

        # Penalize generic spam
        if "perplexity" in text_lower or "subscription" in text_lower or "warranty" in text_lower:
            score -= 10.0

        if score > 0:
            candidates.append({
                "quote": clean_q,
                "source": p.get('source', 'unknown'),
                "url": p.get('url', ''),
                "post_id": p.get('post_id'),
                "score": score
            })

    # Sort by relevance descending
    candidates.sort(key=lambda x: x['score'], reverse=True)

    # Source diversity selection
    selected = []
    used_sources = set()

    # Pass 1: candidates with positive score & distinct source
    for c in candidates:
        if c['source'] not in used_sources:
            selected.append(c)
            used_sources.add(c['source'])
            if len(selected) >= max_quotes:
                break

    # Pass 2: candidates with positive score duplicate source
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

if __name__ == "__main__":
    with open('data/tagged_posts.json', encoding='utf-8') as f:
        posts = json.load(f)

    for q_id in ["q1", "q2", "q3", "q4", "q6", "q8", "q9"]:
        quotes = extract_insights_quotes(posts, q_id)
        print(f"\n==========================================")
        print(f"QUESTION {q_id.upper()} QUOTES (Count: {len(quotes)}):")
        for q in quotes:
            print(f"  [{q['source']}] \"{q['quote']}\"")
