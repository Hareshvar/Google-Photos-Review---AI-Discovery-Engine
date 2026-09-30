import os
import json
import time
import dotenv
dotenv.load_dotenv()

from google import genai
from google.genai import types

gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

posts = json.load(open("data/tagged_posts.json", "r", encoding="utf-8"))[:5]
payload = [{"post_id": p['post_id'], "text": f"Title: {p.get('title','')}\nText: {p.get('raw_text','')}".strip()} for p in posts]

prompt = """You are a senior UX research classification system analyzing public posts about Google Photos search and retrieval struggles.
Extract a structured JSON classification for each post in the input list according to the following 21-field codebook.

Return ONLY a valid JSON object with a root key "results" containing an array of 5 classification objects in input order.

Schema for each object:
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

user_msg = f"Posts to classify:\n{json.dumps(payload, indent=2)}"

t0 = time.time()
g_resp = gemini_client.models.generate_content(
    model="gemini-3.5-flash",
    contents=[prompt, user_msg],
    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        temperature=0.1
    )
)
t1 = time.time()
print(f"Gemini 3.5 Flash batch call succeeded in {t1-t0:.2f}s")
data = json.loads(g_resp.text)
results = data.get("results", data)
if isinstance(results, dict):
    results = list(results.values())
print(f"Returned {len(results)} items")
print("First item:", json.dumps(results[0], indent=2))
