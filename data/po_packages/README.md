# PO Packages — Carton List & Mapping

This folder holds the **carton/package list** for each PO (Purchase Order). When an associate says a PO number during inspection, the app loads this list so they can verify **expected vs actual** and see **match or mismatch**.

## Folder structure

```
data/po_packages/
├── README.md           ← you are here
├── 123456/              ← one folder per PO (digits only)
│   ├── intrasheet.xlsx  ← carton list with expected values
│   └── manifest.json    ← vendor, expected_style_count, expected_units_total (must match intrasheet)
├── 789012/
│   ├── intrasheet.xlsx
│   └── manifest.json
└── ...
```

**manifest.json** should match the intrasheet. After editing intrasheet.xlsx, run:
`uv run scripts/sync_manifest.py` to regenerate manifest.json.

## How to add a new PO

1. Create a folder named with the PO number (digits only), e.g. `123456` for PO 123456.
2. Add `intrasheet.xlsx` inside that folder with the columns below.
3. Keep 3–5 cartons per PO package for manageable verification flows.
4. Or run: `uv run scripts/create_sample_po.py` and edit the generated file.

## intrasheet.xlsx columns

| Column           | Description                          | Used for match check |
|------------------|--------------------------------------|----------------------|
| Carton ID        | Carton identifier                    | —                    |
| Barcode          | Barcode (if different from Carton ID)| —                    |
| Style ID         | Expected style/SKU                   | ✓ Expected vs actual |
| Expected Units   | Expected unit count per carton       | ✓ Expected vs actual |
| Color            | Expected color                       | ✓ Expected vs actual |
| Size             | Expected size                        | ✓ Expected vs actual |
| Units Counted    | Filled during inspection             | Actual               |
| Disposition      | Filled during inspection             | Actual               |
| Status           | Pending / In progress / Done        | —                    |
| Notes            | Free-form notes                      | —                    |

The app loads this list when the PO is spoken, shows it in the UI, and overlays **actual** inspection data as the associate provides it. The user can see at a glance whether each carton **matches** or **doesn't match** the expected values.
