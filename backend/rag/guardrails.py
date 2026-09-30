"""
Safety, PII Scrubbing, and Out-of-Scope Guardrails Subsystem
Enforces security, privacy protection, and structured RefusalCard responses.
"""

import re
import logging
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

# PII Regex Patterns
EMAIL_PATTERN = re.compile(r"[\w\.-]+@[\w\.-]+\.\w+")
PHONE_PATTERN = re.compile(r"\b(\+\d{1,3}[- ]?)?\(?\d{3}\)?[- ]?\d{3}[- ]?\d{4}\b")
SSN_ID_PATTERN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b|\b\d{9,12}\b")

# Jailbreak / Injection Patterns
JAILBREAK_PATTERN = re.compile(
    r"\b(ignore\s+(previous|all)\s+instructions|system\s+prompt|jailbreak|bypass|dan\s+mode|override|act\s+as\s+unrestricted)\b",
    re.IGNORECASE
)

# Out-of-Scope Competitor & Demographic Keywords
OUT_OF_SCOPE_PATTERN = re.compile(
    r"\b(apple\s+photos|samsung\s+gallery|icloud\s+revenue|google\s+stock|demographics|user\s+age|salary|income|revenue\s+projection|competitor\s+market\s+share)\b",
    re.IGNORECASE
)

# In-Domain Keywords related to Google Photos, Photo Retrieval, Search, or Dataset
IN_DOMAIN_KEYWORDS = [
    "photo", "photos", "image", "images", "picture", "pictures", "video", "videos", "media",
    "gallery", "album", "albums", "folder", "search", "searching", "retrieval", "retrieve",
    "find", "finding", "lookup", "locate", "query", "queries", "ask photos", "google photos",
    "backup", "back up", "storage", "date", "time", "year", "month", "location", "place", "city",
    "face", "person", "people", "pet", "dog", "cat", "receipt", "document", "invoice", "ocr", "text",
    "screenshot", "memory", "memories", "tag", "tagging", "kpi", "fail", "failure", "error", "bug",
    "dataset", "feedback", "post", "posts", "user", "users", " friction", "issue", "problem",
    "how many", "what percent", "percentage", "share", "driver", "cause", "workaround"
]


class SafetyGuard:
    """Evaluates incoming chatbot prompts against privacy, security, and scope rules."""

    @staticmethod
    def inspect_prompt(prompt: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Inspects prompt string. Returns (is_safe, refusal_payload_if_unsafe)."""
        if not prompt or not prompt.strip():
            msg = "Please type a valid question to search the dataset."
            return False, {
                "status": "refused",
                "is_refusal": True,
                "refusal_type": "no_evidence",
                "reason": "empty_prompt",
                "answer": msg,
                "message": msg,
                "suggested_questions": [
                    "What photo types do users struggle to retrieve most?",
                    "How often do date-based searches fail?"
                ]
            }

        # 1. PII Check
        if EMAIL_PATTERN.search(prompt) or PHONE_PATTERN.search(prompt) or SSN_ID_PATTERN.search(prompt):
            logger.info("PII detected in chat prompt. Triggering privacy refusal.")
            msg = "For privacy protection, please rephrase your question without personal email addresses, phone numbers, or ID numbers."
            return False, {
                "status": "refused",
                "is_refusal": True,
                "refusal_type": "pii_scrubbed",
                "reason": "pii_detected",
                "answer": msg,
                "message": msg,
                "suggested_questions": [
                    "What photo types do users struggle to find?",
                    "What search workarounds do users try?"
                ]
            }

        # 2. Jailbreak Check
        if JAILBREAK_PATTERN.search(prompt):
            logger.warning("Jailbreak attempt detected in chat prompt. Triggering security refusal.")
            msg = "Requests attempting to bypass system instructions or reveal system prompts are refused."
            return False, {
                "status": "refused",
                "is_refusal": True,
                "refusal_type": "out_of_scope",
                "reason": "jailbreak_attempt",
                "answer": msg,
                "message": msg,
                "suggested_questions": [
                    "Where do major search failures occur?",
                    "What cues do users forget most?"
                ]
            }

        # 3. Explicit Out-of-Scope Competitor/Financial Check
        if OUT_OF_SCOPE_PATTERN.search(prompt):
            logger.info("Out-of-scope query detected in chat prompt. Triggering refusal.")
            msg = "I am Retrieval Lens RAG, designed specifically to answer questions about Google Photos search and retrieval user feedback (N=9,774 dataset). I cannot provide competitor metrics, internal financial data, or out-of-scope general knowledge."
            return False, {
                "status": "refused",
                "is_refusal": True,
                "refusal_type": "out_of_scope",
                "reason": "out_of_scope",
                "answer": msg,
                "message": msg,
                "suggested_questions": [
                    "What photo types do users struggle to retrieve most?",
                    "How do users formulate searches when memory is incomplete?",
                    "Which part of the KPI tree has the most failure evidence?"
                ]
            }

        # 4. Domain Relevance Check (Detect General Knowledge Questions like "Who is Obama?", "Who is the PM of India?")
        prompt_lower = prompt.lower()
        is_in_domain = any(kw in prompt_lower for kw in IN_DOMAIN_KEYWORDS)
        
        # General knowledge patterns (who is, what is, how to, tell me, etc.)
        general_knowledge_patterns = [
            r"\bwho\s+is\s+(the\s+)?(pm|prime\s+minister|president|ceo|king|queen|founder|obama|modi|biden|trump|musk)\b",
            r"\bwho\s+is\b",
            r"\bwho\s+was\b",
            r"\bwho\s+are\b",
            r"\bwhat\s+is\s+(the\s+)?(capital|population|gdp|currency|weather|formula|recipe|meaning|definition)\b",
            r"\bhow\s+to\s+(cook|make|code|program|build|install|fix|play|draw|write)\b",
            r"\btell\s+me\s+a\s+(joke|story|fact|poem|riddle)\b",
            r"\bwrite\s+(a\s+)?(python|javascript|code|essay|script|letter|email)\b",
            r"\bwho\s+won\b"
        ]
        
        is_general_knowledge = any(re.search(pat, prompt_lower) for pat in general_knowledge_patterns)

        # If prompt has no in-domain keyword OR matches general knowledge patterns, refuse politely
        if not is_in_domain or is_general_knowledge:
            logger.info(f"General knowledge / out-of-domain prompt detected: '{prompt}'. Triggering refusal.")
            msg = "I am Retrieval Lens RAG, designed specifically to answer questions about Google Photos search and retrieval user feedback (N=9,774 dataset). Your question appears to be out of scope. Please ask a question related to user photo retrieval friction, search failures, or feedback insights."
            return False, {
                "status": "refused",
                "is_refusal": True,
                "refusal_type": "out_of_scope",
                "reason": "out_of_scope",
                "answer": msg,
                "message": msg,
                "suggested_questions": [
                    "What photo types do users struggle to retrieve most?",
                    "How do users formulate searches when memory is incomplete?",
                    "Which part of the KPI tree has the most failure evidence?"
                ]
            }

        return True, None

        return True, None
