"""
Self-Describing Export Dashboard Bundle Generator for Retrieval Lens
Produces standalone JSON bundle (retrieval_lens_analysis_bundle.json) containing
all precomputed stats, glossary, named clusters, situations, and 9 key insights.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)

GLOSSARY_DEFINITIONS = {
    "target_type": "The category of visual content the user was attempting to retrieve (e.g. document/receipt, place/trip, person/pet, specific event).",
    "primary_cue": "The primary memory clue the user possessed when starting the search (e.g. date/time, location, person face, OCR text).",
    "failure_step": "The specific interaction stage where the retrieval journey broke down (e.g. no or wrong results, scroll not found, search not completed).",
    "memory_break": "The cognitive friction in the user's memory (e.g. forgot key detail, could not put into words, misremembered fact).",
    "opportunity_score": "Composite prioritization metric scaled 0-100: Share (%) x Avg Severity (1-3) x Unresolved Rate (0-1) scaled to 0-100.",
    "unresolved_rate": "Fraction of users in a situation group who either failed to find the photo or gave up searching.",
    "quote_verified": "Boolean indicator showing the extracted user quote was verified via exact substring matching against the source text.",
    "residual_disclosure": "Transparency count of records that did not fit a named theme, excluded from ranked charts per PRD Section 4.3."
}


class BundleBuilder:
    """Builds self-describing research analysis JSON export bundle."""

    def __init__(self, data_dir: str = "./data"):
        self.data_dir = data_dir
        self.precomputed_file = os.path.join(data_dir, "precomputed_stats.json")
        self.clean_report_file = os.path.join(data_dir, "clean_report.json")
        self.source_probe_file = os.path.join(data_dir, "source_probe.json")
        self.bundle_file = os.path.join(data_dir, "retrieval_lens_analysis_bundle.json")

    def build_bundle(self) -> Dict[str, Any]:
        """Load data files and construct self-describing export JSON object."""
        precomputed = self._load_json(self.precomputed_file, {})
        clean_report = self._load_json(self.clean_report_file, {})
        source_probe = self._load_json(self.source_probe_file, [])

        metadata = precomputed.get("metadata", {})

        bundle_payload = {
            "title": "Retrieval Lens - Google Photos Photo Retrieval Research Export Bundle",
            "version": "2.0.0",
            "exported_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "metadata": {
                "total_collected": clean_report.get("total_raw_collected", 0),
                "total_cleaned": clean_report.get("total_cleaned_kept", 0),
                "total_relevant": metadata.get("total_relevant", 0),
                "total_dropped": clean_report.get("total_dropped", 0)
            },
            "glossary": GLOSSARY_DEFINITIONS,
            "pipeline_diagnostics": {
                "source_health": source_probe,
                "cleaning_audit": clean_report
            },
            "themes": precomputed.get("themes", {}),
            "situations": {
                "ranked_situations": precomputed.get("situations", []),
                "tail_aggregated": precomputed.get("situations_tail_aggregated"),
                "formula": precomputed.get("opportunity_score_formula")
            },
            "key_insights": precomputed.get("key_insights", [])
        }

        # Save bundle file
        with open(self.bundle_file, "w", encoding="utf-8") as f:
            json.dump(bundle_payload, f, indent=2, ensure_ascii=False)

        logger.info(f"Generated self-describing export bundle: {self.bundle_file}")
        return bundle_payload

    def _load_json(self, filepath: str, default: Any) -> Any:
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Error loading {filepath}: {str(e)}")
        return default
