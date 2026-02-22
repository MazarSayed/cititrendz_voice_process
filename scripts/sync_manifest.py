#!/usr/bin/env -S uv run
"""
Sync manifest.json from intrasheet.xlsx for each PO package.
Keeps expected_style_count and expected_units_total in sync with the Excel data.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.po_packages import list_available_pos, sync_manifest_from_intrasheet


def main() -> None:
    pos = list_available_pos()
    if not pos:
        print("No PO packages found in data/po_packages/")
        return
    for po in pos:
        m = sync_manifest_from_intrasheet(po)
        if m:
            print(f"PO {po}: vendor={m.get('vendor')}, styles={m.get('expected_style_count')}, units={m.get('expected_units_total')}")
        else:
            print(f"PO {po}: no intrasheet.xlsx")


if __name__ == "__main__":
    main()
