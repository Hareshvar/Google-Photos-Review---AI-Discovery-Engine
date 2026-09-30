import os
import json
import time
import dotenv
dotenv.load_dotenv()

from google import genai
from google.genai import types
from groq import Groq

posts = json.load(open("data/tagged_posts.json", "r", encoding="utf-8"))[:5]
payload = [{"post_id": p['post_id'], "text": f"Title: {p.get('title','')}\nText: {p.get('raw_text','')}".strip()} for p in posts]

prompt = """You are a senior UX research classification system analyzing public posts about Google Photos search and retrieval struggles.
Extract a structured JSON classification for each post in the input list.

Return ONLY a valid JSON object with a root key "results" containing an array of 5 classification objects in input order.

Schema:
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

print("--- Testing Gemini ---")
gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
t0 = time.time()
g_resp = gemini_client.models.generate_content(
    model="gemini-3.8-flash",
    contents=[prompt, user_msg],
    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        temperature=0.1
    )
)
t1 = time.time()
print(f"Gemini succeeded in {t1-t0:.2f}s")
g_data = json.loads(g_resp.text)
print("Gemini results count:", len(g_data.get("results", [])))

print("\n--- Testing Groq (qwen/qwen3.8-27b) ---")
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"), max_retries=0)
t2 = time.time()
resp = groq_client.chat.completions.create(
    model="qwen/qwen3.8-27b",
    messages=[
        {"role": "system", "content": prompt + "\nYou must output strictly valid JSON."},
        {"role": "user", "content": user_msg}
    ],
    temperature=0.1
)
t3 = time.time()
print(f"Groq qwen succeeded in {t3-t2:.2f}s")
# extract json
raw = resp.choices[0].message.content
if "```json" in raw:
    raw = raw.split("```json")[1].split("```")[0]
elif "```" in raw:
    raw = raw.split("```")[1].split("```")[0]
data = json.loads(raw.strip())
print("Groq qwen results count:", len(data.get("results", [])))
