from __future__ import annotations

from .prompts import po_carton_verification_prompt
from ..state import InspectionState, make_event, utc_now


def _stub_po_summary(po_number: str) -> tuple[str | None, int | None, int | None]:
    """
    Temporary stand-in for purchasing system / PO lookup.

    Keep minimal: return known demo values for the example PO; otherwise unknowns.
    """

    if po_number == "123456":
        return ("Acme Apparel", 3, 48)
    return (None, None, None)


def _parse_confirm_mismatch(transcript: str) -> tuple[str | None, str | None]:
    """
    Returns (result, reason)
    - result: "CONFIRMED" | "MISMATCH" | None
    - reason: optional mismatch reason (if present in same utterance)
    """

    t = transcript.strip().lower()
    if not t:
        return (None, None)

    if "confirm" in t:
        return ("CONFIRMED", None)

    if "mismatch" in t or "mis match" in t:
        # Minimal heuristic: anything after the keyword is a reason.
        reason = transcript
        for kw in ("mismatch", "mis match"):
            idx = t.find(kw)
            if idx != -1:
                reason = transcript[idx + len(kw) :].strip(" .,-")
                break
        return ("MISMATCH", reason or None)

    return (None, None)


def po_carton_verification_node(state: InspectionState) -> InspectionState:
    """
    Step 1 from required_flow.md:
    - Reads back PO summary and asks: Confirm or Mismatch.
    - Captures confirmation result (and optional mismatch reason).
    - Advances to CARTON_CONDITION on Confirm.
    """

    s: InspectionState = dict(state)
    s.setdefault("history", [])
    s.setdefault("events", [])

    po_number = s.get("po_number")
    carton_barcode = s.get("carton_barcode")

    # Safety: if we somehow got here without identifying info, send back to step 0.
    if not po_number and not carton_barcode:
        s["current_node"] = "START_IDENTIFICATION"
        s["awaiting_input"] = True
        s["last_prompt"] = {
            "text": "Please scan the carton barcode or say the PO number to begin inspection.",
            "ts": utc_now(),
        }
        s["events"].append(
            make_event(
                node="PO_CARTON_VERIFICATION",
                type_="VALIDATION_FAILED",
                payload={"missing": ["po_number", "carton_barcode"]},
            )
        )
        s["last_user_input"] = {}
        return s

    # Populate stubbed PO summary if missing (v1 placeholder).
    if po_number and (
        s.get("vendor") is None
        or s.get("expected_style_count") is None
        or s.get("expected_units_total") is None
    ):
        vendor, style_count, expected_units = _stub_po_summary(po_number)
        if vendor and s.get("vendor") is None:
            s["vendor"] = vendor
        if style_count is not None and s.get("expected_style_count") is None:
            s["expected_style_count"] = style_count
        if expected_units is not None and s.get("expected_units_total") is None:
            s["expected_units_total"] = expected_units

    # If no user input yet, prompt with summary and stay.
    user_input = s.get("last_user_input") or {}
    transcript = (user_input.get("transcript") or "").strip()

    if not transcript:
        if po_number:
            s["current_node"] = "PO_CARTON_VERIFICATION"
            s["awaiting_input"] = True
            s["last_prompt"] = {
                "text": po_carton_verification_prompt(
                    po_number=po_number,
                    vendor=s.get("vendor"),
                    expected_style_count=s.get("expected_style_count"),
                    expected_units_total=s.get("expected_units_total"),
                ),
                "ts": utc_now(),
            }
        else:
            # If PO is not known yet (e.g., only carton barcode captured), keep prompt minimal for now.
            s["current_node"] = "PO_CARTON_VERIFICATION"
            s["awaiting_input"] = True
            s["last_prompt"] = {
                "text": "Carton scanned. Say Confirm to proceed or say Mismatch.",
                "ts": utc_now(),
            }

        s["events"].append(make_event(node="PO_CARTON_VERIFICATION", type_="PROMPTED", payload={}))
        return s

    result, reason = _parse_confirm_mismatch(transcript)
    if result is None:
        s["current_node"] = "PO_CARTON_VERIFICATION"
        s["awaiting_input"] = True
        s["last_prompt"] = {"text": "Say Confirm or Mismatch.", "ts": utc_now()}
        s["events"].append(
            make_event(
                node="PO_CARTON_VERIFICATION",
                type_="VALIDATION_FAILED",
                payload={"transcript": transcript},
            )
        )
        s["last_user_input"] = {}
        return s

    if result == "MISMATCH" and not reason:
        s["po_verification_result"] = "MISMATCH"
        s["current_node"] = "PO_CARTON_VERIFICATION"
        s["awaiting_input"] = True
        s["last_prompt"] = {"text": "State the mismatch reason.", "ts": utc_now()}
        s["events"].append(
            make_event(
                node="PO_CARTON_VERIFICATION",
                type_="FIELDS_CAPTURED",
                payload={"po_verification_result": "MISMATCH"},
            )
        )
        s["last_user_input"] = {}
        return s

    # Capture fields.
    s["po_verification_result"] = result  # type: ignore[assignment]
    if result == "MISMATCH":
        s["po_mismatch_reason"] = reason or ""

    s["events"].append(
        make_event(
            node="PO_CARTON_VERIFICATION",
            type_="FIELDS_CAPTURED",
            payload={
                "po_verification_result": result,
                **({"po_mismatch_reason": reason} if reason else {}),
            },
        )
    )
    s["history"].append("PO_CARTON_VERIFICATION")

    if result == "CONFIRMED":
        s["awaiting_input"] = False
        s["last_completed_node"] = "PO_CARTON_VERIFICATION"
    else:
        # Stay here when mismatch is recorded (until resolved/escalated later).
        s["current_node"] = "PO_CARTON_VERIFICATION"
        s["awaiting_input"] = True
        s["last_prompt"] = {"text": "Mismatch recorded. Say Confirm when resolved.", "ts": utc_now()}

    s["last_user_input"] = {}
    return s

