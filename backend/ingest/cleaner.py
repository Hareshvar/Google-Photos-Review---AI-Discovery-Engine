"""
Cleaning, Deduplication, and Prefiltration Subsystem for AI Discovery Engine ("Retrieval Lens")
"""

import re
import hashlib
import logging
from typing import List, Tuple, Dict, Set, Any
from backend.models.schema import UnifiedPostRecord, SourceCleanReport, CleanReportSummary

logger = logging.getLogger(__name__)

# Keyword prefilter pattern for photo retrieval terms
RETRIEVAL_KEYWORD_PATTERN = re.compile(
    r"\b(search|find|retrieve|missing|can't find|cannot find|look for|album|date|location|place|face|person|people|pets|text|ocr|screenshot|receipt|medicine|old photo|Ask Photos|photo|picture|gallery|restore|backup)\b",
    re.IGNORECASE
)

PLACEHOLDER_PATTERN = re.compile(
    r"^(\[deleted\]|\[removed\]|null|n/a|none|test|\.|\?)$",
    re.IGNORECASE
)


def get_shingles(text: str, k: int = 3) -> Set[str]:
    """Extract word shingles for MinHash near-duplicate detection."""
    words = re.findall(r"\w+", text.lower())
    if len(words) < k:
        return set([" ".join(words)])
    return set(" ".join(words[i:i+k]) for i in range(len(words) - k + 1))


def jaccard_similarity(set1: Set[str], set2: Set[str]) -> float:
    """Compute Jaccard similarity between two shingle sets."""
    if not set1 or not set2:
        return 0.0
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    return intersection / union if union > 0 else 0.0


def is_english_heuristic(text: str) -> bool:
    """Fast character distribution heuristic to detect English text."""
    if not text:
        return False
    # Check ASCII printable character ratio
    ascii_chars = sum(1 for c in text if ord(c) < 128)
    ratio = ascii_chars / len(text)
    return ratio >= 0.80


class DataCleaner:
    """Pipeline cleaner enforcing deduplication, length floor, placeholder, and keyword prefilters."""

    def __init__(self, near_dup_threshold: float = 0.85, min_words: int = 5):
        self.near_dup_threshold = near_dup_threshold
        self.min_words = min_words

    def clean_records(self, raw_records: List[UnifiedPostRecord]) -> Tuple[List[UnifiedPostRecord], CleanReportSummary]:
        cleaned_records: List[UnifiedPostRecord] = []
        per_source_report: Dict[str, SourceCleanReport] = {}
        
        seen_exact_hashes: Set[str] = set()
        seen_shingles: List[Tuple[str, Set[str]]] = []  # List of (post_id, shingle_set)

        # Initialize report counters per source
        for rec in raw_records:
            if rec.source not in per_source_report:
                per_source_report[rec.source] = SourceCleanReport(
                    source=rec.source,
                    total_raw=0,
                    total_cleaned=0
                )
            per_source_report[rec.source].total_raw += 1

        for rec in raw_records:
            report = per_source_report[rec.source]
            full_text = f"{rec.title} {rec.raw_text}".strip()
            norm_text = " ".join(full_text.lower().split())

            # Rule 1: Placeholder check
            if PLACEHOLDER_PATTERN.match(norm_text) or not norm_text:
                report.placeholder += 1
                continue

            # Rule 2: Length floor check
            word_count = len(norm_text.split())
            if word_count < self.min_words:
                report.short_text += 1
                continue

            # Rule 3: Language check
            if not is_english_heuristic(norm_text):
                report.non_english += 1
                continue

            # Rule 4: Exact deduplication
            text_hash = hashlib.sha256(norm_text.encode("utf-8")).hexdigest()
            if text_hash in seen_exact_hashes:
                report.exact_duplicates += 1
                continue

            # Rule 5: Near-duplicate check
            shingles = get_shingles(norm_text)
            is_near_dup = False
            for prev_id, prev_shingles in seen_shingles[-500:]:  # Check last 500 records for performance
                if jaccard_similarity(shingles, prev_shingles) >= self.near_dup_threshold:
                    is_near_dup = True
                    break

            if is_near_dup:
                report.near_duplicates += 1
                continue

            # Rule 6: Keyword prefilter
            if not RETRIEVAL_KEYWORD_PATTERN.search(norm_text):
                report.prefilter_excluded += 1
                continue

            # If all checks pass, keep record
            seen_exact_hashes.add(text_hash)
            seen_shingles.append((rec.post_id, shingles))
            report.total_cleaned += 1
            cleaned_records.append(rec)

        total_raw = sum(r.total_raw for r in per_source_report.values())
        total_cleaned = len(cleaned_records)
        total_dropped = total_raw - total_cleaned

        summary = CleanReportSummary(
            total_raw_collected=total_raw,
            total_cleaned_kept=total_cleaned,
            total_dropped=total_dropped,
            per_source_report=per_source_report
        )

        logger.info(f"DataCleaner processed {total_raw} raw records -> kept {total_cleaned} clean records ({total_dropped} dropped).")
        return cleaned_records, summary
