from __future__ import annotations

from typing import Any

from .prompts import CARTON_CONDITION_PROMPT
from ..node_runner import run_node
from ..state import InspectionState


def apply_carton(s: InspectionState, ext: Any) -> tuple[bool, dict[str, Any], str | None]:
    if not ext:
        return False, {}, None
    status = (ext.carton_status or "").upper() if ext.carton_status else None
    if status not in ("OK", "DAMAGED"):
        return False, {}, None
    if status == "OK":
        s["carton_status"] = "OK"
        return True, {"carton_status": "OK"}, None
    if not ext.damage_type or not ext.damage_severity:
        return False, {}, "Carton damaged. State the damage type and severity (minor or major)."
    sev = (ext.damage_severity or "").upper()
    if sev not in ("MINOR", "MAJOR"):
        return False, {}, None
    s["carton_status"] = "DAMAGED"
    s["damage_type"] = ext.damage_type
    s["damage_severity"] = sev
    return True, {"carton_status": "DAMAGED", "damage_type": ext.damage_type, "damage_severity": sev}, None


def carton_condition_node(state: InspectionState) -> InspectionState:
    return run_node(state, "CARTON_CONDITION", CARTON_CONDITION_PROMPT, apply_carton)
