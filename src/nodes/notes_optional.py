from __future__ import annotations

from typing import Any

from .prompts import NOTES_PROMPT
from ..node_runner import run_node
from ..state import InspectionState, ensure_current_style


def apply_notes(s: InspectionState, ext: Any) -> tuple[bool, dict[str, Any], str | None]:
    transcript = (s.get("last_user_input") or {}).get("transcript") or ""
    if not ext:
        if transcript:
            style = ensure_current_style(s)
            style["notes"] = transcript
            return True, {"notes": transcript}, None
        return False, {}, None
    n = ext.notes
    if n is not None and isinstance(n, str) and n.lower() in ("no notes", "none", "skip", ""):
        notes = ""
    else:
        notes = str(n) if n is not None else transcript
    style = ensure_current_style(s)
    style["notes"] = notes
    return True, {"notes": notes}, None


def notes_optional_node(state: InspectionState) -> InspectionState:
    return run_node(state, "NOTES_OPTIONAL", NOTES_PROMPT, apply_notes)
