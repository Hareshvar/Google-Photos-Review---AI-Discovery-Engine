"""
Human Validation Ground-Truth Override Engine
Loads human benchmark labels from data/human_labels.json and applies ground-truth overrides.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class HumanOverrideEngine:
    """Manages human ground-truth annotations and overrides."""

    def __init__(self, data_dir: str = "./data"):
        self.human_labels_file = os.path.join(data_dir, "human_labels.json")
        self.labels: Dict[str, Dict[str, Any]] = {}
        self.load_human_labels()

    def load_human_labels(self):
        """Loads human label definitions from data/human_labels.json."""
        if os.path.exists(self.human_labels_file):
            try:
                with open(self.human_labels_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        for item in data:
                            pid = item.get("post_id") or item.get("id") or item.get("title")
                            if pid:
                                self.labels[pid] = item
                    elif isinstance(data, dict):
                        self.labels = data
                logger.info(f"Loaded {len(self.labels)} human benchmark labels.")
            except Exception as e:
                logger.warning(f"Failed to load human labels: {e}")

    def get_override(self, post_id: str) -> Optional[Dict[str, Any]]:
        """Returns human ground-truth label for post_id if present."""
        return self.labels.get(post_id)

    def evaluate_human_agreement(self, post_id: str, model_tax: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Evaluates model classification against human ground truth."""
        human = self.get_override(post_id)
        if not human:
            return None

        matched_fields = 0
        total_fields = 0

        eval_keys = ["relevant", "target_type", "failure_step", "primary_cue", "severity", "outcome"]
        field_matches = {}

        for key in eval_keys:
            if key in human:
                total_fields += 1
                is_match = human[key] == model_tax.get(key)
                field_matches[key] = is_match
                if is_match:
                    matched_fields += 1

        accuracy = matched_fields / max(1, total_fields)
        return {
            "post_id": post_id,
            "human_label": human,
            "field_matches": field_matches,
            "accuracy": round(accuracy, 3),
            "is_exact_match": matched_fields == total_fields
        }
