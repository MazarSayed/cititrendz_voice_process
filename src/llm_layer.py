"""
LLM layer for extraction and validation (see flow_contract.md).

Uses Pydantic Output models per stage: complete=True only when required fields
are extracted; otherwise complete=False and follow_up is the re-prompt.
Nodes then validate in apply_fn and update global state only when requirements pass.
"""

from __future__ import annotations

from typing import Any, Type

from pydantic import BaseModel

from .llm_client import structured_extract
from .models.models import (
    CartonConditionOutput,
    ColorSizeVerificationOutput,
    CompleteStyleOutput,
    DefectInspectionOutput,
    DispositionOutput,
    NotesOptionalOutput,
    PackagingPresentationOutput,
    PhotoCaptureOutput,
    PoCartonVerificationOutput,
    StartIdentificationOutput,
    StyleSkuVerificationOutput,
    TagsLabelingOutput,
    UnitCountBySizeOutput,
)

NODE_SCHEMAS: dict[str, tuple[Type[BaseModel], str, str]] = {
    "START_IDENTIFICATION": (
        StartIdentificationOutput,
        "Extract PO number as pure digits only (e.g. '1, 2, 3, 4, 5, 6' or 'one two three four five six' → '123456') or carton barcode. Used to find package in data/po_packages/.",
        "Extract from user speech. po_number must be digits only, no spaces/commas/prefix. Example: 'PO number 1, 2, 3, 4, 5, 6' → po_number='123456'.",
    ),
    "PO_CARTON_VERIFICATION": (
        PoCartonVerificationOutput,
        "Extract: Confirm/Mismatch. If mismatch, capture reason.",
        "Extract confirmation or mismatch with optional reason.",
    ),
    "CARTON_CONDITION": (
        CartonConditionOutput,
        "Extract: Carton OK, or damage type and severity (minor/major).",
        "Extract carton status. If DAMAGED, need damage_type and damage_severity.",
    ),
    "STYLE_SKU_VERIFICATION": (
        StyleSkuVerificationOutput,
        "Extract: style_id (4-6 digits) and style_entry_method (SCAN or MANUAL).",
        "Extract style number and entry method.",
    ),
    "COLOR_SIZE_VERIFICATION": (
        ColorSizeVerificationOutput,
        "Extract: Match or Mismatch. If mismatch, capture reason.",
        "Extract color/size match result.",
    ),
    "UNIT_COUNT_BY_SIZE": (
        UnitCountBySizeOutput,
        "Extract size_counts: list of {size: S|M|L|XL, qty: number}.",
        "Extract size and quantity pairs from speech.",
    ),
    "DEFECT_INSPECTION_100pct": (
        DefectInspectionOutput,
        "Extract: all_units_ok true, or defects with type, affected_units, severity.",
        "Extract defect info or all units OK.",
    ),
    "TAGS_LABELING": (
        TagsLabelingOutput,
        "Extract: tags_ok true, or tags_issues with issue_type and affected_unit_count.",
        "Extract tags status or issues.",
    ),
    "PACKAGING_PRESENTATION": (
        PackagingPresentationOutput,
        "Extract: packaging_ok true, or packaging_issues.",
        "Extract packaging status.",
    ),
    "PHOTO_CAPTURE_LOOP": (
        PhotoCaptureOutput,
        "Extract: photo_captured true when user confirms photos taken.",
        "Extract photo capture confirmation.",
    ),
    "DISPOSITION": (
        DispositionOutput,
        "Extract: ACCEPT, ACCEPT_WITH_EXCEPTIONS, HOLD, or REJECT.",
        "Extract disposition.",
    ),
    "NOTES_OPTIONAL": (
        NotesOptionalOutput,
        "Extract notes text, or empty if user says no notes/skip.",
        "Extract notes or skip.",
    ),
    "COMPLETE_STYLE": (
        CompleteStyleOutput,
        "Extract: NEXT_STYLE or CLOSE_PO.",
        "Extract next style or close PO.",
    ),
}


def llm_extract(
    node_name: str,
    transcript: str,
    state: dict[str, Any],
    system_prompt: str,
) -> BaseModel:  # Returns *Output model with .complete, .extracted, .follow_up
    """
    Extract using LLM. Returns the Pydantic Output model (complete, extracted, follow_up).
    Uses full conversation history from state["messages"] for context.
    """
    schema_cls, instruction, _ = NODE_SCHEMAS[node_name]
    conversation: list[dict[str, str]] = state.get("messages") or []

    messages: list[dict[str, str]] = [
        {
            "role": "system",
            "content": (
                f"You are a warehouse inspection assistant extracting structured data. "
                f"Current stage: {node_name}. Task: {instruction}\n"
                f"Rules: Extract only what the user explicitly stated. "
                f"Set complete=true only when all required fields are present. "
                f"Set complete=false and provide a short follow_up when info is missing."
            ),
        }
    ]
    # Include recent conversation for context (last 10 turns)
    messages.extend(conversation[-10:])

    # State context + final extraction request
    state_ctx = _state_summary_for_llm(state)
    extract_req = f"Extract the required fields for {node_name}."
    if state_ctx:
        extract_req += f" Inspection context: {state_ctx}."
    extract_req += " Return valid JSON."
    messages.append({"role": "user", "content": extract_req})

    return structured_extract(messages, schema_cls)


def _state_summary_for_llm(state: dict[str, Any]) -> str:
    parts = []
    if state.get("po_number"):
        parts.append(f"po_number={state['po_number']}")
    if state.get("carton_barcode"):
        parts.append("carton_barcode=captured")
    if state.get("vendor"):
        parts.append(f"vendor={state['vendor']}")
    if state.get("current_style"):
        style = state["current_style"]
        if style.get("style_id"):
            parts.append(f"style_id={style['style_id']}")
    return "; ".join(parts) if parts else ""
