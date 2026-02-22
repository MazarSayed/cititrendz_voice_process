from __future__ import annotations

from typing import Any

from .prompts import DISPOSITION_PROMPT
from ..node_runner import run_node
from ..state import Disposition, InspectionState, ensure_current_style


def apply_disposition(s: InspectionState, ext: Any) -> tuple[bool, dict[str, Any], str | None]:
    if not ext or not ext.disposition:
        return False, {}, None
    d = (ext.disposition or "").upper().replace(" ", "_")
    if d not in ("ACCEPT", "ACCEPT_WITH_EXCEPTIONS", "HOLD", "REJECT"):
        return False, {}, None
    disp: Disposition = d  # type: ignore[assignment]
    style = ensure_current_style(s)
    style["disposition"] = disp
    s["disposition"] = disp
    return True, {"disposition": disp}, None


def disposition_node(state: InspectionState) -> InspectionState:
    return run_node(state, "DISPOSITION", DISPOSITION_PROMPT, apply_disposition)
