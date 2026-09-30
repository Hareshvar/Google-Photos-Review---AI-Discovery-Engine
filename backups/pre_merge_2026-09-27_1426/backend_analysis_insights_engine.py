"""
Key Insights Aggregation Engine for the 9 Core PRD Research Questions
Calculates statistical distributions, verbatim query tables, and n < 10 fallback states.
"""

import logging
import re
from collections import Counter
from typing import List, Dict, Any, Tuple
from backend.models.taxonomy import TaggedPostRecord, FAILURE_STEPS

logger = logging.getLogger(__name__)

# Appendix C Failure-Step to KPI Tree Static Reference Table
KPI_TREE_MAPPING = {
    "did_not_search": "Search-bar CTR",
    "search_not_completed": "Search completion rate",
    "no_or_wrong_results": "No-result rate / Image CTR",
    "results_not_recognized": "Image CTR",
    "wrong_photo_opened": "Bounce rate",
    "scroll_not_found": "Scroll rate / Photo-open rate",
    "no_failure": "Baseline retrieval success"
}

HUMAN_LABELS_MAP = {
    "document_info": "Document or receipt",
    "specific_event": "Specific event or party",
    "person_pet": "Person or pet photo",
    "place_trip": "Place or trip photo",
    "object_item": "Specific object or item",
    "date_time": "Photo from a specific time",
    "general_old_photo": "General old memory",
    "other": "Other photo type",

    "context": "Event & Activity Context",
    "event_context": "Event & Activity Context",
    "exact_date": "Exact Date & Time",
    "date_time": "Date / time period",
    "location_place": "Location / place",
    "person_face": "Person / face",
    "text_ocr": "Text inside photo (OCR)",
    "visual_object": "Visual object",
    "album_folder": "Album / folder name",
    "file_metadata": "File metadata",
    "none": "No specific clue",

    "natural_language": "Natural language query",
    "keywords": "Keywords / descriptors",
    "date_range": "Date range",
    "location_name": "Location name",
    "person_name": "Person name",
    "exact_quote": "Exact text in quotes",

    "scroll_timeline": "Scrolled main timeline",
    "check_other_apps": "Switched to competitor / other apps",
    "ask_friends": "Asked friends / family",
    "browse_folders": "Browsed device folders",
    "gave_up": "Gave up search",

    "missing_results": "Missing expected results",
    "wrong_results": "Returned wrong results",
    "ocr_failure": "OCR text extraction failed",
    "face_rec_failure": "Face / person recognition failed",
    "date_index_error": "Date indexing error",
    "ask_photos_hallucination": "Ask Photos hallucinated context",
    "ui_regression": "UI feature regression"
}

def clean_mojibake(text: str) -> str:
    if not text:
        return ""
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
        text = text.replace(bad, good)
    return re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text).strip()

QUESTION_KEYWORDS = {
    "q1": ["receipt", "document", "invoice", "bill", "pdf", "tax", "ticket", "passport", "license", "screenshot", "face", "person", "baby", "pet", "dog", "cat", "trip", "travel", "vacation", "beach", "car", "bike", "event", "wedding", "party", "old photo", "memory"],
    "q2": ["remember", "remembered", "memory", "memories", "wedding", "birthday", "trip", "vacation", "beach", "family", "baby", "kid", "dog", "cat", "pet", "face", "person", "people", "year ago", "years ago", "date", "taken in", "location", "place", "city", "text in photo", "ocr"],
    "q3": ["forgot", "forget", "forgotten", "don't know", "don't remember", "can't remember", "no date", "no location", "missing date", "exact date", "timestamp", "year", "when", "where", "who", "exif", "time"],
    "q4": ["search", "typed", "searched for", "query", "trying to search", "looking for", "natural language", "keywords", "exact quote", "quotes", "ask photos"],
    "q5": ["words", "describe", "how to search", "express", "put into words", "can't explain", "how to find", "search for"],
    "q6": ["search not working", "wrong results", "no results", "ocr failed", "face recognition", "face search", "date index", "hallucinated", "incorrect", "returns nothing", "cant find"],
    "q7": ["thumbnail", "preview", "recognize", "small", "blur", "can't tell", "difficult to see", "which photo", "wrong photo opened", "bounce", "opened"],
    "q8": ["scroll", "scrolling", "timeline", "manual", "gave up", "switched", "gallery", "other app", "drive", "takeout", "folder", "browse"],
    "q9": ["did not search", "search bar", "no results", "wrong results", "scroll timeline", "gave up", "bounce", "ctr", "photo opened"]
}

SPAM_AND_IRRELEVANT_TERMS = [
    "ai models", "orchestrator", "claude/codex", "perplexity", "subscription", "warranty",
    "sub folder", "album permission", "share photo location setting", "uninstall", "storage full",
    "three finger screenshot", "default app", "app crash", "battery drain", "jerks", "crazy",
    "how to delete", "remove memories"
]


class InsightsEngine:
    """Calculates empirical distributions and grounding stats for Q1-Q9."""

    @staticmethod
    def build_all_insights(relevant_posts: List[TaggedPostRecord]) -> List[Dict[str, Any]]:
        if not relevant_posts:
            return []

        total_relevant = len(relevant_posts)

        insights = [
            InsightsEngine._build_q1(relevant_posts, total_relevant),
            InsightsEngine._build_q2(relevant_posts, total_relevant),
            InsightsEngine._build_q3(relevant_posts, total_relevant),
            InsightsEngine._build_q4(relevant_posts, total_relevant),
            InsightsEngine._build_q5(relevant_posts, total_relevant),
            InsightsEngine._build_q6(relevant_posts, total_relevant),
            InsightsEngine._build_q7(relevant_posts, total_relevant),
            InsightsEngine._build_q8(relevant_posts, total_relevant),
            InsightsEngine._build_q9(relevant_posts, total_relevant),
        ]

        logger.info(f"Aggregated statistics for all 9 Key Insights research questions.")
        return insights

    @staticmethod
    def _extract_quotes(posts: List[TaggedPostRecord], q_id: str = "q1", max_quotes: int = 3) -> List[Dict[str, str]]:
        keywords = QUESTION_KEYWORDS.get(q_id, [])
        candidates = []

        for p in posts:
            quote = p.taxonomy.quote or p.title
            if not quote or not p.taxonomy.quote_verified:
                continue

            clean_q = clean_mojibake(quote)
            if len(clean_q) < 20 or len(clean_q) > 220:
                continue

            text_lower = (clean_q + " " + (p.title or '')).lower()
            
            # Calculate relevance score (P0)
            score = 0.0
            for kw in keywords:
                if re.search(r'\b' + re.escape(kw) + r'\b', text_lower):
                    score += 3.5

            # Penalize spam / promotional / irrelevant posts
            for spam in SPAM_AND_IRRELEVANT_TERMS:
                if spam in text_lower:
                    score -= 15.0

            candidates.append({
                "quote": clean_q,
                "source": p.source or 'unknown',
                "url": p.url or '',
                "post_id": p.post_id,
                "score": score
            })

        # Sort candidates by relevance score descending
        candidates.sort(key=lambda x: x['score'], reverse=True)

        # Pick quotes with source diversity as P1 tie-breaker
        selected = []
        used_sources = set()

        # Pass 1: candidates with positive relevance & new source
        for c in candidates:
            if c['score'] > 0 and c['source'] not in used_sources:
                selected.append(c)
                used_sources.add(c['source'])
                if len(selected) >= max_quotes:
                    break

        # Pass 2: candidates with positive relevance score even if duplicate source
        if len(selected) < max_quotes:
            selected_ids = {s['post_id'] for s in selected}
            for c in candidates:
                if c['score'] > 0 and c['post_id'] not in selected_ids:
                    selected.append(c)
                    if len(selected) >= max_quotes:
                        break

        # Pass 3: fallback to highest scoring candidate available if < max_quotes
        if len(selected) < max_quotes:
            selected_ids = {s['post_id'] for s in selected}
            for c in candidates:
                if c['post_id'] not in selected_ids:
                    selected.append(c)
                    if len(selected) >= max_quotes:
                        break

        return [{
            "quote": item["quote"],
            "source": item["source"],
            "url": item["url"],
            "post_id": item["post_id"]
        } for item in selected[:max_quotes]]

    @staticmethod
    def _check_low_evidence(n: int, unclear_count: int, total: int) -> Tuple[bool, str]:
        """PRD Section 6.2 Low Evidence Rule (Threshold: n < 3)."""
        if n < 3:
            return True, f"There isn't enough evidence in the collected data to answer this confidently (n={n}). This should be validated through user research."
        return False, ""

    @staticmethod
    def _build_q1(posts: List[TaggedPostRecord], total_relevant: int) -> Dict[str, Any]:
        target_posts = [p for p in posts if p.taxonomy.failure_step != "no_failure"]
        n = len(target_posts)
        counts = Counter(p.taxonomy.target_type for p in target_posts)
        
        distribution = []
        for type_key, count in counts.most_common():
            distribution.append({
                "category": HUMAN_LABELS_MAP.get(type_key, type_key),
                "key": type_key,
                "count": count,
                "share_pct": round((count / n) * 100, 2) if n > 0 else 0
            })

        is_low, low_msg = InsightsEngine._check_low_evidence(n, counts.get("other", 0), n)

        return {
            "id": "q1",
            "number": 1,
            "question": "What kinds of old photos do users struggle to retrieve?",
            "evidence_n": n,
            "is_low_evidence": is_low,
            "low_evidence_warning": low_msg if is_low else None,
            "chart_type": "bar_chart",
            "distribution": distribution,
            "example_quotes": InsightsEngine._extract_quotes(target_posts, q_id="q1")
        }

    @staticmethod
    def _build_q2(posts: List[TaggedPostRecord], total_relevant: int) -> Dict[str, Any]:
        target_posts = [p for p in posts if p.taxonomy.cues_remembered]
        n = len(target_posts)
        
        all_cues = []
        for p in target_posts:
            all_cues.extend(p.taxonomy.cues_remembered)
        
        counts = Counter(all_cues)
        
        distribution = []
        for cue_key, count in counts.most_common():
            distribution.append({
                "category": HUMAN_LABELS_MAP.get(cue_key, cue_key),
                "key": cue_key,
                "count": count,
                "share_pct": round((count / n) * 100, 2) if n > 0 else 0
            })

        is_low, low_msg = InsightsEngine._check_low_evidence(n, counts.get("none", 0), n)

        return {
            "id": "q2",
            "number": 2,
            "question": "What information do people actually remember about a photo?",
            "evidence_n": n,
            "is_low_evidence": is_low,
            "low_evidence_warning": low_msg if is_low else None,
            "chart_type": "bar_chart",
            "distribution": distribution,
            "example_quotes": InsightsEngine._extract_quotes(target_posts, q_id="q2")
        }

    @staticmethod
    def _build_q3(posts: List[TaggedPostRecord], total_relevant: int) -> Dict[str, Any]:
        target_posts = [p for p in posts if p.taxonomy.cues_forgotten]
        n = len(target_posts)
        
        all_cues = []
        for p in target_posts:
            all_cues.extend(p.taxonomy.cues_forgotten)
        
        counts = Counter(all_cues)
        
        distribution = []
        for cue_key, count in counts.most_common():
            distribution.append({
                "category": HUMAN_LABELS_MAP.get(cue_key, cue_key),
                "key": cue_key,
                "count": count,
                "share_pct": round((count / n) * 100, 2) if n > 0 else 0
            })

        is_low, low_msg = InsightsEngine._check_low_evidence(n, counts.get("none", 0), n)

        return {
            "id": "q3",
            "number": 3,
            "question": "What information have they forgotten?",
            "evidence_n": n,
            "is_low_evidence": is_low,
            "low_evidence_warning": low_msg if is_low else None,
            "chart_type": "bar_chart",
            "distribution": distribution,
            "example_quotes": InsightsEngine._extract_quotes(target_posts, q_id="q3")
        }

    @staticmethod
    def _build_q4(posts: List[TaggedPostRecord], total_relevant: int) -> Dict[str, Any]:
        vague_posts = [
            p for p in posts 
            if p.taxonomy.vague_memory in ("vague", "partial") 
            and (p.taxonomy.query_styles or p.taxonomy.queries_quoted)
        ]
        n = len(vague_posts)
        
        styles = []
        verbatim_queries = []
        for p in vague_posts:
            styles.extend(p.taxonomy.query_styles)
            for q in p.taxonomy.queries_quoted:
                verbatim_queries.append({"query": q, "post_id": p.post_id, "source": p.source})

        counts = Counter(styles)
        distribution = []
        for style_key, count in counts.most_common():
            distribution.append({
                "category": HUMAN_LABELS_MAP.get(style_key, style_key),
                "key": style_key,
                "count": count,
                "share_pct": round((count / n) * 100, 2) if n > 0 else 0
            })

        is_low, low_msg = InsightsEngine._check_low_evidence(n, 0, n)

        return {
            "id": "q4",
            "number": 4,
            "question": "How do users formulate searches when their memory is incomplete?",
            "evidence_n": n,
            "is_low_evidence": is_low,
            "low_evidence_warning": low_msg if is_low else None,
            "chart_type": "bar_chart_plus_table",
            "distribution": distribution,
            "verbatim_queries": verbatim_queries[:10],
            "example_quotes": InsightsEngine._extract_quotes(vague_posts, q_id="q4")
        }

    @staticmethod
    def _build_q5(posts: List[TaggedPostRecord], total_relevant: int) -> Dict[str, Any]:
        target_posts = [
            p for p in posts 
            if p.taxonomy.failure_step == "search_not_completed" or p.taxonomy.memory_break == "could_not_put_into_words"
        ]
        n = len(target_posts)
        is_low, low_msg = InsightsEngine._check_low_evidence(n, 0, total_relevant)

        return {
            "id": "q5",
            "number": 5,
            "question": "Is the user unable to express what they remember?",
            "evidence_n": n,
            "is_low_evidence": is_low,
            "low_evidence_warning": low_msg if is_low else None,
            "chart_type": "stat_count",
            "stat_value": n,
            "share_pct": round((n / total_relevant) * 100, 2),
            "evidence_strength": "Moderate evidence" if n >= 10 else "Thin evidence",
            "example_quotes": InsightsEngine._extract_quotes(target_posts, q_id="q5")
        }

    @staticmethod
    def _build_q6(posts: List[TaggedPostRecord], total_relevant: int) -> Dict[str, Any]:
        target_posts = [p for p in posts if p.taxonomy.failure_step == "no_or_wrong_results"]
        n = len(target_posts)
        
        all_issues = []
        for p in target_posts:
            all_issues.extend(p.taxonomy.system_issues)

        counts = Counter(all_issues)
        distribution = []
        for issue_key, count in counts.most_common():
            distribution.append({
                "category": HUMAN_LABELS_MAP.get(issue_key, issue_key),
                "key": issue_key,
                "count": count,
                "share_pct": round((count / n) * 100, 2) if n > 0 else 0
            })

        is_low, low_msg = InsightsEngine._check_low_evidence(n, 0, n)

        return {
            "id": "q6",
            "number": 6,
            "question": "Does Google Photos fail to understand the clues they provide?",
            "evidence_n": n,
            "is_low_evidence": is_low,
            "low_evidence_warning": low_msg if is_low else None,
            "chart_type": "bar_chart",
            "distribution": distribution,
            "example_quotes": InsightsEngine._extract_quotes(target_posts, q_id="q6")
        }

    @staticmethod
    def _build_q7(posts: List[TaggedPostRecord], total_relevant: int) -> Dict[str, Any]:
        target_posts = [
            p for p in posts 
            if p.taxonomy.failure_step in ("results_not_recognized", "wrong_photo_opened")
        ]
        n = len(target_posts)
        is_low, low_msg = InsightsEngine._check_low_evidence(n, 0, total_relevant)

        return {
            "id": "q7",
            "number": 7,
            "question": "Are potentially relevant results difficult to evaluate?",
            "evidence_n": n,
            "is_low_evidence": is_low,
            "low_evidence_warning": low_msg if is_low else None,
            "chart_type": "stat_count",
            "stat_value": n,
            "share_pct": round((n / total_relevant) * 100, 2),
            "evidence_note": "Evidence is relatively sparse for evaluation friction." if is_low else "Sufficient empirical evidence.",
            "example_quotes": InsightsEngine._extract_quotes(target_posts, q_id="q7")
        }

    @staticmethod
    def _build_q8(posts: List[TaggedPostRecord], total_relevant: int) -> Dict[str, Any]:
        refine_signals = {"scroll_timeline", "check_other_apps", "ask_friends", "browse_folders"}
        target_posts = [
            p for p in posts 
            if any(wa in refine_signals for wa in (p.taxonomy.workarounds or []))
        ]
        n = len(target_posts)
        
        all_workarounds = []
        for p in target_posts:
            for wa in p.taxonomy.workarounds:
                if wa in refine_signals:
                    all_workarounds.append(wa)
        
        counts = Counter(all_workarounds)
        distribution = []
        for wa_key, count in counts.most_common():
            distribution.append({
                "category": HUMAN_LABELS_MAP.get(wa_key, wa_key),
                "key": wa_key,
                "count": count,
                "share_pct": round((count / n) * 100, 2) if n > 0 else 0
            })

        is_low, low_msg = InsightsEngine._check_low_evidence(n, 0, n)

        return {
            "id": "q8",
            "number": 8,
            "question": "Does the user struggle to refine an unsuccessful search?",
            "evidence_n": n,
            "is_low_evidence": is_low,
            "low_evidence_warning": low_msg if is_low else None,
            "chart_type": "bar_chart",
            "distribution": distribution,
            "example_quotes": InsightsEngine._extract_quotes(target_posts, q_id="q8")
        }

    @staticmethod
    def _build_q9(posts: List[TaggedPostRecord], total_relevant: int) -> Dict[str, Any]:
        n = len(posts)
        counts = Counter(p.taxonomy.failure_step for p in posts)
        
        distribution = []
        kpi_mapping_list = []
        for step_key in FAILURE_STEPS:
            count = counts.get(step_key, 0)
            share_pct = round((count / n) * 100, 2)
            kpi_step = KPI_TREE_MAPPING.get(step_key, "Other CTR")
            
            distribution.append({
                "category": step_key.replace("_", " ").title(),
                "key": step_key,
                "count": count,
                "share_pct": share_pct,
                "kpi_tree_step": kpi_step
            })

            kpi_mapping_list.append({
                "failure_step": step_key,
                "kpi_tree_step": kpi_step,
                "count": count
            })

        distribution.sort(key=lambda item: item["count"], reverse=True)
        is_low, low_msg = InsightsEngine._check_low_evidence(n, 0, n)

        return {
            "id": "q9",
            "number": 9,
            "question": "Which part of the KPI tree do the major breaks happen in?",
            "evidence_n": n,
            "is_low_evidence": is_low,
            "low_evidence_warning": low_msg if is_low else None,
            "chart_type": "bar_chart_plus_kpi_table",
            "distribution": distribution,
            "kpi_mapping_table": kpi_mapping_list,
            "example_quotes": InsightsEngine._extract_quotes(posts, q_id="q9")
        }
