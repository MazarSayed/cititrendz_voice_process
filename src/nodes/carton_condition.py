from __future__ import annotations

from .prompts import CARTON_CONDITION_PROMPT
from ..parsers import parse_carton_condition
from ..state import DamageSeverity, InspectionState, make_event, utc_now


def carton_condition_node(state: InspectionState) -> InspectionState:
    """
    Step 2 from required_flow.md:
    - Ask carton condition.
    - Capture OK or (damage_type + damage_severity).
    - Advance to STYLE_SKU_VERIFICATION when captured.
    """

    s: InspectionState = dict(state)
    s.setdefault("history", [])
    s.setdefault("events", [])

    user_input = s.get("last_user_input") or {}
    transcript = (user_input.get("transcript") or "").strip()

    if not transcript:
        s["current_node"] = "CARTON_CONDITION"
        s["awaiting_input"] = True
        s["last_prompt"] = {"text": CARTON_CONDITION_PROMPT, "ts": utc_now()}
        s["events"].append(make_event(node="CARTON_CONDITION", type_="PROMPTED", payload={}))
        return s

    carton_status, damage_type, damage_severity = parse_carton_condition(transcript)

    if carton_status is None:
        s["current_node"] = "CARTON_CONDITION"
        s["awaiting_input"] = True
        s["last_prompt"] = {
            "text": "Say Carton OK, or say the damage type and severity (minor or major).",
            "ts": utc_now(),
        }
        s["events"].append(
            make_event(
                node="CARTON_CONDITION",
                type_="VALIDATION_FAILED",
                payload={"transcript": transcript},
            )
        )
        s["last_user_input"] = {}
        return s

    if carton_status == "OK":
        s["carton_status"] = "OK"
        s["events"].append(
            make_event(node="CARTON_CONDITION", type_="FIELDS_CAPTURED", payload={"carton_status": "OK"})
        )
        s["history"].append("CARTON_CONDITION")
        s["awaiting_input"] = False
        s["last_completed_node"] = "CARTON_CONDITION"
        s["last_user_input"] = {}
        return s

    # DAMAGED case requires both type and severity.
    if not damage_type or not damage_severity:
        missing: list[str] = []
        if not damage_type:
            missing.append("damage_type")
        if not damage_severity:
            missing.append("damage_severity")

        s["carton_status"] = "DAMAGED"
        s["current_node"] = "CARTON_CONDITION"
        s["awaiting_input"] = True
        s["last_prompt"] = {
            "text": "Carton damaged. State the damage type and severity (minor or major).",
            "ts": utc_now(),
        }
        s["events"].append(
            make_event(
                node="CARTON_CONDITION",
                type_="VALIDATION_FAILED",
                payload={"missing": missing, "transcript": transcript},
            )
        )
        s["last_user_input"] = {}
        return s

    s["carton_status"] = "DAMAGED"
    s["damage_type"] = damage_type
    s["damage_severity"] = damage_severity
    s["events"].append(
        make_event(
            node="CARTON_CONDITION",
            type_="FIELDS_CAPTURED",
            payload={
                "carton_status": "DAMAGED",
                "damage_type": damage_type,
                "damage_severity": damage_severity,
            },
        )
    )
    s["history"].append("CARTON_CONDITION")
    s["awaiting_input"] = False
    s["last_completed_node"] = "CARTON_CONDITION"
    s["last_user_input"] = {}
    return s

