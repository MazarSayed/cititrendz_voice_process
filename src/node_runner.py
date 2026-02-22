"""
Centralized node execution for the 14-stage inspection flow.

Flow contract (see src/flow_contract.md):
  1. Required-information validation: only advance when required info is extracted;
     otherwise stay on the same step and re-prompt.
  2. Pydantic: extraction and validation use Pydantic models (complete, extracted, follow_up).
  3. Global state: when info is captured, apply_fn updates state; that state is
     returned to the API and reflected in the UI.
"""

from __future__ import annotations

from typing import Any, Callable

from .llm_layer import llm_extract
from .node_utils import fields_captured, init_node_state, validation_failed
from .state import InspectionState, make_event, utc_now  # noqa: F401


def get_transcript(state: InspectionState) -> tuple[str, str]:
    """Return (transcript, scan)."""
    ui = state.get("last_user_input") or {}
    transcript = (ui.get("transcript") or "").strip()
    scan = (ui.get("scan") or "").strip()
    return transcript, scan


def run_node(
    state: InspectionState,
    node_name: str,
    prompt_text: str,
    apply_fn: Callable[[InspectionState, Any], tuple[bool, dict[str, Any], str | None]],
    *,
    prompt_fn: Callable[[InspectionState], str] | None = None,
    scan_handler: Callable[[InspectionState, str], InspectionState] | None = None,
) -> InspectionState:
    """
    Run one stage: extract with Pydantic, validate, then advance or re-prompt.

    - No transcript: prompt user (or handle scan) and return; awaiting_input=True.
    - Has transcript: LLM extract → apply_fn validates required info.
      - If apply_fn returns ok=True: update global state via fields_captured, set
        awaiting_input=False → graph will advance to next stage.
      - If ok=False or LLM complete=False: stay on same stage, set last_prompt to
        follow_up (repeat question), awaiting_input=True → no advance.
    """
    s = init_node_state(state)
    transcript, scan = get_transcript(state)

    def _msg(role: str, content: str) -> None:
        s.setdefault("messages", []).append({"role": role, "content": content})

    if not transcript:
        if scan and scan_handler:
            return scan_handler(s, scan)
        text = prompt_fn(s) if prompt_fn else prompt_text
        _msg("assistant", text)
        s["current_node"] = node_name
        s["awaiting_input"] = True
        s["last_prompt"] = {"text": text, "ts": utc_now()}
        s.setdefault("events", []).append(make_event(node=node_name, type_="PROMPTED", payload={}))
        return s

    _msg("user", transcript)
    result = llm_extract(node_name, transcript, dict(s), prompt_text)

    if not result.complete:
        follow_up = result.follow_up or prompt_text
        _msg("assistant", follow_up)
        validation_failed(node_name, s, transcript, prompt_text=follow_up)
        return s

    ok, payload, re_prompt = apply_fn(s, result.extracted)
    if ok:
        fields_captured(node_name, s, payload)
        if re_prompt:
            _msg("assistant", re_prompt)
            s["current_node"] = node_name
            s["awaiting_input"] = True
            s["last_prompt"] = {"text": re_prompt, "ts": utc_now()}
    else:
        follow_up = re_prompt or result.follow_up or prompt_text
        _msg("assistant", follow_up)
        s["current_node"] = node_name
        s["awaiting_input"] = True
        s["last_user_input"] = {}
        if re_prompt:
            s["last_prompt"] = {"text": re_prompt, "ts": utc_now()}
        else:
            validation_failed(node_name, s, transcript, prompt_text=follow_up)
    return s
