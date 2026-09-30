"""
REST API Router for Retrieval Lens FastAPI Backend
Exposes endpoints for Overview, Themes, Situations, Key Insights, Method, Bundle Export, and RAG Chatbot.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from backend.exporter.bundle_builder import BundleBuilder, GLOSSARY_DEFINITIONS
from backend.rag.rag_engine import RAGEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")

DATA_DIR = "./data"
PRECOMPUTED_FILE = os.path.join(DATA_DIR, "precomputed_stats.json")
CLEAN_REPORT_FILE = os.path.join(DATA_DIR, "clean_report.json")
SOURCE_PROBE_FILE = os.path.join(DATA_DIR, "source_probe.json")
mapped_tagged_path = os.path.join(DATA_DIR, "final_tagged_dataset_mapped.json")
final_tagged_path = os.path.join(DATA_DIR, "final_tagged_dataset.json")
if os.path.exists(mapped_tagged_path):
    TAGGED_FILE = mapped_tagged_path
elif os.path.exists(final_tagged_path):
    TAGGED_FILE = final_tagged_path
else:
    TAGGED_FILE = os.path.join(DATA_DIR, "tagged_posts.json")


rag_engine = RAGEngine(DATA_DIR)


class ChatRequest(BaseModel):
    prompt: str
    session_id: Optional[str] = "default"
    chat_history: Optional[List[Dict[str, str]]] = None


def load_file(filepath: str, default: Any) -> Any:
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Error loading {filepath}: {str(e)}")
    return default


@router.get("/overview")
def get_overview():
    """Returns Overview page stat cards, pipeline step counts, and source health."""
    precomputed = load_file(PRECOMPUTED_FILE, {})
    clean_report = load_file(CLEAN_REPORT_FILE, {})
    source_probe = load_file(SOURCE_PROBE_FILE, [])
    tagged_posts = load_file(TAGGED_FILE, [])

    total_collected = clean_report.get("total_raw_collected", 0)
    total_cleaned = clean_report.get("total_cleaned_kept", 0)
    metadata = precomputed.get("metadata", {})
    total_relevant = metadata.get("total_relevant", len(tagged_posts))

    relevant_posts = [
        p for p in tagged_posts
        if (p.get("taxonomy", {}).get("relevant") is True or p.get("relevant") is True)
    ]
    if not relevant_posts:
        relevant_posts = tagged_posts

    vague_memory_count = sum(
        1 for p in relevant_posts
        if (p.get("taxonomy", {}).get("vague_memory") or p.get("vague_memory")) in ("vague", "partial")
    )
    search_failures_count = sum(
        1 for p in relevant_posts
        if (p.get("taxonomy", {}).get("failure_step") or p.get("failure_step")) not in ("no_failure", None, "")
    )

    pipeline_steps = [
        {"step": "Collect", "label": "Collected", "count": total_collected},
        {"step": "Clean", "label": "Cleaned", "count": total_cleaned},
        {"step": "Classify", "label": "Classified Relevant", "count": total_relevant},
        {"step": "Analyze", "label": "Analyzed Insights", "count": total_relevant},
        {"step": "Index", "label": "Indexed for Chat", "count": total_relevant},
        {"step": "App", "label": "Rendered in Lens", "count": total_relevant}
    ]

    quality_report_file = os.path.join(DATA_DIR, "judge_validation_report.json")
    if os.path.exists(quality_report_file):
        q_data = load_file(quality_report_file, {})
        checked_count = q_data.get("sample_size", 0)
        pipeline_steps.insert(3, {"step": "Checked", "label": "Checked (Judges + Human)", "count": checked_count})

    for src in source_probe:
        if "relevance_rate" not in src or src["relevance_rate"] is None:
            cleaned = src.get("records_cleaned", 0)
            relevant = src.get("records_relevant", cleaned)
            src["relevance_rate"] = round((relevant / max(1, cleaned)) * 100, 1) if cleaned > 0 else 0.0

    return {
        "stats": {
            "collected": total_collected,
            "cleaned": total_cleaned,
            "relevant": total_relevant,
            "vague_memory_count": vague_memory_count,
            "search_failures_count": search_failures_count
        },
        "pipeline_steps": pipeline_steps,
        "source_health": source_probe
    }


@router.get("/themes")
def get_themes():
    """Returns Themes page Layer A struggle heatmap matrix, Layer B emergent clusters, and residual footnote."""
    precomputed = load_file(PRECOMPUTED_FILE, {})
    themes_data = precomputed.get("themes", {})
    
    return {
        "metadata": precomputed.get("metadata", {}),
        "layer_a_struggle_matrix": themes_data.get("layer_a_struggle_matrix", []),
        "layer_b_emergent_clusters": themes_data.get("layer_b_emergent_clusters", []),
        "residual_disclosure": themes_data.get("residual_disclosure", {"unclassified_count": 0, "unclassified_pct": 0.0})
    }


@router.get("/situations")
def get_situations():
    """Returns Situations page ranked table with Opportunity Scores and tail aggregation row."""
    precomputed = load_file(PRECOMPUTED_FILE, {})
    
    return {
        "situations": precomputed.get("situations", []),
        "tail_aggregated": precomputed.get("situations_tail_aggregated"),
        "formula_caption": precomputed.get("opportunity_score_formula", "Share (%) x Avg Severity (1-3) x Unresolved Rate (0-1) scaled to 0-100")
    }


@router.get("/insights")
def get_insights():
    """Returns Key Insights page 9 research question cards with grounded summaries, charts, and quotes."""
    precomputed = load_file(PRECOMPUTED_FILE, {})
    key_insights = precomputed.get("key_insights", [])
    
    return {
        "key_insights": key_insights
    }


@router.get("/method")
def get_method():
    """Returns Method & Limits page pipeline drop counts, source limits, model metadata, and tag glossary."""
    clean_report = load_file(CLEAN_REPORT_FILE, {})
    source_probe = load_file(SOURCE_PROBE_FILE, [])
    quality_audit = load_file(os.path.join(DATA_DIR, "quality_bar_audit_report.json"), {})

    if clean_report and "per_source_report" in clean_report:
        per_src = clean_report["per_source_report"]
        if "exact_duplicates_dropped" not in clean_report:
            clean_report["exact_duplicates_dropped"] = sum(v.get("exact_duplicates", 0) for v in per_src.values())
        if "minhash_duplicates_dropped" not in clean_report:
            clean_report["minhash_duplicates_dropped"] = sum(v.get("near_duplicates", 0) for v in per_src.values())
        if "non_english_dropped" not in clean_report:
            clean_report["non_english_dropped"] = sum(v.get("non_english", 0) for v in per_src.values())
        if "under_length_dropped" not in clean_report:
            clean_report["under_length_dropped"] = sum(v.get("placeholder", 0) + v.get("short_text", 0) for v in per_src.values())
        if "keyword_miss_dropped" not in clean_report:
            clean_report["keyword_miss_dropped"] = sum(v.get("prefilter_excluded", 0) for v in per_src.values())

    model_metadata = {
        "primary_tagger": os.getenv("GEMINI_MODEL", "gemini-3.6-flash"),
        "fallback_tagger": os.getenv("GROQ_MODEL", "openai/gpt-oss-20b"),
        "embeddings": os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5"),
        "taxonomy_version": "2.0.0"
    }

    return {
        "cleaning_report": clean_report,
        "source_limits": source_probe,
        "model_metadata": model_metadata,
        "quality_bar_audit": quality_audit,
        "tag_glossary": GLOSSARY_DEFINITIONS
    }


@router.get("/quality")
def get_quality():
    """Returns Quality Audit page Multi-LLM judge evaluation report and human validation metrics."""
    quality_report_file = os.path.join(DATA_DIR, "judge_validation_report.json")
    if os.path.exists(quality_report_file):
        return load_file(quality_report_file, {})
    return {"status": "not_executed", "message": "Judge validation pipeline has not been executed yet."}


@router.get("/export")
def download_export_bundle():
    """Generates and downloads the self-describing JSON export bundle."""
    builder = BundleBuilder(DATA_DIR)
    bundle_data = builder.build_bundle()
    bundle_path = builder.bundle_file

    if os.path.exists(bundle_path):
        return FileResponse(
            path=bundle_path,
            filename="retrieval_lens_analysis_bundle.json",
            media_type="application/json"
        )
    return JSONResponse(content=bundle_data)


@router.post("/chat")
def chat_with_data(request: ChatRequest):
    """Grounded RAG Chatbot endpoint ('Ask the Data')."""
    return rag_engine.ask(
        prompt=request.prompt,
        chat_history=request.chat_history,
        session_id=request.session_id
    )
