import React from "react";

/**
 * Displays the carton/package list for the current PO.
 * Shows expected values from Excel and actual values from inspection,
 * with Match/Mismatch so the user can verify.
 */
export function CartonTable({ poNumber, cartons, backendState }) {
  if (!poNumber) {
    return (
      <section className="card carton-table-card">
        <h2 className="carton-table-title">PO packages</h2>
        <p className="carton-table-empty">
          Provide a PO number to load the carton list.
        </p>
      </section>
    );
  }

  const style = backendState?.current_style;
  const cartonMatchResults = backendState?.carton_match_results || {};
  const isVerificationMode = backendState?.current_node === "CARTON_VERIFICATION";
  const currentCartonIndex = backendState?.current_carton_index ?? 0;

  // Merge carton list with live inspection data; use carton_match_results when available
  const rows = (cartons || []).map((c, i) => {
    const cartonKey = c.barcode || c.carton_id;
    const explicitMatch = cartonKey ? cartonMatchResults[String(cartonKey)] : null;

    // During carton verification, highlight the carton at current_carton_index
    const isCurrentCarton = isVerificationMode
      ? i === currentCartonIndex
      : backendState?.carton_barcode === c.barcode ||
        (style?.style_id && String(c.style_id || "").toUpperCase() === String(style.style_id || "").toUpperCase());
    const expectedUnits = c.expected_units ?? c.expected_units_counted;
    const actualUnits = isCurrentCarton && style?.total_units_counted != null
      ? style.total_units_counted
      : c.units_counted;
    const unitsMatch = expectedUnits != null && actualUnits != null
      ? Number(expectedUnits) === Number(actualUnits)
      : null;
    const colorSizeMatch = isCurrentCarton && style?.color_size_match !== undefined
      ? style.color_size_match
      : null;
    const mismatchReason = isCurrentCarton && style?.mismatch_reason
      ? style.mismatch_reason
      : null;

    // Prefer explicit match/mismatch from user speech (carton_match_results)
    const matchStatus =
      explicitMatch != null
        ? explicitMatch
        : unitsMatch === false || colorSizeMatch === false
          ? "Mismatch"
          : unitsMatch === true && (colorSizeMatch === true || colorSizeMatch === null)
            ? "Match"
            : null;

    const status =
      explicitMatch != null
        ? explicitMatch
        : isCurrentCarton
          ? "In progress"
          : c.status || "Pending";

    return {
      ...c,
      isCurrent: isCurrentCarton,
      style_id: isCurrentCarton && style?.style_id ? style.style_id : c.style_id,
      units_counted: actualUnits,
      expected_units: expectedUnits,
      disposition:
        isCurrentCarton && (style?.disposition || backendState?.disposition)
          ? style.disposition || backendState.disposition
          : c.disposition,
      status,
      matchStatus,
      mismatchReason,
    };
  });

  return (
    <section className={`card carton-table-card ${isVerificationMode ? "carton-table-card--verification" : ""}`}>
      <h2 className="carton-table-title">PO packages — {poNumber}</h2>
      <p className="carton-table-subtitle">
        {isVerificationMode
          ? "Data from intrasheet.xlsx — Say Match or Mismatch for each carton. Updates automatically."
          : "Expected values from PO list. Compare with actual inspection to verify match or mismatch."}
      </p>
      <div className="carton-table-scroll">
        <table className="carton-table">
          <thead>
            <tr>
              <th>Carton</th>
              <th>Style ID (expected)</th>
              <th>Expected</th>
              <th>Color / Size</th>
              <th>Units counted</th>
              <th>Match</th>
              <th>Disposition</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 ? (
              <tr>
                <td colSpan={8} className="carton-table-empty-cell">
                  No cartons loaded. Add packages for this PO in{" "}
                  <code>data/po_packages/{poNumber}/intrasheet.xlsx</code> or run{" "}
                  <code>uv run scripts/create_sample_po.py</code>.
                </td>
              </tr>
            ) : (
              rows.map((row, i) => (
                <tr
                  key={row.id || i}
                  className={row.isCurrent ? "carton-table-row--current" : ""}
                >
                  <td>{row.barcode || row.carton_id || "—"}</td>
                  <td>{row.style_id || "—"}</td>
                  <td>{row.expected_units != null ? row.expected_units : "—"}</td>
                  <td>
                    {[row.color, row.size].filter(Boolean).join(" / ") || "—"}
                  </td>
                  <td>{row.units_counted ?? "—"}</td>
                  <td className="carton-table-match">
                    {row.matchStatus === "Match" && (
                      <span className="carton-match-badge carton-match-badge--ok">✓ Match</span>
                    )}
                    {row.matchStatus === "Mismatch" && (
                      <span className="carton-match-badge carton-match-badge--fail" title={row.mismatchReason || ""}>
                        ✗ Mismatch
                      </span>
                    )}
                    {row.matchStatus == null && "—"}
                  </td>
                  <td className="carton-table-disposition">
                    {row.disposition || "—"}
                  </td>
                  <td>{row.status || "—"}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
