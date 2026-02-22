from __future__ import annotations

from typing import Literal

from .state import InspectionState, NodeName


def compute_next_node(state: InspectionState) -> NodeName:
    """
    Centralized transition logic.

    Nodes should focus on capturing fields + emitting events. This function determines
    the next node based on the latest captured state.
    """

    last = state.get("last_completed_node")
    if not last:
        # Nothing completed; stay where we are.
        return state.get("current_node") or "START_IDENTIFICATION"

    # Branching transitions
    if last == "PO_CARTON_VERIFICATION":
        if state.get("po_verification_result") == "CONFIRMED":
            return "CARTON_VERIFICATION"
        return "PO_CARTON_VERIFICATION"

    if last == "CARTON_VERIFICATION":
        return "CARTON_CONDITION"

    if last == "COMPLETE_STYLE":
        action = state.get("complete_style_action")
        if action == "NEXT_STYLE":
            return "STYLE_SKU_VERIFICATION"
        if action == "CLOSE_PO":
            return "CLOSE_PO"
        return "COMPLETE_STYLE"

    # Default linear transitions (happy path)
    next_map: dict[NodeName, NodeName] = {
        "START_IDENTIFICATION": "PO_CARTON_VERIFICATION",
        "CARTON_VERIFICATION": "CARTON_CONDITION",
        "CARTON_CONDITION": "STYLE_SKU_VERIFICATION",
        "STYLE_SKU_VERIFICATION": "COLOR_SIZE_VERIFICATION",
        "COLOR_SIZE_VERIFICATION": "UNIT_COUNT_BY_SIZE",
        "UNIT_COUNT_BY_SIZE": "DEFECT_INSPECTION_100pct",
        "DEFECT_INSPECTION_100pct": "TAGS_LABELING",
        "TAGS_LABELING": "PACKAGING_PRESENTATION",
        "PACKAGING_PRESENTATION": "PHOTO_CAPTURE_LOOP",
        "PHOTO_CAPTURE_LOOP": "DISPOSITION",
        "DISPOSITION": "NOTES_OPTIONAL",
        "NOTES_OPTIONAL": "COMPLETE_STYLE",
        "CLOSE_PO": "CLOSE_PO",
        # CONTROL/ADVANCE not used here
        "CONTROL": "START_IDENTIFICATION",
    }

    return next_map.get(last, state.get("current_node") or "START_IDENTIFICATION")

