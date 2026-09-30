import os
import json
import time
import random
import threading
import concurrent.futures
import dotenv
dotenv.load_dotenv()

from google import genai
from google.genai import types

class TokenBucketRateLimiter:
    def __init__(self, max_rpm: float):
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

limiter = TokenBucketRateLimiter(max_rpm=20.0) # 20 RPM = 3 seconds between requests

posts = json.load(open("data/tagged_posts.json", "r", encoding="utf-8"))[:50]
batches = [posts[i:i+5] for i in range(0, len(posts), 5)]

thread_local = threading.local()

def get_client():
    if not hasattr(thread_local, "client"):
        thread_local.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    return thread_local.client

def run_batch(idx, batch_posts):
    client = get_client()
    payload = [{"post_id": p['post_id'], "text": f"Title: {p.get('title','')}\nText: {p.get('raw_text','')}".strip()} for p in batch_posts]
    prompt = "Classify this JSON array of 5 posts into JSON: " + json.dumps(payload)
    
    for attempt in range(5):
        limiter.acquire()
        try:
            t0 = time.time()
            g_resp = client.models.generate_content(
                model="gemini-3.5-flash-lite",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1
                )
            )
            t1 = time.time()
            print(f"Batch {idx} done in {t1-t0:.2f}s", flush=True)
            return
        except Exception as e:
            print(f"Batch {idx} err attempt {attempt+1}: {e}", flush=True)
            time.sleep(2.0)

t_start = time.time()
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
    futures = [executor.submit(run_batch, idx, b) for idx, b in enumerate(batches)]
    for f in concurrent.futures.as_completed(futures):
        f.result()

print(f"All {len(batches)} batches done in {time.time()-t_start:.2f}s", flush=True)
