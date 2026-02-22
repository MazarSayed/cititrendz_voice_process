import React from "react";

/** Format node name for display (e.g. START_IDENTIFICATION → Start identification) */
function formatNodeName(node) {
  if (!node) return "—";
  return node
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase())
    .replace(/100pct/i, "100%");
}

/** Extract digits from transcript (e.g. "PO 123456" or "PO number 1, 2, 3, 4, 5, 6") */
function digitsFromTranscript(text) {
  if (!text || typeof text !== "string") return null;
  const digits = text.replace(/\D/g, "");
  return digits.length >= 3 ? digits : null;
}

/**
 * Prominent, real-time inspection state panel.
 * Shows session state in a large, easy-to-read format so associates
 * can see updates as the inspection progresses.
 * Uses stepLabel and sessionResponses as fallback when backend state lags.
 */
export function InspectionPanel({
  backendState,
  stepIndex = 0,
  totalSteps = 14,
  stepLabel,
  sessionResponses = {},
}) {
  if (!backendState) {
    return (
      <section className="card inspection-panel">
        <h2 className="inspection-panel-title">Inspection state</h2>
        <p className="inspection-panel-empty">
          Start an inspection to see real-time state updates here.
        </p>
      </section>
    );
  }

  const style = backendState.current_style || {};
  const completedStyles = backendState.completed_styles_data || [];
  const cartonResults = backendState.carton_match_results || {};
  const cartonVerified = Object.keys(cartonResults).length;
  const poVerification = backendState.po_verification_result;

  const displayPoNumber =
    backendState.po_number ||
    (stepIndex >= 1 && sessionResponses.START_IDENTIFICATION?.text
      ? digitsFromTranscript(sessionResponses.START_IDENTIFICATION.text)
      : null);
  const displayStepLabel =
    stepLabel || formatNodeName(backendState.current_node);

  return (
    <section className="card inspection-panel">
      <h2 className="inspection-panel-title">Inspection state</h2>
      <p className="inspection-panel-subtitle">
        Live session — updates as you provide information
      </p>

      <div className="inspection-grid inspection-grid--primary">
        <div className="inspection-block">
          <span className="inspection-label">SESSION</span>
          <span className="inspection-value">{backendState.session_id || "—"}</span>
        </div>
        <div className="inspection-block">
          <span className="inspection-label">CURRENT STEP</span>
          <span className="inspection-value inspection-value--highlight">
            Stage {stepIndex + 1} of {totalSteps} — {displayStepLabel}
          </span>
        </div>
        <div className="inspection-block">
          <span className="inspection-label">PO NUMBER</span>
          <span className="inspection-value inspection-value--po">
            {displayPoNumber || "—"}
          </span>
        </div>
        <div className="inspection-block">
          <span className="inspection-label">CARTON STATUS</span>
          <span className="inspection-value">
            {backendState.carton_status || "—"}
          </span>
        </div>
      </div>

      {(displayPoNumber || poVerification || cartonVerified > 0) && (
        <div className="inspection-section">
          <h3 className="inspection-section-title">PO & carton verification</h3>
          <div className="inspection-grid">
            <div className="inspection-block">
              <span className="inspection-label">VENDOR</span>
              <span className="inspection-value">{backendState.vendor || "—"}</span>
            </div>
            <div className="inspection-block">
              <span className="inspection-label">PO VERIFICATION</span>
              <span className="inspection-value">
                {poVerification === "CONFIRMED"
                  ? "✓ Confirmed"
                  : poVerification === "MISMATCH"
                    ? "✗ Mismatch"
                    : "—"}
              </span>
            </div>
            <div className="inspection-block">
              <span className="inspection-label">CARTONS VERIFIED</span>
              <span className="inspection-value">
                {cartonVerified > 0 ? `${cartonVerified} verified` : "—"}
              </span>
            </div>
          </div>
        </div>
      )}

      {backendState.po_number && (style.style_id || style.style_entry_method) && (
        <div className="inspection-section">
          <h3 className="inspection-section-title">Current style</h3>
          <div className="inspection-grid">
            <div className="inspection-block">
              <span className="inspection-label">STYLE ID</span>
              <span className="inspection-value">{style.style_id || "—"}</span>
            </div>
            <div className="inspection-block">
              <span className="inspection-label">UNITS COUNTED</span>
              <span className="inspection-value">
                {style.total_units_counted ?? "—"}
              </span>
            </div>
            <div className="inspection-block">
              <span className="inspection-label">COLOR/SIZE</span>
              <span className="inspection-value">
                {style.color_size_match === true
                  ? "✓ Match"
                  : style.color_size_match === false
                    ? "✗ Mismatch"
                    : "—"}
              </span>
            </div>
            <div className="inspection-block">
              <span className="inspection-label">DISPOSITION</span>
              <span className="inspection-value inspection-value--disposition">
                {style.disposition || backendState.disposition || "—"}
              </span>
            </div>
          </div>
        </div>
      )}

      {completedStyles.length > 0 && (
        <div className="inspection-section">
          <h3 className="inspection-section-title">
            Completed styles ({completedStyles.length})
          </h3>
          <ul className="inspection-completed-list">
            {completedStyles.map((s, i) => (
              <li key={i} className="inspection-completed-item">
                {s.style_id || `Style ${i + 1}`} — {s.total_units_counted ?? "?"} units —{" "}
                {s.disposition || "—"}
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
