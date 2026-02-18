from __future__ import annotations

from .prompts import COMPLETE_STYLE_PROMPT
from ..state import InspectionState, make_event, utc_now


STYLE_FIELDS_TO_CLEAR = [
    "style_id",
    "style_entry_method",
    "color_size_match",
    "mismatch_reason",
    "size_counts",
    "total_units_counted",
    "all_units_ok",
    "defects",
    "tags_ok",
    "tags_issues",
    "packaging_ok",
    "packaging_issues",
    "photos",
    "disposition",
    "notes",
]


def _clear_style_fields(state: InspectionState) -> None:
    for key in STYLE_FIELDS_TO_CLEAR:
        state.pop(key, None)


def complete_style_node(state: InspectionState) -> InspectionState:
    """
    Step 12 from required_flow.md:
    - 'Next style' → prepare for another style (same PO/carton) and go to STYLE_SKU_VERIFICATION.
    - 'Close PO' → advance to CLOSE_PO.
    """

    s: InspectionState = dict(state)
    s.setdefault("history", [])
    s.setdefault("events", [])

    user_input = s.get("last_user_input") or {}
    transcript = (user_input.get("transcript") or "").strip()

    if not transcript:
        s["current_node"] = "COMPLETE_STYLE"
        s["awaiting_input"] = True
        s["last_prompt"] = {"text": COMPLETE_STYLE_PROMPT, "ts": utc_now()}
        s["events"].append(make_event(node="COMPLETE_STYLE", type_="PROMPTED", payload={}))
        return s

    t = transcript.lower()
    if "next style" in t or t.startswith("next"):
        s["completed_styles"] = int(s.get("completed_styles", 0)) + 1
        _clear_style_fields(s)
        s["complete_style_action"] = "NEXT_STYLE"
        s["events"].append(
            make_event(
                node="COMPLETE_STYLE",
                type_="FIELDS_CAPTURED",
                payload={"action": "NEXT_STYLE", "completed_styles": s["completed_styles"]},
            )
        )
        s["history"].append("COMPLETE_STYLE")
        s["awaiting_input"] = False
        s["last_completed_node"] = "COMPLETE_STYLE"
        s["last_user_input"] = {}
        return s

    if "close po" in t or t.startswith("close"):
        s["completed_styles"] = int(s.get("completed_styles", 0)) + 1
        s["complete_style_action"] = "CLOSE_PO"
        s["events"].append(
            make_event(
                node="COMPLETE_STYLE",
                type_="FIELDS_CAPTURED",
                payload={"action": "CLOSE_PO", "completed_styles": s["completed_styles"]},
            )
        )
        s["history"].append("COMPLETE_STYLE")
        s["awaiting_input"] = False
        s["last_completed_node"] = "COMPLETE_STYLE"
        s["last_user_input"] = {}
        return s

    s["current_node"] = "COMPLETE_STYLE"
    s["awaiting_input"] = True
    s["last_prompt"] = {"text": COMPLETE_STYLE_PROMPT, "ts": utc_now()}
    s["events"].append(
        make_event(
            node="COMPLETE_STYLE",
            type_="VALIDATION_FAILED",
            payload={"transcript": transcript},
        )
    )
    s["last_user_input"] = {}
    return s

