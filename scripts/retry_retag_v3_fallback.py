"""
Retry Fallback Posts Script for retag_sample_v3 (1,239 posts)
=============================================================
- Reads data/retag_sample_v3_1500.json (read-only).
- Extracts the 1,240 records with tag_source == "fallback".
- Excludes synthetic/demo post 'demo_goa' (1 excluded, leaving 1,239 posts).
- Retags remaining 1,239 posts in 5-post batches using Groq API with robust 429 rate limit backoff.
- Writes results strictly to NEW file data/retag_v3_fallback_retry.json.
"""

import os
import sys
import json
import time
import re
import logging

import dotenv
dotenv.load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("retry_retag_v3_fallback")

import sys
sys.path.insert(0, ".")
from scripts.retag_sample_v3 import (
    SYSTEM_TAXONOMY_PROMPT,
    TagVerifier,
    rule_classifier,
    parse_json_safely
)

class RobustGroqEngine:
    def __init__(self):
        self.groq_key = os.getenv("GROQ_API_KEY", "")
        self.groq_client = None
        if self.groq_key and self.groq_key != "your_groq_api_key_here":
            try:
                from groq import Groq
                self.groq_client = Groq(api_key=self.groq_key, max_retries=0)
            except Exception as e:
                logger.warning(f"Could not initialize Groq client: {e}")

    def process_batch(self, batch_records: list, batch_idx: int, total_batches: int) -> list:
        payload = []
        for r in batch_records:
            content = f"Title: {r.get('title','')}\nText: {r.get('raw_text','')}".strip()
            payload.append({"post_id": r["post_id"], "text": content})

        user_prompt = f"Here is a JSON array of {len(batch_records)} posts to classify:\n{json.dumps(payload, indent=2)}"

        tags_map, tag_src, err_reason = self._call_groq_with_backoff(user_prompt, batch_idx, total_batches)

        output_records = []
        for r in batch_records:
            pid = r["post_id"]
            content = f"Title: {r.get('title','')}\nText: {r.get('raw_text','')}".strip()

            if tags_map and pid in tags_map:
                verified_taxonomy = TagVerifier.verify_and_coerce(content, tags_map[pid])
                record_source = "llm"
                record_reason = None
            else:
                raw_rule = rule_classifier(r.get("title", ""), r.get("raw_text", ""))
                verified_taxonomy = TagVerifier.verify_and_coerce(content, raw_rule)
                record_source = "fallback"
                record_reason = err_reason or "All LLM retries exhausted"

            rec = dict(r)
            rec["tag_source"] = record_source
            rec["fallback_reason"] = record_reason
            rec["taxonomy"] = verified_taxonomy
            output_records.append(rec)

        return output_records

    def _call_groq_with_backoff(self, user_prompt: str, batch_idx: int, total_batches: int):
        if not self.groq_client:
            return None, "fallback", "Groq API key not configured"

        # Models available on this Groq account
        groq_models = ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b"]
        last_error = None

        # Round robin across models: 3 cycles across all models
        for cycle in range(3):
            for g_model in groq_models:
                try:
                    resp = self.groq_client.chat.completions.create(
                        model=g_model,
                        messages=[
                            {"role": "system", "content": SYSTEM_TAXONOMY_PROMPT},
                            {"role": "user", "content": user_prompt}
                        ],
                        temperature=0.1
                    )
                    content = resp.choices[0].message.content
                    if content:
                        data = parse_json_safely(content)
                        if data:
                            items = data.get("results", data)
                            if isinstance(items, dict):
                                items = list(items.values())
                            if isinstance(items, list):
                                res_map = {}
                                for it in items:
                                    if isinstance(it, dict) and "post_id" in it:
                                        res_map[it["post_id"]] = it
                                if res_map:
                                    # Pacing sleep to stay within TPM limit
                                    time.sleep(4.0)
                                    return res_map, "llm", None
                except Exception as e:
                    err_str = str(e)
                    last_error = f"Groq API ({g_model}) Error (cycle {cycle+1}): {err_str}"
                    
                    if "429" in err_str or "rate" in err_str.lower() or "tpm" in err_str.lower() or "otpm" in err_str.lower():
                        logger.warning(f"Batch {batch_idx+1}/{total_batches} [{g_model}] 429 RateLimit. Trying next available model...")
                        time.sleep(1.0)
                    else:
                        logger.warning(f"Batch {batch_idx+1}/{total_batches} [{g_model}] non-rate-limit error: {err_str}")
                        time.sleep(1.0)

            # If all models hit 429 in this cycle, pause 10s before next cycle
            time.sleep(10.0)

        return None, "fallback", last_error

def main():
    v3_file = "data/retag_sample_v3_1500.json"
    output_file = "data/retag_v3_fallback_retry.json"

    logger.info(f"Reading v3 dataset from {v3_file}...")
    with open(v3_file, "r", encoding="utf-8") as f:
        v3_records = json.load(f)

    # Filter to fallback records
    fallback_records = [r for r in v3_records if r.get("tag_source") == "fallback"]
    logger.info(f"Total fallback records in v3: {len(fallback_records)}")

    # Exclude synthetic/demo posts
    demo_pids = {"demo_receipt", "demo_dog", "demo_cake", "demo_goa", "demo_sister", "demo_praise"}
    retry_records = [r for r in fallback_records if r["post_id"] not in demo_pids]
    excluded_demo_count = len(fallback_records) - len(retry_records)
    logger.info(f"Excluded {excluded_demo_count} demo record(s). Final retry pool count: {len(retry_records)}")

    # Checkpoint loading if output_file partially exists
    final_records = []
    already_done_ids = set()
    if os.path.exists(output_file):
        try:
            with open(output_file, "r", encoding="utf-8") as f:
                final_records = json.load(f)
            already_done_ids = {r["post_id"] for r in final_records if isinstance(r, dict) and "post_id" in r}
            logger.info(f"Loaded existing checkpoint from {output_file} with {len(already_done_ids)} records.")
        except Exception as e:
            logger.warning(f"Could not load existing checkpoint: {e}")

    batch_size = 5
    batches = [retry_records[i:i+batch_size] for i in range(0, len(retry_records), batch_size)]
    total_batches = len(batches)

    engine = RobustGroqEngine()

    for b_idx, batch in enumerate(batches):
        batch_pids = {r["post_id"] for r in batch}
        if batch_pids.issubset(already_done_ids):
            continue

        processed = engine.process_batch(batch, b_idx, total_batches)
        final_records.extend(processed)
        already_done_ids.update(batch_pids)

        # Save checkpoint after every batch
        post_order = {r["post_id"]: idx for idx, r in enumerate(retry_records)}
        final_records.sort(key=lambda r: post_order.get(r["post_id"], 0))
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(final_records, f, indent=2, ensure_ascii=False)

        llm_c = sum(1 for r in final_records if r.get("tag_source") == "llm")
        fb_c = sum(1 for r in final_records if r.get("tag_source") == "fallback")
        logger.info(f"Progress: {len(final_records)}/{len(retry_records)} posts processed. Current LLM: {llm_c}, Fallback: {fb_c}")

    logger.info(f"=== FINISHED RETRY RUN ===")
    logger.info(f"Total retry posts: {len(final_records)}")
    llm_c = sum(1 for r in final_records if r.get("tag_source") == "llm")
    fb_c = sum(1 for r in final_records if r.get("tag_source") == "fallback")
    logger.info(f"LLM tagged count: {llm_c}")
    logger.info(f"Fallback count: {fb_c}")

if __name__ == "__main__":
    main()
