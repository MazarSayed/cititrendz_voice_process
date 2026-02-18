from __future__ import annotations

from .prompts import PHOTO_CAPTURE_PROMPT
from ..state import InspectionState, ensure_current_style, make_event, utc_now


def _has_exceptions(state: InspectionState) -> bool:
    if state.get("carton_status") == "DAMAGED":
        return True
    style = ensure_current_style(state)
    if style.get("color_size_match") is False:
        return True
    if style.get("all_units_ok") is False:
        return True
    if style.get("tags_ok") is False:
        return True
    if style.get("packaging_ok") is False:
        return True
    return False


def photo_capture_node(state: InspectionState) -> InspectionState:
    """
    Step 9 from required_flow.md (simplified):
    - If no exceptions → skip photos and go straight to DISPOSITION.
    - If exceptions → prompt for photos and wait for 'Photo captured'.
    - On 'Photo captured' → record a stub entry and advance to DISPOSITION.
    """

    s: InspectionState = dict(state)
    s.setdefault("history", [])
    s.setdefault("events", [])

    if not _has_exceptions(s):
        # No exceptions: skip photo step.
        s.setdefault("photos", [])
        s["events"].append(
            make_event(
                node="PHOTO_CAPTURE_LOOP",
                type_="PHOTO_SKIPPED_NO_EXCEPTIONS",
                payload={},
            )
        )
        s["history"].append("PHOTO_CAPTURE_LOOP")
        s["awaiting_input"] = False
        s["last_completed_node"] = "PHOTO_CAPTURE_LOOP"
        s["last_user_input"] = {}
        # Optional, short system message for UX.
        s["last_prompt"] = {
            "text": "No exceptions detected. Proceeding to disposition. State Accept, Accept with exceptions, Hold, or Reject.",
            "ts": utc_now(),
        }
        return s

    user_input = s.get("last_user_input") or {}
    transcript = (user_input.get("transcript") or "").strip().lower()

    if not transcript:
        s["current_node"] = "PHOTO_CAPTURE_LOOP"
        s["awaiting_input"] = True
        s["last_prompt"] = {"text": PHOTO_CAPTURE_PROMPT, "ts": utc_now()}
        s["events"].append(make_event(node="PHOTO_CAPTURE_LOOP", type_="PROMPTED", payload={}))
        return s

    if "photo captured" in transcript or "captured" in transcript:
        s.setdefault("photos", [])
        # For now, just record a stub marker; real implementation will attach actual photo metadata.
        s["photos"].append({"status": "captured"})  # type: ignore[list-item]
        s["events"].append(
            make_event(
                node="PHOTO_CAPTURE_LOOP",
                type_="FIELDS_CAPTURED",
                payload={"photos": s["photos"]},
            )
        )
        s["history"].append("PHOTO_CAPTURE_LOOP")
        s["awaiting_input"] = False
        s["last_completed_node"] = "PHOTO_CAPTURE_LOOP"
        s["last_user_input"] = {}
        return s

    # Unrecognized response, re-prompt.
    s["current_node"] = "PHOTO_CAPTURE_LOOP"
    s["awaiting_input"] = True
    s["last_prompt"] = {"text": PHOTO_CAPTURE_PROMPT, "ts": utc_now()}
    s["events"].append(
        make_event(
            node="PHOTO_CAPTURE_LOOP",
            type_="VALIDATION_FAILED",
            payload={"transcript": user_input.get("transcript")},
        )
    )
    s["last_user_input"] = {}
    return s

