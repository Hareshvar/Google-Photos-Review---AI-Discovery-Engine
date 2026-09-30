"""
Gemini Tiebreaker Engine (Judge B)
Resolves classification disputes between Primary Tagger and Groq Judge A.
"""

import os
import json
import logging
from typing import Dict, Any, Optional

from backend.models.taxonomy import TaggedTaxonomy

logger = logging.getLogger(__name__)

SYSTEM_TIEBREAKER_PROMPT = """You are the Senior Arbitration Judge for a UX research taxonomy classification project on Google Photos retrieval issues.

Two independent AI classifiers disagreed on how to categorize a user's post.
Your job is to read the post, review the conflicting classifications, and determine the single most accurate, objective consensus tag.

Return ONLY a valid JSON object with the final resolved fields and your brief rationale:
{
  "consensus_target_type": "string enum",
  "consensus_failure_step": "string enum",
  "consensus_primary_cue": "string enum",
  "consensus_outcome": "string enum",
  "consensus_severity": "string enum",
  "winning_judge": "primary" | "judge_a" | "synthesis",
  "resolution_reasoning": "Concise 1-sentence explanation of why this classification was chosen"
}
"""


class GeminiTiebreaker:
    """Judge B resolving classification conflicts between Primary Tagger & Judge A."""

    def __init__(self, gemini_api_key: Optional[str] = None):
        self.gemini_key = gemini_api_key or os.getenv("GEMINI_API_KEY", "")
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
        self._client = None

        if self.gemini_key and self.gemini_key != "your_gemini_api_key_here":
            try:
                from google import genai
                self._client = genai.Client(api_key=self.gemini_key)
            except Exception as e:
                logger.debug(f"Could not initialize Gemini Tiebreaker: {e}")

    def resolve_dispute(
        self,
        title: str,
        raw_text: str,
        primary_tax: Dict[str, Any],
        judge_a_tax: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Resolves tag conflict between Primary Tagger and Judge A."""
        dispute_prompt = f"""
Post Title: {title}
Post Text: {raw_text}

Classifier 1 (Primary Tagger):
- Target Type: {primary_tax.get('target_type')}
- Failure Step: {primary_tax.get('failure_step')}
- Primary Cue: {primary_tax.get('primary_cue')}
- Outcome: {primary_tax.get('outcome')}
- Severity: {primary_tax.get('severity')}

Classifier 2 (Judge A - Blind Groq):
- Target Type: {judge_a_tax.get('target_type')}
- Failure Step: {judge_a_tax.get('failure_step')}
- Primary Cue: {judge_a_tax.get('primary_cue')}
- Outcome: {judge_a_tax.get('outcome')}
- Severity: {judge_a_tax.get('severity')}
"""

        res = self._call_llm(dispute_prompt)
        if res:
            return res

        # Deterministic fallback synthesis if API unavailable
        return self._deterministic_fallback(primary_tax, judge_a_tax)

    def _call_llm(self, prompt: str) -> Optional[Dict[str, Any]]:
        if not self._client:
            return None

        from google.genai import types

        try:
            response = self._client.models.generate_content(
                model=self.gemini_model,
                contents=[SYSTEM_TIEBREAKER_PROMPT, prompt],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1
                )
            )
            if response.text:
                return json.loads(response.text)
        except Exception as e:
            logger.debug(f"Gemini Tiebreaker LLM call failed: {e}")

        return None

    def _deterministic_fallback(
        self, primary_tax: Dict[str, Any], judge_a_tax: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fallback tiebreaker selection favoring higher confidence or non-generic enum values."""
        target_type = primary_tax.get("target_type")
        if target_type == "other" and judge_a_tax.get("target_type") != "other":
            target_type = judge_a_tax.get("target_type")
            winning_judge = "judge_a"
        else:
            winning_judge = "primary"

        failure_step = primary_tax.get("failure_step")
        if failure_step == "unclear" and judge_a_tax.get("failure_step") != "unclear":
            failure_step = judge_a_tax.get("failure_step")

        return {
            "consensus_target_type": target_type,
            "consensus_failure_step": failure_step,
            "consensus_primary_cue": primary_tax.get("primary_cue"),
            "consensus_outcome": primary_tax.get("outcome"),
            "consensus_severity": primary_tax.get("severity"),
            "winning_judge": winning_judge,
            "resolution_reasoning": "Selected specific non-generic taxonomy enum through rule-based tiebreaking."
        }
