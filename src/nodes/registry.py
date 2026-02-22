"""
Node registry: maps node names to NodeDef instances.

The graph factory iterates NODES to wire up the StateGraph instead of
importing each *_node function individually.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Any

from ..state import InspectionState


@dataclass
class NodeDef:
    name: str
    prompt: str
    schema_key: str
    apply_fn: Callable | None = None
    prompt_fn: Callable | None = None
    handler: Callable | None = None
    scan_handler: Callable | None = None


# Import apply_fns and handlers from each node file.
# Using qualified names to avoid conflicts between files that share function names.

from .start_identification import apply_start_id
from .start_identification import scan_handler as _start_scan_handler
from .po_carton_verification import apply_po_carton
from .po_carton_verification import prompt_fn as _po_carton_prompt_fn
from .carton_verification import carton_verification_node
from .carton_condition import apply_carton
from .style_sku_verification import apply_style_sku
from .style_sku_verification import scan_handler as _style_scan_handler
from .color_size_verification import apply_color_size
from .unit_count_by_size import apply_unit_count
from .defect_inspection import apply_defect
from .tags_labeling import apply_tags
from .packaging_presentation import apply_packaging
from .photo_capture import photo_capture_node
from .disposition import apply_disposition
from .notes_optional import apply_notes
from .complete_style import apply_complete_style
from .close_po import close_po_node
from .prompts import (
    START_IDENTIFICATION_PROMPT,
    CARTON_CONDITION_PROMPT,
    STYLE_SKU_VERIFICATION_PROMPT,
    COLOR_SIZE_VERIFICATION_PROMPT,
    UNIT_COUNT_BY_SIZE_PROMPT,
    DEFECT_INSPECTION_PROMPT,
    TAGS_LABELING_PROMPT,
    PACKAGING_PRESENTATION_PROMPT,
    PHOTO_CAPTURE_PROMPT,
    DISPOSITION_PROMPT,
    NOTES_PROMPT,
    COMPLETE_STYLE_PROMPT,
    CLOSE_PO_PROMPT,
)

NODES: dict[str, NodeDef] = {
    "START_IDENTIFICATION": NodeDef(
        name="START_IDENTIFICATION",
        prompt=START_IDENTIFICATION_PROMPT,
        schema_key="START_IDENTIFICATION",
        apply_fn=apply_start_id,
        scan_handler=_start_scan_handler,
    ),
    "PO_CARTON_VERIFICATION": NodeDef(
        name="PO_CARTON_VERIFICATION",
        prompt="Say Confirm or Mismatch.",
        schema_key="PO_CARTON_VERIFICATION",
        apply_fn=apply_po_carton,
        prompt_fn=_po_carton_prompt_fn,
    ),
    # CARTON_VERIFICATION has custom logic (iterates cartons one by one)
    "CARTON_VERIFICATION": NodeDef(
        name="CARTON_VERIFICATION",
        prompt="Say Match or Mismatch.",
        schema_key="CARTON_VERIFICATION",
        handler=carton_verification_node,
    ),
    "CARTON_CONDITION": NodeDef(
        name="CARTON_CONDITION",
        prompt=CARTON_CONDITION_PROMPT,
        schema_key="CARTON_CONDITION",
        apply_fn=apply_carton,
    ),
    "STYLE_SKU_VERIFICATION": NodeDef(
        name="STYLE_SKU_VERIFICATION",
        prompt=STYLE_SKU_VERIFICATION_PROMPT,
        schema_key="STYLE_SKU_VERIFICATION",
        apply_fn=apply_style_sku,
        scan_handler=_style_scan_handler,
    ),
    "COLOR_SIZE_VERIFICATION": NodeDef(
        name="COLOR_SIZE_VERIFICATION",
        prompt=COLOR_SIZE_VERIFICATION_PROMPT,
        schema_key="COLOR_SIZE_VERIFICATION",
        apply_fn=apply_color_size,
    ),
    "UNIT_COUNT_BY_SIZE": NodeDef(
        name="UNIT_COUNT_BY_SIZE",
        prompt=UNIT_COUNT_BY_SIZE_PROMPT,
        schema_key="UNIT_COUNT_BY_SIZE",
        apply_fn=apply_unit_count,
    ),
    "DEFECT_INSPECTION_100pct": NodeDef(
        name="DEFECT_INSPECTION_100pct",
        prompt=DEFECT_INSPECTION_PROMPT,
        schema_key="DEFECT_INSPECTION_100pct",
        apply_fn=apply_defect,
    ),
    "TAGS_LABELING": NodeDef(
        name="TAGS_LABELING",
        prompt=TAGS_LABELING_PROMPT,
        schema_key="TAGS_LABELING",
        apply_fn=apply_tags,
    ),
    "PACKAGING_PRESENTATION": NodeDef(
        name="PACKAGING_PRESENTATION",
        prompt=PACKAGING_PRESENTATION_PROMPT,
        schema_key="PACKAGING_PRESENTATION",
        apply_fn=apply_packaging,
    ),
    # PHOTO_CAPTURE_LOOP has custom logic (skip when no exceptions)
    "PHOTO_CAPTURE_LOOP": NodeDef(
        name="PHOTO_CAPTURE_LOOP",
        prompt=PHOTO_CAPTURE_PROMPT,
        schema_key="PHOTO_CAPTURE_LOOP",
        handler=photo_capture_node,
    ),
    "DISPOSITION": NodeDef(
        name="DISPOSITION",
        prompt=DISPOSITION_PROMPT,
        schema_key="DISPOSITION",
        apply_fn=apply_disposition,
    ),
    "NOTES_OPTIONAL": NodeDef(
        name="NOTES_OPTIONAL",
        prompt=NOTES_PROMPT,
        schema_key="NOTES_OPTIONAL",
        apply_fn=apply_notes,
    ),
    "COMPLETE_STYLE": NodeDef(
        name="COMPLETE_STYLE",
        prompt=COMPLETE_STYLE_PROMPT,
        schema_key="COMPLETE_STYLE",
        apply_fn=apply_complete_style,
    ),
    # CLOSE_PO has custom logic (terminal node)
    "CLOSE_PO": NodeDef(
        name="CLOSE_PO",
        prompt=CLOSE_PO_PROMPT,
        schema_key="CLOSE_PO",
        handler=close_po_node,
    ),
}
