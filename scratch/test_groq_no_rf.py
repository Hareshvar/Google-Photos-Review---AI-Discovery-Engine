import os
import json
import time
import re
import dotenv
dotenv.load_dotenv()

from groq import Groq

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"), max_retries=0)
posts = json.load(open("data/tagged_posts.json", "r", encoding="utf-8"))[:5]

payload = [{"post_id": p['post_id'], "text": f"Title: {p.get('title','')}\nText: {p.get('raw_text','')}".strip()} for p in posts]

prompt = """You are a senior UX research classification system analyzing public posts about Google Photos search and retrieval struggles.
Extract a structured JSON classification for each post in the input list.

Return ONLY a valid JSON object wrapped in ```json ... ``` codeblocks or raw JSON:
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

user_msg = f"Posts to classify:\n{json.dumps(payload, indent=2)}"

t0 = time.time()
resp = groq_client.chat.completions.create(
    model="openai/gpt-oss-20b",
    messages=[
        {"role": "system", "content": prompt},
        {"role": "user", "content": user_msg}
    ],
    temperature=0.1
)
t1 = time.time()
print(f"Call succeeded in {t1-t0:.2f}s")
raw = resp.choices[0].message.content
if "```json" in raw:
    raw = raw.split("```json")[1].split("```")[0]
elif "```" in raw:
    raw = raw.split("```")[1].split("```")[0]

data = json.loads(raw.strip())
results = data.get("results", [])
print(f"Returned {len(results)} items")
print("First item post_id:", results[0].get("post_id"))
