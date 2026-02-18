from __future__ import annotations

import re

from .prompts import PACKAGING_PRESENTATION_PROMPT
from ..parsers import extract_count
from ..state import InspectionState, PackagingIssue, ensure_current_style, make_event, utc_now


def _issue_type(transcript: str) -> str:
    t = transcript.lower()
    if "fold" in t or "folding" in t:
        return "folding"
    if "polybag" in t or "poly bag" in t:
        return "polybag"
    if "hanger" in t:
        return "hanger"
    if "insert" in t:
        return "insert"
    if "missing" in t:
        return "missing_packaging"
    return "other"


def packaging_presentation_node(state: InspectionState) -> InspectionState:
    """
    Step 8 from required_flow.md:
    - Say Packaging OK OR describe issue (optionally with count).
    - Capture packaging_ok OR packaging_issues[].
    - Advance to PHOTO_CAPTURE_LOOP (still TODO).
    """

    s: InspectionState = dict(state)
    s.setdefault("history", [])
    s.setdefault("events", [])

    user_input = s.get("last_user_input") or {}
    transcript = (user_input.get("transcript") or "").strip()

    if not transcript:
        s["current_node"] = "PACKAGING_PRESENTATION"
        s["awaiting_input"] = True
        s["last_prompt"] = {"text": PACKAGING_PRESENTATION_PROMPT, "ts": utc_now()}
        s["events"].append(make_event(node="PACKAGING_PRESENTATION", type_="PROMPTED", payload={}))
        return s

    t = transcript.lower()
    if "packaging ok" in t or t == "ok":
        style = ensure_current_style(s)
        style["packaging_ok"] = True
        style["packaging_issues"] = []  # type: ignore[assignment]
        s["events"].append(
            make_event(
                node="PACKAGING_PRESENTATION",
                type_="FIELDS_CAPTURED",
                payload={"packaging_ok": True, "packaging_issues": []},
            )
        )
        s["history"].append("PACKAGING_PRESENTATION")
        s["awaiting_input"] = False
        s["last_completed_node"] = "PACKAGING_PRESENTATION"
        s["last_user_input"] = {}
        return s

    cnt = extract_count(transcript)
    issue: PackagingIssue = {
        "issue_type": _issue_type(transcript),
        "raw": transcript,
        "affected_unit_count": cnt or 0,
    }

    style = ensure_current_style(s)
    style["packaging_ok"] = False
    style["packaging_issues"] = [issue]
    s["events"].append(
        make_event(
            node="PACKAGING_PRESENTATION",
            type_="FIELDS_CAPTURED",
            payload={"packaging_ok": False, "packaging_issues": [issue]},
        )
    )
    s["history"].append("PACKAGING_PRESENTATION")
    s["awaiting_input"] = False
    s["last_completed_node"] = "PACKAGING_PRESENTATION"
    s["last_user_input"] = {}
    return s

