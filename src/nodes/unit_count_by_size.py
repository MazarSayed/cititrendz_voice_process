from __future__ import annotations

import re

from .prompts import UNIT_COUNT_BY_SIZE_PROMPT
from ..state import InspectionState, ensure_current_style, make_event, utc_now


_SIZE_MAP: dict[str, str] = {
    "xs": "XS",
    "extra small": "XS",
    "x-small": "XS",
    "s": "S",
    "small": "S",
    "m": "M",
    "medium": "M",
    "l": "L",
    "large": "L",
    "xl": "XL",
    "x l": "XL",
    "x-large": "XL",
    "extra large": "XL",
    "xxl": "XXL",
    "2xl": "XXL",
    "xxxl": "XXXL",
    "3xl": "XXXL",
}


def _canonical_size(token: str) -> str | None:
    t = token.strip().lower()
    t = re.sub(r"[^a-z0-9\s-]", "", t)
    t = re.sub(r"\s+", " ", t)
    if t in _SIZE_MAP:
        return _SIZE_MAP[t]
    # handle bare "xlarge" etc
    t2 = t.replace("-", "").replace(" ", "")
    if t2 in ("xsmall", "extrasmall"):
        return "XS"
    if t2 in ("xlarge", "extralarge"):
        return "XL"
    return None


def _parse_size_counts(transcript: str) -> list[dict[str, int | str]]:
    """
    Minimal parser for phrases like:
      'Small 8. Medium 12. Large 16. Extra-large 12.'

    Notes:
    - v1 expects numeric quantities (Deepgram smart_format usually yields digits)
    - ignores unrecognized sizes
    """

    text = transcript.lower()
    # Normalize separators
    text = text.replace("-", " ")
    text = text.replace(",", " ").replace(".", " ").replace(";", " ").replace("\n", " ")
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []

    results: list[dict[str, int | str]] = []

    # Greedy scan for <size-ish words> <number>
    # We'll look for known size keywords optionally with 'extra' etc, followed by an integer.
    pattern = re.compile(
        r"(?P<size>(extra\s+small|extra\s+large|x\s*small|x\s*large|xxxl|xxl|xl|xs|small|medium|large|\b[smld]\b))\s+(?P<qty>\d+)"
    )
    for m in pattern.finditer(text):
        size_raw = m.group("size")
        qty_raw = m.group("qty")
        size = _canonical_size(size_raw)
        if size is None:
            continue
        try:
            qty = int(qty_raw)
        except ValueError:
            continue
        results.append({"size": size, "qty": qty})

    # Coalesce duplicates (e.g., repeated size mentioned twice)
    if not results:
        return []
    summed: dict[str, int] = {}
    for item in results:
        sz = str(item["size"])
        q = int(item["qty"])
        summed[sz] = summed.get(sz, 0) + q

    return [{"size": sz, "qty": qty} for sz, qty in summed.items()]


def unit_count_by_size_node(state: InspectionState) -> InspectionState:
    """
    Step 5 from required_flow.md:
    - Prompt: 'Count units by size...'
    - Capture structured size_counts[].
    - Advance to DEFECT_INSPECTION_100pct.
    """

    s: InspectionState = dict(state)
    s.setdefault("history", [])
    s.setdefault("events", [])

    user_input = s.get("last_user_input") or {}
    transcript = (user_input.get("transcript") or "").strip()

    if not transcript:
        s["current_node"] = "UNIT_COUNT_BY_SIZE"
        s["awaiting_input"] = True
        s["last_prompt"] = {"text": UNIT_COUNT_BY_SIZE_PROMPT, "ts": utc_now()}
        s["events"].append(make_event(node="UNIT_COUNT_BY_SIZE", type_="PROMPTED", payload={}))
        return s

    size_counts = _parse_size_counts(transcript)
    if not size_counts:
        s["current_node"] = "UNIT_COUNT_BY_SIZE"
        s["awaiting_input"] = True
        s["last_prompt"] = {
            "text": "State each size and quantity. Example: Small 8. Medium 12. Large 16.",
            "ts": utc_now(),
        }
        s["events"].append(
            make_event(
                node="UNIT_COUNT_BY_SIZE",
                type_="VALIDATION_FAILED",
                payload={"transcript": transcript},
            )
        )
        s["last_user_input"] = {}
        return s

    total = sum(int(x["qty"]) for x in size_counts)
    style = ensure_current_style(s)
    style["size_counts"] = size_counts  # type: ignore[assignment]
    style["total_units_counted"] = total
    s["events"].append(
        make_event(
            node="UNIT_COUNT_BY_SIZE",
            type_="FIELDS_CAPTURED",
            payload={"size_counts": size_counts, "total_units_counted": total},
        )
    )
    s["history"].append("UNIT_COUNT_BY_SIZE")
    s["awaiting_input"] = False
    s["last_completed_node"] = "UNIT_COUNT_BY_SIZE"
    s["last_user_input"] = {}
    return s

