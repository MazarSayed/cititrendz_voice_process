from __future__ import annotations

from typing import Any

from .prompts import STYLE_SKU_VERIFICATION_PROMPT
from ..node_runner import run_node
from ..node_utils import fields_captured
from ..state import InspectionState, ensure_current_style


def apply_style_sku(s: InspectionState, ext: Any) -> tuple[bool, dict[str, Any], str | None]:
    if not ext:
        return False, {}, None
    style_id = ext.style_id
    method = ext.style_entry_method
    if isinstance(style_id, str):
        style_id = "".join(c for c in style_id if c.isdigit())
        if len(style_id) < 4:
            style_id = None
    if not style_id or not method:
        return False, {}, None
    style = ensure_current_style(s)
    style["style_id"] = style_id
    style["style_entry_method"] = method or "MANUAL"
    return True, {"style_id": style_id, "style_entry_method": method or "MANUAL"}, None


def scan_handler(s: InspectionState, scan: str) -> InspectionState:
    style = ensure_current_style(s)
    style["style_id"] = scan
    style["style_entry_method"] = "SCAN"
    return fields_captured("STYLE_SKU_VERIFICATION", s, {"style_id": scan, "style_entry_method": "SCAN"})


def style_sku_verification_node(state: InspectionState) -> InspectionState:
    return run_node(
        state,
        "STYLE_SKU_VERIFICATION",
        STYLE_SKU_VERIFICATION_PROMPT,
        apply_style_sku,
        scan_handler=scan_handler,
    )
