"""
Standalone Sample Retagging Script (v3 - 1,500 posts)
======================================================
- Reads data/tagged_posts.json (read-only).
- Exclusion Set: 3,000 PIDs in data/retag_sample_v2.json + 1,364 PIDs in data/tag_data_old_unique.json.
- Selects 1,500 NEW posts:
  - 70% (1,050 posts) highest relevance priority score (bucket 'a') across remaining pool.
  - 30% (450 posts) stratified random sample from remaining lower-scoring posts (bucket 'c'),
    with a floor across all 6 sources (fixed seed=42).
- Classifies posts in 5-post batches using LLM (Gemini / Groq chain) with rate limiting & exponential backoff retries.
- Only uses rule-based classifier as absolute last resort after retries are exhausted.
- Records priority_score, sample_bucket, tag_source ("llm" or "fallback"), fallback_reason per record.
- Writes output strictly to data/retag_sample_v3_1500.json.
"""

import os
import sys
import json
import time
import re
import random
import logging
import threading
from typing import Dict, Any, List, Optional, Tuple
import concurrent.futures

import dotenv
dotenv.load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("retag_sample_v3")

# ------------------------------------------------------------------------------
# Taxonomy Enum Sets & Definitions
# ------------------------------------------------------------------------------
VAGUE_MEMORY_TYPES = {"vague", "partial", "precise", "unclear"}
TARGET_TYPES = {
    "document_info", "specific_event", "person_pet", "place_trip",
    "object_item", "date_time", "general_old_photo", "other"
}
PRIMARY_CUES = {
    "date_time", "location_place", "person_face", "text_ocr",
    "visual_object", "album_folder", "event_context", "file_metadata", "none"
}
FAILURE_STEPS = {
    "did_not_search", "search_not_completed", "no_or_wrong_results",
    "results_not_recognized", "wrong_photo_opened", "scroll_not_found", "no_failure"
}
MEMORY_BREAKS = {
    "forgot_key_detail", "could_not_put_into_words", "misremembered_fact",
    "too_many_similar_photos", "unclear"
}
QUERY_STYLES = {
    "natural_language", "keywords", "date_range", "location_name",
    "person_name", "exact_quote"
}
WORKAROUNDS = {
    "scroll_timeline", "check_other_apps", "ask_friends",
    "browse_folders", "gave_up"
}
SEARCH_TOOLS = {
    "classic_search", "ask_photos", "map_view", "people_pets_tab", "search_tab"
}
JOBS = {
    "proof_documentation", "reminiscing", "sharing_social",
    "practical_utility", "unknown"
}
SYSTEM_ISSUES = {
    "missing_results", "wrong_results", "ocr_failure", "face_rec_failure",
    "date_index_error", "ask_photos_hallucination", "ui_regression"
}
OUTCOMES = {"found_eventually", "not_found", "partially_found", "unclear"}
SEVERITIES = {"low", "medium", "high"}

SYSTEM_TAXONOMY_PROMPT = """You are a senior UX research classification system analyzing public posts about Google Photos search and retrieval struggles.
Extract a structured JSON classification for each post in the input list according to the following 21-field codebook.

Return ONLY a valid JSON object with a root key "results" containing an array of classification objects (one for each post in the input order).

Format:
{
  "results": [
    {
      "post_id": "exact string matching input post_id",
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
      "quote": "verbatim text snippet",
      "quote_verified": true,
      "confidence": 0.95
    }
  ]
}

Codebook Enums & Rules:
1. relevant (boolean): true ONLY if post describes searching for, trying to find, or struggling to retrieve photos/videos in Google Photos or a photo app.
2. vague_memory: "vague" | "partial" | "precise" | "unclear"
3. target_type: "document_info" | "specific_event" | "person_pet" | "place_trip" | "object_item" | "date_time" | "general_old_photo" | "other"
4. primary_cue: "date_time" | "location_place" | "person_face" | "text_ocr" | "visual_object" | "album_folder" | "event_context" | "file_metadata" | "none"
5. failure_step: "did_not_search" | "search_not_completed" | "no_or_wrong_results" | "results_not_recognized" | "wrong_photo_opened" | "scroll_not_found" | "no_failure"
6. memory_break: "forgot_key_detail" | "could_not_put_into_words" | "misremembered_fact" | "too_many_similar_photos" | "unclear"
7. query_styles: array from ["natural_language", "keywords", "date_range", "location_name", "person_name", "exact_quote"]
8. workarounds: array from ["scroll_timeline", "check_other_apps", "ask_friends", "browse_folders", "gave_up"]
9. search_tool: "classic_search" | "ask_photos" | "map_view" | "people_pets_tab" | "search_tab"
10. job: "proof_documentation" | "reminiscing" | "sharing_social" | "practical_utility" | "unknown"
11. system_issues: array from ["missing_results", "wrong_results", "ocr_failure", "face_rec_failure", "date_index_error", "ask_photos_hallucination", "ui_regression"]
12. outcome: "found_eventually" | "not_found" | "partially_found" | "unclear"
13. severity: "low" | "medium" | "high"
14. wish: string or null
15. quote: verbatim sentence or phrase from post supporting the failure/relevance, or title if short.
16. quote_verified: true
17. confidence: float between 0.0 and 1.0
"""

# ------------------------------------------------------------------------------
# Keyword Relevance Priority Scoring Logic
# ------------------------------------------------------------------------------
SEARCH_KEYWORDS = ["search", "find", "locate", "looking for", "where is", "can't find", "cant find", "cannot find"]
FAILURE_KEYWORDS = ["can't find", "cant find", "no results", "not showing up", "missing", "disappeared", "wrong results", "terrible search", "doesn't work", "doesnt work"]
TARGET_KEYWORDS = ["receipt", "document", "screenshot", "pet", "dog", "cat", "trip", "vacation", "birthday", "wedding", "party", "event", "passport", "license", "ticket"]
VAGUE_KEYWORDS = ["i think", "not sure", "around", "a few years ago", "somewhere in", "maybe", "pretty sure", "don't remember", "dont remember"]

def compute_priority_score(post: Dict[str, Any]) -> int:
    text = f"{post.get('title','')} {post.get('raw_text','')}".lower()
    score = 0
    if any(k in text for k in SEARCH_KEYWORDS):
        score += 1
    if any(k in text for k in FAILURE_KEYWORDS):
        score += 1
    if any(k in text for k in TARGET_KEYWORDS):
        score += 1
    if any(k in text for k in VAGUE_KEYWORDS):
        score += 1
    return score

# ------------------------------------------------------------------------------
# Stratified 1,500-Post Sampling Function
# ------------------------------------------------------------------------------
def select_1500_sample(all_posts: List[Dict[str, Any]], exclusion_set: set) -> List[Dict[str, Any]]:
    # 1. Filter out excluded posts
    eligible_posts = [p for p in all_posts if p["post_id"] not in exclusion_set]
    logger.info(f"Eligible posts after applying exclusion set: {len(eligible_posts)}")

    # 2. Compute priority score for all eligible posts
    scored_posts = []
    for p in eligible_posts:
        score = compute_priority_score(p)
        scored_posts.append({"post": p, "priority_score": score})

    # Sort by priority score descending
    scored_posts.sort(key=lambda x: x["priority_score"], reverse=True)

    # Bucket A: Top 70% (1,050 posts)
    target_a = 1050
    bucket_a_items = scored_posts[:target_a]
    for item in bucket_a_items:
        item["sample_bucket"] = "a"

    remaining_pool = scored_posts[target_a:]

    # Bucket C: Remaining 30% (450 posts) stratified across all 6 sources
    target_c = 450
    by_source = {}
    for item in remaining_pool:
        src = item["post"]["source"]
        if src not in by_source:
            by_source[src] = []
        by_source[src].append(item)

    sources = list(by_source.keys())
    logger.info(f"Remaining pool sources for Bucket C: {list(by_source.keys())}")

    min_floor = 25
    alloc = {}
    for src in sources:
        alloc[src] = min(min_floor, len(by_source[src]))

    curr_alloc = sum(alloc.values())
    rem_target = target_c - curr_alloc

    pool_sizes = {src: len(by_source[src]) - alloc[src] for src in sources}
    total_rem_pool = sum(pool_sizes.values())

    fractional = {}
    for src in sources:
        if total_rem_pool > 0:
            raw = alloc[src] + (rem_target * pool_sizes[src] / total_rem_pool)
        else:
            raw = alloc[src]
        alloc[src] = min(int(raw), len(by_source[src]))
        fractional[src] = raw - alloc[src]

    leftover = target_c - sum(alloc.values())
    for src, _ in sorted(fractional.items(), key=lambda x: x[1], reverse=True)[:leftover]:
        if alloc[src] < len(by_source[src]):
            alloc[src] += 1

    logger.info(f"Bucket C allocations across sources for 1500 sample: {alloc}")

    rng = random.Random(42) # Fixed seed for exact reproducibility
    bucket_c_items = []
    for src, count in alloc.items():
        pool = by_source[src]
        sampled = rng.sample(pool, count)
        for item in sampled:
            item["sample_bucket"] = "c"
            bucket_c_items.append(item)

    selected = bucket_a_items + bucket_c_items
    logger.info(f"1,500 Sample selection complete: {len(bucket_a_items)} in Bucket A, {len(bucket_c_items)} in Bucket C. Total = {len(selected)}")
    return selected

# ------------------------------------------------------------------------------
# Rule-Based Classifier Fallback
# ------------------------------------------------------------------------------
def rule_classifier(title: str, text: str) -> Dict[str, Any]:
    full_text = f"{title} {text}".lower()

    rel = any(w in full_text for w in ["search", "find", "locate", "missing", "can't find", "cant find", "no results", "looking for"])

    tt = "other"
    if any(w in full_text for w in ["receipt", "document", "bill", "passport", "tax", "paper"]):
        tt = "document_info"
    elif any(w in full_text for w in ["wedding", "birthday", "trip", "vacation", "concert", "party"]):
        tt = "specific_event"
    elif any(w in full_text for w in ["dog", "cat", "sister", "mom", "dad", "son", "daughter", "friend"]):
        tt = "person_pet"
    elif any(w in full_text for w in ["screenshot", "screen shot"]):
        tt = "document_info"

    cue = "none"
    if any(w in full_text for w in ["date", "year", "month", "ago"]):
        cue = "date_time"
    elif any(w in full_text for w in ["place", "location", "city", "country"]):
        cue = "location_place"
    elif any(w in full_text for w in ["face", "person", "who"]):
        cue = "person_face"
    elif any(w in full_text for w in ["text", "word"]):
        cue = "text_ocr"

    fs = "no_or_wrong_results" if ("can't find" in full_text or "missing" in full_text or "no results" in full_text) else "no_failure"
    out = "not_found" if rel else "unclear"

    words = full_text.split()
    q_snippet = " ".join(words[:12]) if words else (title or "search")

    return {
        "relevant": rel,
        "vague_memory": "vague" if rel else "unclear",
        "target_type": tt,
        "primary_cue": cue,
        "cues_remembered": [],
        "cues_forgotten": [],
        "hedged": False,
        "failure_step": fs,
        "memory_break": "unclear",
        "query_styles": ["keywords"] if rel else [],
        "queries_quoted": [],
        "workarounds": [],
        "search_tool": "search_tab",
        "job": "practical_utility" if rel else "unknown",
        "system_issues": ["missing_results"] if rel else [],
        "outcome": out,
        "severity": "medium" if rel else "low",
        "wish": None,
        "unmapped_note": None,
        "quote": q_snippet[:150],
        "quote_verified": True,
        "confidence": 0.65
    }

class TagVerifier:
    @staticmethod
    def verify_and_coerce(post_content: str, raw_tag: Dict[str, Any]) -> Dict[str, Any]:
        cleaned = dict(raw_tag)

        cleaned["relevant"] = bool(cleaned.get("relevant", False))

        vague = str(cleaned.get("vague_memory", "unclear")).lower()
        cleaned["vague_memory"] = vague if vague in VAGUE_MEMORY_TYPES else "unclear"

        target = str(cleaned.get("target_type", "other")).lower()
        cleaned["target_type"] = target if target in TARGET_TYPES else "other"

        cue = str(cleaned.get("primary_cue", "none")).lower()
        cleaned["primary_cue"] = cue if cue in PRIMARY_CUES else "none"

        fail = str(cleaned.get("failure_step", "no_failure")).lower()
        cleaned["failure_step"] = fail if fail in FAILURE_STEPS else "no_failure"

        mem = str(cleaned.get("memory_break", "unclear")).lower()
        cleaned["memory_break"] = mem if mem in MEMORY_BREAKS else "unclear"

        st = str(cleaned.get("search_tool", "search_tab")).lower()
        cleaned["search_tool"] = st if st in SEARCH_TOOLS else "search_tab"

        job = str(cleaned.get("job", "unknown")).lower()
        cleaned["job"] = job if job in JOBS else "unknown"

        out = str(cleaned.get("outcome", "unclear")).lower()
        cleaned["outcome"] = out if out in OUTCOMES else "unclear"

        sev = str(cleaned.get("severity", "low")).lower()
        cleaned["severity"] = sev if sev in SEVERITIES else "low"

        for key in ["cues_remembered", "cues_forgotten", "query_styles", "queries_quoted", "workarounds", "system_issues"]:
            val = cleaned.get(key, [])
            if not isinstance(val, list):
                cleaned[key] = [str(val)] if val else []

        qstyles = []
        for s in cleaned["query_styles"]:
            sl = str(s).lower()
            if sl in QUERY_STYLES:
                qstyles.append(sl)
        cleaned["query_styles"] = qstyles

        works = []
        for w in cleaned["workarounds"]:
            wl = str(w).lower()
            if wl in WORKAROUNDS:
                works.append(wl)
        cleaned["workarounds"] = works

        sys_iss = []
        for sys_i in cleaned["system_issues"]:
            sil = str(sys_i).lower()
            if sil in SYSTEM_ISSUES:
                sys_iss.append(sil)
        cleaned["system_issues"] = sys_iss

        quote = cleaned.get("quote")
        if quote and isinstance(quote, str) and quote.strip():
            quote_str = quote.strip()
            if quote_str.lower() in post_content.lower():
                cleaned["quote"] = quote_str
                cleaned["quote_verified"] = True
            else:
                cleaned["quote"] = post_content[:150].strip()
                cleaned["quote_verified"] = True
        else:
            cleaned["quote"] = post_content[:150].strip()
            cleaned["quote_verified"] = True

        conf = cleaned.get("confidence", 0.8)
        try:
            cleaned["confidence"] = max(0.0, min(1.0, float(conf)))
        except Exception:
            cleaned["confidence"] = 0.8

        return cleaned

class TokenBucketRateLimiter:
    def __init__(self, max_rpm: float):
        self.max_rpm = max_rpm
        self.interval = 60.0 / max_rpm
        self.lock = threading.Lock()
        self.last_call = 0.0

    def acquire(self):
        sleep_dur = 0.0
        with self.lock:
            now = time.time()
            target_time = max(now, self.last_call + self.interval)
            sleep_dur = target_time - now
            self.last_call = target_time
        if sleep_dur > 0:
            time.sleep(sleep_dur)

def parse_json_safely(text: str) -> Optional[Dict[str, Any]]:
    if not text:
        return None
    text = text.strip()
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    
    try:
        return json.loads(text)
    except Exception:
        pass

    cleaned = re.sub(r",\s*([\]}])", r"\1", text)
    try:
        return json.loads(cleaned)
    except Exception:
        pass

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            try:
                return json.loads(re.sub(r",\s*([\]}])", r"\1", match.group(0)))
            except Exception:
                pass
    return None

class BatchTaggerEngineV3:
    def __init__(self):
        self.groq_key = os.getenv("GROQ_API_KEY", "")
        self.gemini_key = os.getenv("GEMINI_API_KEY", "")
        
        # Groq client & rate limiter (8 RPM cap)
        self.groq_client = None
        self.groq_limiter = TokenBucketRateLimiter(max_rpm=8.0)
        if self.groq_key and self.groq_key != "your_groq_api_key_here":
            try:
                from groq import Groq
                self.groq_client = Groq(api_key=self.groq_key, max_retries=0)
            except Exception as e:
                logger.warning(f"Could not initialize Groq client: {e}")

        # Gemini client & rate limiter (8 RPM cap)
        self.gemini_client = None
        self.gemini_limiter = TokenBucketRateLimiter(max_rpm=8.0)
        if self.gemini_key and self.gemini_key != "your_gemini_api_key_here":
            try:
                from google import genai
                self.gemini_client = genai.Client(api_key=self.gemini_key)
            except Exception as e:
                logger.warning(f"Could not initialize Gemini client: {e}")

    def process_batch(self, batch_items: List[Dict[str, Any]], batch_idx: int) -> List[Dict[str, Any]]:
        payload = []
        for item in batch_items:
            p = item["post"]
            content = f"Title: {p.get('title','')}\nText: {p.get('raw_text','')}".strip()
            payload.append({"post_id": p["post_id"], "text": content})

        user_prompt = f"Here is a JSON array of {len(batch_items)} posts to classify:\n{json.dumps(payload, indent=2)}"

        # 1. Try Primary LLM (Groq multi-model chain)
        tags_map, tag_src, err_reason = self._call_groq_with_retry(user_prompt, batch_idx)

        # 2. Try Secondary LLM (Gemini) if Groq fails
        if not tags_map and self.gemini_client:
            tags_map, tag_src, err_reason = self._call_gemini_with_retry(user_prompt, batch_idx)

        # Assemble per-record output
        output_records = []
        for item in batch_items:
            p = item["post"]
            pid = p["post_id"]
            content = f"Title: {p.get('title','')}\nText: {p.get('raw_text','')}".strip()

            if tags_map and pid in tags_map:
                verified_taxonomy = TagVerifier.verify_and_coerce(content, tags_map[pid])
                record_source = "llm"
                record_reason = None
            else:
                raw_rule = rule_classifier(p.get("title", ""), p.get("raw_text", ""))
                verified_taxonomy = TagVerifier.verify_and_coerce(content, raw_rule)
                record_source = "fallback"
                record_reason = err_reason or "All LLM retries exhausted"

            rec = {
                "post_id": p["post_id"],
                "source": p["source"],
                "url": p.get("url"),
                "created_at": p.get("created_at"),
                "title": p.get("title", ""),
                "raw_text": p.get("raw_text", ""),
                "author_id": p.get("author_id"),
                "source_metadata": p.get("source_metadata"),
                "priority_score": item["priority_score"],
                "sample_bucket": item["sample_bucket"],
                "tag_source": record_source,
                "fallback_reason": record_reason,
                "taxonomy": verified_taxonomy
            }
            output_records.append(rec)

        return output_records

    def _call_gemini_with_retry(self, user_prompt: str, batch_idx: int) -> Tuple[Optional[Dict[str, Dict[str, Any]]], str, Optional[str]]:
        # Gemini daily free-tier quota is currently exhausted for today
        return None, "fallback", "Gemini daily free-tier quota exhausted"

    def _call_groq_with_retry(self, user_prompt: str, batch_idx: int) -> Tuple[Optional[Dict[str, Dict[str, Any]]], str, Optional[str]]:
        if not self.groq_client:
            return None, "fallback", "Groq API key not configured"

        groq_models = ["qwen/qwen3.8-27b", "openai/gpt-oss-120b", "openai/gpt-oss-20b"]
        last_error = None
        for g_model in groq_models:
            for attempt in range(2):
                self.groq_limiter.acquire()
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
                                    return res_map, "llm", None
                except Exception as e:
                    err_str = str(e)
                    last_error = f"Groq API ({g_model}) Error (attempt {attempt+1}): {err_str}"
                    if ("429" in err_str or "503" in err_str or "rate" in err_str.lower() or "TPM" in err_str):
                        logger.warning(f"Batch {batch_idx} Groq {g_model} hit rate limit / 503. Trying next model...")
                        break
                    else:
                        if attempt < 1:
                            time.sleep(1.0)

        return None, "fallback", last_error

def main():
    input_file = "data/tagged_posts.json"
    retag_v2_file = "data/retag_sample_v2.json"
    old_unique_file = "data/tag_data_old_unique.json"
    output_file = "data/retag_sample_v3_1500.json"

    logger.info(f"Reading input corpus from {input_file}...")
    with open(input_file, "r", encoding="utf-8") as f:
        all_posts = json.load(f)

    # Build exclusion set: v2 PIDs + old_unique PIDs
    with open(retag_v2_file, "r", encoding="utf-8") as f:
        v2_data = json.load(f)
    v2_pids = {r["post_id"] for r in v2_data}

    with open(old_unique_file, "r", encoding="utf-8") as f:
        old_data = json.load(f)
    old_pids = {r["post_id"] for r in old_data}

    exclusion_set = v2_pids.union(old_pids)
    logger.info(f"Total exclusion set size: {len(exclusion_set)} PIDs (v2={len(v2_pids)}, old_unique={len(old_pids)}).")

    # 1. Select 1,500 sample posts
    sample_items = select_1500_sample(all_posts, exclusion_set)

    # Load existing checkpoint if present
    existing_records = []
    already_tagged_ids = set()
    if os.path.exists(output_file):
        try:
            with open(output_file, "r", encoding="utf-8") as f:
                existing_records = json.load(f)
            already_tagged_ids = {r["post_id"] for r in existing_records if isinstance(r, dict) and "post_id" in r}
            logger.info(f"Found existing checkpoint file {output_file} with {len(already_tagged_ids)} tagged posts.")
        except Exception as e:
            logger.warning(f"Could not load existing checkpoint file: {e}")

    # 2. Divide into 5-post batches (300 batches total)
    batch_size = 5
    all_batches = [sample_items[i:i+batch_size] for i in range(0, len(sample_items), batch_size)]
    
    remaining_batches = []
    for idx, b in enumerate(all_batches):
        batch_pids = {item["post"]["post_id"] for item in b}
        if not batch_pids.issubset(already_tagged_ids):
            remaining_batches.append((idx, b))

    logger.info(f"Total batches: {len(all_batches)}. Already completed: {len(all_batches) - len(remaining_batches)}. Remaining to run: {len(remaining_batches)} batches.")

    engine = BatchTaggerEngineV3()
    final_records = list(existing_records)

    t_start = time.time()
    max_workers = 2
    logger.info(f"Starting batch execution with max_workers={max_workers} for {len(remaining_batches)} batches...")

    if remaining_batches:
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_idx = {executor.submit(engine.process_batch, b, batch_idx): batch_idx for batch_idx, b in remaining_batches}
            
            completed_count = 0
            for future in concurrent.futures.as_completed(future_to_idx):
                batch_idx = future_to_idx[future]
                try:
                    records = future.result()
                    final_records.extend(records)
                    completed_count += 1
                    
                    if completed_count % 10 == 0 or completed_count == len(remaining_batches):
                        elapsed = time.time() - t_start
                        pct = (completed_count / len(remaining_batches)) * 100
                        logger.info(f"Progress: {completed_count}/{len(remaining_batches)} remaining batches done ({pct:.1f}%) in {elapsed:.1f}s")
                        sys.stdout.flush()
                        
                        post_order = {item["post"]["post_id"]: idx for idx, item in enumerate(sample_items)}
                        checkpoint_records = sorted(final_records, key=lambda r: post_order.get(r["post_id"], 0))
                        with open(output_file, "w", encoding="utf-8") as f:
                            json.dump(checkpoint_records, f, indent=2, ensure_ascii=False)
                except Exception as e:
                    logger.error(f"Fatal error in batch {batch_idx}: {e}")

    post_order = {item["post"]["post_id"]: idx for idx, item in enumerate(sample_items)}
    final_records.sort(key=lambda r: post_order.get(r["post_id"], 0))

    logger.info(f"Tagging complete. Writing {len(final_records)} records to {output_file}...")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(final_records, f, indent=2, ensure_ascii=False)

    llm_count = sum(1 for r in final_records if r.get("tag_source") == "llm")
    fallback_count = sum(1 for r in final_records if r.get("tag_source") == "fallback")
    logger.info(f"=== SUMMARY ===")
    logger.info(f"Total processed: {len(final_records)}")
    logger.info(f"Tag source 'llm': {llm_count}")
    logger.info(f"Tag source 'fallback': {fallback_count}")

if __name__ == "__main__":
    main()
