import json

def dry_run_step3():
    with open("data/final_tagged_dataset_mapped.json", "r", encoding="utf-8") as f:
        raw_data = json.load(f)
        
    posts = [p for p in raw_data if p.get("taxonomy", {}).get("relevant", False)]
    total_relevant = len(posts)
    
    print(f"Total relevant posts: {total_relevant}")
    
    # 1. cluster_03 (face recognition) -> system_issues contains 'face_rec_failure'
    c3_posts = [p for p in posts if "face_rec_failure" in (p.get("taxonomy", {}).get("system_issues") or [])]
    print(f"cluster_03 (face_rec_failure): n = {len(c3_posts)} (expected 158)")
    
    # 2. cluster_01 (date indexing) -> system_issues contains 'date_index_error'
    c1_posts = [p for p in posts if "date_index_error" in (p.get("taxonomy", {}).get("system_issues") or [])]
    print(f"cluster_01 (date_index_error): n = {len(c1_posts)} (expected 30)")
    
    # 3. cluster_04 (OCR) -> system_issues contains 'ocr_failure' (or 'no_text_in_photo_search')
    c4_ocr_failure = [p for p in posts if "ocr_failure" in (p.get("taxonomy", {}).get("system_issues") or [])]
    c4_no_text = [p for p in posts if "no_text_in_photo_search" in (p.get("taxonomy", {}).get("system_issues") or [])]
    print(f"cluster_04 (ocr_failure): n = {len(c4_ocr_failure)}")
    print(f"cluster_04 (no_text_in_photo_search): n = {len(c4_no_text)} (matching Q6 n=13)")
    
    # 4. cluster_05 (locations) -> primary_cue == 'location_place' OR cues_remembered/cues_forgotten contains 'location_place'
    c5_posts = [
        p for p in posts 
        if p.get("taxonomy", {}).get("primary_cue") == "location_place"
        or "location_place" in (p.get("taxonomy", {}).get("cues_remembered") or [])
        or "location_place" in (p.get("taxonomy", {}).get("cues_forgotten") or [])
    ]
    print(f"cluster_05 (location_place in primary_cue / cues_remembered / cues_forgotten): n = {len(c5_posts)} ({len(c5_posts)/total_relevant*100:.2f}%)")
    
    # 5. cluster_02 (Ask Photos regression) -> tightened keyword matching
    # Require explicit product/update reference
    c2_terms = ["ask photos", "ask photo", "gemini", "ask ai", "ask feature", "new search tab"]
    c2_posts = [
        p for p in posts 
        if "ask_photos_hallucination" in (p.get("taxonomy", {}).get("system_issues") or [])
        or any(t in f"{p.get('title', '')} {p.get('raw_text', '')}".lower() for t in c2_terms)
    ]
    print(f"cluster_02 (tightened Ask Photos terms + ask_photos_hallucination): n = {len(c2_posts)} ({len(c2_posts)/total_relevant*100:.2f}%)")

if __name__ == "__main__":
    dry_run_step3()
