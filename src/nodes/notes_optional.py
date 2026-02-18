from __future__ import annotations

from .prompts import NOTES_PROMPT
from ..state import InspectionState, ensure_current_style, make_event, utc_now


def notes_optional_node(state: InspectionState) -> InspectionState:
    """
    Step 11 from required_flow.md:
    - Optional notes: either 'No notes' or free text.
    - Advance to COMPLETE_STYLE.
    """

    s: InspectionState = dict(state)
    s.setdefault("history", [])
    s.setdefault("events", [])

    user_input = s.get("last_user_input") or {}
    transcript = (user_input.get("transcript") or "").strip()

    if not transcript:
        s["current_node"] = "NOTES_OPTIONAL"
        s["awaiting_input"] = True
        s["last_prompt"] = {"text": NOTES_PROMPT, "ts": utc_now()}
        s["events"].append(make_event(node="NOTES_OPTIONAL", type_="PROMPTED", payload={}))
        return s

    t = transcript.lower()
    if "no notes" in t or t in ("none", "no note"):
        style = ensure_current_style(s)
        style["notes"] = ""
    else:
        style = ensure_current_style(s)
        style["notes"] = transcript

    s["events"].append(
        make_event(
            node="NOTES_OPTIONAL",
            type_="FIELDS_CAPTURED",
            payload={"notes": style.get("notes", "")},
        )
    )
    s["history"].append("NOTES_OPTIONAL")
    s["awaiting_input"] = False
    s["last_completed_node"] = "NOTES_OPTIONAL"
    s["last_user_input"] = {}
    return s

