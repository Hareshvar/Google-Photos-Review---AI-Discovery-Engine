import os
import json
import time
import random
import dotenv
dotenv.load_dotenv()

from groq import Groq

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"), max_retries=0)

posts = json.load(open("data/tagged_posts.json", "r", encoding="utf-8"))[:10]
payload = [{"post_id": p['post_id'], "text": f"Title: {p.get('title','')}\nText: {p.get('raw_text','')}".strip()} for p in posts]

prompt = """You are a senior UX research classification system analyzing public posts about Google Photos search and retrieval struggles.
Extract a structured JSON classification for each post in the input list.

Return ONLY a JSON object formatted as follows:
{
  "results": [
    {
      "post_id": "string",
      "relevant": true,
      "vague_memory": "unclear",
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

for i in range(3):
    try:
        t0 = time.time()
        resp = groq_client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"Posts to classify:\n{json.dumps(payload[:5], indent=2)}"}
            ],
            response_format={"type": "json_object"},
            temperature=0.1
        )
        t1 = time.time()
        print(f"Attempt {i+1} Groq succeeded in {t1-t0:.2f}s")
    except Exception as e:
        print(f"Attempt {i+1} Groq FAILED: {e}")
