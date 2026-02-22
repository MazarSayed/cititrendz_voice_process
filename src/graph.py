from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, StateGraph

from .config import settings
from .node_runner import run_node
from .nodes.registry import NODES, NodeDef
from .routing import compute_next_node
from .state import InspectionState


def _make_node_fn(node_def: NodeDef):
    """Return the callable to register for a node in the StateGraph."""
    if node_def.handler:
        return node_def.handler

    def fn(state: InspectionState) -> InspectionState:
        return run_node(
            state,
            node_def.name,
            node_def.prompt,
            node_def.apply_fn,
            prompt_fn=node_def.prompt_fn,
            scan_handler=node_def.scan_handler,
        )

    return fn


def build_graph(db_path: str | None = None) -> tuple[Any, SqliteSaver]:
    """
    Build and compile the 14-stage inspection StateGraph with a SqliteSaver checkpointer.

    Returns (compiled_graph, checkpointer).
    Pass db_path=":memory:" or a tmp path in tests; defaults to settings.DB_PATH in production.
    """
    resolved_path = db_path or settings.DB_PATH
    if resolved_path != ":memory:":
        p = Path(resolved_path).resolve()
        p.parent.mkdir(parents=True, exist_ok=True)
        resolved_path = str(p)

    conn = sqlite3.connect(resolved_path, check_same_thread=False)
    checkpointer = SqliteSaver(conn)

    sg: StateGraph[InspectionState] = StateGraph(InspectionState)

    # Router node (handles Back/Undo/Jump in the future).
    sg.add_node("CONTROL", lambda s: s)
    sg.add_node(
        "ADVANCE",
        lambda st: {**dict(st), "current_node": compute_next_node(st), "awaiting_input": True},
    )

    for name, nd in NODES.items():
        sg.add_node(name, _make_node_fn(nd))

    sg.set_entry_point("CONTROL")

    # CONTROL routes to the current node (or start).
    sg.add_conditional_edges(
        "CONTROL",
        lambda s: s.get("current_node") or "START_IDENTIFICATION",
    )

    # After each node: if awaiting_input stop run, else advance to next node.
    def _route_after_node(st: InspectionState) -> str:
        return END if st.get("awaiting_input", True) else "ADVANCE"

    for name in NODES:
        sg.add_conditional_edges(name, _route_after_node)

    # ADVANCE routes to the newly computed current_node.
    sg.add_conditional_edges(
        "ADVANCE",
        lambda st: st.get("current_node") or "START_IDENTIFICATION",
        {name: name for name in NODES},
    )

    compiled = sg.compile(checkpointer=checkpointer)
    return compiled, checkpointer


def state_to_dict(state: InspectionState) -> dict[str, Any]:
    return dict(state)
