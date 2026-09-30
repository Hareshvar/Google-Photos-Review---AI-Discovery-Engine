"""
Code-Side Tag Verification and Quote Substring Checker
Ensures zero enum hallucinations and enforces exact substring quote verification.
"""

import re
import logging
from typing import Dict, Any, Tuple
from backend.models.taxonomy import (
    TaggedTaxonomy,
    VAGUE_MEMORY_TYPES,
    TARGET_TYPES,
    PRIMARY_CUES,
    FAILURE_STEPS,
    MEMORY_BREAKS,
    QUERY_STYLES,
    WORKAROUNDS,
    SEARCH_TOOLS,
    JOBS,
    SYSTEM_ISSUES,
    OUTCOMES,
    SEVERITIES
)

logger = logging.getLogger(__name__)


def normalize_string(text: str) -> str:
    """Normalize whitespace and punctuation for exact substring matching."""
    if not text:
        return ""
    text = re.sub(r"[^\w\s]", "", text.lower())
    return " ".join(text.split())


def verify_substring(original_text: str, snippet: str) -> bool:
    """Check if snippet is an exact normalized substring of original_text."""
    norm_orig = normalize_string(original_text)
    norm_snip = normalize_string(snippet)
    if not norm_snip:
        return False
    return norm_snip in norm_orig


class TagVerifier:
    """Code-side tag verifier enforcing schema compliance and quote validation."""

    @staticmethod
    def verify_and_coerce(original_text: str, raw_tags: Dict[str, Any]) -> TaggedTaxonomy:
        """Coerce enum fields to allowed sets and verify extracted quote substrings."""
        
        # 1. Coerce boolean relevance
        relevant = bool(raw_tags.get("relevant", True))

        # 2. Coerce Single-Select Enums
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

        # 3. Coerce Multi-Select Enums
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

        # 4. Verify Quote Substring Match
        quote = str(raw_tags.get("quote", "")).strip()
        quote_verified = False
        if quote:
            quote_verified = verify_substring(original_text, quote)
            if not quote_verified:
                logger.debug(f"Quote failed substring verification: '{quote}'")

        # 5. Verify Quoted Queries Substring Matches
        raw_queries = raw_tags.get("queries_quoted", [])
        verified_queries = []
        if isinstance(raw_queries, list):
            for q in raw_queries:
                q_str = str(q).strip()
                if q_str and verify_substring(original_text, q_str):
                    verified_queries.append(q_str)

        # Build verified taxonomy object
        return TaggedTaxonomy(
            relevant=relevant,
            vague_memory=vague_memory,
            target_type=target_type,
            primary_cue=primary_cue,
            cues_remembered=[str(c) for c in cues_remembered],
            cues_forgotten=[str(c) for c in cues_forgotten],
            hedged=bool(raw_tags.get("hedged", False)),
            failure_step=failure_step,
            memory_break=memory_break,
            query_styles=query_styles,
            queries_quoted=verified_queries,
            workarounds=workarounds,
            search_tool=search_tool,
            job=job,
            system_issues=system_issues,
            outcome=outcome,
            severity=severity,
            wish=raw_tags.get("wish"),
            unmapped_note=raw_tags.get("unmapped_note"),
            quote=quote,
            quote_verified=quote_verified,
            confidence=float(raw_tags.get("confidence", 0.90))
        )
