from __future__ import annotations

from .prompts import COLOR_SIZE_VERIFICATION_PROMPT
from ..parsers import parse_confirm_mismatch
from ..state import InspectionState, ensure_current_style, make_event, utc_now


def color_size_verification_node(state: InspectionState) -> InspectionState:
    """
    Step 4 from required_flow.md:
    - Ask Match or Mismatch, then issue.
    - Capture `color_size_match` + optional `mismatch_reason`.
    - Advance to UNIT_COUNT_BY_SIZE.
    """

    s: InspectionState = dict(state)
    s.setdefault("history", [])
    s.setdefault("events", [])

    user_input = s.get("last_user_input") or {}
    transcript = (user_input.get("transcript") or "").strip()

    if not transcript:
        s["current_node"] = "COLOR_SIZE_VERIFICATION"
        s["awaiting_input"] = True
        s["last_prompt"] = {"text": COLOR_SIZE_VERIFICATION_PROMPT, "ts": utc_now()}
        s["events"].append(make_event(node="COLOR_SIZE_VERIFICATION", type_="PROMPTED", payload={}))
        return s

    match, reason = parse_confirm_mismatch(transcript)
    if match is None:
        s["current_node"] = "COLOR_SIZE_VERIFICATION"
        s["awaiting_input"] = True
        s["last_prompt"] = {
            "text": "Say Match or Mismatch, then state the issue.",
            "ts": utc_now(),
        }
        s["events"].append(
            make_event(
                node="COLOR_SIZE_VERIFICATION",
                type_="VALIDATION_FAILED",
                payload={"transcript": transcript},
            )
        )
        s["last_user_input"] = {}
        return s

    if match is False and not reason:
        style = ensure_current_style(s)
        style["color_size_match"] = False
        s["current_node"] = "COLOR_SIZE_VERIFICATION"
        s["awaiting_input"] = True
        s["last_prompt"] = {"text": "State the mismatch issue.", "ts": utc_now()}
        s["events"].append(
            make_event(
                node="COLOR_SIZE_VERIFICATION",
                type_="VALIDATION_FAILED",
                payload={"missing": ["mismatch_reason"], "transcript": transcript},
            )
        )
        s["last_user_input"] = {}
        return s

    style = ensure_current_style(s)
    style["color_size_match"] = match
    if match is False:
        style["mismatch_reason"] = reason or ""

    s["events"].append(
        make_event(
            node="COLOR_SIZE_VERIFICATION",
            type_="FIELDS_CAPTURED",
            payload={
                "color_size_match": match,
                **({"mismatch_reason": reason} if reason else {}),
            },
        )
    )
    s["history"].append("COLOR_SIZE_VERIFICATION")
    s["awaiting_input"] = False
    s["last_completed_node"] = "COLOR_SIZE_VERIFICATION"
    s["last_user_input"] = {}
    return s

