# cititrends_voice_process

Voice-first receiving inspection scaffold using LangGraph.

## Run the current flow (typed)

```bash
PYTHONPATH=src python -m cititrends_voice_process.run_voice_flow
```

This prints system prompts and accepts typed responses. It will stop when it hits an unimplemented (TODO) node.

## Run with voice in/out

Install voice extras:

```bash
pip install -e ".[voice]"
export DEEPGRAM_API_KEY="YOUR_KEY"
PYTHONPATH=src python -m cititrends_voice_process.run_voice_flow --voice
```

Notes:
- If TTS/STT dependencies aren’t installed or `DEEPGRAM_API_KEY` isn’t set, it will fall back to typed input.

## Run tests

```bash
pip install -e ".[dev]"
PYTHONPATH=src pytest -q
```