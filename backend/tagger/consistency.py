"""
Appendix B Automated Consistency Auditor
Detects logical contradiction anomalies across taxonomy tags (Rules C1-C5).
"""

from typing import List, Dict, Any
from backend.models.taxonomy import TaggedTaxonomy


class ConsistencyAuditor:
    """Audits tagged taxonomy records against Appendix B rules."""

    @staticmethod
    def audit_record(post_id: str, taxonomy: TaggedTaxonomy) -> List[Dict[str, Any]]:
        flags: List[Dict[str, Any]] = []

        # C1: failure_step = no_failure but outcome = not_found or severity != low
        if taxonomy.failure_step == "no_failure" and (taxonomy.outcome == "not_found" or taxonomy.severity != "low"):
            flags.append({
                "rule_id": "C1",
                "post_id": post_id,
                "description": "failure_step is 'no_failure' but outcome is 'not_found' or severity is not 'low'",
                "fields": {
                    "failure_step": taxonomy.failure_step,
                    "outcome": taxonomy.outcome,
                    "severity": taxonomy.severity
                }
            })

        # C2: failure_step = did_not_search but queries_quoted is non-empty
        if taxonomy.failure_step == "did_not_search" and len(taxonomy.queries_quoted) > 0:
            flags.append({
                "rule_id": "C2",
                "post_id": post_id,
                "description": "failure_step is 'did_not_search' but user quoted search queries",
                "fields": {
                    "failure_step": taxonomy.failure_step,
                    "queries_quoted": taxonomy.queries_quoted
                }
            })

        # C3: vague_memory = precise but cues_forgotten is non-empty
        if taxonomy.vague_memory == "precise" and len(taxonomy.cues_forgotten) > 0:
            flags.append({
                "rule_id": "C3",
                "post_id": post_id,
                "description": "vague_memory is 'precise' but cues_forgotten is non-empty",
                "fields": {
                    "vague_memory": taxonomy.vague_memory,
                    "cues_forgotten": taxonomy.cues_forgotten
                }
            })

        # C4: workarounds contains gave_up but outcome = found_eventually
        if "gave_up" in taxonomy.workarounds and taxonomy.outcome == "found_eventually":
            flags.append({
                "rule_id": "C4",
                "post_id": post_id,
                "description": "workarounds contains 'gave_up' but outcome is 'found_eventually'",
                "fields": {
                    "workarounds": taxonomy.workarounds,
                    "outcome": taxonomy.outcome
                }
            })

        # C5: Same cue appears in both cues_remembered and cues_forgotten
        rem_set = set(c.lower().strip() for c in taxonomy.cues_remembered)
        forg_set = set(c.lower().strip() for c in taxonomy.cues_forgotten)
        overlap = rem_set.intersection(forg_set)
        if overlap:
            flags.append({
                "rule_id": "C5",
                "post_id": post_id,
                "description": f"Overlapping cues in remembered and forgotten sets: {list(overlap)}",
                "fields": {
                    "cues_remembered": taxonomy.cues_remembered,
                    "cues_forgotten": taxonomy.cues_forgotten,
                    "overlap": list(overlap)
                }
            })

        return flags
