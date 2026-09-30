"""
Unified Pydantic Schemas for AI Discovery Engine ("Retrieval Lens")
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class UnifiedPostRecord(BaseModel):
    """Normalized schema across all ingested public post sources."""
    post_id: str = Field(..., description="Unique post identifier across sources")
    source: str = Field(..., description="Source identifier (help_community, reddit_googlephotos, reddit_geminiai, play_store, app_store, youtube)")
    url: Optional[str] = Field(None, description="Direct URL to original public post if available")
    created_at: str = Field(..., description="ISO creation date string (YYYY-MM-DD)")
    title: str = Field(default="", description="Post title or header")
    raw_text: str = Field(..., description="Full body text of the post")
    author_id: Optional[str] = Field(default=None, description="Always None for privacy preservation")
    source_metadata: Dict[str, Any] = Field(default_factory=dict, description="Source-specific metadata dictionary")


class SourceProbeRecord(BaseModel):
    """Source health and volume tracking record."""
    source: str
    display_name: str
    records_collected: int = 0
    records_cleaned: int = 0
    records_relevant: int = 0
    status: str = "active"  # "active", "uncollected", "failed"
    error_message: Optional[str] = None


class RuleDropCount(BaseModel):
    """Audit count of dropped records for a specific cleaning rule."""
    rule_name: str
    count_dropped: int


class SourceCleanReport(BaseModel):
    """Detailed cleaning audit report for a specific source."""
    source: str
    total_raw: int
    total_cleaned: int
    exact_duplicates: int = 0
    near_duplicates: int = 0
    non_english: int = 0
    placeholder: int = 0
    short_text: int = 0
    prefilter_excluded: int = 0
    malformed: int = 0


class CleanReportSummary(BaseModel):
    """Overall cleaning report summary across all sources."""
    total_raw_collected: int
    total_cleaned_kept: int
    total_dropped: int
    per_source_report: Dict[str, SourceCleanReport]
