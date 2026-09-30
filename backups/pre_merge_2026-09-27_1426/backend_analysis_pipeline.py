"""
Phase 3 & Phase 4 Precomputation Pipeline Orchestrator for AI Discovery Engine ("Retrieval Lens")
Generates Themes matrix, emergent Layer B clusters, Situations matrix, and 9 Key Insights summaries.
"""

import os
import json
import logging
from typing import Dict, Any, List

from backend.models.taxonomy import TaggedPostRecord
from backend.analysis.themes_engine import ThemesEngine
from backend.analysis.cluster_engine import ClusterEngine
from backend.analysis.situations_engine import SituationsEngine
from backend.analysis.insights_engine import InsightsEngine
from backend.analysis.summary_writer import SummaryWriter

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("AnalysisPipeline")


class AnalysisPipeline:
    """Orchestrates precomputations for Themes, Situations, and Key Insights."""

    def __init__(self, data_dir: str = "./data"):
        self.data_dir = data_dir
        self.tagged_file = os.path.join(data_dir, "tagged_posts.json")
        self.precomputed_file = os.path.join(data_dir, "precomputed_stats.json")

    def run(self) -> Dict[str, Any]:
        logger.info("Starting Precomputation Pipeline (Phases 3 & 4)...")

        if not os.path.exists(self.tagged_file):
            raise FileNotFoundError(f"Tagged posts file not found at {self.tagged_file}. Please run Phase 2 first.")

        with open(self.tagged_file, "r", encoding="utf-8") as f:
            tagged_data = json.load(f)

        tagged_records = [TaggedPostRecord(**item) for item in tagged_data]
        relevant_posts = [p for p in tagged_records if p.taxonomy.relevant]
        total_relevant = len(relevant_posts)

        logger.info(f"Loaded {len(tagged_records)} tagged post records. Total relevant posts: {total_relevant}")

        # 1. Build Themes Layer A Matrix ("Where do people struggle")
        layer_a_matrix = ThemesEngine.build_layer_a_matrix(relevant_posts)

        # 2. Build Themes Layer B Emergent Clusters ("What people are discussing") & Residual Disclosure
        cluster_engine = ClusterEngine(n_clusters=5)
        layer_b_clusters, residual_disclosure = cluster_engine.build_emergent_themes(relevant_posts)

        # 3. Build Situations Matrix & Opportunity Scores
        situations_data = SituationsEngine.build_situations_matrix(relevant_posts)

        # 4. Build Key Insights Cards (9 Core Research Questions)
        raw_insights = InsightsEngine.build_all_insights(relevant_posts)

        # 5. Generate Grounded LLM Summaries for Key Insights
        summary_writer = SummaryWriter()
        key_insights = summary_writer.write_summaries(raw_insights)

        # Load existing precomputed_stats if present
        existing_stats = {}
        if os.path.exists(self.precomputed_file):
            try:
                with open(self.precomputed_file, "r", encoding="utf-8") as f:
                    existing_stats = json.load(f)
            except Exception:
                existing_stats = {}

        # Construct merged precomputed stats payload
        precomputed_payload = {
            **existing_stats,
            "metadata": {
                "total_tagged": len(tagged_records),
                "total_relevant": total_relevant,
                "generated_at": os.path.basename(self.precomputed_file)
            },
            "themes": {
                "layer_a_struggle_matrix": layer_a_matrix,
                "layer_b_emergent_clusters": layer_b_clusters,
                "residual_disclosure": residual_disclosure
            },
            "situations": situations_data["situations"],
            "situations_tail_aggregated": situations_data["tail_aggregated"],
            "opportunity_score_formula": "Share (%) x Avg Severity (1-3) x Unresolved Rate (0-1) scaled to 0-100",
            "key_insights": key_insights
        }

        # Save precomputed stats
        with open(self.precomputed_file, "w", encoding="utf-8") as f:
            json.dump(precomputed_payload, f, indent=2, ensure_ascii=False)

        logger.info("Pipeline execution completed successfully!")
        logger.info(f"Precomputed Stats Saved: {self.precomputed_file}")

        return {
            "total_relevant": total_relevant,
            "layer_a_combinations": len(layer_a_matrix),
            "layer_b_clusters": len(layer_b_clusters),
            "situations_ranked": len(situations_data["situations"]),
            "key_insights_generated": len(key_insights)
        }


if __name__ == "__main__":
    pipeline = AnalysisPipeline()
    result = pipeline.run()
    print("\nPhase 4 Pipeline Execution Result:", result)
