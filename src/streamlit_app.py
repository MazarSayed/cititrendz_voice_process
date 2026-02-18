"""
Minimal Streamlit app for testing the LangGraph inspection flow (text-only).

Usage (from repo root):
  pip install -e ".[app]"
  streamlit run src/cititrends_voice_process/streamlit_app.py
"""

from __future__ import annotations

import sys
import uuid
from pathlib import Path

import streamlit as st

# Ensure the src/ directory is on sys.path when running via a file path.
ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from cititrends_voice_process.graph import build_graph
from cititrends_voice_process.state import InspectionState, new_session_state


SESSION_KEY_STATE = "inspection_state"
SESSION_KEY_GRAPH = "inspection_graph"
SESSION_KEY_ACTION_ID = "inspection_action_id"


def get_graph_and_state() -> tuple[any, InspectionState]:
    if SESSION_KEY_GRAPH not in st.session_state:
        st.session_state[SESSION_KEY_GRAPH] = build_graph()
    if SESSION_KEY_STATE not in st.session_state:
        st.session_state[SESSION_KEY_STATE] = new_session_state(
            session_id=f"sess_{uuid.uuid4().hex[:8]}"
        )
    if SESSION_KEY_ACTION_ID not in st.session_state:
        st.session_state[SESSION_KEY_ACTION_ID] = 1
    return st.session_state[SESSION_KEY_GRAPH], st.session_state[SESSION_KEY_STATE]


def save_state(state: InspectionState) -> None:
    st.session_state[SESSION_KEY_STATE] = state


def main() -> None:
    st.title("Inspection Flow (LangGraph) – Simple Tester")

    graph, state = get_graph_and_state()
    action_id: int = st.session_state[SESSION_KEY_ACTION_ID]

    with st.sidebar:
        st.markdown("### Session")
        if st.button("Reset session"):
            st.session_state.clear()
            st.experimental_rerun()

    st.markdown("### Current state")
    st.write(f"Current node: `{state.get('current_node', 'START_IDENTIFICATION')}`")
    last_prompt = (state.get("last_prompt") or {}).get("text")
    if last_prompt:
        st.markdown("**Last prompt:**")
        st.info(last_prompt)
    else:
        st.markdown("_No prompt yet. Click **Advance (no input)** to start._")

    st.markdown("### Advance flow")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Advance (no input)"):
            # Invoke the graph with no new input (useful to get initial prompt).
            new_state = graph.invoke(state)
            save_state(new_state)
            st.experimental_rerun()

    with col2:
        typed_input = st.text_input("Typed input for this step", key="typed_input")
        if st.button("Send typed"):
            ui = {
                "client_action_id": f"cli_{action_id}",
                "transcript": typed_input,
            }
            state["last_user_input"] = ui  # type: ignore[index]
            new_state = graph.invoke(state)
            st.session_state[SESSION_KEY_ACTION_ID] = action_id + 1
            save_state(new_state)
            st.experimental_rerun()

    st.markdown("### Debug view (state snapshot)")
    with st.expander("Show state dict"):
        st.json(state)


if __name__ == "__main__":
    main()
