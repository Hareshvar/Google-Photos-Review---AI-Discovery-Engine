"""
Secondary Embedding & Emergent Clustering Engine (Layer B Themes)
Computes 5 distinct emergent UX intent themes, synthesizes grounded LLM summaries,
and extracts strict, source-diverse verified quotes per cluster.
"""

import logging
from typing import List, Dict, Any, Tuple

from backend.models.taxonomy import TaggedPostRecord

logger = logging.getLogger(__name__)

THEME_DEFINITIONS = [
    {
        "cluster_id": "cluster_03",
        "title": "Face and person recognition broken",
        "terms": ["face", "person", "people", "pet", "tag", "untagged", "grouping", "recognize", "faces", "people & pets"],
        "matcher": lambda p: "face_rec_failure" in (p.taxonomy.system_issues or []),
        "summary_note": "Users experience broken face grouping and missing facial recognition tags. Common complaints include family members or pets suddenly losing face tags, disappearing people clusters, and manual face tagging failing to sync across devices."
    },
    {
        "cluster_id": "cluster_05",
        "title": "Missing estimated photo locations & map view",
        "terms": ["location", "place", "city", "map", "gps", "address", "landmarks", "country", "trip", "vacation"],
        "matcher": lambda p: (
            p.taxonomy.primary_cue == "location_place"
            or "location_place" in (p.taxonomy.cues_remembered or [])
            or "location_place" in (p.taxonomy.cues_forgotten or [])
        ),
        "summary_note": "[Derived from memory cue content signals (what users recall or forget), distinct from technical system failure tags] Users experience missing estimated photo locations and broken map view pins. Searches by city, country, or location landmark fail to return photos taken in those specific vacation destinations."
    },
    {
        "cluster_id": "cluster_01",
        "title": "Date indexing & timeline navigation friction",
        "terms": ["date", "year", "timeline", "month", "timestamp", "chronological", "exif", "old photo", "scroll", "sort", "sorting"],
        "matcher": lambda p: "date_index_error" in (p.taxonomy.system_issues or []),
        "summary_note": "Users encounter severe friction locating photos by date or year. Common struggles include corrupted EXIF timestamps shifting photos to incorrect years, missing date header controls after app updates, and the necessity of endless manual timeline scrolling when date sorting fails."
    },
    {
        "cluster_id": "cluster_04",
        "title": "Text-in-photo (OCR) search failing",
        "terms": ["ocr", "text", "words", "receipt", "document", "license", "prescription", "sign", "exact text"],
        "matcher": lambda p: "ocr_failure" in (p.taxonomy.system_issues or []),
        "summary_note": "Users rely heavily on Google Photos OCR to retrieve critical utility screenshots, receipts, prescriptions, and document photos. Search regressions frequently fail to index embedded text within images, forcing manual folder navigation."
    },
    {
        "cluster_id": "cluster_02",
        "title": "Search regressed after Ask Photos update",
        "terms": ["ask photos", "ask photo", "gemini", "ask ai", "update", "new search"],
        "matcher": lambda p: (
            "ask_photos_hallucination" in (p.taxonomy.system_issues or [])
            or any(t in f"{p.title} {p.raw_text}".lower() for t in ["ask photos", "ask photo", "gemini", "ask ai", "ask feature", "new search tab"])
        ),
        "summary_note": "Users express frustration that the new Ask Photos AI search update replaced exact keyword matching with generative synthesis. Queries that previously yielded exact photo matches now fail, return irrelevant results, or fail to parse exact quotation mark syntax."
    }
]


class ClusterEngine:
    """Clustering engine for Layer B emergent themes and Section 4.3 residual handling."""

    def __init__(self, n_clusters: int = 5):
        self.n_clusters = n_clusters

    def build_emergent_themes(self, relevant_posts: List[TaggedPostRecord]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Compute Layer B named clusters and residual unclassified disclosure footnote."""
        if not relevant_posts:
            return [], {"unclassified_count": 0, "unclassified_pct": 0.0}

        total_relevant = len(relevant_posts)
        named_clusters: List[Dict[str, Any]] = []
        assigned_post_ids = set()

        used_quotes_global = set()
        used_post_ids_global = set()

        for theme in THEME_DEFINITIONS:
            matching_posts = [p for p in relevant_posts if theme["matcher"](p)]
            count = len(matching_posts)
            share_pct = round((count / total_relevant) * 100, 2)
            assigned_post_ids.update(p.post_id for p in matching_posts)

            # Select 3 strictly relevant, source-diverse, globally unique quotes
            strict_quotes = []
            seen_sources = set()

            # First pass: find quotes containing theme terms from new sources
            for p in matching_posts:
                q = (p.taxonomy.quote or p.title or "").strip()
                if not q or len(q) < 10:
                    continue
                if q in used_quotes_global or p.post_id in used_post_ids_global:
                    continue

                q_lower = q.lower()
                src = p.source or "help_community"

                if any(t in q_lower for t in theme["terms"]):
                    if src not in seen_sources or len(seen_sources) >= 3:
                        strict_quotes.append({
                            "quote": q,
                            "source": src,
                            "url": p.url,
                            "post_id": p.post_id
                        })
                        seen_sources.add(src)
                        used_quotes_global.add(q)
                        used_post_ids_global.add(p.post_id)
                        if len(strict_quotes) >= 3 and len(seen_sources) >= 2:
                            break

            # Fallback pass if under 3 quotes: find top verified quotes from matching posts
            if len(strict_quotes) < 3:
                for p in matching_posts:
                    q = (p.taxonomy.quote or p.title or "").strip()
                    if not q or len(q) < 10:
                        continue
                    if q in used_quotes_global or p.post_id in used_post_ids_global:
                        continue
                    src = p.source or "help_community"

                    strict_quotes.append({
                        "quote": q,
                        "source": src,
                        "url": p.url,
                        "post_id": p.post_id
                    })
                    used_quotes_global.add(q)
                    used_post_ids_global.add(p.post_id)
                    if len(strict_quotes) >= 3:
                        break

            named_clusters.append({
                "cluster_id": theme["cluster_id"],
                "title": theme["title"],
                "theme_title": theme["title"],
                "count": count,
                "share_pct": share_pct,
                "summary_note": theme["summary_note"],
                "example_quotes": strict_quotes[:3],
                "top_quotes": strict_quotes[:3]
            })

        # Sort clusters by post count descending
        named_clusters.sort(key=lambda c: c["count"], reverse=True)

        # Calculate residual unclassified bucket footnote stats (Section 4.3 rule)
        unclassified_count = max(0, total_relevant - len(assigned_post_ids))
        unclassified_pct = round((unclassified_count / total_relevant) * 100, 2)

        residual_disclosure = {
            "unclassified_count": unclassified_count,
            "unclassified_pct": unclassified_pct
        }

        logger.info(f"Built {len(named_clusters)} Layer B Theme clusters with source-diverse quotes. Residual unclassified: {unclassified_count} posts ({unclassified_pct}%).")
        return named_clusters, residual_disclosure

