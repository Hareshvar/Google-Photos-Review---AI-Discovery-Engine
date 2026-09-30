"""
Grounded LLM Summary Writer for Key Insights (Q1-Q9)
Writes grounded research summaries from precomputed stats (Zero LLM arithmetic).
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

SUMMARY_PROMPT = """You are a Senior UX Researcher & Product Manager analyzing public feedback on Google Photos retrieval failure.

Write a clear, structured, and insightful executive summary paragraph (3-4 sentences) answering this research question for product stakeholders:
"{question}"

Empirical Data provided:
- Total evidence sample: n={n}
- Category Breakdown / Distribution: {distribution_summary}
- Representative verified user quotes: {quotes_summary}

Strict Grounding & Formatting Rules:
1. Explain clearly what this question measures and what the primary categories/drivers represent for product design.
2. State ONLY exact numbers, percentages, and figures provided in the data above. NEVER invent figures.
3. Highlight key user behaviors or friction points illustrated by the verbatim quotes.
4. FORMATTING RULE: ALWAYS use formal human-readable category labels (e.g. "Exact Date & Time", "Event Context", "Document or Receipt", "Remembered Location"). NEVER use raw technical enum strings like "exact_date", "context", "date_time", "cues_remembered", or "target_type", and NEVER use erratic markdown bolding like **exact_date** or **context**.
5. Keep the tone professional, objective, and executive-ready.
"""


class SummaryWriter:
    """Generates grounded research summaries for all 9 Key Insight cards."""

    def __init__(self):
        self.gemini_key = os.getenv("GEMINI_API_KEY", "")
        self.groq_key = os.getenv("GROQ_API_KEY", "")
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self.groq_model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        
        self._gemini_client = None
        self._groq_client = None

        if self.groq_key and self.groq_key != "your_groq_api_key_here":
            try:
                from groq import Groq
                self._groq_client = Groq(api_key=self.groq_key, max_retries=1)
            except Exception as e:
                logger.warning(f"Failed to initialize Groq client: {e}")

        if self.gemini_key and self.gemini_key != "your_gemini_api_key_here":
            try:
                from google import genai
                self._gemini_client = genai.Client(api_key=self.gemini_key)
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini client: {e}")

    def write_summaries(self, insight_cards: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        for card in insight_cards:
            # PRD Section 6.2 Low Evidence Rule Safeguard
            if card.get("is_low_evidence", False):
                card["summary"] = card.get("low_evidence_warning") or f"Low empirical evidence (n={card.get('evidence_n', 0)}). Requires qualitative research validation."
                logger.info(f"Q{card['number']} marked as low evidence. Set fallback warning summary.")
                continue

            # Generate grounded LLM summary from precomputed numbers
            question = card["question"]
            n = card.get("evidence_n") or card.get("n_sample") or 0
            dist = card.get("distribution", [])
            dist_str = json.dumps(dist)
            quotes_str = json.dumps([q.get("quote") if isinstance(q, dict) else q for q in card.get("example_quotes", [])])

            prompt = SUMMARY_PROMPT.format(
                question=question,
                n=n,
                distribution_summary=dist_str,
                quotes_summary=quotes_str
            )

            raw_summary = self._generate_text(prompt)
            if not raw_summary:
                # Rich deterministic fallback if LLM is offline
                top_item = dist[0] if dist else {}
                top_cat = top_item.get("category") or top_item.get("label", "primary driver")
                top_pct = top_item.get("share_pct") or top_item.get("pct", 0)
                top_count = top_item.get("count", 0)
                raw_summary = (
                    f"Analysis of n={n:,} user feedback records reveals that '{top_cat}' represents the largest retrieval hurdle, "
                    f"accounting for {top_pct}% ({top_count:,} posts) of reported cases. "
                    f"Users encounter significant friction attempting to query this category, highlighting critical gaps in search indexing and contextual metadata matching."
                )

            clean_summary = self._clean_summary_text(raw_summary)
            card["summary"] = clean_summary
            logger.info(f"Generated grounded summary for Q{card['number']}.")

        return insight_cards

    def _clean_summary_text(self, summary: str) -> str:
        if not summary:
            return ""
        
        # Clean Mojibake encoding artifacts
        replacements = {
            "â€œ": '"',
            "â€": '"',
            "â€™": "'",
            "â€˜": "'",
            "â€”": "—",
            "â€“": "–",
            "â€¦": "...",
            "â€¢": "•",
            "âpets and peopleâ": '"pets and people"',
            "â": "",
            "Ã©": "é",
        }
        for bad, good in replacements.items():
            summary = summary.replace(bad, good)

        # Standardize technical enum terms into clean human labels without bold asterisks
        raw_enum_map = {
            "**exact_date**": "Exact Date & Time",
            "**context**": "Event & Memory Context",
            "**date_time**": "Date & Time",
            "**location_place**": "Remembered Location",
            "**person_face**": "Person / Face",
            "**text_ocr**": "Text inside Photo (OCR)",
            "**document_info**": "Document or Receipt",
            "**person_pet**": "Person or Pet Photo",
            "**place_trip**": "Place or Trip Photo",
            "**general_old_photo**": "General Old Memory",
            "\"exact_date\"": "Exact Date & Time",
            "\"context\"": "Event & Memory Context",
            "\"date_time\"": "Date & Time",
            "`exact_date`": "Exact Date & Time",
            "`context`": "Event Context",
            " exact_date ": " Exact Date ",
        }
        for bad, good in raw_enum_map.items():
            summary = summary.replace(bad, good)

        return summary.strip()

    def _generate_text(self, prompt: str) -> Optional[str]:
        # Try Groq API first
        if self._groq_client:
            try:
                resp = self._groq_client.chat.completions.create(
                    model=self.groq_model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2
                )
                if resp.choices and resp.choices[0].message.content:
                    return resp.choices[0].message.content.strip()
            except Exception as e:
                logger.warning(f"Groq API call failed: {e}")

        # Try Gemini API second
        if self._gemini_client:
            try:
                resp = self._gemini_client.models.generate_content(
                    model=self.gemini_model,
                    contents=prompt
                )
                if resp.text:
                    return resp.text.strip()
            except Exception as e:
                logger.warning(f"Gemini API call failed: {e}")

        return None

