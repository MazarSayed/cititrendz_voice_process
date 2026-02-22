from __future__ import annotations

from typing import Any

from .prompts import DEFECT_INSPECTION_PROMPT
from ..node_runner import run_node
from ..state import InspectionState, ensure_current_style


def apply_defect(s: InspectionState, ext: Any) -> tuple[bool, dict[str, Any], str | None]:
    if not ext:
        return False, {}, None
    if ext.all_units_ok is True:
        style = ensure_current_style(s)
        style["all_units_ok"] = True
        style["defects"] = []
        return True, {"all_units_ok": True, "defects": []}, None
    if not ext.defects:
        return False, {}, None

    for d in ext.defects:
        if d.affected_units is None or d.severity is None:
            return False, {}, None

    defects = [
        {"type": d.type or "other",
         "affected_units": d.affected_units,
         "severity": d.severity.upper()}
        for d in ext.defects
    ]
    style = ensure_current_style(s)
    style["all_units_ok"] = False
    style["defects"] = defects
    return True, {"all_units_ok": False, "defects": defects}, None


def defect_inspection_node(state: InspectionState) -> InspectionState:
    return run_node(state, "DEFECT_INSPECTION_100pct", DEFECT_INSPECTION_PROMPT, apply_defect)
