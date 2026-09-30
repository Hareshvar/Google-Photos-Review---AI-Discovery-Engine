import os
import json
import dotenv
import time
from groq import Groq

dotenv.load_dotenv()

# Pass max_retries=0 to capture exact API exception immediately
client = Groq(api_key=os.getenv("GROQ_API_KEY"), max_retries=0)
v3_data = json.load(open("data/retag_sample_v3_1500.json", encoding="utf-8"))
fallback_posts = [r for r in v3_data if r.get("tag_source") == "fallback"]

print(f"Total fallback posts in v3: {len(fallback_posts)}")

models = ["qwen/qwen3.8-27b", "openai/gpt-oss-120b", "openai/gpt-oss-20b"]

import sys
sys.path.append(".")
from scripts.retag_sample_v3 import SYSTEM_TAXONOMY_PROMPT

errors = []
for batch_idx in range(5):
    batch = fallback_posts[batch_idx*5 : (batch_idx+1)*5]
    payload = [{"post_id": r["post_id"], "text": f"Title: {r.get('title','')}\nText: {r.get('raw_text','')}"} for r in batch]
    prompt = f"Here is a JSON array of {len(payload)} posts to classify:\n{json.dumps(payload, indent=2)}"
    
    for m in models:
        try:
            print(f"Testing Batch {batch_idx} with Model {m}...")
            resp = client.chat.completions.create(
                model=m,
                messages=[{"role": "system", "content": SYSTEM_TAXONOMY_PROMPT}, {"role": "user", "content": prompt}],
                temperature=0.1
            )
            print(f"-> Batch {batch_idx} Model {m}: SUCCESS! Response length: {len(resp.choices[0].message.content or '')}")
            break
        except Exception as e:
            err_msg = f"Batch {batch_idx} Model {m}: {type(e).__name__} - {str(e)}"
            errors.append(err_msg)
            print(f"-> {err_msg}")
            time.sleep(0.5)

print("\n--- SUMMARY OF ALL ERRORS CAPTURED ---")
for idx, err in enumerate(errors, 1):
    print(f"{idx}. {err}")
