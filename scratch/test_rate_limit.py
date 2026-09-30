import os
import time
import json
import dotenv
dotenv.load_dotenv()

from google import genai
from google.genai import types

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

posts = json.load(open("data/tagged_posts.json", "r", encoding="utf-8"))[:5]
batch_payload = [{"item_index": idx, "post_id": p['post_id'], "text": f"Title: {p.get('title','')}\nText: {p.get('raw_text','')}".strip()} for idx, p in enumerate(posts)]

prompt = """You are a taxonomy tagger. Return JSON object {"results": [...]} with 5 taxonomy classifications."""

t0 = time.time()
successes = 0
errors = []

for i in range(20):
    try:
        t_start = time.time()
        g_resp = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=[prompt, f"Data:\n{json.dumps(batch_payload)}"],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.1
            )
        )
        t_dur = time.time() - t_start
        successes += 1
        print(f"Call {i+1} succeeded in {t_dur:.2f}s (Total elapsed: {time.time()-t0:.2f}s)")
    except Exception as e:
        print(f"Call {i+1} FAILED at {time.time()-t0:.2f}s: {e}")
        errors.append(str(e))
        time.sleep(1)

print(f"\nCompleted {successes}/20 calls in {time.time()-t0:.2f}s. Errors: {len(errors)}")
