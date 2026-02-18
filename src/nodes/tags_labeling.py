from __future__ import annotations

import re

from .prompts import TAGS_LABELING_PROMPT
from ..parsers import extract_count
from ..state import InspectionState, TagIssue, ensure_current_style, make_event, utc_now


def _issue_type(transcript: str) -> str:
    t = transcript.lower()
    if "upc" in t:
        return "upc"
    if "price" in t:
        return "price_ticket"
    if "size tag" in t or ("size" in t and "tag" in t):
        return "size_tag"
    if "country" in t:
        return "country_of_origin"
    if "missing" in t:
        return "missing_tag"
    return "other"


def tags_labeling_node(state: InspectionState) -> InspectionState:
    """
    Step 7 from required_flow.md:
    - Say Tags OK OR Issue + unit count.
    - Capture tags_ok OR tags_issues[].
    - Advance to PACKAGING_PRESENTATION.
    """

    s: InspectionState = dict(state)
    s.setdefault("history", [])
    s.setdefault("events", [])

    user_input = s.get("last_user_input") or {}
    transcript = (user_input.get("transcript") or "").strip()

    if not transcript:
        s["current_node"] = "TAGS_LABELING"
        s["awaiting_input"] = True
        s["last_prompt"] = {"text": TAGS_LABELING_PROMPT, "ts": utc_now()}
        s["events"].append(make_event(node="TAGS_LABELING", type_="PROMPTED", payload={}))
        return s

    t = transcript.lower()
    if "tags ok" in t or t == "ok":
        style = ensure_current_style(s)
        style["tags_ok"] = True
        style["tags_issues"] = []  # type: ignore[assignment]
        s["events"].append(
            make_event(node="TAGS_LABELING", type_="FIELDS_CAPTURED", payload={"tags_ok": True})
        )
        s["history"].append("TAGS_LABELING")
        s["awaiting_input"] = False
        s["last_completed_node"] = "TAGS_LABELING"
        s["last_user_input"] = {}
        return s

    count = extract_count(transcript)
    if count is None:
        s["current_node"] = "TAGS_LABELING"
        s["awaiting_input"] = True
        s["last_prompt"] = {"text": "State the issue and unit count. Example: Missing price tags, four units.", "ts": utc_now()}
        s["events"].append(
            make_event(
                node="TAGS_LABELING",
                type_="VALIDATION_FAILED",
                payload={"missing": ["affected_unit_count"], "transcript": transcript},
            )
        )
        s["last_user_input"] = {}
        return s

    issue: TagIssue = {"issue_type": _issue_type(transcript), "affected_unit_count": count, "raw": transcript}
    style = ensure_current_style(s)
    style["tags_ok"] = False
    style["tags_issues"] = [issue]  # type: ignore[assignment]
    s["events"].append(
        make_event(
            node="TAGS_LABELING",
            type_="FIELDS_CAPTURED",
            payload={"tags_ok": False, "tags_issues": [issue]},
        )
    )
    s["history"].append("TAGS_LABELING")
    s["awaiting_input"] = False
    s["last_completed_node"] = "TAGS_LABELING"
    s["last_user_input"] = {}
    return s

