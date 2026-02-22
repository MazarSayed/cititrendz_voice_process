"""Pytest configuration and fixtures."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

# Add project root and src to path so tests can import from src
ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


@pytest.fixture(autouse=True)
def mock_llm_extract_for_tests(monkeypatch: pytest.MonkeyPatch) -> None:
    """Use rule-based mock for LLM extraction in tests (no external API calls)."""
    tests_dir = ROOT / "tests"
    if str(tests_dir) not in sys.path:
        sys.path.insert(0, str(tests_dir))
    from mock_llm import mock_llm_extract

    monkeypatch.setattr("src.node_runner.llm_extract", mock_llm_extract)
