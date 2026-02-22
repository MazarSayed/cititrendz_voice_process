export const demoSteps = [
  {
    id: "START_IDENTIFICATION",
    title: "Start / Identification",
    nodeLabel: "START_IDENTIFICATION",
    systemPrompt:
      "Scan the carton barcode or say the PO number to begin inspection.",
    helperText:
      "Capture the PO number or carton barcode to open a new receiving inspection.",
    inputPlaceholder: "Example: PO one two three four five six",
  },
  {
    id: "PO_CARTON_VERIFICATION",
    title: "PO + Carton verification",
    nodeLabel: "PO_CARTON_VERIFICATION",
    systemPrompt:
      "PO details from package folder. Say Confirm or Mismatch.",
    helperText:
      "System reads PO header from data/po_packages/{po}/ (vendor, style count, expected units). Say Confirm or Mismatch.",
    inputPlaceholder: "Example: Confirm.",
  },
  {
    id: "CARTON_VERIFICATION",
    title: "Carton verification",
    nodeLabel: "CARTON_VERIFICATION",
    systemPrompt:
      "Carton BC001. Say Match or Mismatch.",
    helperText:
      "System reads each carton ID from the PO list. Say Match or Mismatch for each.",
    inputPlaceholder: "Example: Match.",
  },
  {
    id: "CARTON_CONDITION",
    title: "Carton condition check",
    nodeLabel: "CARTON_CONDITION",
    systemPrompt:
      "Inspect the carton. Say Carton OK or say damage type and severity.",
    helperText:
      "Classify the carton as OK or DAMAGED and capture structured damage details when present.",
    inputPlaceholder: "Example: Puncture, minor.",
  },
  {
    id: "STYLE_SKU_VERIFICATION",
    title: "Style / SKU verification",
    nodeLabel: "STYLE_SKU_VERIFICATION",
    systemPrompt:
      "Scan the first item barcode. If unable, say Manual entry and read the style number.",
    helperText:
      "Identify the style or SKU and start a new style-level inspection context.",
    inputPlaceholder: "Example: Manual entry. Style four eight seven nine two.",
  },
  {
    id: "COLOR_SIZE_VERIFICATION",
    title: "Color & size verification",
    nodeLabel: "COLOR_SIZE_VERIFICATION",
    systemPrompt:
      "Verify color and size against the PO. Say Match or Mismatch, then state the issue.",
    helperText:
      "Confirm color and size against the PO and record any mismatches with reasons.",
    inputPlaceholder: "Example: Mismatch. Color received navy, PO says black.",
  },
  {
    id: "UNIT_COUNT_BY_SIZE",
    title: "Unit count by size",
    nodeLabel: "UNIT_COUNT_BY_SIZE",
    systemPrompt:
      "Count units by size. State each size and quantity for this style.",
    helperText:
      "Record unit counts by size so the system can compare actuals to the PO.",
    inputPlaceholder: "Example: Small eight. Medium twelve. Large sixteen.",
  },
  {
    id: "DEFECT_INSPECTION_100pct",
    title: "Workmanship & defect inspection",
    nodeLabel: "DEFECT_INSPECTION_100pct",
    systemPrompt:
      "Inspect every unit. Say All units OK or describe defect type, count, and severity.",
    helperText:
      "Capture structured defect entries per style, including type, affected units, and severity.",
    inputPlaceholder: "Example: Stains, three units, minor.",
  },
  {
    id: "TAGS_LABELING",
    title: "Tags & labeling",
    nodeLabel: "TAGS_LABELING",
    systemPrompt:
      "Check tickets and labels. Say Tags OK or describe the issue and unit count.",
    helperText:
      "Validate tickets and labels and record any issues with affected unit counts.",
    inputPlaceholder: "Example: Missing price tags, four units.",
  },
  {
    id: "PACKAGING_PRESENTATION",
    title: "Packaging & presentation",
    nodeLabel: "PACKAGING_PRESENTATION",
    systemPrompt:
      "Check packaging requirements. Say Packaging OK or describe the issue.",
    helperText:
      "Confirm packaging requirements are met and record any presentation or packaging exceptions.",
    inputPlaceholder: "Example: Missing polybags, six units.",
  },
  {
    id: "PHOTO_CAPTURE_LOOP",
    title: "Photo capture (exceptions only)",
    nodeLabel: "PHOTO_CAPTURE_LOOP",
    systemPrompt:
      "Exceptions detected. Take photos now. Say Photo captured when complete.",
    helperText:
      "Capture and attach photo evidence for any recorded exceptions.",
    inputPlaceholder: "Example: Photo captured.",
  },
  {
    id: "DISPOSITION",
    title: "Disposition",
    nodeLabel: "DISPOSITION",
    systemPrompt:
      "Based on checks and defects, confirm the disposition for this style or PO.",
    helperText:
      "Set the final disposition for the style or PO based on recorded results and thresholds.",
    inputPlaceholder: "Example: Accept with exceptions.",
  },
  {
    id: "NOTES_OPTIONAL",
    title: "Notes (optional)",
    nodeLabel: "NOTES_OPTIONAL",
    systemPrompt:
      "Add any additional notes the buyer or QC team should see. Say Skip to continue.",
    helperText:
      "Store additional free-text notes alongside the structured inspection results.",
    inputPlaceholder: "Example: Carton slightly crushed but units OK.",
  },
  {
    id: "COMPLETE_STYLE",
    title: "Complete style",
    nodeLabel: "COMPLETE_STYLE",
    systemPrompt:
      "Confirm this style is complete. Say Next style or Close PO to finish receiving.",
    helperText:
      "Close out the current style and either move to the next style or close the PO.",
    inputPlaceholder: "Example: Close PO.",
  },
];

export function makeEmptySessionSummary() {
  return {
    startedAt: new Date().toISOString(),
    responses: {},
  };
}

