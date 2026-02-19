from __future__ import annotations

import re
from typing import Tuple

from .state import DamageSeverity

_WORD_NUMBERS: dict[str, int] = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
    "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18,
    "nineteen": 19, "twenty": 20,
}


def parse_confirm_mismatch(transcript: str) -> Tuple[bool | None, str | None]:
    """
    Generic Match / Mismatch parser.
    Returns (is_match, mismatch_reason).
    """

    t = transcript.strip().lower()
    if not t:
        return (None, None)

    if "mismatch" in t or "mis match" in t:
        reason = transcript
        for kw in ("mismatch", "mis match"):
            idx = t.find(kw)
            if idx != -1:
                reason = transcript[idx + len(kw) :].strip(" .,-")
                break
        return (False, reason or None)

    if "match" in t:
        return (True, None)

    return (None, None)


def parse_carton_condition(transcript: str) -> tuple[str | None, str | None, DamageSeverity | None]:
    """
    Returns (carton_status, damage_type, damage_severity)
    """

    t = transcript.strip().lower()
    if not t:
        return (None, None, None)

    if "carton ok" in t or t == "ok":
        return ("OK", None, None)

    # Detect severity.
    sev: DamageSeverity | None = None
    if "minor" in t:
        sev = "MINOR"
    elif "major" in t:
        sev = "MAJOR"

    # Detect damage type keywords.
    dmg_type: str | None = None
    if "puncture" in t:
        dmg_type = "puncture"
    elif "crush" in t or "crushing" in t:
        dmg_type = "crushing"
    elif "water" in t:
        dmg_type = "water_damage"
    elif "retape" in t or "re-tape" in t or "re tape" in t:
        dmg_type = "retape"
    elif "damage" in t:
        dmg_type = "other"

    if dmg_type or sev:
        return ("DAMAGED", dmg_type, sev)

    return (None, None, None)


def extract_count(transcript: str) -> int | None:
    """
    Extract the first integer from a transcript, used for unit counts.
    Handles both digit numbers ("3") and word numbers ("three").
    """

    t = transcript.lower()
    m = re.search(r"\b(\d+)\b", t)
    if m:
        return int(m.group(1))
    return next((v for k, v in _WORD_NUMBERS.items() if re.search(rf"\b{k}\b", t)), None)

