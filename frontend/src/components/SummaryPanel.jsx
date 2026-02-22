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
                    {step.id === "START_IDENTIFICATION" && backendState?.po_number
                      ? backendState.po_number
                      : response.text}
                  </p>
                )}
              </li>
            );
          })}
        </ol>

      </div>
    </section>
  );
}

