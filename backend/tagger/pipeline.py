"""
Phase 2 Tagging Pipeline Orchestrator for AI Discovery Engine ("Retrieval Lens")
Executes taxonomy classification, quote verification, consistency checks, and saves tagged artifacts.
"""

import os
import json
import logging
from typing import List, Dict, Any, Tuple

from backend.models.schema import UnifiedPostRecord
from backend.models.taxonomy import TaggedPostRecord, TaggedTaxonomy
from backend.tagger.gemini_tagger import LLMTagger
from backend.tagger.consistency import ConsistencyAuditor

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("TaggingPipeline")


def load_env(env_path: str = ".env"):
    """Load environment variables from .env file."""
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ[k.strip()] = v.strip()


class TaggingPipeline:
    """Orchestrates Phase 2 LLM tagging and verification pass."""

    def __init__(self, data_dir: str = "./data"):
        self.data_dir = data_dir
        self.cleaned_file = os.path.join(data_dir, "cleaned_posts.json")
        self.tagged_file = os.path.join(data_dir, "tagged_posts.json")
        self.flags_file = os.path.join(data_dir, "consistency_flags.json")
        self.source_probe_file = os.path.join(data_dir, "source_probe.json")
        
        load_env()
        self.tagger = LLMTagger()

    def run(self, max_posts: int = 0) -> Dict[str, Any]:
        logger.info("Starting Phase 2 Taxonomy Tagging Pipeline...")

        if not os.path.exists(self.cleaned_file):
            raise FileNotFoundError(f"Cleaned posts file not found at {self.cleaned_file}. Please run Phase 1 first.")

        with open(self.cleaned_file, "r", encoding="utf-8") as f:
            cleaned_data = json.load(f)

        if max_posts > 0:
            cleaned_data = cleaned_data[:max_posts]

        total_posts = len(cleaned_data)
        logger.info(f"Loaded {total_posts} cleaned post records for taxonomy classification.")

        # Load existing tagged records into cache map
        existing_tagged_map: Dict[str, TaggedPostRecord] = {}
        if os.path.exists(self.tagged_file):
            try:
                with open(self.tagged_file, "r", encoding="utf-8") as f:
                    existing_items = json.load(f)
                for item in existing_items:
                    rec = TaggedPostRecord(**item)
                    existing_tagged_map[rec.post_id] = rec
                logger.info(f"Loaded {len(existing_tagged_map)} existing tagged post records from cache.")
            except Exception as e:
                logger.warning(f"Error loading existing tagged posts cache: {str(e)}")

        tagged_records: List[TaggedPostRecord] = []
        all_consistency_flags: List[Dict[str, Any]] = []
        source_relevant_counts: Dict[str, int] = {}
        unprocessed_items: List[UnifiedPostRecord] = []

        # Check cached vs untagged
        for item in cleaned_data:
            post_rec = UnifiedPostRecord(**item)
            if post_rec.post_id in existing_tagged_map:
                cached_rec = existing_tagged_map[post_rec.post_id]
                tagged_records.append(cached_rec)
                if cached_rec.taxonomy.relevant:
                    source_relevant_counts[cached_rec.source] = source_relevant_counts.get(cached_rec.source, 0) + 1
                flags = ConsistencyAuditor.audit_record(cached_rec.post_id, cached_rec.taxonomy)
                if flags:
                    all_consistency_flags.extend(flags)
            else:
                unprocessed_items.append(post_rec)

        logger.info(f"Reused {len(tagged_records)} cached tagged posts. Untagged posts to process: {len(unprocessed_items)}.")

        # Process untagged posts with ThreadPoolExecutor
        if unprocessed_items:
            import concurrent.futures

            def _process_single(post_rec: UnifiedPostRecord) -> Tuple[TaggedPostRecord, List[Dict[str, Any]]]:
                taxonomy = self.tagger.tag_post(post_rec.title, post_rec.raw_text)
                tagged_post = TaggedPostRecord(
                    post_id=post_rec.post_id,
                    source=post_rec.source,
                    url=post_rec.url,
                    created_at=post_rec.created_at,
                    title=post_rec.title,
                    raw_text=post_rec.raw_text,
                    author_id=post_rec.author_id,
                    source_metadata=post_rec.source_metadata,
                    taxonomy=taxonomy
                )
                flags = ConsistencyAuditor.audit_record(post_rec.post_id, taxonomy)
                return tagged_post, flags

            logger.info(f"Processing {len(unprocessed_items)} untagged records using parallel worker threads...")
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                future_to_rec = {executor.submit(_process_single, rec): rec for rec in unprocessed_items}
                processed_count = 0
                for future in concurrent.futures.as_completed(future_to_rec):
                    processed_count += 1
                    try:
                        tagged_post, flags = future.result()
                        tagged_records.append(tagged_post)
                        if tagged_post.taxonomy.relevant:
                            source_relevant_counts[tagged_post.source] = source_relevant_counts.get(tagged_post.source, 0) + 1
                        if flags:
                            all_consistency_flags.extend(flags)

                        if processed_count % 500 == 0 or processed_count == len(unprocessed_items):
                            logger.info(f"Tagged {processed_count}/{len(unprocessed_items)} new records...")
                            # Atomic save checkpoint
                            tmp_file = self.tagged_file + ".tmp"
                            with open(tmp_file, "w", encoding="utf-8") as f:
                                json.dump([r.model_dump() for r in tagged_records], f, indent=2, ensure_ascii=False)
                            os.replace(tmp_file, self.tagged_file)
                    except Exception as e:
                        logger.error(f"Error processing record: {str(e)}")

        # Final Update Source Probe file with relevant counts
        self._update_source_probe(source_relevant_counts)

        # Save artifacts atomically
        tmp_file = self.tagged_file + ".tmp"
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump([r.model_dump() for r in tagged_records], f, indent=2, ensure_ascii=False)
        os.replace(tmp_file, self.tagged_file)

        with open(self.flags_file, "w", encoding="utf-8") as f:
            json.dump(all_consistency_flags, f, indent=2, ensure_ascii=False)

        relevant_count = sum(1 for r in tagged_records if r.taxonomy.relevant)
        verified_quotes_count = sum(1 for r in tagged_records if r.taxonomy.quote_verified)

        logger.info("Phase 2 Pipeline execution completed successfully!")
        logger.info(f"Tagged Posts Saved: {self.tagged_file} (Total: {total_posts}, Relevant: {relevant_count})")
        logger.info(f"Verified Quotes Count: {verified_quotes_count}")
        logger.info(f"Consistency Flags Saved: {self.flags_file} (Total Flags: {len(all_consistency_flags)})")

        return {
            "total_posts": total_posts,
            "relevant_posts": relevant_count,
            "verified_quotes": verified_quotes_count,
            "consistency_flags": len(all_consistency_flags)
        }

    def _update_source_probe(self, relevant_counts: Dict[str, int]):
        if not os.path.exists(self.source_probe_file):
            return

        try:
            with open(self.source_probe_file, "r", encoding="utf-8") as f:
                probes = json.load(f)

            for probe in probes:
                src = probe.get("source")
                if src in relevant_counts:
                    probe["records_relevant"] = relevant_counts[src]

            with open(self.source_probe_file, "w", encoding="utf-8") as f:
                json.dump(probes, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"Could not update source probe file: {str(e)}")


if __name__ == "__main__":
    pipeline = TaggingPipeline()
    result = pipeline.run()
    print("\nPhase 2 Pipeline Execution Result:", result)
