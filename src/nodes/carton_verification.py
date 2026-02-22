"""
Carton verification: read cartons from Excel one by one, user says Match or Mismatch.
"""
from __future__ import annotations

from ..node_utils import init_node_state
from ..po_packages import get_cartons_for_po
from ..state import InspectionState, make_event, utc_now


def _parse_match_mismatch(transcript: str) -> bool | None:
    t = (transcript or "").strip().lower()
    if "match" in t and "mismatch" not in t:
        return True
    if "mismatch" in t or "not match" in t:
        return False
    return None


def _prompt_for_carton(s: InspectionState) -> str:
    po_number = s.get("po_number")
    cartons = get_cartons_for_po(po_number) if po_number else []
    idx = s.get("current_carton_index", 0)
    if idx >= len(cartons):
        return "All cartons verified. Proceeding to carton condition."
    carton = cartons[idx]
    cid = carton.get("barcode") or carton.get("carton_id") or f"Carton {idx + 1}"
    return f"Carton {cid}. Say Match or Mismatch."


def carton_verification_node(state: InspectionState) -> InspectionState:
    s = init_node_state(state)
    po_number = s.get("po_number")
    cartons = get_cartons_for_po(po_number) if po_number else []

    def _msg(role: str, content: str) -> None:
        s.setdefault("messages", []).append({"role": role, "content": content})

    if not cartons:
        text = "No cartons in PO list. Proceeding to carton condition."
        _msg("assistant", text)
        s["current_node"] = "CARTON_CONDITION"
        s["awaiting_input"] = False
        s["last_completed_node"] = "CARTON_VERIFICATION"
        s["last_prompt"] = {"text": text, "ts": utc_now()}
        return s

    transcript = (s.get("last_user_input") or {}).get("transcript") or ""
    idx = s.get("current_carton_index", 0)

    if idx >= len(cartons):
        text = "All cartons verified. Proceeding to carton condition."
        _msg("assistant", text)
        s["current_node"] = "CARTON_CONDITION"
        s["awaiting_input"] = False
        s["last_completed_node"] = "CARTON_VERIFICATION"
        s["last_prompt"] = {"text": text, "ts": utc_now()}
        return s

    if not transcript.strip():
        text = _prompt_for_carton(s)
        _msg("assistant", text)
        s["current_node"] = "CARTON_VERIFICATION"
        s["awaiting_input"] = True
        s["last_prompt"] = {"text": text, "ts": utc_now()}
        s.setdefault("events", []).append(make_event(node="CARTON_VERIFICATION", type_="PROMPTED", payload={}))
        return s

    _msg("user", transcript)
    match = _parse_match_mismatch(transcript)
    if match is None:
        text = "Say Match or Mismatch."
        _msg("assistant", text)
        s["current_node"] = "CARTON_VERIFICATION"
        s["awaiting_input"] = True
        s["last_prompt"] = {"text": text, "ts": utc_now()}
        return s

    results = s.setdefault("carton_match_results", {})
    carton = cartons[idx]
    cid = str(carton.get("barcode") or carton.get("carton_id") or "")
    results[cid] = "Match" if match else "Mismatch"
    s["current_carton_index"] = idx + 1

    if idx + 1 >= len(cartons):
        text = "All cartons verified. Proceeding to carton condition."
        _msg("assistant", text)
        s["current_node"] = "CARTON_CONDITION"
        s["awaiting_input"] = False
        s["last_completed_node"] = "CARTON_VERIFICATION"
        s["last_prompt"] = {"text": text, "ts": utc_now()}
        s.setdefault("history", []).append("CARTON_VERIFICATION")
        s.setdefault("events", []).append(
            make_event(node="CARTON_VERIFICATION", type_="FIELDS_CAPTURED", payload={"carton_match_results": dict(results)})
        )
        return s

    next_carton = cartons[idx + 1]
    next_cid = next_carton.get("barcode") or next_carton.get("carton_id") or f"Carton {idx + 2}"
    next_text = f"Carton {next_cid}. Say Match or Mismatch."
    _msg("assistant", next_text)
    s["current_node"] = "CARTON_VERIFICATION"
    s["awaiting_input"] = True
    s["last_prompt"] = {"text": next_text, "ts": utc_now()}
    s.setdefault("history", []).append("CARTON_VERIFICATION")
    s.setdefault("events", []).append(
        make_event(node="CARTON_VERIFICATION", type_="FIELDS_CAPTURED", payload={"carton_match_results": dict(results)})
    )
    s["last_user_input"] = {}
    return s
