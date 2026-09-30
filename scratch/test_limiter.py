import os
import json
import time
import random
import threading
import dotenv
dotenv.load_dotenv()

from groq import Groq
from google import genai

class RateLimiter:
    def __init__(self, max_rpm: float):
        self.max_rpm = max_rpm
        self.interval = 60.0 / max_rpm
        self.lock = threading.Lock()
        self.last_call = 0.0

    def acquire(self):
        with self.lock:
            now = time.time()
            elapsed = now - self.last_call
            if elapsed < self.interval:
                time.sleep(self.interval - elapsed)
            self.last_call = time.time()

groq_limiter = RateLimiter(max_rpm=25.0) # 25 RPM for Groq
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

posts = json.load(open("data/tagged_posts.json", "r", encoding="utf-8"))

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

def process_batch(batch, batch_idx):
    payload = [{"item_index": idx, "post_id": p['post_id'], "text": f"Title: {p.get('title','')}\nText: {p.get('raw_text','')}".strip()} for idx, p in enumerate(batch)]
    user_prompt = f"Here is a JSON array of 5 posts to classify:\n{json.dumps(payload, indent=2)}"
    
    # Retry loop with exponential backoff
    for attempt in range(5): # initial + 4 retries
        groq_limiter.acquire()
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
            data = json.loads(resp.choices[0].message.content)
            results = data.get("results", [])
            print(f"Batch {batch_idx} SUCCESS on attempt {attempt+1}: {len(results)} items parsed", flush=True)
            return results, "llm", None
        except Exception as e:
            err_str = str(e)
            if ("429" in err_str or "503" in err_str or "rate" in err_str.lower()) and attempt < 4:
                backoff = (2 ** attempt) + random.uniform(0.5, 1.5)
                print(f"Batch {batch_idx} hit {err_str[:40]} on attempt {attempt+1}. Sleeping {backoff:.2f}s...", flush=True)
                time.sleep(backoff)
            else:
                print(f"Batch {batch_idx} FAILED attempt {attempt+1}: {err_str[:80]}", flush=True)
                if attempt == 4:
                    return None, "fallback", err_str

batches = [posts[i:i+5] for i in range(0, 50, 5)] # 10 batches = 50 posts
t0 = time.time()
print(f"Starting {len(batches)} batches...", flush=True)

import concurrent.futures
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
    futures = [executor.submit(process_batch, b, idx) for idx, b in enumerate(batches)]
    for f in concurrent.futures.as_completed(futures):
        f.result()

print(f"Done in {time.time()-t0:.2f}s", flush=True)
