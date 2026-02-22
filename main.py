from __future__ import annotations

import io
import json
import os
import pathlib
import sys
import urllib.error
import urllib.request
import uuid
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv

# Ensure `src/` is on sys.path so we can import the package without
# requiring an editable install or PYTHONPATH configuration.
ROOT = pathlib.Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# Load environment variables from a local `.env` file (for DEEPGRAM_API_KEY, etc.).
load_dotenv()

from src.graph import build_graph, state_to_dict  # type: ignore  # noqa: E402
from src.po_packages import (  # type: ignore  # noqa: E402
    create_intrasheet_template,
    get_cartons_for_po,
    list_available_pos,
)
from src.state import (  # type: ignore  # noqa: E402
    InspectionState,
    new_session_state,
)


app = FastAPI(
    title="Cititrends Receiving Inspection API",
    description=(
        "Thin FastAPI wrapper around the LangGraph-powered voice-first "
        "receiving inspection flow. Designed for the React demo frontend."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Single shared graph instance for all sessions (fine for this demo).
_graph = build_graph()

# In-memory session store for demo purposes.
_sessions: dict[str, InspectionState] = {}


class StartSessionResponse(BaseModel):
    session_id: str
    state: dict[str, Any]
    current_node: str | None = None
    last_prompt: str | None = None


class StepRequest(BaseModel):
    transcript: str


class StepResponse(BaseModel):
    session_id: str
    state: dict[str, Any]
    current_node: str | None = None
    last_prompt: str | None = None


class SttResponse(BaseModel):
    transcript: str


class TtsRequest(BaseModel):
    text: str


@app.get("/health")
def health() -> dict[str, str]:
    """Simple liveness probe."""

    return {"status": "ok"}


@app.post("/api/session", response_model=StartSessionResponse)
def start_session() -> StartSessionResponse:
    """
    Start a new inspection session.

    - Creates a new LangGraph state using `new_session_state`.
    - Runs one graph tick to produce the first system prompt.
    - Stores the state in an in-memory session store.
    """

    session_id = f"sess_{uuid.uuid4().hex[:8]}"
    state = new_session_state(session_id=session_id)

    # First tick: produce the initial system prompt for the frontend to show.
    state = _graph.invoke(state)
    _sessions[session_id] = state

    raw = state_to_dict(state)
    last_prompt = _extract_last_prompt(raw)
    current_node = raw.get("current_node")

    return StartSessionResponse(
        session_id=session_id,
        state=raw,
        current_node=current_node,
        last_prompt=last_prompt,
    )


@app.get("/api/session/{session_id}/state")
def get_session_state(session_id: str) -> dict[str, Any]:
    """
    Return the current session state for real-time UI updates.
    """
    state = _sessions.get(session_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Unknown session_id")
    return {"state": state_to_dict(state)}


@app.get("/api/po")
def list_pos() -> dict[str, Any]:
    """Return list of available PO packages for identification."""
    return {"po_numbers": list_available_pos()}


@app.get("/api/po/{po_number}/cartons")
def get_po_cartons(po_number: str) -> dict[str, Any]:
    """
    Return the carton/package list for a PO from Excel intrasheet.
    """
    cartons = get_cartons_for_po(po_number)
    return {"po_number": po_number, "cartons": cartons}


@app.post("/api/po/{po_number}/init")
def init_po_packages(po_number: str) -> dict[str, Any]:
    """
    Create PO package folder and intrasheet.xlsx template if they don't exist.
    """
    path = create_intrasheet_template(po_number)
    cartons = get_cartons_for_po(po_number)
    return {
        "po_number": po_number,
        "path": str(path),
        "cartons": cartons,
    }


@app.post("/api/session/{session_id}/step", response_model=StepResponse)
def send_step(session_id: str, payload: StepRequest) -> StepResponse:
    """
    Advance an existing session by providing a transcript.

    The transcript is written into `state['last_user_input']`, and the LangGraph
    is invoked once. The updated state (including the next prompt) is returned.
    """

    state = _sessions.get(session_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Unknown session_id")

    state["last_user_input"] = {
        "client_action_id": f"api_{uuid.uuid4().hex[:6]}",
        "transcript": payload.transcript,
    }

    state = _graph.invoke(state)
    _sessions[session_id] = state

    # Global state: returned to frontend so UI reflects current step, PO number, etc.
    raw = state_to_dict(state)
    last_prompt = _extract_last_prompt(raw)
    current_node = raw.get("current_node")

    return StepResponse(
        session_id=session_id,
        state=raw,
        current_node=current_node,
        last_prompt=last_prompt,
    )


@app.post("/api/stt", response_model=SttResponse)
async def transcribe_audio(audio: UploadFile = File(...)) -> SttResponse:
    """
    Transcribe an audio clip using Deepgram.

    The frontend records short microphone snippets and posts them as a single
    audio file (e.g. audio/webm). This endpoint forwards the bytes to Deepgram's
    prerecorded API and returns the best transcript.
    """

    data = await audio.read()
    print(f"[STT] Received audio bytes: {len(data) if data else 0}")
    if not data:
        raise HTTPException(status_code=400, detail="Empty audio payload.")

    # Call Deepgram's /v1/listen HTTP API directly, following the
    # documentation at https://developers.deepgram.com/reference/speech-to-text/listen-streaming
    dg_key = os.getenv("DEEPGRAM_API_KEY")
    if not dg_key:
        print("[STT] Missing DEEPGRAM_API_KEY.")
        raise HTTPException(
            status_code=503,
            detail="DEEPGRAM_API_KEY not configured on server.",
        )

    url = "https://api.deepgram.com/v1/listen?model=nova-2&smart_format=true"
    headers = {
        "Authorization": f"Token {dg_key}",
        "Content-Type": audio.content_type or "audio/webm",
    }

    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    print("[STT] Sending audio to Deepgram /v1/listen...")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read()
            print(f"[STT] Deepgram HTTP status: {resp.status}")
    except urllib.error.HTTPError as http_err:
        detail = http_err.read().decode("utf-8", errors="ignore")
        print(f"[STT] Deepgram HTTP error {http_err.code}: {detail}")
        raise HTTPException(
            status_code=502,
            detail=f"Deepgram HTTP error {http_err.code}",
        ) from http_err
    except urllib.error.URLError as url_err:
        print(f"[STT] Deepgram URL error: {url_err}")
        raise HTTPException(
            status_code=502,
            detail="Failed to reach Deepgram API.",
        ) from url_err

    try:
        payload = json.loads(body)
    except json.JSONDecodeError as e:
        print(f"[STT] Failed to parse Deepgram JSON: {e} | body={body!r}")
        raise HTTPException(
            status_code=502,
            detail="Deepgram returned invalid JSON.",
        ) from e

    print(f"[STT] Raw Deepgram JSON: {payload}")

    # Expected shape: results.channels[0].alternatives[0].transcript
    text = ""
    try:
        results = payload.get("results") or {}
        channels = results.get("channels") or []
        if channels:
            alts = channels[0].get("alternatives") or []
            if alts:
                text = (alts[0].get("transcript") or "").strip()
    except Exception as parse_exc:
        print(f"[STT] Error parsing Deepgram response: {parse_exc!r}")
        text = ""

    transcript = text
    print(f"[STT] Parsed transcript: {transcript!r}")
    # Return 200 even when empty (silence/unclear audio) so frontend can prompt retry
    return SttResponse(transcript=transcript)


@app.post("/api/tts")
async def synthesize_speech(body: TtsRequest) -> StreamingResponse:
    """
    Convert text into speech using Deepgram's /v1/speak HTTP API.

    The frontend will play the returned audio blob for the associate.
    """

    dg_key = os.getenv("DEEPGRAM_API_KEY")
    if not dg_key:
        print("[TTS] Missing DEEPGRAM_API_KEY.")
        raise HTTPException(
            status_code=503,
            detail="DEEPGRAM_API_KEY not configured on server.",
        )

    text = (body.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text is required for TTS.")

    # Use one of Deepgram's Aura English voices; see docs:
    # https://developers.deepgram.com/reference/text-to-speech/speak-streaming
    url = "https://api.deepgram.com/v1/speak?model=aura-asteria-en&encoding=linear16"
    payload = json.dumps({"text": text}).encode("utf-8")
    headers = {
        "Authorization": f"Token {dg_key}",
        "Content-Type": "application/json",
    }

    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    print(f"[TTS] Sending text to Deepgram /v1/speak: {text!r}")

    try:
        resp = urllib.request.urlopen(req, timeout=30)
    except urllib.error.HTTPError as http_err:
        detail = http_err.read().decode("utf-8", errors="ignore")
        print(f"[TTS] Deepgram HTTP error {http_err.code}: {detail}")
        raise HTTPException(
            status_code=502,
            detail=f"Deepgram TTS HTTP error {http_err.code}",
        ) from http_err
    except urllib.error.URLError as url_err:
        print(f"[TTS] Deepgram URL error: {url_err}")
        raise HTTPException(
            status_code=502,
            detail="Failed to reach Deepgram TTS API.",
        ) from url_err

    audio_bytes = resp.read()
    content_type = resp.headers.get("Content-Type", "audio/wav")
    print(f"[TTS] Deepgram TTS bytes: {len(audio_bytes)} | content-type={content_type}")

    return StreamingResponse(io.BytesIO(audio_bytes), media_type=content_type)


def _extract_last_prompt(state: dict[str, Any]) -> str | None:
    last_prompt = state.get("last_prompt") or {}
    text = last_prompt.get("text")
    if isinstance(text, str) and text.strip():
        return text
    return None


if __name__ == "__main__":
    # Run FastAPI app directly via uvicorn when executing:
    #   uv run main.py
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


