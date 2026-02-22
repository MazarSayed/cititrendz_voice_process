from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal, TypedDict


CartonStatus = Literal["OK", "DAMAGED", "UNKNOWN"]
DamageSeverity = Literal["MINOR", "MAJOR"]

Disposition = Literal["ACCEPT", "ACCEPT_WITH_EXCEPTIONS", "HOLD", "REJECT"]

NodeName = Literal[
    "CONTROL",
    "START_IDENTIFICATION",
    "PO_CARTON_VERIFICATION",
    "CARTON_VERIFICATION",
    "CARTON_CONDITION",
    "STYLE_SKU_VERIFICATION",
    "COLOR_SIZE_VERIFICATION",
    "UNIT_COUNT_BY_SIZE",
    "DEFECT_INSPECTION_100pct",
    "TAGS_LABELING",
    "PACKAGING_PRESENTATION",
    "PHOTO_CAPTURE_LOOP",
    "DISPOSITION",
    "NOTES_OPTIONAL",
    "COMPLETE_STYLE",
    "CLOSE_PO",
]


class Message(TypedDict):
    role: str      # "user" | "assistant"
    content: str


class Event(TypedDict, total=False):
    ts: str
    node: str
    type: str
    payload: dict[str, Any]


class LastPrompt(TypedDict, total=False):
    text: str
    ts: str


class UserInput(TypedDict, total=False):
    """
    What the server receives on each resume call.
    Keep this flexible early; tighten as you implement each node.
    """

    client_action_id: str
    transcript: str
    scan: str
    confirm: bool
    photos: list[dict[str, Any]]
    ui_input: dict[str, Any]


class SizeCount(TypedDict):
    size: str
    qty: int


class DefectEntry(TypedDict, total=False):
    type: str
    affected_units: int
    severity: DamageSeverity


class TagIssue(TypedDict, total=False):
    issue_type: str
    affected_unit_count: int
    raw: str


class PackagingIssue(TypedDict, total=False):
    issue_type: str
    raw: str
    affected_unit_count: int


class StyleInspection(TypedDict, total=False):
    style_id: str
    style_entry_method: Literal["SCAN", "MANUAL"]

    color_size_match: bool
    mismatch_reason: str

    size_counts: list[SizeCount]
    total_units_counted: int

    all_units_ok: bool
    defects: list[DefectEntry]

    tags_ok: bool
    tags_issues: list[TagIssue]

    packaging_ok: bool
    packaging_issues: list[PackagingIssue]

    photos: list[dict[str, str]]

    disposition: Disposition
    notes: str


class InspectionState(TypedDict, total=False):
    """
    LangGraph state object (stored via checkpointer).

    LangGraph commonly operates on dict-like state; using TypedDict keeps the scaffold lightweight
    while still documenting the contract.
    """

    session_id: str
    current_node: NodeName
    awaiting_input: bool
    last_completed_node: NodeName

    # Used for "Back"/"Undo"/auditability.
    history: list[NodeName]
    events: list[Event]

    # Set on resume; consumed by nodes; typically overwritten each turn.
    last_user_input: UserInput

    # Common top-level inspection identifiers (PO/carton/associate).
    po_number: str
    carton_barcode: str
    associate_id: str
    vendor: str
    expected_style_count: int
    expected_units_total: int

    po_verification_result: Literal["CONFIRMED", "MISMATCH"]
    po_mismatch_reason: str

    carton_status: CartonStatus
    damage_type: str
    damage_severity: DamageSeverity

    # Per-style inspection data.
    current_style: StyleInspection
    completed_styles_data: list[StyleInspection]
    completed_styles: int

    disposition: Disposition  # convenience mirror of current_style.disposition for now
    complete_style_action: Literal["NEXT_STYLE", "CLOSE_PO"]

    # Snapshots of the most recent prompt (useful for reconnect UX).
    last_prompt: LastPrompt

    # Full conversation record (assistant prompts + user transcripts).
    messages: list[Message]

    # Generic bucket for counters/errors (supports re-prompt loops).
    attempts: dict[str, Any]

    # Per-carton match/mismatch status (carton_id or barcode -> "Match" | "Mismatch").
    carton_match_results: dict[str, str]

    # Carton verification: index of current carton being verified.
    current_carton_index: int


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def make_event(node: str, type_: str, payload: dict[str, Any] | None = None) -> Event:
    return {
        "ts": utc_now(),
        "node": node,
        "type": type_,
        "payload": payload or {},
    }


def ensure_current_style(state: InspectionState) -> StyleInspection:
    """
    Return the current_style dict, ensuring it exists.
    """

    style = state.get("current_style") or {}
    state["current_style"] = style
    return style  # type: ignore[return-value]


def new_session_state(session_id: str) -> InspectionState:
    """
    Minimal initializer for a new inspection session.
    """

    return {
        "session_id": session_id,
        "current_node": "START_IDENTIFICATION",
        "awaiting_input": True,
        "history": [],
        "events": [],
        "attempts": {},
        "messages": [],
        "current_style": {},
        "completed_styles_data": [],
        "completed_styles": 0,
    }

