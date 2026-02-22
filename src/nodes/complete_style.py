from __future__ import annotations

from typing import Any

from .prompts import COMPLETE_STYLE_PROMPT
from ..node_runner import run_node
from ..state import InspectionState

STYLE_FIELDS_TO_CLEAR = [
    "style_id", "style_entry_method", "color_size_match", "mismatch_reason",
    "size_counts", "total_units_counted", "all_units_ok", "defects",
    "tags_ok", "tags_issues", "packaging_ok", "packaging_issues",
    "photos", "disposition", "notes",
]


def apply_complete_style(s: InspectionState, ext: Any) -> tuple[bool, dict[str, Any], str | None]:
    if not ext or not ext.complete_style_action:
        return False, {}, None
    action = ext.complete_style_action
    s["completed_styles"] = int(s.get("completed_styles", 0)) + 1
    s["complete_style_action"] = action
    if action == "NEXT_STYLE":
        for key in STYLE_FIELDS_TO_CLEAR:
            s.pop(key, None)
    return True, {"action": action, "completed_styles": s["completed_styles"]}, None


def complete_style_node(state: InspectionState) -> InspectionState:
    return run_node(state, "COMPLETE_STYLE", COMPLETE_STYLE_PROMPT, apply_complete_style)
