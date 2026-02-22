from __future__ import annotations

from typing import Any

from .prompts import PACKAGING_PRESENTATION_PROMPT
from ..node_runner import run_node
from ..state import InspectionState, ensure_current_style


def apply_packaging(s: InspectionState, ext: Any) -> tuple[bool, dict[str, Any], str | None]:
    if not ext:
        return False, {}, None
    if ext.packaging_ok is True:
        style = ensure_current_style(s)
        style["packaging_ok"] = True
        style["packaging_issues"] = []
        return True, {"packaging_ok": True}, None
    if not ext.packaging_issues:
        return False, {}, None

    transcript = (s.get("last_user_input") or {}).get("transcript") or ""
    issues = [
        {"issue_type": i.issue_type or "other",
         "raw": i.raw or transcript,
         "affected_unit_count": i.affected_unit_count or 0}
        for i in ext.packaging_issues
    ]
    style = ensure_current_style(s)
    style["packaging_ok"] = False
    style["packaging_issues"] = issues
    return True, {"packaging_ok": False, "packaging_issues": issues}, None


def packaging_presentation_node(state: InspectionState) -> InspectionState:
    return run_node(state, "PACKAGING_PRESENTATION", PACKAGING_PRESENTATION_PROMPT, apply_packaging)
