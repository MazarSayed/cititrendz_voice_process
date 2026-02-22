from __future__ import annotations

from typing import Any

from .prompts import START_IDENTIFICATION_PROMPT
from ..node_runner import run_node
from ..node_utils import fields_captured
from ..parsers import normalize_po_number
from ..po_packages import list_available_pos, resolve_po
from ..state import InspectionState


def apply_start_id(s: InspectionState, ext: Any) -> tuple[bool, dict[str, Any], str | None]:
    if not ext:
        return False, {}, None
    po = ext.po_number
    carton = ext.carton_barcode
    if carton:
        s["carton_barcode"] = carton
        return True, {"carton_barcode": carton}, None
    if isinstance(po, str):
        raw = normalize_po_number(po)
        if len(raw) >= 3:
            resolved = resolve_po(raw) or resolve_po(po)
            if resolved:
                s["po_number"] = resolved
                return True, {"po_number": resolved}, None
            # PO not in our packages list
            available = list_available_pos()
            avail_str = ", ".join(available[:8]) + ("..." if len(available) > 8 else "")
            return False, {}, f"PO {raw} is not available. Available POs: {avail_str}. Please say a valid PO number."
    return False, {}, None


def scan_handler(s: InspectionState, scan: str) -> InspectionState:
    s["carton_barcode"] = scan
    return fields_captured("START_IDENTIFICATION", s, {"carton_barcode": scan})


def start_identification_node(state: InspectionState) -> InspectionState:
    return run_node(
        state,
        "START_IDENTIFICATION",
        START_IDENTIFICATION_PROMPT,
        apply_start_id,
        scan_handler=scan_handler,
    )
