from __future__ import annotations

from .prompts import DISPOSITION_PROMPT
from ..state import Disposition, InspectionState, ensure_current_style, make_event, utc_now


def _parse_disposition(transcript: str) -> Disposition | None:
    t = transcript.strip().lower()
    if not t:
        return None

    if t.startswith("accept with") or "accept with exceptions" in t or "accept with exception" in t:
        return "ACCEPT_WITH_EXCEPTIONS"
    if t.startswith("accept"):
        return "ACCEPT"
    if t.startswith("hold"):
        return "HOLD"
    if t.startswith("reject"):
        return "REJECT"
    return None


def disposition_node(state: InspectionState) -> InspectionState:
    """
    Step 10 from required_flow.md:
    - Capture disposition: Accept, Accept with exceptions, Hold, or Reject.
    - Advance to NOTES_OPTIONAL (still TODO).
    """

    s: InspectionState = dict(state)
    s.setdefault("history", [])
    s.setdefault("events", [])

    user_input = s.get("last_user_input") or {}
    transcript = (user_input.get("transcript") or "").strip()

    if not transcript:
        s["current_node"] = "DISPOSITION"
        s["awaiting_input"] = True
        s["last_prompt"] = {"text": DISPOSITION_PROMPT, "ts": utc_now()}
        s["events"].append(make_event(node="DISPOSITION", type_="PROMPTED", payload={}))
        return s

    disp = _parse_disposition(transcript)
    if disp is None:
        s["current_node"] = "DISPOSITION"
        s["awaiting_input"] = True
        s["last_prompt"] = {"text": DISPOSITION_PROMPT, "ts": utc_now()}
        s["events"].append(
            make_event(
                node="DISPOSITION",
                type_="VALIDATION_FAILED",
                payload={"transcript": transcript},
            )
        )
        s["last_user_input"] = {}
        return s

    style = ensure_current_style(s)
    style["disposition"] = disp
    s["disposition"] = disp  # convenience mirror
    s["events"].append(
        make_event(
            node="DISPOSITION",
            type_="FIELDS_CAPTURED",
            payload={"disposition": disp},
        )
    )
    s["history"].append("DISPOSITION")
    s["awaiting_input"] = False
    s["last_completed_node"] = "DISPOSITION"
    s["last_user_input"] = {}
    return s

