from __future__ import annotations

from .prompts import STYLE_SKU_VERIFICATION_PROMPT
from ..state import InspectionState, ensure_current_style, make_event, utc_now


def _extract_style_number(transcript: str) -> str | None:
    """
    Minimal style extraction for manual entry:
    - Keep conservative: grab digits only and require minimum length.
    """

    digits = "".join(ch for ch in transcript if ch.isdigit())
    if len(digits) >= 4:
        return digits
    return None


def style_sku_verification_node(state: InspectionState) -> InspectionState:
    """
    Step 3 from required_flow.md:
    - Scan first item barcode OR say 'Manual entry' and the style number.
    - Capture `style_id` + `style_entry_method`.
    - Advance to COLOR_SIZE_VERIFICATION.
    """

    s: InspectionState = dict(state)
    s.setdefault("history", [])
    s.setdefault("events", [])

    user_input = s.get("last_user_input") or {}
    transcript = (user_input.get("transcript") or "").strip()
    scan = (user_input.get("scan") or "").strip()

    if not transcript and not scan:
        s["current_node"] = "STYLE_SKU_VERIFICATION"
        s["awaiting_input"] = True
        s["last_prompt"] = {"text": STYLE_SKU_VERIFICATION_PROMPT, "ts": utc_now()}
        s["events"].append(make_event(node="STYLE_SKU_VERIFICATION", type_="PROMPTED", payload={}))
        return s

    if scan:
        style = ensure_current_style(s)
        style["style_id"] = scan
        style["style_entry_method"] = "SCAN"
        s["events"].append(
                make_event(
                    node="STYLE_SKU_VERIFICATION",
                    type_="FIELDS_CAPTURED",
                    payload={"style_id": scan, "style_entry_method": "SCAN"},
                )
        )
        s["history"].append("STYLE_SKU_VERIFICATION")
        s["awaiting_input"] = False
        s["last_completed_node"] = "STYLE_SKU_VERIFICATION"
        s["last_user_input"] = {}
        return s

    t = transcript.lower()
    if "manual" in t:
        style = _extract_style_number(transcript)
        if style:
            style_state = ensure_current_style(s)
            style_state["style_id"] = style
            style_state["style_entry_method"] = "MANUAL"
            s["events"].append(
                make_event(
                    node="STYLE_SKU_VERIFICATION",
                    type_="FIELDS_CAPTURED",
                    payload={"style_id": style, "style_entry_method": "MANUAL"},
                )
            )
            s["history"].append("STYLE_SKU_VERIFICATION")
            s["awaiting_input"] = False
            s["last_completed_node"] = "STYLE_SKU_VERIFICATION"
            s["last_user_input"] = {}
            return s

        s["current_node"] = "STYLE_SKU_VERIFICATION"
        s["awaiting_input"] = True
        s["last_prompt"] = {"text": "Manual entry. Read the style number.", "ts": utc_now()}
        s["events"].append(
            make_event(
                node="STYLE_SKU_VERIFICATION",
                type_="VALIDATION_FAILED",
                payload={"missing": ["style_id"], "transcript": transcript},
            )
        )
        s["last_user_input"] = {}
        return s

    # Unrecognized response
    s["current_node"] = "STYLE_SKU_VERIFICATION"
    s["awaiting_input"] = True
    s["last_prompt"] = {"text": "Scan the item barcode, or say Manual entry and the style number.", "ts": utc_now()}
    s["events"].append(
        make_event(
            node="STYLE_SKU_VERIFICATION",
            type_="VALIDATION_FAILED",
            payload={"transcript": transcript},
        )
    )
    s["last_user_input"] = {}
    return s

