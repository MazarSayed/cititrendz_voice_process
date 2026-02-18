import React from "react";

export function HeaderBar({ onReset }) {
  return (
    <header className="header-bar">
      <div className="header-left">
        <img src="/image (9).png" alt="Cititrends logo" className="logo" />
        <div className="brand-text">
          <div className="brand-title">Receiving Inspection</div>
          <div className="brand-subtitle">Voice-first quality checks</div>
        </div>
      </div>
      <button type="button" className="chip-button" onClick={onReset}>
        Reset session
      </button>
    </header>
  );
}

