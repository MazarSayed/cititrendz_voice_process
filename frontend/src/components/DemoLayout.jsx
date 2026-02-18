import React from "react";
import { HeaderBar } from "./HeaderBar.jsx";

export function DemoLayout({ children, onReset }) {
  return (
    <div className="app-root">
      <HeaderBar onReset={onReset} />
      <main className="app-main">
        <section className="app-main-column">{children}</section>
      </main>
    </div>
  );
}

