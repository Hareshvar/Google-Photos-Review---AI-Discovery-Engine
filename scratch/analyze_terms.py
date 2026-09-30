import json

def main():
    with open("data/final_tagged_dataset_mapped.json", "r", encoding="utf-8") as f:
        raw_data = json.load(f)
    
    posts = [p for p in raw_data if p.get("taxonomy", {}).get("relevant", False)]
    print(f"Total relevant posts: {len(posts)}")
    
    print("\n=== CLUSTER 05 MATCH ANALYSIS ===")
    c5_terms = ["location", "place", "city", "map", "gps", "address", "landmarks", "country", "trip", "vacation"]
    
    c5_system_issue_matches = 0
    c5_cue_matches = 0
    c5_keyword_matches = 0
    
    term_counts = {t: 0 for t in c5_terms}
    
    for p in posts:
        tax = p.get("taxonomy", {})
        text = f"{p.get('title', '')} {p.get('raw_text', '')}".lower()
        
        has_si = "missing_results" in (tax.get("system_issues") or [])
        has_cue = tax.get("primary_cue") == "location_place"
        matched_terms = [t for t in c5_terms if t in text]
        
        if has_si:
            c5_system_issue_matches += 1
        if has_cue:
            c5_cue_matches += 1
        if matched_terms:
            c5_keyword_matches += 1
            for t in matched_terms:
                term_counts[t] += 1
                
    total_c5 = len([p for p in posts if 'missing_results' in (p.get('taxonomy', {}).get('system_issues') or []) or p.get('taxonomy', {}).get('primary_cue') == 'location_place' or any(t in f"{p.get('title', '')} {p.get('raw_text', '')}".lower() for t in c5_terms)])
    print(f"Total Posts Matched to Cluster 05: {total_c5}")
    print(f"  - Matched due to system_issue match ('missing_results'): {c5_system_issue_matches} posts!")
    print(f"  - Matched due to primary_cue match ('location_place'): {c5_cue_matches} posts")
    print(f"  - Matched due to keyword list: {c5_keyword_matches} posts")
    print("\nKeyword hit breakdown for cluster_05 terms:")
    for t, cnt in sorted(term_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  '{t}': {cnt} hits")

    print("\n=== CLUSTER 02 MATCH ANALYSIS ===")
    c2_terms = ["ask photos", "update", "exact text", "quotation", "regress", "new search", "gemini", "broken search", "useless search"]
    c2_term_counts = {t: 0 for t in c2_terms}
    c2_primary_cue_ocr_matches = 0
    
    for p in posts:
        tax = p.get("taxonomy", {})
        text = f"{p.get('title', '')} {p.get('raw_text', '')}".lower()
        if tax.get("primary_cue") == "text_ocr":
            c2_primary_cue_ocr_matches += 1
        matched_terms = [t for t in c2_terms if t in text]
        if matched_terms:
            for t in matched_terms:
                c2_term_counts[t] += 1
                
    print(f"Primary cue 'text_ocr' (incorrectly configured as primary_cue_match for cluster_02): {c2_primary_cue_ocr_matches} posts")
    print("Keyword hit breakdown for cluster_02 terms:")
    for t, cnt in sorted(c2_term_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  '{t}': {cnt} hits")

if __name__ == "__main__":
    main()
