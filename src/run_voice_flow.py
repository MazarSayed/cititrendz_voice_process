"""
Run the current flow end-to-end with:

- Voice out (TTS): speaks system prompts
- Voice in (STT): records mic and transcribes via Deepgram

Degrades gracefully:
- If voice dependencies are missing or DEEPGRAM_API_KEY is not set,
  it prints prompts and uses typed input.

Usage (editable install recommended):
  pip install -e ".[voice]"
  export DEEPGRAM_API_KEY="..."
  PYTHONPATH=src python -m cititrends_voice_process.run_voice_flow --voice
"""

from __future__ import annotations

import argparse
import uuid

from .graph import build_graph
from .state import new_session_state
from .voice import listen, speak, voice_available


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--voice", action="store_true", help="Enable TTS + STT (if available).")
    parser.add_argument(
        "--max-turns",
        type=int,
        default=30,
        help="Safety limit to stop runaway loops during early development.",
    )
    args = parser.parse_args()

    graph = build_graph()
    state = new_session_state(session_id=f"sess_{uuid.uuid4().hex[:8]}")
    action_id = 1

    tts_ok, stt_ok = voice_available()
    use_voice = bool(args.voice and tts_ok and stt_ok)
    use_tts = bool(args.voice and tts_ok)

    if args.voice and not (tts_ok and stt_ok):
        print(
            f"[Info] Voice not fully available (tts={tts_ok}, stt={stt_ok}). "
            "Falling back to typed input where needed."
        )

    for _ in range(args.max_turns):
        state = graph.invoke(state)

        prompt = (state.get("last_prompt") or {}).get("text") or ""
        if prompt:
            speak(prompt, use_tts=use_tts)

        # Stop if we hit an unimplemented node placeholder.
        if prompt.startswith("TODO: implement node"):
            print(f"[Stop] Reached unimplemented node prompt: {prompt}")
            break

        if state.get("current_node") == "CLOSE_PO":
            print("[Done] Close PO.")
            break

        # Collect user input.
        transcript = listen(use_stt=use_voice)
        if not transcript:
            transcript = input("[You]: ").strip()

        state["last_user_input"] = {
            "client_action_id": f"cli_{action_id}",
            "transcript": transcript,
        }
        action_id += 1
    else:
        print("[Stop] Max turns reached.")


if __name__ == "__main__":
    main()

