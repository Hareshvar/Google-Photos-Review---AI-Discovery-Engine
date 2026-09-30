"""
Taxonomy Data Models for AI Discovery Engine ("Retrieval Lens")
Defines the 21-field schema and allowed enum sets for post classification.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

# ------------------------------------------------------------------------------
# Allowed Enum Sets
# ------------------------------------------------------------------------------
VAGUE_MEMORY_TYPES = {"vague", "partial", "precise", "unclear"}

TARGET_TYPES = {
    "document_info", "specific_event", "person_pet", "place_trip",
    "object_item", "date_time", "general_old_photo", "other"
}

PRIMARY_CUES = {
    "date_time", "location_place", "person_face", "text_ocr",
    "visual_object", "album_folder", "event_context", "file_metadata", "none"
}

FAILURE_STEPS = {
    "did_not_search", "search_not_completed", "no_or_wrong_results",
    "results_not_recognized", "wrong_photo_opened", "scroll_not_found", "no_failure"
}

MEMORY_BREAKS = {
    "forgot_key_detail", "could_not_put_into_words", "misremembered_fact",
    "too_many_similar_photos", "unclear"
}

QUERY_STYLES = {
    "natural_language", "keywords", "date_range", "location_name",
    "person_name", "exact_quote"
}

WORKAROUNDS = {
    "scroll_timeline", "check_other_apps", "ask_friends",
    "browse_folders", "gave_up"
}

SEARCH_TOOLS = {
    "classic_search", "ask_photos", "map_view", "people_pets_tab", "search_tab"
}

JOBS = {
    "proof_documentation", "reminiscing", "sharing_social",
    "practical_utility", "unknown"
}

SYSTEM_ISSUES = {
    "missing_results", "wrong_results", "ocr_failure", "face_rec_failure",
    "date_index_error", "ask_photos_hallucination", "ui_regression"
}

OUTCOMES = {"found_eventually", "not_found", "partially_found", "unclear"}

SEVERITIES = {"low", "medium", "high"}


# ------------------------------------------------------------------------------
# Taxonomy Pydantic Schema
# ------------------------------------------------------------------------------
class TaggedTaxonomy(BaseModel):
    """The 21-field taxonomy schema extracted for each post."""
    relevant: bool = Field(..., description="Whether post describes photo retrieval difficulty")
    vague_memory: str = Field(default="unclear", description="vague | partial | precise | unclear")
    target_type: str = Field(default="other", description="Kind of photo being searched for")
    primary_cue: str = Field(default="none", description="Main clue user remembered")
    cues_remembered: List[str] = Field(default_factory=list, description="Cues user remembered")
    cues_forgotten: List[str] = Field(default_factory=list, description="Cues user forgot")
    hedged: bool = Field(default=False, description="Whether user expressed uncertainty")
    failure_step: str = Field(default="no_failure", description="Where retrieval journey broke")
    memory_break: str = Field(default="unclear", description="How user memory broke")
    query_styles: List[str] = Field(default_factory=list, description="Search formulation styles")
    queries_quoted: List[str] = Field(default_factory=list, description="Verbatim search terms attempted")
    workarounds: List[str] = Field(default_factory=list, description="Workaround actions taken")
    search_tool: str = Field(default="search_tab", description="Search surface used")
    job: str = Field(default="unknown", description="Why user needed the photo")
    system_issues: List[str] = Field(default_factory=list, description="Technical system failures")
    outcome: str = Field(default="unclear", description="Final retrieval outcome")
    severity: str = Field(default="low", description="Severity level: low | medium | high")
    wish: Optional[str] = Field(default=None, description="Expressed feature request")
    unmapped_note: Optional[str] = Field(default=None, description="Unmapped context")
    quote: str = Field(default="", description="Representative verbatim quote snippet")
    quote_verified: bool = Field(default=False, description="Verified by exact code substring match")
    confidence: float = Field(default=0.90, description="Classification confidence score")


class TaggedPostRecord(BaseModel):
    """Full post record combining original post info with verified taxonomy tags."""
    post_id: str
    source: str
    url: Optional[str] = None
    created_at: str
    title: str
    raw_text: str
    author_id: Optional[str] = None
    source_metadata: Dict[str, Any] = Field(default_factory=dict)
    taxonomy: TaggedTaxonomy
