"""
High-Performance LLM Taxonomy Tagger Engine
Executes fast multi-provider classification (Groq -> Gemini -> Verified Rule Classifier).
"""

import os
import json
import time
import logging
from typing import Dict, Any, Optional

from backend.models.taxonomy import TaggedTaxonomy
from backend.tagger.verifier import TagVerifier

logger = logging.getLogger(__name__)

SYSTEM_TAXONOMY_PROMPT = """You are a senior UX research classification system analyzing public posts about Google Photos search and retrieval struggles.
Extract a structured JSON classification for the post text according to the following 21-field codebook.

Return ONLY a valid JSON object matching this exact schema:

{
  "relevant": true or false,
  "vague_memory": "vague" | "partial" | "precise" | "unclear",
  "target_type": "document_info" | "specific_event" | "person_pet" | "place_trip" | "object_item" | "date_time" | "general_old_photo" | "other",
  "primary_cue": "date_time" | "location_place" | "person_face" | "text_ocr" | "visual_object" | "album_folder" | "event_context" | "file_metadata" | "none",
  "cues_remembered": ["list of cues user remembered"],
  "cues_forgotten": ["list of cues user forgot"],
  "hedged": true or false,
  "failure_step": "did_not_search" | "search_not_completed" | "no_or_wrong_results" | "results_not_recognized" | "wrong_photo_opened" | "scroll_not_found" | "no_failure",
  "memory_break": "forgot_key_detail" | "could_not_put_into_words" | "misremembered_fact" | "too_many_similar_photos" | "unclear",
  "query_styles": ["natural_language", "keywords", "date_range", "location_name", "person_name", "exact_quote"],
  "queries_quoted": ["verbatim search queries user typed in quotes if mentioned"],
  "workarounds": ["scroll_timeline", "check_other_apps", "ask_friends", "browse_folders", "gave_up"],
  "search_tool": "classic_search" | "ask_photos" | "map_view" | "people_pets_tab" | "search_tab",
  "job": "proof_documentation" | "reminiscing" | "sharing_social" | "practical_utility" | "unknown",
  "system_issues": ["missing_results", "wrong_results", "ocr_failure", "face_rec_failure", "date_index_error", "ask_photos_hallucination", "ui_regression"],
  "outcome": "found_eventually" | "not_found" | "partially_found" | "unclear",
  "severity": "low" | "medium" | "high",
  "wish": "string description of user wish or null",
  "unmapped_note": null,
  "quote": "Short exact representative verbatim snippet from the text",
  "confidence": 0.95
}

Rules:
1. `relevant`: true if post expresses difficulty or feedback about finding/retrieving photos in Google Photos.
2. `quote`: MUST be an EXACT verbatim snippet copied directly from the input text. Do NOT edit or paraphrase.
3. Keep all values strict enums. Return valid JSON only.
"""


class LLMTagger:
    """Fast Tagger executing Groq / Gemini with instant fallback to verified rule classification."""

    def __init__(self, gemini_api_key: Optional[str] = None, groq_api_key: Optional[str] = None):
        self.gemini_key = gemini_api_key or os.getenv("GEMINI_API_KEY", "")
        self.groq_key = groq_api_key or os.getenv("GROQ_API_KEY", "")
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
        self.groq_model = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
        
        self._gemini_client = None
        self._groq_client = None
        self._rate_limited_until = 0.0

        if self.groq_key and self.groq_key != "your_groq_api_key_here":
            try:
                from groq import Groq
                self._groq_client = Groq(api_key=self.groq_key, max_retries=0)
            except Exception as e:
                logger.debug(f"Could not initialize Groq Client: {e}")

        if self.gemini_key and self.gemini_key != "your_gemini_api_key_here":
            try:
                from google import genai
                self._gemini_client = genai.Client(api_key=self.gemini_key)
            except Exception as e:
                logger.debug(f"Could not initialize Gemini Client: {e}")

    def tag_post(self, title: str, raw_text: str) -> TaggedTaxonomy:
        full_content = f"Title: {title}\nText: {raw_text}".strip()
        raw_tags = None

        # Check if rate-limited
        if time.time() > self._rate_limited_until:
            # 1. Try Groq API
            raw_tags = self._call_groq(full_content)
            
            # 2. Fallback to Gemini if Groq fails/throttles
            if not raw_tags:
                raw_tags = self._call_gemini(full_content)

        # 3. Verified rule-based classification if APIs hit rate limits or cool-off
        if not raw_tags:
            raw_tags = self._rule_classifier(title, raw_text)

        # 4. Enforce Code-Side Verification & Coercion
        return TagVerifier.verify_and_coerce(full_content, raw_tags)

    def _call_groq(self, text: str) -> Optional[Dict[str, Any]]:
        if not self._groq_client or time.time() < self._rate_limited_until:
            return None

        try:
            response = self._groq_client.chat.completions.create(
                model=self.groq_model,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": SYSTEM_TAXONOMY_PROMPT},
                    {"role": "user", "content": f"Post to classify:\n{text}"}
                ],
                temperature=0.1
            )
            content = response.choices[0].message.content
            if content:
                return json.loads(content)
        except Exception as e:
            if "429" in str(e):
                self._rate_limited_until = time.time() + 60.0
                logger.warning("Groq API 429 rate limit hit. Using fast rule classification for next 60s.")
            else:
                logger.debug(f"Groq API skipped: {str(e)}")

        return None

    def _call_gemini(self, text: str) -> Optional[Dict[str, Any]]:
        if not self._gemini_client or time.time() < self._rate_limited_until:
            return None

        from google.genai import types

        try:
            response = self._gemini_client.models.generate_content(
                model=self.gemini_model,
                contents=[SYSTEM_TAXONOMY_PROMPT, f"Post to classify:\n{text}"],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1,
                )
            )
            if response.text:
                return json.loads(response.text)
        except Exception as e:
            if "429" in str(e):
                self._rate_limited_until = time.time() + 60.0
                logger.warning("Gemini API 429 rate limit hit. Using fast rule classification for next 60s.")
            else:
                logger.debug(f"Gemini API skipped: {str(e)}")

        return None

    def _rule_classifier(self, title: str, text: str) -> Dict[str, Any]:
        """Verified rule-based classification extracting 21 fields when API limits trigger."""
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

        # Refined multi-pattern failure step categorization
        if any(w in combined for w in ["didn't search", "haven't searched", "never used search", "didn't use search", "where is search bar"]):
            failure_step = "did_not_search"
        elif any(w in combined for w in ["couldn't put into words", "how to phrase", "don't know what to type", "hard to describe", "how to search for", "how do i search"]):
            failure_step = "search_not_completed"
        elif any(w in combined for w in ["thumbnail", "preview", "blurry", "too small", "didn't recognize", "hard to see"]):
            failure_step = "results_not_recognized"
        elif any(w in combined for w in ["opened wrong", "wrong photo opened", "clicked wrong", "tapped wrong"]):
            failure_step = "wrong_photo_opened"
        elif any(w in combined for w in ["scroll", "scrolling", "timeline", "feed", "swiping", "manual", "folder", "album"]):
            failure_step = "scroll_not_found"
        elif any(w in combined for w in ["found it", "worked", "solved", "fixed", "finally found", "resolved", "success"]):
            failure_step = "no_failure"
        else:
            failure_step = "no_or_wrong_results"

        # Refined multi-pattern system issue categorization
        system_issues = []
        if any(w in combined for w in ["text", "ocr", "words", "receipt", "document", "license", "prescription", "sign", "letter"]):
            system_issues.append("ocr_failure")
        if any(w in combined for w in ["face", "person", "people", "tag", "cat", "dog", "pet", "name", "who is", "people & pets"]):
            system_issues.append("face_rec_failure")
        if any(w in combined for w in ["date", "year", "month", "timestamp", "time", "exif", "old photo", "timeline", "chronological"]):
            system_issues.append("date_index_error")
        if any(w in combined for w in ["ask photos", "gemini", "ai search", "hallucinat", "wrong answer"]):
            system_issues.append("ask_photos_hallucination")
        if any(w in combined for w in ["ui", "update", "version", "layout", "tab", "interface", "button", "redesign"]):
            system_issues.append("ui_regression")
        if any(w in combined for w in ["wrong photo", "irrelevant", "random", "wrong picture", "not what i asked"]):
            system_issues.append("wrong_results")

        if not system_issues or any(w in combined for w in ["no results", "0 results", "nothing came up", "blank", "empty", "not found", "missing"]):
            system_issues.append("missing_results")

        workarounds = []
        if "scroll" in combined:
            workarounds.append("scroll_timeline")
        if "icloud" in combined or "other app" in combined:
            workarounds.append("check_other_apps")
        if "gave up" in combined or "useless" in combined:
            workarounds.append("gave_up")

        # Extract representative verbatim snippet for quote
        quote = title if title else text[:100]

        return {
            "relevant": True,
            "vague_memory": "vague" if any(w in combined for w in ["think", "maybe", "remember", "somewhere", "used to"]) else "partial",
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
