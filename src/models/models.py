"""
Pydantic models for structured LLM extraction. Each node has an output model
with complete, extracted (node-specific), and follow_up.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


# --- START_IDENTIFICATION ---
class StartIdentificationExtracted(BaseModel):
    po_number: str | None = Field(
        None,
        description="Pure digits only. E.g. 'PO number 1, 2, 3, 4, 5, 6' → '123456'. Used to identify package in data/po_packages/{po_number}/",
    )
    carton_barcode: str | None = None


class StartIdentificationOutput(BaseModel):
    complete: bool = False
    extracted: StartIdentificationExtracted | None = None
    follow_up: str | None = Field(None, description="Short prompt when complete=False")


# --- PO_CARTON_VERIFICATION ---
class PoCartonVerificationExtracted(BaseModel):
    po_verification_result: Literal["CONFIRMED", "MISMATCH"] | None = None
    po_mismatch_reason: str | None = None


class PoCartonVerificationOutput(BaseModel):
    complete: bool = False
    extracted: PoCartonVerificationExtracted | None = None
    follow_up: str | None = None


# --- CARTON_CONDITION ---
class CartonConditionExtracted(BaseModel):
    carton_status: Literal["OK", "DAMAGED"] | None = None
    damage_type: str | None = None
    damage_severity: Literal["MINOR", "MAJOR"] | None = None


class CartonConditionOutput(BaseModel):
    complete: bool = False
    extracted: CartonConditionExtracted | None = None
    follow_up: str | None = None


# --- STYLE_SKU_VERIFICATION ---
class StyleSkuVerificationExtracted(BaseModel):
    style_id: str | None = Field(None, description="4-6 digit style number")
    style_entry_method: Literal["SCAN", "MANUAL"] | None = None


class StyleSkuVerificationOutput(BaseModel):
    complete: bool = False
    extracted: StyleSkuVerificationExtracted | None = None
    follow_up: str | None = None


# --- COLOR_SIZE_VERIFICATION ---
class ColorSizeVerificationExtracted(BaseModel):
    color_size_match: bool | None = None
    mismatch_reason: str | None = None


class ColorSizeVerificationOutput(BaseModel):
    complete: bool = False
    extracted: ColorSizeVerificationExtracted | None = None
    follow_up: str | None = None


# --- UNIT_COUNT_BY_SIZE ---
class SizeCount(BaseModel):
    size: Literal["S", "M", "L", "XL", "XS", "XXL"]
    qty: int


class UnitCountBySizeExtracted(BaseModel):
    size_counts: list[SizeCount] = Field(default_factory=list)


class UnitCountBySizeOutput(BaseModel):
    complete: bool = False
    extracted: UnitCountBySizeExtracted | None = None
    follow_up: str | None = None


# --- DEFECT_INSPECTION_100pct ---
class DefectEntry(BaseModel):
    type: str = "other"
    affected_units: int | None = None
    severity: Literal["MINOR", "MAJOR"] | None = None


class DefectInspectionExtracted(BaseModel):
    all_units_ok: bool | None = None
    defects: list[DefectEntry] = Field(default_factory=list)


class DefectInspectionOutput(BaseModel):
    complete: bool = False
    extracted: DefectInspectionExtracted | None = None
    follow_up: str | None = None


# --- TAGS_LABELING ---
class TagIssueEntry(BaseModel):
    issue_type: str = "other"
    affected_unit_count: int | None = None


class TagsLabelingExtracted(BaseModel):
    tags_ok: bool | None = None
    tags_issues: list[TagIssueEntry] = Field(default_factory=list)


class TagsLabelingOutput(BaseModel):
    complete: bool = False
    extracted: TagsLabelingExtracted | None = None
    follow_up: str | None = None


# --- PACKAGING_PRESENTATION ---
class PackagingIssueEntry(BaseModel):
    issue_type: str = "other"
    raw: str = ""
    affected_unit_count: int | None = None


class PackagingPresentationExtracted(BaseModel):
    packaging_ok: bool | None = None
    packaging_issues: list[PackagingIssueEntry] = Field(default_factory=list)


class PackagingPresentationOutput(BaseModel):
    complete: bool = False
    extracted: PackagingPresentationExtracted | None = None
    follow_up: str | None = None


# --- PHOTO_CAPTURE_LOOP ---
class PhotoCaptureExtracted(BaseModel):
    photo_captured: bool | None = None


class PhotoCaptureOutput(BaseModel):
    complete: bool = False
    extracted: PhotoCaptureExtracted | None = None
    follow_up: str | None = None


# --- DISPOSITION ---
class DispositionExtracted(BaseModel):
    disposition: Literal["ACCEPT", "ACCEPT_WITH_EXCEPTIONS", "HOLD", "REJECT"] | None = None


class DispositionOutput(BaseModel):
    complete: bool = False
    extracted: DispositionExtracted | None = None
    follow_up: str | None = None


# --- NOTES_OPTIONAL ---
class NotesOptionalExtracted(BaseModel):
    notes: str | None = None


class NotesOptionalOutput(BaseModel):
    complete: bool = False
    extracted: NotesOptionalExtracted | None = None
    follow_up: str | None = None


# --- COMPLETE_STYLE ---
class CompleteStyleExtracted(BaseModel):
    complete_style_action: Literal["NEXT_STYLE", "CLOSE_PO"] | None = None


class CompleteStyleOutput(BaseModel):
    complete: bool = False
    extracted: CompleteStyleExtracted | None = None
    follow_up: str | None = None
