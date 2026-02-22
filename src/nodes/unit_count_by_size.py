from __future__ import annotations

from typing import Any

from .prompts import UNIT_COUNT_BY_SIZE_PROMPT
from ..node_runner import run_node
from ..state import InspectionState, ensure_current_style


def apply_unit_count(s: InspectionState, ext: Any) -> tuple[bool, dict[str, Any], str | None]:
    if not ext or not ext.size_counts:
        return False, {}, None
    size_counts = [{"size": str(x.size), "qty": x.qty} for x in ext.size_counts if x.size in ("S", "M", "L", "XL", "XS", "XXL")]
    if not size_counts:
        return False, {}, None
    total = sum(x["qty"] for x in size_counts)
    style = ensure_current_style(s)
    style["size_counts"] = size_counts
    style["total_units_counted"] = total
    return True, {"size_counts": size_counts, "total_units_counted": total}, None


def unit_count_by_size_node(state: InspectionState) -> InspectionState:
    return run_node(state, "UNIT_COUNT_BY_SIZE", UNIT_COUNT_BY_SIZE_PROMPT, apply_unit_count)
