from __future__ import annotations

from typing import Any

from .prompts import COLOR_SIZE_VERIFICATION_PROMPT
from ..node_runner import run_node
from ..po_packages import get_cartons_for_po
from ..state import InspectionState, ensure_current_style


def _record_carton_match(state: InspectionState, match: bool) -> None:
    """Record match/mismatch for the current carton in carton_match_results."""
    results = state.setdefault("carton_match_results", {})
    po_number = state.get("po_number")
    carton_barcode = state.get("carton_barcode")
    style = state.get("current_style") or {}
    style_id = style.get("style_id")

    cartons = get_cartons_for_po(po_number) if po_number else []
    value = "Match" if match else "Mismatch"

    # Prefer carton_barcode if it's in our list
    if carton_barcode:
        for c in cartons:
            cid = c.get("barcode") or c.get("carton_id")
            if cid and str(cid).upper() == str(carton_barcode).upper():
                results[str(cid)] = value
                return

    # Else associate with first carton matching current style that has no result yet
    if style_id:
        style_id_str = str(style_id).upper()
        for c in cartons:
            cid = c.get("barcode") or c.get("carton_id")
            if not cid or str(cid) in results:
                continue
            c_style = str(c.get("style_id") or "").upper()
            # Match exact or by digit suffix (e.g. style "10001" matches carton "STY-10001")
            if c_style == style_id_str or style_id_str in c_style or c_style.endswith(style_id_str):
                results[str(cid)] = value
                return


def apply_color_size(s: InspectionState, ext: Any) -> tuple[bool, dict[str, Any], str | None]:
    if not ext or ext.color_size_match is None:
        return False, {}, None
    if ext.color_size_match is False and not ext.mismatch_reason:
        return False, {}, "State the mismatch issue."
    style = ensure_current_style(s)
    style["color_size_match"] = ext.color_size_match
    if ext.color_size_match is False:
        style["mismatch_reason"] = ext.mismatch_reason or ""
    _record_carton_match(s, ext.color_size_match)
    payload = {"color_size_match": ext.color_size_match}
    if ext.mismatch_reason:
        payload["mismatch_reason"] = ext.mismatch_reason
    return True, payload, None


def color_size_verification_node(state: InspectionState) -> InspectionState:
    return run_node(state, "COLOR_SIZE_VERIFICATION", COLOR_SIZE_VERIFICATION_PROMPT, apply_color_size)
