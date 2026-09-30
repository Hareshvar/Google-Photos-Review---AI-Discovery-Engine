import json

def verify_system_issues():
    with open("data/final_tagged_dataset_mapped.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        
    relevant_posts = [p for p in data if p.get("taxonomy", {}).get("relevant", False)]
    total_relevant = len(relevant_posts)
    print(f"Total relevant posts: {total_relevant}")
    
    # Collect all system_issues values and counts
    system_issues_counts = {}
    for p in relevant_posts:
        issues = p.get("taxonomy", {}).get("system_issues") or []
        for iss in issues:
            system_issues_counts[iss] = system_issues_counts.get(iss, 0) + 1
            
    print("\n=== FULL DISTINCT SYSTEM_ISSUES VALUES & COUNTS (among N=916 relevant posts) ===")
    for iss, count in sorted(system_issues_counts.items(), key=lambda x: x[1], reverse=True):
        pct = (count / total_relevant) * 100
        print(f"  '{iss}': {count} posts ({pct:.2f}%)")
        
    print("\n=== ALSO CHECKING ALL POSTS IN DATASET (N=3719) ===")
    all_system_issues_counts = {}
    for p in data:
        issues = p.get("taxonomy", {}).get("system_issues") or []
        for iss in issues:
            all_system_issues_counts[iss] = all_system_issues_counts.get(iss, 0) + 1
    for iss, count in sorted(all_system_issues_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  '{iss}': {count} posts total")
        
    # Check specific questions
    print("\n=== VERIFYING SPECIFIC QUESTIONS ===")
    date_err = system_issues_counts.get("date_index_error", 0)
    date_ing_err = system_issues_counts.get("date_indexing_error", 0)
    print(f"1. 'date_index_error' count: {date_err} | 'date_indexing_error' count: {date_ing_err}")
    
    ocr_fail = system_issues_counts.get("ocr_failure", 0)
    no_text = system_issues_counts.get("no_text_in_photo_search", 0)
    print(f"2. 'ocr_failure' count: {ocr_fail} | 'no_text_in_photo_search' count: {no_text}")

    # Re-run dry run for all 5 clusters
    print("\n=== RE-RUN DRY RUN FOR ALL 5 CLUSTERS ===")
    
    # cluster_03: face_rec_failure
    c3 = [p for p in relevant_posts if "face_rec_failure" in (p.get("taxonomy", {}).get("system_issues") or [])]
    # cluster_01: date_index_error
    c1 = [p for p in relevant_posts if "date_index_error" in (p.get("taxonomy", {}).get("system_issues") or [])]
    # cluster_04: ocr_failure
    c4 = [p for p in relevant_posts if "ocr_failure" in (p.get("taxonomy", {}).get("system_issues") or [])]
    # cluster_05: location_place in primary_cue / cues_remembered / cues_forgotten
    c5 = [
        p for p in relevant_posts 
        if p.get("taxonomy", {}).get("primary_cue") == "location_place"
        or "location_place" in (p.get("taxonomy", {}).get("cues_remembered") or [])
        or "location_place" in (p.get("taxonomy", {}).get("cues_forgotten") or [])
    ]
    # cluster_02: ask_photos_hallucination OR explicit product keywords
    c2_terms = ["ask photos", "ask photo", "gemini", "ask ai", "ask feature", "new search tab"]
    c2 = [
        p for p in relevant_posts 
        if "ask_photos_hallucination" in (p.get("taxonomy", {}).get("system_issues") or [])
        or any(t in f"{p.get('title', '')} {p.get('raw_text', '')}".lower() for t in c2_terms)
    ]
    
    print(f"cluster_03 (Face recognition): n = {len(c3)} ({len(c3)/total_relevant*100:.2f}%)")
    print(f"cluster_01 (Date indexing): n = {len(c1)} ({len(c1)/total_relevant*100:.2f}%)")
    print(f"cluster_04 (Text OCR): n = {len(c4)} ({len(c4)/total_relevant*100:.2f}%)")
    print(f"cluster_05 (Locations/Maps): n = {len(c5)} ({len(c5)/total_relevant*100:.2f}%)")
    print(f"cluster_02 (Ask Photos AI): n = {len(c2)} ({len(c2)/total_relevant*100:.2f}%)")

if __name__ == "__main__":
    verify_system_issues()
