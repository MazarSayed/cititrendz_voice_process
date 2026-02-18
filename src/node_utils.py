from __future__ import annotations

from typing import Any, Tuple

from .state import InspectionState, UserInput, make_event, utc_now


def init_node_state(state: InspectionState) -> InspectionState:
    """
    Common boilerplate for node functions:
    - clone state
    - ensure history/events lists
    """

    s: InspectionState = dict(state)
    s.setdefault("history", [])
    s.setdefault("events", [])
    return s


def get_user_input(state: InspectionState) -> Tuple[str, str, UserInput]:
    """
    Return (transcript, scan, raw_user_input) with safe defaults.
    """

    ui: UserInput = state.get("last_user_input") or {}  # type: ignore[assignment]
    transcript = (ui.get("transcript") or "").strip()
    scan = (ui.get("scan") or "").strip()
    return transcript, scan, ui


def prompt(node: str, state: InspectionState, text: str) -> InspectionState:
    """
    Set prompt for a node and mark it as awaiting input.
    """

    state["current_node"] = node  # type: ignore[index]
    state["awaiting_input"] = True  # type: ignore[index]
    state["last_prompt"] = {"text": text, "ts": utc_now()}  # type: ignore[index]
    state.setdefault("events", []).append(
        make_event(node=node, type_="PROMPTED", payload={})
    )
    return state


def validation_failed(
    node: str,
    state: InspectionState,
    transcript: str,
    extra_payload: dict[str, Any] | None = None,
    prompt_text: str | None = None,
) -> InspectionState:
    """
    Record a validation failure and optionally re-prompt.
    """

    payload: dict[str, Any] = {"transcript": transcript}
    if extra_payload:
        payload.update(extra_payload)

    state["current_node"] = node  # type: ignore[index]
    state["awaiting_input"] = True  # type: ignore[index]
    if prompt_text:
        state["last_prompt"] = {"text": prompt_text, "ts": utc_now()}  # type: ignore[index]
    state.setdefault("events", []).append(
        make_event(node=node, type_="VALIDATION_FAILED", payload=payload)
    )
    state["last_user_input"] = {}  # type: ignore[index]
    return state


def fields_captured(
    node: str,
    state: InspectionState,
    payload: dict[str, Any],
) -> InspectionState:
    """
    Record fields captured and mark the node as completed for this run.
    """

    state.setdefault("events", []).append(
        make_event(node=node, type_="FIELDS_CAPTURED", payload=payload)
    )
    state.setdefault("history", []).append(node)
    state["awaiting_input"] = False  # type: ignore[index]
    state["last_completed_node"] = node  # type: ignore[index]
    state["last_user_input"] = {}  # type: ignore[index]
    return state

