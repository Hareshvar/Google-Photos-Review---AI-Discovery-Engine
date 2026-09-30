import json
import re

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

with open('data/tagged_posts.json', encoding='utf-8') as f:
    posts = json.load(f)

# Q2 specific keywords: Remembering photo clues (event, face, location, date, text, ocr)
REMEMBRANCE_KEYWORDS = [
    "remember", "remembered", "memory", "memories", "wedding", "birthday", "trip", "vacation",
    "beach", "family", "baby", "kid", "dog", "cat", "pet", "face", "person", "people",
    "year ago", "years ago", "date", "taken in", "location", "place", "city", "text in photo", "ocr"
]

SPAM_AND_IRRELEVANT_TERMS = [
    "ai models", "orchestrator", "claude/codex", "perplexity", "subscription", "warranty",
    "sub folder", "album permission", "share photo location setting", "uninstall", "storage full",
    "three finger screenshot", "default app", "app crash", "battery drain", "jerks", "crazy",
    "how to delete", "remove memories"
]

candidates = []
for p in posts:
    tax = p.get('taxonomy', {})
    quote = tax.get('quote') or p.get('title')
    if not quote or not tax.get('quote_verified', True):
        continue

    clean_q = clean_mojibake(quote)
    if len(clean_q) < 25 or len(clean_q) > 220:
        continue

    text_lower = (clean_q + " " + (p.get('title') or '')).lower()

    score = 0.0
    for kw in REMEMBRANCE_KEYWORDS:
        if re.search(r'\b' + re.escape(kw) + r'\b', text_lower):
            score += 3.5

    for spam in SPAM_AND_IRRELEVANT_TERMS:
        if spam in text_lower:
            score -= 15.0

    if score > 0:
        candidates.append({
            "quote": clean_q,
            "source": p.get('source', 'unknown'),
            "url": p.get('url', ''),
            "post_id": p.get('post_id'),
            "score": score
        })

candidates.sort(key=lambda x: x['score'], reverse=True)

selected = []
used_sources = set()

for c in candidates:
    if c['source'] not in used_sources:
        selected.append(c)
        used_sources.add(c['source'])
        if len(selected) >= 3:
            break

if len(selected) < 3:
    selected_ids = {s['post_id'] for s in selected}
    for c in candidates:
        if c['post_id'] not in selected_ids:
            selected.append(c)
            if len(selected) >= 3:
                break

print("Top 3 Selected Quotes for Q2:")
for q in selected:
    print(f" [{q['source']} | score={q['score']:.1f}] \"{q['quote']}\"")
