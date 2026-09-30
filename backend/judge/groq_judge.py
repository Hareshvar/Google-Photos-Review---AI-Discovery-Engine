"""
Groq Multi-LLM Blind Judge Engine (Judge A)
Re-tags sample posts without seeing original model tags to evaluate inter-judge agreement.
"""

import os
import json
import time
import logging
from typing import Dict, Any, Optional, List

from backend.models.taxonomy import TaggedTaxonomy
from backend.tagger.verifier import TagVerifier

logger = logging.getLogger(__name__)

SYSTEM_JUDGE_PROMPT = """You are an independent senior UX evaluation judge analyzing user posts about Google Photos search and retrieval struggles.
Re-classify the given user post text according to the exact 21-field codebook below.
You MUST NOT assume any prior labels. Perform a clean, objective blind evaluation.

Return ONLY a valid JSON object matching this schema:
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
  "queries_quoted": [],
  "workarounds": ["scroll_timeline", "check_other_apps", "ask_friends", "browse_folders", "gave_up"],
  "search_tool": "classic_search" | "ask_photos" | "map_view" | "people_pets_tab" | "search_tab",
  "job": "proof_documentation" | "reminiscing" | "sharing_social" | "practical_utility" | "unknown",
  "system_issues": ["missing_results", "wrong_results", "ocr_failure", "face_rec_failure", "date_index_error", "ask_photos_hallucination", "ui_regression"],
  "outcome": "found_eventually" | "not_found" | "partially_found" | "unclear",
  "severity": "low" | "medium" | "high",
  "wish": null,
  "unmapped_note": null,
  "quote": "Exact verbatim snippet from text",
  "confidence": 0.95
}
"""


class GroqJudge:
    """Judge A running blind re-classification via Groq or fallback LLM."""

    def __init__(self, groq_api_key: Optional[str] = None, gemini_api_key: Optional[str] = None):
        self.groq_key = groq_api_key or os.getenv("GROQ_API_KEY", "")
        self.gemini_key = gemini_api_key or os.getenv("GEMINI_API_KEY", "")
        self.groq_model = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

        self._groq_client = None
        self._gemini_client = None

        if self.groq_key and self.groq_key != "your_groq_api_key_here":
            try:
                from groq import Groq
                self._groq_client = Groq(api_key=self.groq_key, max_retries=0)
            except Exception as e:
                logger.debug(f"Could not initialize Groq Judge: {e}")

        if self.gemini_key and self.gemini_key != "your_gemini_api_key_here":
            try:
                from google import genai
                self._gemini_client = genai.Client(api_key=self.gemini_key)
            except Exception as e:
                logger.debug(f"Could not initialize Gemini Judge: {e}")

    def evaluate_post(self, title: str, raw_text: str) -> TaggedTaxonomy:
        full_content = f"Title: {title}\nText: {raw_text}".strip()
        raw_tags = self._call_groq(full_content)

        if not raw_tags:
            raw_tags = self._call_gemini(full_content)

        if not raw_tags:
            raw_tags = self._rule_judge(title, raw_text)

        return TagVerifier.verify_and_coerce(full_content, raw_tags)

    def _call_groq(self, text: str) -> Optional[Dict[str, Any]]:
        if not self._groq_client:
            return None

        try:
            response = self._groq_client.chat.completions.create(
                model=self.groq_model,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": SYSTEM_JUDGE_PROMPT},
                    {"role": "user", "content": f"Post text to re-evaluate:\n{text}"}
                ],
                temperature=0.1
            )
            content = response.choices[0].message.content
            if content:
                return json.loads(content)
        except Exception as e:
            logger.debug(f"Groq judge error: {str(e)}")

        return None

    def _call_gemini(self, text: str) -> Optional[Dict[str, Any]]:
        if not self._gemini_client:
            return None

        from google.genai import types

        try:
            response = self._gemini_client.models.generate_content(
                model=self.gemini_model,
                contents=[SYSTEM_JUDGE_PROMPT, f"Post text to re-evaluate:\n{text}"],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1,
                )
            )
            if response.text:
                return json.loads(response.text)
        except Exception as e:
            logger.debug(f"Gemini judge fallback error: {str(e)}")

        return None

    def _rule_judge(self, title: str, text: str) -> Dict[str, Any]:
        """Independent rule-based judge logic for fallback evaluation."""
        combined = f"{title} {text}".lower()
        
        target_type = "other"
        if any(w in combined for w in ["receipt", "document", "id", "passport", "prescription"]):
            target_type = "document_info"
        elif any(w in combined for w in ["trip", "vacation", "goa", "paris", "hotel", "beach"]):
            target_type = "place_trip"
        elif any(w in combined for w in ["wedding", "birthday", "party", "event"]):
            target_type = "specific_event"
        elif any(w in combined for w in ["face", "person", "dog", "cat", "pet"]):
            target_type = "person_pet"
        elif any(w in combined for w in ["date", "year", "2023", "2024", "2025"]):
            target_type = "date_time"

        primary_cue = "none"
        if "date" in combined or "year" in combined:
            primary_cue = "date_time"
        elif "place" in combined or "location" in combined:
            primary_cue = "location_place"
        elif "face" in combined or "person" in combined:
            primary_cue = "person_face"

        failure_step = "no_or_wrong_results"
        if "scroll" in combined:
            failure_step = "scroll_not_found"

        return {
            "relevant": True,
            "vague_memory": "vague" if "think" in combined else "partial",
            "target_type": target_type,
            "primary_cue": primary_cue,
            "cues_remembered": [primary_cue] if primary_cue != "none" else ["context"],
            "cues_forgotten": ["exact_date"],
            "hedged": False,
            "failure_step": failure_step,
            "memory_break": "forgot_key_detail",
            "query_styles": ["keywords"],
            "queries_quoted": [],
            "workarounds": ["scroll_timeline"],
            "search_tool": "search_tab",
            "job": "proof_documentation" if target_type == "document_info" else "reminiscing",
            "system_issues": ["missing_results"],
            "outcome": "not_found",
            "severity": "medium",
            "wish": None,
            "unmapped_note": None,
            "quote": title if title else text[:80],
            "confidence": 0.85
        }
