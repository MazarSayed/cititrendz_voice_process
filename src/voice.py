"""
Voice in (STT) and voice out (TTS) for the inspection flow.

- STT: Deepgram (env DEEPGRAM_API_KEY). Fallback: return None → caller uses typed input.
- TTS: edge-tts. Fallback: print prompt to console.

Install voice extras: pip install -e ".[voice]"
"""

from __future__ import annotations

import os
import subprocess
import tempfile
from typing import Optional, Tuple

from dotenv import load_dotenv
from deepgram import DeepgramClient

try:  # Optional TTS dependency
    import edge_tts  # type: ignore[import]
except ImportError:  # pragma: no cover - handled by voice_available
    edge_tts = None  # type: ignore[assignment]

try:  # Optional audio dependencies for STT
    import numpy as np  # type: ignore[import]
    import sounddevice as sd  # type: ignore[import]
    import soundfile as sf  # type: ignore[import]
except ImportError:  # pragma: no cover - handled by listen/voice_available
    np = None  # type: ignore[assignment]
    sd = None  # type: ignore[assignment]
    sf = None  # type: ignore[assignment]


SAMPLE_RATE = 16_000
CHANNELS = 1
DURATION_SEC = 10  # max record length per turn

# Load .env from the project root when this module is imported so that
# DEEPGRAM_API_KEY is available when constructing the client.
load_dotenv()


def get_deepgram_client() -> DeepgramClient | None:
    """
    Return a DeepgramClient instance or None if anything is misconfigured.

    We deliberately swallow SDK/credential errors here so callers (like the
    FastAPI /api/stt endpoint) can degrade gracefully instead of raising 500s.
    """

    key = os.getenv("DEEPGRAM_API_KEY")
    if not key:
        return None
    try:
        # Newer Deepgram SDK expects the API key as a keyword argument.
        return DeepgramClient(api_key=key)
    except Exception:
        return None

def speak(text: str, use_tts: bool = True) -> None:
    """
    Speak text via TTS (edge-tts). If TTS unavailable or use_tts=False, print to console.
    """
    if not text or not text.strip():
        return
    # Fallback to printing if TTS is disabled or not installed.
    if not use_tts or edge_tts is None:
        print(f"[System]: {text}")
        return
    try:
        import asyncio

        async def _synthesize() -> str:
            assert edge_tts is not None  # for type checkers
            communicate = edge_tts.Communicate(text.strip(), "en-US-GuyNeural")
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                tmp = f.name
            await communicate.save(tmp)
            return tmp

        path = asyncio.run(_synthesize())
        try:
            # Prefer afplay on macOS; otherwise we just print the text.
            subprocess.run(
                ["afplay", path],
                check=True,
                capture_output=True,
                timeout=60,
            )
        except Exception:
            print(f"[System]: {text}")
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass
    except Exception:
        print(f"[System]: {text}")


def listen(use_stt: bool = True) -> Optional[str]:
    """
    Record from microphone and transcribe with Deepgram.
    Returns transcript or None if STT unavailable / no API key / error.
    """
    client = get_deepgram_client()
    if client is None:
        return None
    try:
        # Record to memory (WAV bytes).
        frames = int(SAMPLE_RATE * DURATION_SEC)
        rec = sd.rec(frames, samplerate=SAMPLE_RATE, channels=CHANNELS, dtype=np.int16)
        sd.wait()
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            sf.write(f.name, rec, SAMPLE_RATE)
            path = f.name
        try:
            with open(path, "rb") as audio:
                payload = {"buffer": audio}
                try:
                    from deepgram.options import PrerecordedOptions

                    options = PrerecordedOptions(model="nova-2", smart_format=True)
                except Exception:
                    options = {}

                response = client.listen.rest.v("1").transcribe_file(payload, options)
            # Response shape: response.results.channels[0].alternatives[0].transcript
            if getattr(response, "results", None) and getattr(
                response.results, "channels", None
            ):
                ch = response.results.channels[0]
                if getattr(ch, "alternatives", None) and len(ch.alternatives) > 0:
                    transcript = getattr(ch.alternatives[0], "transcript", None) or ""
                    return transcript.strip() or None
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass
    except Exception:
        pass
    return None


