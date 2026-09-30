import os
import json
import time
import dotenv
dotenv.load_dotenv()

from groq import Groq

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

posts = json.load(open("data/tagged_posts.json", "r", encoding="utf-8"))[10:15]

batch_payload = []
for idx, p in enumerate(posts):
    content = f"Title: {p.get('title','')}\nText: {p.get('raw_text','')}".strip()
    batch_payload.append({"item_index": idx, "post_id": p['post_id'], "text": content})

SYSTEM_TAXONOMY_PROMPT = """You are a senior UX research classification system analyzing public posts about Google Photos search and retrieval struggles.
Extract a structured JSON classification for each post text in the input list according to the following 21-field codebook.

Return ONLY a JSON object formatted as follows:
{
  "results": [
    {
      "post_id": "string matching input post_id",
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
      "quote": "verbatim snippet",
      "confidence": 0.95
    }
  ]
}
"""

user_prompt = f"Here is a JSON array of 5 posts to classify:\n{json.dumps(batch_payload, indent=2)}"

t0 = time.time()
try:
    resp = groq_client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {"role": "system", "content": SYSTEM_TAXONOMY_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        response_format={"type": "json_object"},
        temperature=0.1
    )
    t1 = time.time()
    print(f"Groq completed in {t1-t0:.2f}s")
    data = json.loads(resp.choices[0].message.content)
    results = data.get("results", [])
    print(f"Returned {len(results)} items")
    for r in results:
        print("  - Post ID:", r.get("post_id"), "| Quote:", r.get("quote"))
except Exception as e:
    print(f"Groq FAILED: {e}")
