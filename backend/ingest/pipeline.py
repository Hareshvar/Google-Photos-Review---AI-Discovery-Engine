"""
End-to-End Phase 1 Ingestion and Cleaning Pipeline Orchestrator for AI Discovery Engine ("Retrieval Lens")
"""

import os
import json
import logging
from typing import List, Dict, Any

from backend.models.schema import UnifiedPostRecord, SourceProbeRecord, CleanReportSummary
from backend.ingest.adapters import (
    HelpCommunityAdapter,
    RedditAdapter,
    PlayStoreAdapter,
    AppStoreAdapter,
    YouTubeAdapter,
    JSONLAdapter
)
from backend.ingest.cleaner import DataCleaner

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("IngestionPipeline")


class IngestionPipeline:
    """Orchestrates collection across all 6 public sources and executes cleaning."""

    def __init__(self, data_dir: str = "./data", csv_filepath: str = "help_community_V2.csv"):
        self.data_dir = data_dir
        self.raw_dir = os.path.join(data_dir, "raw")
        self.csv_filepath = csv_filepath
        
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.raw_dir, exist_ok=True)

    def run(self) -> Dict[str, Any]:
        logger.info("Starting Phase 1 Ingestion & Cleaning Pipeline...")
        raw_records: List[UnifiedPostRecord] = []
        source_probes: List[SourceProbeRecord] = []
        prev_dir = "Previous data"

        # 1. Ingest Google Photos Help Community CSV
        logger.info("Ingesting Google Photos Help Community CSV...")
        csv_adapter = HelpCommunityAdapter(self.csv_filepath)
        csv_recs, csv_probe = csv_adapter.collect()
        raw_records.extend(csv_recs)
        source_probes.append(csv_probe)
        self._save_json(os.path.join(self.raw_dir, "help_community_raw.json"), [r.model_dump() for r in csv_recs])

        # 2. Ingest Reddit r/googlephotos (from Previous data/reddit.jsonl or live)
        logger.info("Ingesting Reddit r/googlephotos...")
        reddit_jsonl_path = os.path.join(prev_dir, "reddit.jsonl")
        if os.path.exists(reddit_jsonl_path):
            gp_adapter = JSONLAdapter(reddit_jsonl_path, "reddit_googlephotos", "Reddit r/googlephotos", target_subreddit="googlephotos")
        else:
            gp_adapter = RedditAdapter(subreddit="googlephotos", limit=2000)
        gp_recs, gp_probe = gp_adapter.collect()
        raw_records.extend(gp_recs)
        source_probes.append(gp_probe)
        self._save_json(os.path.join(self.raw_dir, "reddit_googlephotos_raw.json"), [r.model_dump() for r in gp_recs])

        # 3. Ingest Reddit r/GeminiAI (from Previous data/reddit.jsonl or live)
        logger.info("Ingesting Reddit r/GeminiAI...")
        if os.path.exists(reddit_jsonl_path):
            gemini_adapter = JSONLAdapter(reddit_jsonl_path, "reddit_geminiai", "Reddit r/GeminiAI", target_subreddit="GeminiAI")
        else:
            gemini_adapter = RedditAdapter(subreddit="GeminiAI", limit=1000)
        gemini_recs, gemini_probe = gemini_adapter.collect()
        raw_records.extend(gemini_recs)
        source_probes.append(gemini_probe)
        self._save_json(os.path.join(self.raw_dir, "reddit_geminiai_raw.json"), [r.model_dump() for r in gemini_recs])

        # 4. Ingest Google Play Store Reviews (combining Previous data/playstore.jsonl + live scraper with deduplication)
        logger.info("Ingesting Google Play Store Reviews...")
        ps_recs: List[UnifiedPostRecord] = []
        playstore_jsonl_path = os.path.join(prev_dir, "playstore.jsonl")
        if os.path.exists(playstore_jsonl_path):
            ps_jsonl_adapter = JSONLAdapter(playstore_jsonl_path, "play_store", "Google Play Store Reviews")
            ps_j_recs, _ = ps_jsonl_adapter.collect()
            ps_recs.extend(ps_j_recs)

        playstore_scraper_adapter = PlayStoreAdapter(count_target=3000)
        ps_s_recs, ps_probe = playstore_scraper_adapter.collect()
        ps_recs.extend(ps_s_recs)

        ps_probe.records_collected = len(ps_recs)
        ps_probe.status = "active"
        ps_probe.error_message = None
        raw_records.extend(ps_recs)
        source_probes.append(ps_probe)
        self._save_json(os.path.join(self.raw_dir, "playstore_raw.json"), [r.model_dump() for r in ps_recs])

        # 5. Ingest Apple App Store Reviews (from Previous data/appstore.jsonl or live)
        logger.info("Ingesting Apple App Store Reviews...")
        appstore_jsonl_path = os.path.join(prev_dir, "appstore.jsonl")
        if os.path.exists(appstore_jsonl_path):
            as_adapter = JSONLAdapter(appstore_jsonl_path, "app_store", "Apple App Store Reviews")
        else:
            as_adapter = AppStoreAdapter()
        as_recs, as_probe = as_adapter.collect()
        raw_records.extend(as_recs)
        source_probes.append(as_probe)
        self._save_json(os.path.join(self.raw_dir, "appstore_raw.json"), [r.model_dump() for r in as_recs])

        # 6. Ingest YouTube Comments (from Previous data/youtube.jsonl or live)
        logger.info("Ingesting YouTube Comments...")
        youtube_jsonl_path = os.path.join(prev_dir, "youtube.jsonl")
        if os.path.exists(youtube_jsonl_path):
            yt_adapter = JSONLAdapter(youtube_jsonl_path, "youtube", "YouTube Comments")
        else:
            yt_adapter = YouTubeAdapter()
        yt_recs, yt_probe = yt_adapter.collect()
        raw_records.extend(yt_recs)
        source_probes.append(yt_probe)
        self._save_json(os.path.join(self.raw_dir, "youtube_raw.json"), [r.model_dump() for r in yt_recs])

        logger.info(f"Total raw records collected across all sources: {len(raw_records)}")

        # 7. Execute Data Cleaning & Prefiltering (Deduplication + Prefilters)
        cleaner = DataCleaner(near_dup_threshold=0.85, min_words=5)
        cleaned_records, clean_summary = cleaner.clean_records(raw_records)

        # Update source probe cleaned counts
        probe_dict = {p.source: p for p in source_probes}
        for source_name, report in clean_summary.per_source_report.items():
            if source_name in probe_dict:
                probe_dict[source_name].records_cleaned = report.total_cleaned

        # 8. Save Pipeline Artifacts
        cleaned_file = os.path.join(self.data_dir, "cleaned_posts.json")
        clean_report_file = os.path.join(self.data_dir, "clean_report.json")
        source_probe_file = os.path.join(self.data_dir, "source_probe.json")

        self._save_json(cleaned_file, [r.model_dump() for r in cleaned_records])
        self._save_json(clean_report_file, clean_summary.model_dump())
        self._save_json(source_probe_file, [p.model_dump() for p in source_probes])

        logger.info("Phase 1 Pipeline execution completed successfully!")
        logger.info(f"Artifacts saved:\n - {cleaned_file}\n - {clean_report_file}\n - {source_probe_file}")

        return {
            "total_raw": len(raw_records),
            "total_cleaned": len(cleaned_records),
            "sources_processed": len(source_probes)
        }

    def _save_json(self, filepath: str, data: Any):
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    pipeline = IngestionPipeline()
    result = pipeline.run()
    print("\nPhase 1 Pipeline Execution Result:", result)
