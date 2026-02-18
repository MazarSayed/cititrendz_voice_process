from __future__ import annotations

import re

from .prompts import DEFECT_INSPECTION_PROMPT
from ..state import DefectEntry, InspectionState, ensure_current_style, make_event, utc_now


_DEFECT_KEYWORDS: dict[str, str] = {
    "stain": "stains",
    "stains": "stains",
    "hole": "holes",
    "holes": "holes",
    "tear": "tears",
    "tears": "tears",
    "seam": "seam_defect",
    "misprint": "misprint",
    "misprints": "misprint",
    "odor": "odor",
    "smell": "odor",
}


def _parse_defect(transcript: str) -> tuple[str | None, int | None, str | None]:
    """
    Returns (defect_type, affected_unit_count, severity) where severity is MINOR|MAJOR.

    Minimal and conservative:
    - requires a numeric count
    - requires severity word
    - defect type guessed from keywords (else 'other')
    """

    t = transcript.strip().lower()
    if not t:
        return (None, None, None)

    # Defect type
    defect_type = None
    for kw, normalized in _DEFECT_KEYWORDS.items():
        if kw in t:
            defect_type = normalized
            break
    if defect_type is None:
        defect_type = "other"

    # Count: first integer mentioned
    m = re.search(r"\b(\d+)\b", t)
    count = int(m.group(1)) if m else None

    # Severity
    severity = None
    if "minor" in t:
        severity = "MINOR"
    elif "major" in t:
        severity = "MAJOR"

    return (defect_type, count, severity)


def defect_inspection_node(state: InspectionState) -> InspectionState:
    """
    Step 6 from required_flow.md:
    - If "All units OK" → set all_units_ok=true, defects=[]
    - Else capture a single defect entry (type, affected count, severity) for now
    - Advance to TAGS_LABELING (still TODO)
    """

    s: InspectionState = dict(state)
    s.setdefault("history", [])
    s.setdefault("events", [])

    user_input = s.get("last_user_input") or {}
    transcript = (user_input.get("transcript") or "").strip()

    if not transcript:
        s["current_node"] = "DEFECT_INSPECTION_100pct"
        s["awaiting_input"] = True
        s["last_prompt"] = {"text": DEFECT_INSPECTION_PROMPT, "ts": utc_now()}
        s["events"].append(make_event(node="DEFECT_INSPECTION_100pct", type_="PROMPTED", payload={}))
        return s

    t = transcript.lower()
    if "all units ok" in t or "all unit ok" in t:
        style = ensure_current_style(s)
        style["all_units_ok"] = True
        style["defects"] = []  # type: ignore[assignment]
        s["events"].append(
            make_event(
                node="DEFECT_INSPECTION_100pct",
                type_="FIELDS_CAPTURED",
                payload={"all_units_ok": True, "defects": []},
            )
        )
        s["history"].append("DEFECT_INSPECTION_100pct")
        s["awaiting_input"] = False
        s["last_completed_node"] = "DEFECT_INSPECTION_100pct"
        s["last_user_input"] = {}
        return s

    defect_type, count, severity = _parse_defect(transcript)
    if count is None or severity is None:
        missing: list[str] = []
        if count is None:
            missing.append("affected_unit_count")
        if severity is None:
            missing.append("severity")
        s["current_node"] = "DEFECT_INSPECTION_100pct"
        s["awaiting_input"] = True
        s["last_prompt"] = {
            "text": "Say defect type, affected unit count, and severity (minor or major).",
            "ts": utc_now(),
        }
        s["events"].append(
            make_event(
                node="DEFECT_INSPECTION_100pct",
                type_="VALIDATION_FAILED",
                payload={"missing": missing, "transcript": transcript},
            )
        )
        s["last_user_input"] = {}
        return s

    defect: DefectEntry = {"type": defect_type or "other", "affected_units": count, "severity": severity}
    style = ensure_current_style(s)
    style["all_units_ok"] = False
    style["defects"] = [defect]
    s["events"].append(
        make_event(
            node="DEFECT_INSPECTION_100pct",
            type_="FIELDS_CAPTURED",
            payload={"all_units_ok": False, "defects": [defect]},
        )
    )
    s["history"].append("DEFECT_INSPECTION_100pct")
    s["awaiting_input"] = False
    s["last_completed_node"] = "DEFECT_INSPECTION_100pct"
    s["last_user_input"] = {}
    return s

