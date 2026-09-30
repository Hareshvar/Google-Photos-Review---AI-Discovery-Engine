import json
from backend.models.taxonomy import TaggedPostRecord

def test_cluster_rederivation():
    with open("data/final_tagged_dataset_mapped.json", "r", encoding="utf-8") as f:
        raw_data = json.load(f)
        
    posts = [TaggedPostRecord(**p) for p in raw_data if p.get("taxonomy", {}).get("relevant", False)]
    total_relevant = len(posts)
    
    theme_rules = [
        {
            "cluster_id": "cluster_03",
            "title": "Face and person recognition broken",
            "summary_note": "Users experience broken face grouping and missing facial recognition tags. Common complaints include family members or pets suddenly losing face tags, disappearing people clusters, and manual face tagging failing to sync across devices.",
            "matcher": lambda p: "face_rec_failure" in (p.taxonomy.system_issues or []),
            "terms": ["face", "person", "people", "pet", "tag", "untagged", "grouping", "recognize", "faces", "people & pets"]
        },
        {
            "cluster_id": "cluster_05",
            "title": "Missing estimated photo locations & map view",
            "summary_note": "Users experience missing estimated photo locations and broken map view pins. Searches by city, country, or location landmark fail to return photos taken in those specific vacation destinations.",
            "matcher": lambda p: (
                p.taxonomy.primary_cue == "location_place"
                or "location_place" in (p.taxonomy.cues_remembered or [])
                or "location_place" in (p.taxonomy.cues_forgotten or [])
            ),
            "terms": ["location", "place", "city", "map", "gps", "address", "landmarks", "country", "trip", "vacation"]
        },
        {
            "cluster_id": "cluster_01",
            "title": "Date indexing & timeline navigation friction",
            "summary_note": "Users encounter severe friction locating photos by date or year. Common struggles include corrupted EXIF timestamps shifting photos to incorrect years, missing date header controls after app updates, and the necessity of endless manual timeline scrolling when date sorting fails.",
            "matcher": lambda p: "date_index_error" in (p.taxonomy.system_issues or []),
            "terms": ["date", "year", "timeline", "month", "timestamp", "chronological", "exif", "old photo", "scroll", "sort", "sorting"]
        },
        {
            "cluster_id": "cluster_04",
            "title": "Text-in-photo (OCR) search failing",
            "summary_note": "Users rely heavily on Google Photos OCR to retrieve critical utility screenshots, receipts, prescriptions, and document photos. Search regressions frequently fail to index embedded text within images, forcing manual folder navigation.",
            "matcher": lambda p: "ocr_failure" in (p.taxonomy.system_issues or []),
            "terms": ["ocr", "text", "words", "receipt", "document", "license", "prescription", "sign", "exact text"]
        },
        {
            "cluster_id": "cluster_02",
            "title": "Search regressed after Ask Photos update",
            "summary_note": "Users express frustration that the new Ask Photos AI search update replaced exact keyword matching with generative synthesis. Queries that previously yielded exact photo matches now fail, return irrelevant results, or fail to parse exact quotation mark syntax.",
            "matcher": lambda p: (
                "ask_photos_hallucination" in (p.taxonomy.system_issues or [])
                or any(t in f"{p.title} {p.raw_text}".lower() for t in ["ask photos", "ask photo", "gemini", "ask ai", "ask feature", "new search tab"])
            ),
            "terms": ["ask photos", "ask photo", "gemini", "ask ai", "update", "new search"]
        }
    ]
    
    used_quotes_global = set()
    used_post_ids_global = set()
    
    results = []
    
    for theme in theme_rules:
        matching_posts = [p for p in posts if theme["matcher"](p)]
        count = len(matching_posts)
        share_pct = round((count / total_relevant) * 100, 2)
        
        # Select up to 3 quotes strictly from matching_posts and not previously used anywhere
        selected_quotes = []
        seen_sources = set()
        
        # Pass 1: Try quotes matching terms with source diversity
        for p in matching_posts:
            q = (p.taxonomy.quote or p.title or "").strip()
            if not q or len(q) < 10:
                continue
            if q in used_quotes_global or p.post_id in used_post_ids_global:
                continue
            
            q_lower = q.lower()
            src = p.source or "help_community"
            
            if any(t in q_lower for t in theme["terms"]):
                if src not in seen_sources or len(seen_sources) >= 3:
                    selected_quotes.append({
                        "quote": q,
                        "source": src,
                        "url": p.url,
                        "post_id": p.post_id
                    })
                    seen_sources.add(src)
                    used_quotes_global.add(q)
                    used_post_ids_global.add(p.post_id)
                    if len(selected_quotes) >= 3:
                        break
                        
        # Pass 2: Fallback if under 3
        if len(selected_quotes) < 3:
            for p in matching_posts:
                q = (p.taxonomy.quote or p.title or "").strip()
                if not q or len(q) < 10:
                    continue
                if q in used_quotes_global or p.post_id in used_post_ids_global:
                    continue
                src = p.source or "help_community"
                
                selected_quotes.append({
                    "quote": q,
                    "source": src,
                    "url": p.url,
                    "post_id": p.post_id
                })
                used_quotes_global.add(q)
                used_post_ids_global.add(p.post_id)
                if len(selected_quotes) >= 3:
                    break
                    
        results.append({
            "cluster_id": theme["cluster_id"],
            "title": theme["title"],
            "count": count,
            "share_pct": share_pct,
            "quotes": selected_quotes
        })
        
    print("\n=== CLUSTER RE-DERIVATION RESULTS ===")
    all_quotes_collected = []
    for r in results:
        print(f"[{r['cluster_id']}] {r['title']} | Count: {r['count']} ({r['share_pct']}%) | Selected Quotes: {len(r['quotes'])}")
        for q in r['quotes']:
            all_quotes_collected.append(q['quote'])
            print(f"  - ({q['source']}) \"{q['quote'][:80]}...\"")
            
    # Check for duplicates across clusters
    dup_quotes = len(all_quotes_collected) - len(set(all_quotes_collected))
    print(f"\nTotal quotes collected across all clusters: {len(all_quotes_collected)}")
    print(f"Duplicate quotes count across clusters: {dup_quotes} (Target: 0)")

if __name__ == "__main__":
    test_cluster_rederivation()
