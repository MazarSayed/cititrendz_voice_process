## Apparel Receiving — Voice-First Full Inspection Requirements

This document defines the **required flow**, **required data capture**, and **required voice interactions** for a warehouse apparel receiving inspection. It is intentionally written as a product/ops requirements spec (not implementation).

---

## Roles

- **Associate**: performs inspection, responds by voice, scans barcodes, captures photos.
- **System** (headphones): prompts the associate step-by-step and records structured outcomes.

---

## Core principles

- **Voice-first**: every step must be operable hands-free via voice (with scan/camera as needed).
- **Step-locked**: the system must guide the associate in order and prevent missing required steps.
- **Structured capture**: outcomes must be stored as typed fields (not only free text).
- **Exception-driven**: photos are required when exceptions occur.
- **Repeatable & auditable**: the same inputs should produce the same recorded outputs.

---

## Use case context (warehouse receiving loop)

- **Physical flow**:
  - Associate walks to a carton/box at receiving.
  - Box moves through the warehouse after inspection is completed/recorded.
  - Associate opens the next box and repeats.
- **System flow**:
  - Associate inputs/speaks the **PO number** (and/or scans carton barcode) into the app.
  - App guides the associate through **quality inspection**, comparing **PO lines** to actual box contents.
  - Captured inspection data is sent from the app to the **purchasing system**.

---

## Global voice behaviors (apply to all steps)

- **Confirmations**: when the system reads back critical info (PO, disposition, counts), the associate must be able to say **“Confirm”** or **“Mismatch”**.
- **Corrections**: the associate must be able to re-answer the current question if they misspoke.
- **Clarity**: if the system cannot understand, it must re-prompt with a shorter example.

---

## Required workflow (by step)

### 0) Start / Identification (Required)

- **System prompt**: “Scan the carton barcode or say the PO number to begin inspection.”
- **Associate input (example)**: “PO one two three four five six.”
- **Required outcome**:
  - either `po_number` is captured
  - or `carton_barcode` is captured (and then resolved to a PO)

---

### 1) PO + Carton Verification (Required)

- **System prompt** (example): “PO 123456, Vendor Acme Apparel, Style count 3, Expected units 48. Say Confirm or Mismatch.”
- **Associate response**: “Confirm.” or “Mismatch.”
- **Required captured fields**:
  - `po_number`
  - `vendor`
  - `expected_style_count`
  - `expected_units_total`
  - `po_verification_result` = `CONFIRMED|MISMATCH`
  - if mismatch: `po_mismatch_reason` (brief structured/free text)
- **Loop condition**:
  - if `MISMATCH`, the system must keep the associate in this step until resolved/escalated.

---

### 2) Carton Condition Check (Required)

- **System prompt**: “Inspect the carton… Say Carton OK or say Damage type and severity.”
- **Associate examples**:
  - “Carton OK.”
  - “Puncture, minor.”
  - “Water damage, major.”
- **Required captured fields**:
  - `carton_status` = `OK|DAMAGED`
  - if damaged:
    - `damage_type` (e.g., crushing, puncture, water damage, retape, other)
    - `damage_severity` = `MINOR|MAJOR`
- **Loop condition**:
  - if `carton_status=DAMAGED` but missing `damage_type` or `damage_severity`, the system must re-prompt for the missing detail(s).

---

### 3) Style / SKU Verification (Required, per style)

- **System prompt**: “Scan the first item barcode. If unable, say Manual entry and read the style number.”
- **Associate examples**:
  - “Scan successful.”
  - “Manual entry. Style four eight seven nine two.”
- **Required captured fields**:
  - `style_id` (or `sku`)
  - `style_entry_method` = `SCAN|MANUAL`
- **Loop condition**:
  - if scan fails and manual is not provided, re-prompt with “Say Manual entry and read the style number.”

---

### 4) Color & Size Verification (Required, per style)

- **System prompt**: “Verify color and size against the PO. Say Match or Mismatch, then state the issue.”
- **Associate examples**:
  - “Match.”
  - “Mismatch. Color received navy, PO says black.”
- **Required captured fields**:
  - `color_match` = `true|false`
  - `size_match` = `true|false` (if checked separately) OR a combined `color_size_match`
  - if mismatch: `mismatch_reason` (brief structured/free text)
- **Loop condition**:
  - if mismatch but no reason is captured, re-prompt: “State the issue (example: color received navy, PO says black).”

---

### 5) Unit Count by Size (Required, per style)

- **System prompt**: “Count units by size. State each size and quantity.”
- **Associate example**: “Small eight. Medium twelve. Large sixteen. Extra-large twelve.”
- **Required captured fields**:
  - `size_counts[]` (structured array of size → qty)

Example structure:

```json
[
  { "size": "S", "qty": 8 },
  { "size": "M", "qty": 12 },
  { "size": "L", "qty": 16 },
  { "size": "XL", "qty": 12 }
]
```

- **Required validations**:
  - every entry must include a recognized `size` and numeric `qty`
  - total quantity must be computed (for downstream disposition/exceptions)
- **Loop condition**:
  - if any size/qty is missing or unparseable, re-prompt for the full list or the missing parts.

---

### 6) Workmanship & Defect Inspection (100% Check) (Required, per style)

- **System prompt**: “Inspect every unit… If all units pass, say All units OK. If defects are found, say Defect type, affected unit count, and severity.”
- **Associate examples**:
  - “All units OK.”
  - “Stains, three units, minor.”
  - “Seam tear, one unit, major.”
  - “Strong odor, five units, major.”
- **Required captured fields**:
  - either `all_units_ok = true`
  - or `defects[]` where each defect includes:
    - `defect_type` (stains, holes, tears, seam defects, misprints, odor, other)
    - `affected_unit_count` (integer)
    - `severity` = `MINOR|MAJOR`
- **Severity meaning**:
  - `MINOR`: cosmetic
  - `MAJOR`: unsellable
- **Loop condition**:
  - if a defect is reported without count or severity, re-prompt for missing details.

---

### 7) Tags & Labeling (Required, per style)

- **System prompt**: “Check tickets and labels… Say Tags OK or say Issue and unit count.”
- **Associate examples**:
  - “Tags OK.”
  - “Missing price tags, four units.”
  - “Wrong country label, two units.”
- **Required captured fields**:
  - either `tags_ok = true`
  - or `tags_issues[]` with:
    - `issue_type` (UPC, price ticket, size tag, country of origin, other)
    - `affected_unit_count`

---

### 8) Packaging & Presentation (Required, per style)

- **System prompt**: “Check packaging requirements… Say Packaging OK or describe the issue.”
- **Associate examples**:
  - “Packaging OK.”
  - “Missing polybags, six units.”
- **Required captured fields**:
  - either `packaging_ok = true`
  - or `packaging_issues[]` with:
    - `issue_type` (folding, polybag, hanger, inserts, other)
    - `affected_unit_count` (if applicable)

---

### 9) Photo Capture (Exception-Driven) (Conditionally Required)

- **Entry condition**: if any exception was recorded in steps 2, 4, 6, 7, or 8.
- **System prompt**: “Exceptions detected. Take photos now. Say Photo captured when complete.”
- **Associate response**: “Photo captured.”
- **Required outcome**:
  - at least one photo is captured and associated to the exception category (carton damage, defect, tags, packaging, mismatch).
- **Loop condition**:
  - if multiple exception categories exist, the system must ensure sufficient photos are captured to document each category (at minimum one per category).

---

### 10) Disposition Decision (Required, per style)

- **System prompt**: “State disposition: Accept, Accept with exceptions, Hold, or Reject.”
- **Associate responses**:
  - “Accept.”
  - “Accept with exceptions.”
  - “Hold.”
  - “Reject.”
- **Required captured field**:
  - `disposition` = `ACCEPT|ACCEPT_WITH_EXCEPTIONS|HOLD|REJECT`
- **Loop condition**:
  - if disposition is not recognized, re-prompt with the 4 allowed options.

---

### 11) Notes (Optional but Structured)

- **System prompt**: “Add notes if needed. Otherwise say No notes.”
- **Associate examples**:
  - “Vendor carton retaped. No internal damage.”
  - “No notes.”
- **Captured fields**:
  - `notes` (string, may be empty)

---

### 12) Completion (Required)

- **System prompt**: “Inspection complete for this style. Say Next style or Close PO.”
- **Associate outcomes**:
  - `next_style` (repeat steps 3–12 for the next style)
  - or `close_po` (end the inspection session)

---

## Exceptions (definition)

An **exception** exists if any of the following occur:

- carton damage recorded
- color/size mismatch recorded
- any defects recorded
- any tags/labeling issue recorded
- any packaging/presentation issue recorded
- disposition is `HOLD` or `REJECT` (and typically `ACCEPT_WITH_EXCEPTIONS`)

Exceptions must trigger the photo step and must be visible in the final inspection summary.