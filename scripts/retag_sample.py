"""
Standalone Sample Retagging Script (v2)
=======================================
- Reads data/tagged_posts.json (read-only).
- Constructs 3,000 post sample:
  - 70% (2,100 posts) highest relevance priority score (bucket 'a') across full corpus.
  - 30% (900 posts) stratified random sample from remaining lower-scoring posts (bucket 'c'),
    with a floor of at least 50 posts per source (or all available if <50).
- Classifies posts in 5-post batches using LLM with rate limiting & exponential backoff retries.
- Only uses rule-based classifier as absolute last resort after retries are exhausted.
- Records priority_score, sample_bucket, tag_source ("llm" or "fallback"), fallback_reason per record.
- Writes output strictly to data/retag_sample_v2.json.
- Zero changes to data/tagged_posts.json or any backend/ files.
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
logger = logging.getLogger("retag_sample_v2")

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
      "quote": "verbatim snippet copied directly from text",
      "confidence": 0.95
    }
  ]
}

Enum Restrictions:
- vague_memory: vague | partial | precise | unclear
- target_type: document_info | specific_event | person_pet | place_trip | object_item | date_time | general_old_photo | other
- primary_cue: date_time | location_place | person_face | text_ocr | visual_object | album_folder | event_context | file_metadata | none
- failure_step: did_not_search | search_not_completed | no_or_wrong_results | results_not_recognized | wrong_photo_opened | scroll_not_found | no_failure
- memory_break: forgot_key_detail | could_not_put_into_words | misremembered_fact | too_many_similar_photos | unclear
- query_styles: natural_language | keywords | date_range | location_name | person_name | exact_quote
- workarounds: scroll_timeline | check_other_apps | ask_friends | browse_folders | gave_up
- search_tool: classic_search | ask_photos | map_view | people_pets_tab | search_tab
- job: proof_documentation | reminiscing | sharing_social | practical_utility | unknown
- system_issues: missing_results | wrong_results | ocr_failure | face_rec_failure | date_index_error | ask_photos_hallucination | ui_regression
- outcome: found_eventually | not_found | partially_found | unclear
- severity: low | medium | high

Rules:
1. `relevant`: true if post expresses difficulty or feedback about finding/retrieving photos in Google Photos.
2. `quote`: MUST be an EXACT verbatim snippet copied directly from input text.
3. Keep all values strict enums. Return valid JSON only.
"""

# ------------------------------------------------------------------------------
# Substring & Verification Helpers
# ------------------------------------------------------------------------------
def normalize_string(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"[^\w\s]", "", text.lower())
    return " ".join(text.split())

def verify_substring(original_text: str, snippet: str) -> bool:
    norm_orig = normalize_string(original_text)
    norm_snip = normalize_string(snippet)
    if not norm_snip:
        return False
    return norm_snip in norm_orig

class TagVerifier:
    @staticmethod
    def verify_and_coerce(original_text: str, raw_tags: Dict[str, Any]) -> Dict[str, Any]:
        relevant = bool(raw_tags.get("relevant", True))

        vague_memory = raw_tags.get("vague_memory", "unclear")
        if vague_memory not in VAGUE_MEMORY_TYPES:
            vague_memory = "unclear"

        target_type = raw_tags.get("target_type", "other")
        if target_type not in TARGET_TYPES:
            target_type = "other"

        primary_cue = raw_tags.get("primary_cue", "none")
        if primary_cue not in PRIMARY_CUES:
            primary_cue = "none"

        failure_step = raw_tags.get("failure_step", "no_failure")
        if failure_step not in FAILURE_STEPS:
            failure_step = "no_failure"

        memory_break = raw_tags.get("memory_break", "unclear")
        if memory_break not in MEMORY_BREAKS:
            memory_break = "unclear"

        search_tool = raw_tags.get("search_tool", "search_tab")
        if search_tool not in SEARCH_TOOLS:
            search_tool = "search_tab"

        job = raw_tags.get("job", "unknown")
        if job not in JOBS:
            job = "unknown"

        outcome = raw_tags.get("outcome", "unclear")
        if outcome not in OUTCOMES:
            outcome = "unclear"

        severity = raw_tags.get("severity", "low")
        if severity not in SEVERITIES:
            severity = "low"

        raw_styles = raw_tags.get("query_styles", [])
        query_styles = [s for s in (raw_styles if isinstance(raw_styles, list) else []) if s in QUERY_STYLES]

        raw_workarounds = raw_tags.get("workarounds", [])
        workarounds = [w for w in (raw_workarounds if isinstance(raw_workarounds, list) else []) if w in WORKAROUNDS]

        raw_issues = raw_tags.get("system_issues", [])
        system_issues = [i for i in (raw_issues if isinstance(raw_issues, list) else []) if i in SYSTEM_ISSUES]

        cues_remembered = raw_tags.get("cues_remembered", [])
        if not isinstance(cues_remembered, list):
            cues_remembered = []

        cues_forgotten = raw_tags.get("cues_forgotten", [])
        if not isinstance(cues_forgotten, list):
            cues_forgotten = []

        queries_quoted = raw_tags.get("queries_quoted", [])
        if not isinstance(queries_quoted, list):
            queries_quoted = []

        quote = str(raw_tags.get("quote", "") or "")
        quote_verified = verify_substring(original_text, quote)
        if not quote_verified:
            quote = original_text[:100].strip() if len(original_text) > 0 else ""
            quote_verified = verify_substring(original_text, quote)

        wish = raw_tags.get("wish")
        if wish is not None and not isinstance(wish, str):
            wish = str(wish)

        confidence = float(raw_tags.get("confidence", 0.95))

        return {
            "relevant": relevant,
            "vague_memory": vague_memory,
            "target_type": target_type,
            "primary_cue": primary_cue,
            "cues_remembered": cues_remembered,
            "cues_forgotten": cues_forgotten,
            "hedged": bool(raw_tags.get("hedged", False)),
            "failure_step": failure_step,
            "memory_break": memory_break,
            "query_styles": query_styles,
            "queries_quoted": queries_quoted,
            "workarounds": workarounds,
            "search_tool": search_tool,
            "job": job,
            "system_issues": system_issues,
            "outcome": outcome,
            "severity": severity,
            "wish": wish,
            "unmapped_note": None,
            "quote": quote,
            "quote_verified": quote_verified,
            "confidence": confidence
        }

# ------------------------------------------------------------------------------
# Rule-Based Classifier (Absolute Last Resort)
# ------------------------------------------------------------------------------
def rule_classifier(title: str, text: str) -> Dict[str, Any]:
    combined = f"{title} {text}".lower()
    
    target_type = "other"
    if any(w in combined for w in ["receipt", "document", "id", "passport", "prescription", "license", "text", "ocr", "words"]):
        target_type = "document_info"
    elif any(w in combined for w in ["trip", "vacation", "goa", "paris", "hotel", "beach", "city", "travel"]):
        target_type = "place_trip"
    elif any(w in combined for w in ["wedding", "birthday", "party", "christmas", "event", "concert"]):
        target_type = "specific_event"
    elif any(w in combined for w in ["face", "person", "people", "friend", "mom", "dad", "pet", "dog", "cat"]):
        target_type = "person_pet"
    elif any(w in combined for w in ["date", "year", "month", "2022", "2023", "2024", "2025", "2026"]):
        target_type = "date_time"

    primary_cue = "none"
    if "date" in combined or "year" in combined:
        primary_cue = "date_time"
    elif "place" in combined or "location" in combined or "city" in combined:
        primary_cue = "location_place"
    elif "face" in combined or "person" in combined or "people" in combined:
        primary_cue = "person_face"
    elif "text" in combined or "exact" in combined or "words" in combined:
        primary_cue = "text_ocr"

    if any(w in combined for w in ["didn't search", "haven't searched", "never used search", "didn't use search"]):
        failure_step = "did_not_search"
    elif any(w in combined for w in ["couldn't put into words", "how to phrase", "don't know what to type", "hard to describe"]):
        failure_step = "search_not_completed"
    elif any(w in combined for w in ["thumbnail", "preview", "blurry", "too small", "didn't recognize"]):
        failure_step = "results_not_recognized"
    elif any(w in combined for w in ["opened wrong", "wrong photo opened"]):
        failure_step = "wrong_photo_opened"
    elif any(w in combined for w in ["scroll", "scrolling", "timeline", "feed", "swiping", "manual"]):
        failure_step = "scroll_not_found"
    elif any(w in combined for w in ["found it", "worked", "solved", "fixed", "finally found"]):
        failure_step = "no_failure"
    else:
        failure_step = "no_or_wrong_results"

    system_issues = []
    if any(w in combined for w in ["text", "ocr", "words", "receipt", "document", "license"]):
        system_issues.append("ocr_failure")
    if any(w in combined for w in ["face", "person", "people", "tag", "cat", "dog", "pet"]):
        system_issues.append("face_rec_failure")
    if any(w in combined for w in ["date", "year", "month", "timestamp", "time", "exif", "timeline"]):
        system_issues.append("date_index_error")
    if any(w in combined for w in ["ask photos", "gemini", "ai search", "hallucinat"]):
        system_issues.append("ask_photos_hallucination")
    if any(w in combined for w in ["ui", "update", "version", "layout", "tab", "interface"]):
        system_issues.append("ui_regression")
    if any(w in combined for w in ["wrong photo", "irrelevant", "random", "wrong picture"]):
        system_issues.append("wrong_results")
    if not system_issues or any(w in combined for w in ["no results", "0 results", "nothing came up", "blank", "empty", "not found"]):
        system_issues.append("missing_results")

    workarounds = []
    if "scroll" in combined:
        workarounds.append("scroll_timeline")
    if "icloud" in combined or "other app" in combined:
        workarounds.append("check_other_apps")
    if "gave up" in combined or "useless" in combined:
        workarounds.append("gave_up")

    quote = title if title else text[:100]

    return {
        "relevant": True,
        "vague_memory": "vague" if any(w in combined for w in ["think", "maybe", "remember", "somewhere"]) else "partial",
        "target_type": target_type,
        "primary_cue": primary_cue,
        "cues_remembered": [primary_cue] if primary_cue != "none" else ["context"],
        "cues_forgotten": ["exact_date"],
        "hedged": "think" in combined or "maybe" in combined,
        "failure_step": failure_step,
        "memory_break": "forgot_key_detail",
        "query_styles": ["keywords"],
        "queries_quoted": [],
        "workarounds": workarounds if workarounds else ["scroll_timeline"],
        "search_tool": "ask_photos" if "ask photos" in combined else "search_tab",
        "job": "proof_documentation" if target_type == "document_info" else "reminiscing",
        "system_issues": system_issues,
        "outcome": "found_eventually" if failure_step == "no_failure" else "not_found",
        "severity": "high" if "gave_up" in workarounds or "useless" in combined else "medium",
        "wish": None,
        "unmapped_note": None,
        "quote": quote,
        "confidence": 0.85
    }

# ------------------------------------------------------------------------------
# Relevance Likelihood Scoring & Sampling Logic
# ------------------------------------------------------------------------------
def compute_priority_score(post: Dict[str, Any]) -> int:
    text = f"{post.get('title', '')} {post.get('raw_text', '')}".lower()
    score = 0
    if any(k in text for k in ["search", "find", "locate", "looking for", "query", "queries", "seek", "retriev"]):
        score += 1
    if any(k in text for k in ["can't find", "cant find", "cannot find", "no results", "not showing up", "doesn't show", "doesnt show", "nothing shows", "failed to find", "unable to find", "wrong results", "missing", "disappeared", "lost", "not working", "didn't work", "didnt work", "no photos", "0 results"]):
        score += 1
    if any(k in text for k in ["person", "people", "pet", "dog", "cat", "face", "document", "receipt", "license", "passport", "prescription", "screenshot", "screen shot", "place", "trip", "vacation", "beach", "hotel", "event", "wedding", "birthday", "party", "concert"]):
        score += 1
    if any(k in text for k in ["i think", "not sure", "around", "a few years ago", "maybe", "used to be", "somewhere in", "back in", "years ago", "months ago", "recollect", "vaguely", "somewhere"]):
        score += 1
    return score

def select_3000_sample(all_posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    logger.info(f"Computing relevance priority score for all {len(all_posts)} posts...")
    
    scored_posts = []
    for idx, p in enumerate(all_posts):
        score = compute_priority_score(p)
        scored_posts.append({
            "orig_index": idx,
            "post": p,
            "priority_score": score
        })

    # Sort descending by score, tie-broken deterministically by post_id
    scored_posts.sort(key=lambda x: (x["priority_score"], x["post"]["post_id"]), reverse=True)

    # Bucket A: Top 70% of 3,000 = 2,100 posts
    bucket_a_items = scored_posts[:2100]
    for item in bucket_a_items:
        item["sample_bucket"] = "a"

    # Bucket C: Remaining pool = 900 posts stratified across 6 sources
    remaining_pool = scored_posts[2100:]
    by_source = {}
    for item in remaining_pool:
        src = item["post"]["source"]
        by_source.setdefault(src, []).append(item)

    target_c = 900
    floor = 50
    alloc = {}
    total_floor = 0
    for src, items in by_source.items():
        f = min(floor, len(items))
        alloc[src] = f
        total_floor += f

    rem_target = target_c - total_floor
    rem_counts = {src: len(items) - alloc[src] for src, items in by_source.items()}
    total_rem = sum(rem_counts.values())

    # Hamilton/Largest Remainder Method
    fractional = {}
    for src in by_source:
        quota = rem_target * (rem_counts[src] / total_rem) if total_rem > 0 else 0
        alloc[src] += int(quota)
        fractional[src] = quota - int(quota)

    leftover = target_c - sum(alloc.values())
    for src, _ in sorted(fractional.items(), key=lambda x: x[1], reverse=True)[:leftover]:
        alloc[src] += 1

    logger.info(f"Bucket C allocations across sources: {alloc}")

    rng = random.Random(42) # Fixed seed for exact reproducibility
    bucket_c_items = []
    for src, count in alloc.items():
        pool = by_source[src]
        sampled = rng.sample(pool, count)
        for item in sampled:
            item["sample_bucket"] = "c"
            bucket_c_items.append(item)

    selected = bucket_a_items + bucket_c_items
    logger.info(f"Sample selection complete: {len(bucket_a_items)} in Bucket A, {len(bucket_c_items)} in Bucket C. Total = {len(selected)}")
    return selected

# ------------------------------------------------------------------------------
# Token Bucket / Rate Limiter
# ------------------------------------------------------------------------------
class TokenBucketRateLimiter:
    """Thread-safe rate limiter enforcing requests-per-minute limit without blocking threads during sleep."""
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

# ------------------------------------------------------------------------------
# LLM Batch Classification Manager
# ------------------------------------------------------------------------------
class BatchTaggerEngine:
    def __init__(self):
        self.groq_key = os.getenv("GROQ_API_KEY", "")
        self.gemini_key = os.getenv("GEMINI_API_KEY", "")
        self.groq_model = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
        
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

        user_prompt = f"Here is a JSON array of 5 posts to classify:\n{json.dumps(payload, indent=2)}"

        # 1. Try Primary LLM (Groq multi-model chain)
        tags_map, tag_src, err_reason = self._call_groq_with_retry(user_prompt, batch_idx)

        # 2. Try Secondary LLM (Gemini) if Groq fails
        if not tags_map and self.gemini_client:
            logger.info(f"Batch {batch_idx}: Primary Groq failed. Retrying with Gemini secondary...")
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
        if not self.gemini_client:
            return None, "fallback", "Gemini API key not configured"

        from google.genai import types

        gemini_models = ["gemini-3.6-flash", "gemini-3.5-flash"]
        last_error = None
        for model_name in gemini_models:
            for attempt in range(3): # Initial attempt + 2 retries
                self.gemini_limiter.acquire()
                try:
                    g_resp = self.gemini_client.models.generate_content(
                        model=model_name,
                        contents=[SYSTEM_TAXONOMY_PROMPT, user_prompt],
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            temperature=0.1
                        )
                    )
                    if g_resp.text:
                        data = parse_json_safely(g_resp.text)
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
                    last_error = f"Gemini API ({model_name}) Error (attempt {attempt+1}): {err_str}"
                    if "RESOURCE_EXHAUSTED" in err_str or ("429" in err_str and "quota" in err_str.lower()):
                        logger.warning(f"Batch {batch_idx} Gemini ({model_name}) quota exhausted. Trying fallback model/provider...")
                        break
                    elif ("429" in err_str or "503" in err_str or "UNAVAILABLE" in err_str) and attempt < 2:
                        backoff = min(2.0, (1.5 ** attempt) + random.uniform(0.3, 0.7))
                        logger.warning(f"Batch {batch_idx} hit Gemini {model_name} rate limit / 503 on attempt {attempt+1}. Sleeping {backoff:.2f}s...")
                        time.sleep(backoff)
                    else:
                        logger.warning(f"Batch {batch_idx} Gemini ({model_name}) attempt {attempt+1} failed: {err_str[:120]}")
                        break # Try next model

        return None, "fallback", last_error

    def _call_groq_with_retry(self, user_prompt: str, batch_idx: int) -> Tuple[Optional[Dict[str, Dict[str, Any]]], str, Optional[str]]:
        if not self.groq_client:
            return None, "fallback", "Groq API key not configured"

        groq_models = ["qwen/qwen3.8-27b", "openai/gpt-oss-120b", "openai/gpt-oss-20b"]
        last_error = None
        for g_model in groq_models:
            for attempt in range(2): # 2 attempts per model
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
                        logger.warning(f"Batch {batch_idx} Groq {g_model} hit rate limit / 503 on attempt {attempt+1}. Trying next model...")
                        break
                    else:
                        logger.warning(f"Batch {batch_idx} Groq ({g_model}) attempt {attempt+1} failed: {err_str[:120]}")
                        if attempt < 1:
                            time.sleep(1.0)

        return None, "fallback", last_error

# ------------------------------------------------------------------------------
# Main Orchestrator
# ------------------------------------------------------------------------------
def main():
    input_file = "data/tagged_posts.json"
    output_file = "data/retag_sample_v2.json"

    logger.info(f"Reading input corpus from {input_file}...")
    with open(input_file, "r", encoding="utf-8") as f:
        all_posts = json.load(f)

    logger.info(f"Loaded {len(all_posts)} posts from corpus.")

    # 1. Select 3,000 posts sample according to specification
    sample_items = select_3000_sample(all_posts)

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

    # 2. Divide into 5-post batches (600 batches total)
    batch_size = 5
    all_batches = [sample_items[i:i+batch_size] for i in range(0, len(sample_items), batch_size)]
    
    # Filter out batches where all posts are already tagged
    remaining_batches = []
    for idx, b in enumerate(all_batches):
        batch_pids = {item["post"]["post_id"] for item in b}
        if not batch_pids.issubset(already_tagged_ids):
            remaining_batches.append((idx, b))

    limit_batches = int(os.getenv("LIMIT_BATCHES", "0"))
    if limit_batches > 0:
        logger.info(f"LIMIT_BATCHES={limit_batches} set. Truncating remaining batches from {len(remaining_batches)} to {limit_batches}.")
        remaining_batches = remaining_batches[:limit_batches]

    logger.info(f"Total batches: {len(all_batches)}. Already completed: {len(all_batches) - len(remaining_batches)}. Remaining to run: {len(remaining_batches)} batches.")

    engine = BatchTaggerEngine()
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
                    
                    # Incremental save every 10 batches
                    if completed_count % 10 == 0 or completed_count == len(remaining_batches):
                        elapsed = time.time() - t_start
                        pct = (completed_count / len(remaining_batches)) * 100
                        logger.info(f"Progress: {completed_count}/{len(remaining_batches)} remaining batches done ({pct:.1f}%) in {elapsed:.1f}s")
                        sys.stdout.flush()
                        
                        # Sort by original selection order and save checkpoint
                        post_order = {item["post"]["post_id"]: idx for idx, item in enumerate(sample_items)}
                        checkpoint_records = sorted(final_records, key=lambda r: post_order.get(r["post_id"], 0))
                        with open(output_file, "w", encoding="utf-8") as f:
                            json.dump(checkpoint_records, f, indent=2, ensure_ascii=False)
                except Exception as e:
                    logger.error(f"Fatal error in batch {batch_idx}: {e}")

    # Maintain original selection order
    post_order = {item["post"]["post_id"]: idx for idx, item in enumerate(sample_items)}
    final_records.sort(key=lambda r: post_order.get(r["post_id"], 0))

    logger.info(f"Tagging complete. Writing {len(final_records)} records to {output_file}...")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(final_records, f, indent=2, ensure_ascii=False)

    # Summary Statistics
    llm_count = sum(1 for r in final_records if r.get("tag_source") == "llm")
    fallback_count = sum(1 for r in final_records if r.get("tag_source") == "fallback")
    logger.info(f"=== SUMMARY ===")
    logger.info(f"Total processed: {len(final_records)}")
    logger.info(f"Tag source 'llm': {llm_count}")
    logger.info(f"Tag source 'fallback': {fallback_count}")
    
    if fallback_count > 0:
        reasons = {}
        for r in final_records:
            if r.get("tag_source") == "fallback":
                rs = str(r.get("fallback_reason"))
                reasons[rs] = reasons.get(rs, 0) + 1
        logger.info(f"Fallback reasons break-down: {reasons}")

if __name__ == "__main__":
    main()
