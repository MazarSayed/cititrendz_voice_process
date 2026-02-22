from __future__ import annotations

from typing import Any

from .prompts import PHOTO_CAPTURE_PROMPT
from ..node_runner import run_node
from ..node_utils import init_node_state
from ..state import InspectionState, ensure_current_style, make_event, utc_now


def has_exceptions(state: InspectionState) -> bool:
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


def apply_photo(s: InspectionState, ext: Any) -> tuple[bool, dict[str, Any], str | None]:
    if not ext or ext.photo_captured is not True:
        return False, {}, None
    s.setdefault("photos", [])
    s["photos"].append({"status": "captured"})  # type: ignore[list-item]
    return True, {"photos": s["photos"]}, None


def photo_capture_node(state: InspectionState) -> InspectionState:
    s = init_node_state(state)
    if not has_exceptions(s):
        s.setdefault("photos", [])
        s.setdefault("events", []).append(
            make_event(node="PHOTO_CAPTURE_LOOP", type_="PHOTO_SKIPPED_NO_EXCEPTIONS", payload={})
        )
        s.setdefault("history", []).append("PHOTO_CAPTURE_LOOP")
        s["awaiting_input"] = False
        s["last_completed_node"] = "PHOTO_CAPTURE_LOOP"
        s["last_user_input"] = {}
        s["last_prompt"] = {
            "text": "No exceptions detected. Proceeding to disposition. State Accept, Accept with exceptions, Hold, or Reject.",
            "ts": utc_now(),
        }
        return s
    return run_node(state, "PHOTO_CAPTURE_LOOP", PHOTO_CAPTURE_PROMPT, apply_photo)
