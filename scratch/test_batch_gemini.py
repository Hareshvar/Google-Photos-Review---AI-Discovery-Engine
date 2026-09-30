import os
import json
import time
import dotenv
dotenv.load_dotenv()

from google import genai
from google.genai import types

posts = json.load(open("data/tagged_posts.json", "r", encoding="utf-8"))[10:15]

batch_payload = []
for idx, p in enumerate(posts):
    content = f"Title: {p.get('title','')}\nText: {p.get('raw_text','')}".strip()
    batch_payload.append({"item_index": idx, "post_id": p['post_id'], "text": content})

SYSTEM_TAXONOMY_PROMPT = """You are a senior UX research classification system analyzing public posts about Google Photos search and retrieval struggles.
Extract a structured JSON classification for each post text in the input list according to the following 21-field codebook.

Return ONLY a valid JSON object with a root key "results" containing a JSON array of exactly 5 classification objects (one for each post in the input order).

Each object must match this schema:
{
  "post_id": "string matching input post_id",
  "relevant": true or false,
  "vague_memory": "vague" | "partial" | "precise" | "unclear",
  "target_type": "document_info" | "specific_event" | "person_pet" | "place_trip" | "object_item" | "date_time" | "general_old_photo" | "other",
  "primary_cue": "date_time" | "location_place" | "person_face" | "text_ocr" | "visual_object" | "album_folder" | "event_context" | "file_metadata" | "none",
  "cues_remembered": ["list of strings"],
  "cues_forgotten": ["list of strings"],
  "hedged": true or false,
  "failure_step": "did_not_search" | "search_not_completed" | "no_or_wrong_results" | "results_not_recognized" | "wrong_photo_opened" | "scroll_not_found" | "no_failure",
  "memory_break": "forgot_key_detail" | "could_not_put_into_words" | "misremembered_fact" | "too_many_similar_photos" | "unclear",
  "query_styles": ["natural_language", "keywords", "date_range", "location_name", "person_name", "exact_quote"],
  "queries_quoted": ["verbatim search queries"],
  "workarounds": ["scroll_timeline", "check_other_apps", "ask_friends", "browse_folders", "gave_up"],
  "search_tool": "classic_search" | "ask_photos" | "map_view" | "people_pets_tab" | "search_tab",
  "job": "proof_documentation" | "reminiscing" | "sharing_social" | "practical_utility" | "unknown",
  "system_issues": ["missing_results", "wrong_results", "ocr_failure", "face_rec_failure", "date_index_error", "ask_photos_hallucination", "ui_regression"],
  "outcome": "found_eventually" | "not_found" | "partially_found" | "unclear",
  "severity": "low" | "medium" | "high",
  "wish": null,
  "unmapped_note": null,
  "quote": "Short exact representative verbatim snippet from the text",
  "confidence": 0.95
}
"""

gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

t0 = time.time()
g_resp = gemini_client.models.generate_content(
    model="gemini-3.8-flash",
    contents=[SYSTEM_TAXONOMY_PROMPT, f"Classify this array of 5 posts into JSON:\n{json.dumps(batch_payload, indent=2)}"],
    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        temperature=0.1
    )
)
t1 = time.time()
print(f"Call completed in {t1-t0:.2f}s")
res = json.loads(g_resp.text)
items = res.get("results", res)
print("Items count:", len(items))
for it in items:
    print(f"ID: {it.get('post_id')} | Rel: {it.get('relevant')} | Target: {it.get('target_type')} | Quote: {it.get('quote')}")
