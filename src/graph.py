from __future__ import annotations

from typing import Any, Callable

from langgraph.graph import END, StateGraph

from .nodes import (
    carton_condition_node,
    color_size_verification_node,
    defect_inspection_node,
    disposition_node,
    packaging_presentation_node,
    photo_capture_node,
    po_carton_verification_node,
    start_identification_node,
    style_sku_verification_node,
    tags_labeling_node,
    unit_count_by_size_node,
    close_po_node,
    complete_style_node,
    notes_optional_node,
)
from .routing import compute_next_node
from .state import InspectionState, NodeName, make_event, utc_now


def todo_interrupt_prompt(node: NodeName) -> dict[str, Any]:
    # Intentionally minimal: nodes will be implemented incrementally later.
    return {
        "prompt": f"TODO: implement node {node}.",
        "node": node,
    }

# Minimal “happy path” ordering (no branching yet).
# As nodes get implemented, routing will move to conditional edges / Command(goto=...).
NEXT_NODE: dict[NodeName, NodeName] = {}


def make_todo_node(node: NodeName) -> Callable[[InspectionState], InspectionState]:
    def fn(state: InspectionState) -> InspectionState:
        # Minimal placeholder behavior:
        # - record node entry
        # - set last_prompt text (client will eventually speak it)
        # - advance current_node to the next step in the happy path
        # - end this graph run (the API layer will "resume" for the next step)
        s: InspectionState = dict(state)
        s["last_prompt"] = {"text": todo_interrupt_prompt(node)["prompt"], "ts": utc_now()}
        s.setdefault("history", []).append(node)
        s.setdefault("events", []).append(make_event(node=node, type_="NODE_ENTERED", payload={"todo": True}))
        s["awaiting_input"] = False
        s["last_completed_node"] = node
        return s

    return fn


def route_from_control(state: InspectionState) -> NodeName | str:
    """
    Minimal router:
    - If state.current_node is set, route there.
    - Otherwise start at START_IDENTIFICATION.

    Later, this is where global commands like Back/Undo/Jump will be parsed from state.last_user_input.
    """

    return state.get("current_node") or "START_IDENTIFICATION"


def build_graph() -> Any:
    """
    Returns a compiled LangGraph.

    This is the smallest useful "first layer":
    - state schema exists
    - graph wiring exists
    - nodes are placeholders (no business logic yet)
    """

    sg: StateGraph[InspectionState] = StateGraph(InspectionState)

    # Router node (will later handle Back/Undo/Jump).
    sg.add_node("CONTROL", lambda s: s)
    sg.add_node(
        "ADVANCE",
        lambda st: {**dict(st), "current_node": compute_next_node(st), "awaiting_input": True},
    )

    # First real nodes.
    sg.add_node("START_IDENTIFICATION", start_identification_node)
    sg.add_node("PO_CARTON_VERIFICATION", po_carton_verification_node)
    sg.add_node("CARTON_CONDITION", carton_condition_node)
    sg.add_node("STYLE_SKU_VERIFICATION", style_sku_verification_node)
    sg.add_node("COLOR_SIZE_VERIFICATION", color_size_verification_node)
    sg.add_node("UNIT_COUNT_BY_SIZE", unit_count_by_size_node)
    sg.add_node("DEFECT_INSPECTION_100pct", defect_inspection_node)
    sg.add_node("TAGS_LABELING", tags_labeling_node)
    sg.add_node("PACKAGING_PRESENTATION", packaging_presentation_node)
    sg.add_node("PHOTO_CAPTURE_LOOP", photo_capture_node)
    sg.add_node("DISPOSITION", disposition_node)
    sg.add_node("NOTES_OPTIONAL", notes_optional_node)
    sg.add_node("COMPLETE_STYLE", complete_style_node)
    sg.add_node("CLOSE_PO", close_po_node)

    sg.set_entry_point("CONTROL")

    # CONTROL routes to the current node (or start).
    sg.add_conditional_edges("CONTROL", route_from_control)

    def route_after_node(st: InspectionState) -> str:
        # If node is waiting for user input, stop this run. Otherwise advance.
        return END if st.get("awaiting_input", True) else "ADVANCE"

    for node in (
        "START_IDENTIFICATION",
        "PO_CARTON_VERIFICATION",
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
    ):
        sg.add_conditional_edges(node, route_after_node)

    sg.add_edge("ADVANCE", END)

    return sg.compile()


def state_to_dict(state: InspectionState) -> dict[str, Any]:
    """
    Convenience for APIs later. Keeps this layer tiny while still being useful.
    """

    return dict(state)

