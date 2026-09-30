import os
import json
import time
import dotenv
dotenv.load_dotenv()

from groq import Groq

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"), max_retries=0)

posts = json.load(open("data/tagged_posts.json", "r", encoding="utf-8"))[:5]
payload = [{"post_id": p['post_id'], "text": f"Title: {p.get('title','')}\nText: {p.get('raw_text','')}".strip()} for p in posts]

prompt = """You are a senior UX research classification system analyzing public posts about Google Photos search and retrieval struggles.
Extract a structured JSON classification for each post in the input list.

Return ONLY a valid JSON object with a root key "results" containing an array of 5 classification objects in input order.

Schema for each object:
{
  "post_id": "string",
  "relevant": true,
  "vague_memory": "vague",
  "target_type": "other",
  "primary_cue": "none",
  "cues_remembered": [],
  "cues_forgotten": [],
  "hedged": false,
  "failure_step": "no_failure",
  "memory_break": "unclear",
  "query_styles": [],
  "queries_quoted": [],
  "workarounds": [],
  "search_tool": "search_tab",
  "job": "unknown",
  "system_issues": [],
  "outcome": "unclear",
  "severity": "low",
  "wish": null,
  "unmapped_note": null,
  "quote": "string snippet",
  "confidence": 0.95
}

Enum options:
- vague_memory: vague, partial, precise, unclear
- target_type: document_info, specific_event, person_pet, place_trip, object_item, date_time, general_old_photo, other
- primary_cue: date_time, location_place, person_face, text_ocr, visual_object, album_folder, event_context, file_metadata, none
- failure_step: did_not_search, search_not_completed, no_or_wrong_results, results_not_recognized, wrong_photo_opened, scroll_not_found, no_failure
- memory_break: forgot_key_detail, could_not_put_into_words, misremembered_fact, too_many_similar_photos, unclear
- query_styles: natural_language, keywords, date_range, location_name, person_name, exact_quote
- workarounds: scroll_timeline, check_other_apps, ask_friends, browse_folders, gave_up
- search_tool: classic_search, ask_photos, map_view, people_pets_tab, search_tab
- job: proof_documentation, reminiscing, sharing_social, practical_utility, unknown
- system_issues: missing_results, wrong_results, ocr_failure, face_rec_failure, date_index_error, ask_photos_hallucination, ui_regression
- outcome: found_eventually, not_found, partially_found, unclear
- severity: low, medium, high
"""

user_msg = f"Posts to classify:\n{json.dumps(payload, indent=2)}"

t0 = time.time()
resp = groq_client.chat.completions.create(
    model="openai/gpt-oss-20b",
    messages=[
        {"role": "system", "content": prompt},
        {"role": "user", "content": user_msg}
    ],
    response_format={"type": "json_object"},
    temperature=0.1
)
t1 = time.time()
print(f"Call succeeded in {t1-t0:.2f}s")
data = json.loads(resp.choices[0].message.content)
print("Keys in response:", list(data.keys()))
items = data.get("results", [])
print(f"Returned {len(items)} items. First post_id: {items[0].get('post_id') if items else 'N/A'}")
