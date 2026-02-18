from __future__ import annotations

from .prompts import START_IDENTIFICATION_PROMPT
from ..state import InspectionState, make_event, utc_now


def _extract_po_number(transcript: str) -> str | None:
    """
    Minimal PO extraction.

    v1: keep it conservative—only extract digits and require a minimum length.
    Later we can add number-word parsing ("one two three") and vendor-specific formats.
    """

    digits = "".join(ch for ch in transcript if ch.isdigit())
    if len(digits) >= 5:
        return digits
    return None


def start_identification_node(state: InspectionState) -> InspectionState:
    """
    Step 0 from required_flow.md:
    - Prompt for carton barcode scan OR spoken PO number.
    - If not provided/parsed, re-prompt and stay on this node.
    - If captured, advance to PO_CARTON_VERIFICATION.
    """

    s: InspectionState = dict(state)
    s.setdefault("history", [])
    s.setdefault("events", [])

    # If no user input yet, just prompt.
    user_input = s.get("last_user_input") or {}
    transcript = (user_input.get("transcript") or "").strip()
    scan = (user_input.get("scan") or "").strip()

    if not transcript and not scan:
        s["current_node"] = "START_IDENTIFICATION"
        s["awaiting_input"] = True
        s["last_prompt"] = {"text": START_IDENTIFICATION_PROMPT, "ts": utc_now()}
        s["events"].append(make_event(node="START_IDENTIFICATION", type_="PROMPTED", payload={}))
        return s

    # Prefer scan if present.
    if scan:
        s["carton_barcode"] = scan
        s["events"].append(
            make_event(
                node="START_IDENTIFICATION",
                type_="FIELDS_CAPTURED",
                payload={"carton_barcode": scan},
            )
        )
        s["history"].append("START_IDENTIFICATION")
        s["awaiting_input"] = False
        s["last_completed_node"] = "START_IDENTIFICATION"
        s["last_user_input"] = {}
        return s

    po = _extract_po_number(transcript)
    if po:
        s["po_number"] = po
        s["events"].append(
            make_event(node="START_IDENTIFICATION", type_="FIELDS_CAPTURED", payload={"po_number": po})
        )
        s["history"].append("START_IDENTIFICATION")
        s["awaiting_input"] = False
        s["last_completed_node"] = "START_IDENTIFICATION"
        s["last_user_input"] = {}
        return s

    # Could not parse; re-prompt and stay.
    s["current_node"] = "START_IDENTIFICATION"
    s["awaiting_input"] = True
    s["last_prompt"] = {
        "text": "I didn’t catch that. Scan the carton barcode or say the PO number to begin inspection.",
        "ts": utc_now(),
    }
    s["events"].append(
        make_event(
            node="START_IDENTIFICATION",
            type_="VALIDATION_FAILED",
            payload={"transcript": transcript},
        )
    )
    s["last_user_input"] = {}
    return s

