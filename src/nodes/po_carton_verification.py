from __future__ import annotations

from typing import Any

from .prompts import po_carton_verification_prompt
from ..node_runner import run_node
from ..node_utils import init_node_state
from ..po_packages import get_cartons_for_po, get_po_manifest
from ..state import InspectionState, make_event, utc_now


def _po_summary_from_packages(po_number: str) -> tuple[str | None, int | None, int | None]:
    """Derive vendor, style count, expected units from PO package manifest + intrasheet."""
    manifest = get_po_manifest(po_number)
    cartons = get_cartons_for_po(po_number)
    vendor = manifest.get("vendor")
    style_count = manifest.get("expected_style_count")
    expected_units = manifest.get("expected_units_total")
    if cartons:
        if style_count is None:
            styles = {str(c.get("style_id") or "").strip() for c in cartons if c.get("style_id")}
            styles.discard("")
            style_count = len(styles) or None
        if expected_units is None:
            expected_units = sum(
                int(c.get("expected_units") or c.get("expected_units_counted") or 0) for c in cartons
            )
    if not vendor:
        vendor = "Unknown vendor"
    return (vendor, style_count, expected_units)


def apply_po_carton(s: InspectionState, ext: Any) -> tuple[bool, dict[str, Any], str | None]:
    if not ext:
        return False, {}, None
    result = (ext.po_verification_result or "").upper()
    if result not in ("CONFIRMED", "MISMATCH"):
        return False, {}, None
    reason = ext.po_mismatch_reason
    if result == "MISMATCH" and not reason:
        s["po_verification_result"] = "MISMATCH"
        s.setdefault("events", []).append(
            make_event(node="PO_CARTON_VERIFICATION", type_="FIELDS_CAPTURED", payload={"po_verification_result": "MISMATCH"})
        )
        return False, {}, "State the mismatch reason."
    s["po_verification_result"] = result
    if result == "MISMATCH":
        s["po_mismatch_reason"] = reason or ""
    payload = {"po_verification_result": result}
    if reason:
        payload["po_mismatch_reason"] = reason
    stay_prompt = "Mismatch recorded. Say Confirm when resolved." if result == "MISMATCH" else None
    return True, payload, stay_prompt


def prompt_fn(s: InspectionState) -> str:
    po_number = s.get("po_number")
    if po_number:
        cartons = get_cartons_for_po(po_number)
        return po_carton_verification_prompt(
            po_number=po_number,
            vendor=s.get("vendor"),
            expected_style_count=s.get("expected_style_count"),
            expected_units_total=s.get("expected_units_total"),
            carton_count=len(cartons) if cartons else None,
        )
    return "Carton scanned. Say Confirm to proceed or say Mismatch."


def po_carton_verification_node(state: InspectionState) -> InspectionState:
    s = init_node_state(state)
    po_number = s.get("po_number")
    carton_barcode = s.get("carton_barcode")

    if not po_number and not carton_barcode:
        s["current_node"] = "START_IDENTIFICATION"
        s["awaiting_input"] = True
        s["last_prompt"] = {"text": "Please scan the carton barcode or say the PO number to begin inspection.", "ts": utc_now()}
        s.setdefault("events", []).append(
            make_event(node="PO_CARTON_VERIFICATION", type_="VALIDATION_FAILED", payload={"missing": ["po_number", "carton_barcode"]})
        )
        s["last_user_input"] = {}
        return s

    if po_number and (s.get("vendor") is None or s.get("expected_style_count") is None or s.get("expected_units_total") is None):
        vendor, style_count, expected_units = _po_summary_from_packages(po_number)
        if vendor:
            s["vendor"] = vendor
        if style_count is not None:
            s["expected_style_count"] = style_count
        if expected_units is not None:
            s["expected_units_total"] = expected_units

    return run_node(s, "PO_CARTON_VERIFICATION", "Say Confirm or Mismatch.", apply_po_carton, prompt_fn=prompt_fn)
