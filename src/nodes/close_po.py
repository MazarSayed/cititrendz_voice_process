from __future__ import annotations

from .prompts import CLOSE_PO_PROMPT
from ..state import InspectionState, make_event, utc_now


def close_po_node(state: InspectionState) -> InspectionState:
    """
    Final PO closure node.
    """

    s: InspectionState = dict(state)
    s.setdefault("history", [])
    s.setdefault("events", [])

    # Always be in CLOSE_PO and stop the run here.
    s["current_node"] = "CLOSE_PO"
    s["awaiting_input"] = True
    s["last_prompt"] = {"text": CLOSE_PO_PROMPT, "ts": utc_now()}
    if s.get("history", [])[-1:] != ["CLOSE_PO"]:
        s["events"].append(make_event(node="CLOSE_PO", type_="PROMPTED", payload={}))
        s.setdefault("history", []).append("CLOSE_PO")

    s["last_user_input"] = {}
    return s

