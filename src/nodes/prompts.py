"""
Central place for node prompt strings.

Keeps each node file focused on logic while still making prompts easy to edit.
"""

START_IDENTIFICATION_PROMPT = (
    "Scan the carton barcode or say the PO number to begin. "
    "The system will verify the PO is available in our packages list."
)

CARTON_CONDITION_PROMPT = (
    "Inspect the carton. Look for crushing, punctures, water damage, or retape. "
    "Say Carton OK or say Damage type and severity."
)

STYLE_SKU_VERIFICATION_PROMPT = (
    "Scan the first item barcode. If unable, say Manual entry and read the style number."
)

COLOR_SIZE_VERIFICATION_PROMPT = (
    "Verify color and size against the PO. Say Match or Mismatch, then state the issue."
)

UNIT_COUNT_BY_SIZE_PROMPT = "Count units by size. State each size and quantity."

DEFECT_INSPECTION_PROMPT = (
    "Inspect every unit for stains, holes, tears, seam defects, misprints, or odor. "
    "If all units pass, say All units OK. "
    "If defects are found, say Defect type, affected unit count, and severity."
)

TAGS_LABELING_PROMPT = (
    "Check tickets and labels. Verify UPC, price ticket, size tag, and country of origin. "
    "Say Tags OK or say Issue and unit count."
)

PACKAGING_PRESENTATION_PROMPT = (
    "Check packaging requirements: folding, polybag, hanger, and inserts if required. "
    "Say Packaging OK or describe the issue."
)

PHOTO_CAPTURE_PROMPT = (
    "Exceptions detected. Take photos now. Say Photo captured when complete."
)

DISPOSITION_PROMPT = (
    "State disposition: Accept, Accept with exceptions, Hold, or Reject."
)

NOTES_PROMPT = "Add notes if needed. Otherwise say No notes."

COMPLETE_STYLE_PROMPT = "Inspection complete for this style. Say Next style or Close PO."

CLOSE_PO_PROMPT = "Inspection complete. PO closed."


def po_carton_verification_prompt(
    *,
    po_number: str,
    vendor: str | None,
    expected_style_count: int | None,
    expected_units_total: int | None,
    carton_count: int | None = None,
) -> str:
    parts = [f"PO {po_number}"]
    parts.append(f"Vendor {vendor or 'Unknown vendor'}")
    if expected_style_count is not None:
        parts.append(f"Style count {expected_style_count}")
    if expected_units_total is not None:
        parts.append(f"Expected units {expected_units_total}")
    if carton_count is not None:
        parts.append(f"{carton_count} cartons to verify")
    parts.append("Say Confirm or Mismatch.")
    return ", ".join(parts) + "."

