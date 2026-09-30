"""
Themes Layer A Heatmap Matrix Engine ("Where do people struggle")
Computes structured failure_step x system_issues matrix.
"""

import logging
from typing import List, Dict, Any
from backend.models.taxonomy import TaggedPostRecord

logger = logging.getLogger(__name__)


class ThemesEngine:
    """Computes Layer A failure_step x system_issues struggle matrix."""

    @staticmethod
    def build_layer_a_matrix(relevant_posts: List[TaggedPostRecord]) -> List[Dict[str, Any]]:
        if not relevant_posts:
            return []

        total_relevant = len(relevant_posts)
        crosstab: Dict[Tuple[str, str], int] = {}

        for p in relevant_posts:
            step = p.taxonomy.failure_step
            issues = p.taxonomy.system_issues if p.taxonomy.system_issues else ["missing_results"]
            for sys_issue in issues:
                key = (step, sys_issue)
                crosstab[key] = crosstab.get(key, 0) + 1

        matrix: List[Dict[str, Any]] = []
        for (step, sys_issue), count in crosstab.items():
            share_pct = round((count / total_relevant) * 100, 2)
            matrix.append({
                "failure_step": step,
                "system_issue": sys_issue,
                "count": count,
                "share_pct": share_pct
            })

        # Sort matrix by count descending
        matrix.sort(key=lambda item: item["count"], reverse=True)

        logger.info(f"Built Themes Layer A matrix with {len(matrix)} distinct failure_step x system_issue combinations.")
        return matrix
