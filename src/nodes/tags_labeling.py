from __future__ import annotations

from typing import Any

from .prompts import TAGS_LABELING_PROMPT
from ..node_runner import run_node
from ..state import InspectionState, ensure_current_style


def apply_tags(s: InspectionState, ext: Any) -> tuple[bool, dict[str, Any], str | None]:
    if not ext:
        return False, {}, None
    if ext.tags_ok is True:
        style = ensure_current_style(s)
        style["tags_ok"] = True
        style["tags_issues"] = []
        return True, {"tags_ok": True}, None
    if not ext.tags_issues:
        return False, {}, None

    transcript = (s.get("last_user_input") or {}).get("transcript") or ""
    for i in ext.tags_issues:
        if i.affected_unit_count is None:
            return False, {}, None

    issues = [
        {"issue_type": i.issue_type or "other",
         "affected_unit_count": i.affected_unit_count,
         "raw": transcript}
        for i in ext.tags_issues
    ]
    style = ensure_current_style(s)
    style["tags_ok"] = False
    style["tags_issues"] = issues
    return True, {"tags_ok": False, "tags_issues": issues}, None


def tags_labeling_node(state: InspectionState) -> InspectionState:
    return run_node(state, "TAGS_LABELING", TAGS_LABELING_PROMPT, apply_tags)
