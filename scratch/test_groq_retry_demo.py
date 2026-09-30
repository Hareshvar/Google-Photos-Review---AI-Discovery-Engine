import os
import json
import time
import random
import dotenv
dotenv.load_dotenv()

from groq import Groq

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"), max_retries=0)
posts = json.load(open("data/tagged_posts.json", "r", encoding="utf-8"))[:25]

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

def call_batch_with_retry(batch_idx, batch_posts):
    payload = [{"post_id": p['post_id'], "text": f"Title: {p.get('title','')}\nText: {p.get('raw_text','')}".strip()} for p in batch_posts]
    user_msg = f"Posts to classify:\n{json.dumps(payload, indent=2)}"
    
    for attempt in range(5):
        try:
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
            print(f"Batch {batch_idx} SUCCESS on attempt {attempt+1} in {t1-t0:.2f}s", flush=True)
            data = json.loads(resp.choices[0].message.content)
            return data.get("results", []), "llm", None
        except Exception as e:
            err_str = str(e)
            if ("429" in err_str or "503" in err_str or "rate_limit" in err_str or "TPM" in err_str) and attempt < 4:
                # Extract wait time if given or default exponential backoff
                backoff = (2 ** (attempt + 1)) + random.uniform(1.0, 2.0)
                print(f"Batch {batch_idx} hit rate limit on attempt {attempt+1}. Sleeping {backoff:.2f}s...", flush=True)
                time.sleep(backoff)
            else:
                print(f"Batch {batch_idx} attempt {attempt+1} failed: {err_str[:100]}", flush=True)
                if attempt == 4:
                    return None, "fallback", err_str

batches = [posts[i:i+5] for i in range(0, len(posts), 5)]
t_start = time.time()

for idx, b in enumerate(batches):
    res, src, err = call_batch_with_retry(idx, b)
    print(f"Result batch {idx}: source={src}, items={len(res) if res else 0}", flush=True)
    # Pause slightly to keep TPM steady
    time.sleep(8.0)

print(f"All {len(batches)} batches done in {time.time()-t_start:.2f}s", flush=True)
