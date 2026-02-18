import React from "react";
import { demoSteps } from "../demoData.js";

export function SummaryPanel({ stepIndex, totalSteps, summary, backendState }) {
  const completedCount = Object.keys(summary.responses).length;

  return (
    <section className="card summary-card">
      <div className="summary-header">
        <h2 className="summary-title">Session snapshot</h2>
        <span className="summary-badge">
          {completedCount}/{totalSteps} steps captured
        </span>
      </div>

      <div className="summary-body">
        <p className="summary-meta">
          Started&nbsp;
          <time dateTime={summary.startedAt}>
            {new Date(summary.startedAt).toLocaleTimeString()}
          </time>
        </p>

        <ol className="summary-list">
          {demoSteps.map((step, index) => {
            const response = summary.responses[step.id];
            const isCurrent = index === stepIndex;

            return (
              <li
                key={step.id}
                className={`summary-item ${
                  response ? "summary-item--done" : ""
                } ${isCurrent ? "summary-item--current" : ""}`}
              >
                <div className="summary-item-header">
                  <div className="summary-dot" />
                  <div className="summary-texts">
                    <div className="summary-step-title">{step.title}</div>
                    <div className="summary-step-node">{step.nodeLabel}</div>
                  </div>
                </div>
                {response && (
                  <p className="summary-response">
                    <span className="summary-response-label">Associate:</span>{" "}
                    {response.text}
                  </p>
                )}
              </li>
            );
          })}
        </ol>

        {backendState && (
          <>
            <hr style={{ border: "none", borderTop: "1px solid rgba(255,255,255,0.18)", margin: "12px 0" }} />
            <h3 className="summary-title" style={{ marginTop: 0 }}>
              Inspection state
            </h3>
            <div className="summary-body">
              <p className="summary-response">
                <span className="summary-response-label">Session:</span>{" "}
                {backendState.session_id || "—"}
              </p>
              <p className="summary-response">
                <span className="summary-response-label">Current node:</span>{" "}
                {backendState.current_node || "—"}
              </p>
              <p className="summary-response">
                <span className="summary-response-label">PO number:</span>{" "}
                {backendState.po_number || "—"}
              </p>
              <p className="summary-response">
                <span className="summary-response-label">Carton status:</span>{" "}
                {backendState.carton_status || "—"}
              </p>
              {backendState.current_style && (
                <>
                  <p className="summary-response">
                    <span className="summary-response-label">Style ID:</span>{" "}
                    {backendState.current_style.style_id || "—"}
                  </p>
                  <p className="summary-response">
                    <span className="summary-response-label">Total units counted:</span>{" "}
                    {backendState.current_style.total_units_counted ?? "—"}
                  </p>
                  <p className="summary-response">
                    <span className="summary-response-label">Disposition:</span>{" "}
                    {backendState.current_style.disposition || backendState.disposition || "—"}
                  </p>
                </>
              )}
            </div>
          </>
        )}
      </div>
    </section>
  );
}

