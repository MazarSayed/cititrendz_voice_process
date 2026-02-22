"""
Rule-based mock for LLM extraction. Used when OPENAI_API_KEY is not set.
Maps common transcripts to expected extraction outputs.
"""
from __future__ import annotations

import re
from typing import Any

from src.parsers import normalize_po_number
from src.models.models import (
    CartonConditionExtracted,
    CartonConditionOutput,
    ColorSizeVerificationExtracted,
    ColorSizeVerificationOutput,
    CompleteStyleExtracted,
    CompleteStyleOutput,
    DefectInspectionExtracted,
    DefectInspectionOutput,
    DispositionExtracted,
    DispositionOutput,
    NotesOptionalExtracted,
    NotesOptionalOutput,
    PackagingPresentationExtracted,
    PackagingPresentationOutput,
    PhotoCaptureExtracted,
    PhotoCaptureOutput,
    PoCartonVerificationExtracted,
    PoCartonVerificationOutput,
    StartIdentificationExtracted,
    StartIdentificationOutput,
    StyleSkuVerificationExtracted,
    StyleSkuVerificationOutput,
    TagsLabelingExtracted,
    TagsLabelingOutput,
    UnitCountBySizeExtracted,
    UnitCountBySizeOutput,
)


def _digits(s: str) -> str:
    """Extract digits only from string (for style_id etc.)."""
    return "".join(c for c in (s or "") if c.isdigit())


def mock_llm_extract(node_name: str, transcript: str, state: dict[str, Any], _: str) -> Any:
    t = (transcript or "").strip().lower()

    if node_name == "START_IDENTIFICATION":
        po = normalize_po_number(transcript)
        m = re.search(r"\b(\d{4,})\b", transcript)
        if m:
            po = po or m.group(1)
        if po and len(po) >= 3:
            return StartIdentificationOutput(complete=True, extracted=StartIdentificationExtracted(po_number=po, carton_barcode=None))
        return StartIdentificationOutput(complete=False, follow_up="Please say the PO number.")

    if node_name == "PO_CARTON_VERIFICATION":
        if "confirm" in t:
            return PoCartonVerificationOutput(complete=True, extracted=PoCartonVerificationExtracted(po_verification_result="CONFIRMED", po_mismatch_reason=None))
        if "mismatch" in t:
            reason = transcript[t.find("mismatch") + 8 :].strip(" .,-") or "Mismatch"
            return PoCartonVerificationOutput(complete=True, extracted=PoCartonVerificationExtracted(po_verification_result="MISMATCH", po_mismatch_reason=reason))
        return PoCartonVerificationOutput(complete=False, follow_up="Say Confirm or Mismatch.")

    if node_name == "CARTON_CONDITION":
        if "carton ok" in t or t == "ok":
            return CartonConditionOutput(complete=True, extracted=CartonConditionExtracted(carton_status="OK", damage_type=None, damage_severity=None))
        if "damage" in t or "puncture" in t or "crush" in t:
            sev = "MAJOR" if "major" in t else "MINOR"
            dmg = "puncture" if "puncture" in t else ("crushing" if "crush" in t else "other")
            return CartonConditionOutput(complete=True, extracted=CartonConditionExtracted(carton_status="DAMAGED", damage_type=dmg, damage_severity=sev))
        return CartonConditionOutput(complete=False, follow_up="Say Carton OK or describe damage.")

    if node_name == "STYLE_SKU_VERIFICATION":
        style = _digits(transcript)
        if not style:
            m = re.search(r"style\s+(\S+)", t)
            style = _digits(m.group(1)) if m else ""
        if style and len(style) >= 4:
            method = "MANUAL" if "manual" in t else "SCAN"
            return StyleSkuVerificationOutput(complete=True, extracted=StyleSkuVerificationExtracted(style_id=style, style_entry_method=method))
        return StyleSkuVerificationOutput(complete=False, follow_up="Say the style number.")

    if node_name == "COLOR_SIZE_VERIFICATION":
        if "match" in t and "mismatch" not in t:
            return ColorSizeVerificationOutput(complete=True, extracted=ColorSizeVerificationExtracted(color_size_match=True, mismatch_reason=None))
        if "mismatch" in t:
            reason = transcript[t.find("mismatch") :].strip(" .,-") or "Mismatch"
            return ColorSizeVerificationOutput(complete=True, extracted=ColorSizeVerificationExtracted(color_size_match=False, mismatch_reason=reason))
        return ColorSizeVerificationOutput(complete=False, follow_up="Say Match or Mismatch.")

    if node_name == "UNIT_COUNT_BY_SIZE":
        from src.models.models import SizeCount

        counts = []
        for m in re.finditer(r"(?:extra-?large|extra large|xl)\s*(\d+)", t):
            counts.append(SizeCount(size="XL", qty=int(m.group(1))))
        for m in re.finditer(r"(?:small|s)\s*(\d+)", t):
            counts.append(SizeCount(size="S", qty=int(m.group(1))))
        for m in re.finditer(r"(?:medium|m)\s*(\d+)", t):
            counts.append(SizeCount(size="M", qty=int(m.group(1))))
        # Match "large" only when not part of "extra-large" (remove XL matches first)
        t_no_xl = re.sub(r"(?:extra-?large|extra large|xl)\s*\d+", " ", t)
        for m in re.finditer(r"(?:large|l)\s*(\d+)", t_no_xl):
            counts.append(SizeCount(size="L", qty=int(m.group(1))))
        if not counts:
            for m in re.finditer(r"(\d+)", transcript):
                counts.append(SizeCount(size="M", qty=int(m.group(1))))
        if counts:
            return UnitCountBySizeOutput(complete=True, extracted=UnitCountBySizeExtracted(size_counts=counts[:10]))
        return UnitCountBySizeOutput(complete=False, follow_up="State size and quantity.")

    if node_name == "DEFECT_INSPECTION_100pct":
        from src.models.models import DefectEntry

        if "all units ok" in t or "all ok" in t:
            return DefectInspectionOutput(complete=True, extracted=DefectInspectionExtracted(all_units_ok=True, defects=[]))
        return DefectInspectionOutput(complete=True, extracted=DefectInspectionExtracted(all_units_ok=False, defects=[DefectEntry(type="other", affected_units=1, severity="MINOR")]))

    if node_name == "TAGS_LABELING":
        from src.models.models import TagIssueEntry

        if "tags ok" in t or "ok" in t:
            return TagsLabelingOutput(complete=True, extracted=TagsLabelingExtracted(tags_ok=True, tags_issues=[]))
        return TagsLabelingOutput(complete=True, extracted=TagsLabelingExtracted(tags_ok=False, tags_issues=[TagIssueEntry(issue_type="other", affected_unit_count=1)]))

    if node_name == "PACKAGING_PRESENTATION":
        from src.models.models import PackagingIssueEntry

        if "packaging ok" in t or "ok" in t:
            return PackagingPresentationOutput(complete=True, extracted=PackagingPresentationExtracted(packaging_ok=True, packaging_issues=[]))
        return PackagingPresentationOutput(complete=True, extracted=PackagingPresentationExtracted(packaging_ok=False, packaging_issues=[PackagingIssueEntry(issue_type="other", raw="")]))

    if node_name == "PHOTO_CAPTURE_LOOP":
        if "photo" in t and ("capture" in t or "taken" in t or "done" in t):
            return PhotoCaptureOutput(complete=True, extracted=PhotoCaptureExtracted(photo_captured=True))
        return PhotoCaptureOutput(complete=True, extracted=PhotoCaptureExtracted(photo_captured=True))

    if node_name == "DISPOSITION":
        if "accept" in t and "exception" not in t:
            return DispositionOutput(complete=True, extracted=DispositionExtracted(disposition="ACCEPT"))
        if "accept" in t and "exception" in t:
            return DispositionOutput(complete=True, extracted=DispositionExtracted(disposition="ACCEPT_WITH_EXCEPTIONS"))
        if "hold" in t:
            return DispositionOutput(complete=True, extracted=DispositionExtracted(disposition="HOLD"))
        if "reject" in t:
            return DispositionOutput(complete=True, extracted=DispositionExtracted(disposition="REJECT"))
        return DispositionOutput(complete=True, extracted=DispositionExtracted(disposition="ACCEPT"))

    if node_name == "NOTES_OPTIONAL":
        if "no notes" in t or "skip" in t or "none" in t:
            return NotesOptionalOutput(complete=True, extracted=NotesOptionalExtracted(notes=""))
        return NotesOptionalOutput(complete=True, extracted=NotesOptionalExtracted(notes=transcript[:200] or ""))

    if node_name == "COMPLETE_STYLE":
        if "close" in t and "po" in t:
            return CompleteStyleOutput(complete=True, extracted=CompleteStyleExtracted(complete_style_action="CLOSE_PO"))
        return CompleteStyleOutput(complete=True, extracted=CompleteStyleExtracted(complete_style_action="NEXT_STYLE"))

    raise ValueError(f"Unknown node: {node_name}")
