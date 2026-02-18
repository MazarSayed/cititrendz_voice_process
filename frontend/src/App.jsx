import React, { useState } from "react";
import { DemoLayout } from "./components/DemoLayout.jsx";
import { StepNavigator } from "./components/StepNavigator.jsx";
import { SummaryPanel } from "./components/SummaryPanel.jsx";
import { demoSteps, makeEmptySessionSummary } from "./demoData.js";

const API_BASE = "http://localhost:8000";

export default function App() {
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [sessionSummary, setSessionSummary] = useState(
    makeEmptySessionSummary(),
  );
  const [started, setStarted] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [backendState, setBackendState] = useState(null);

  const step = demoSteps[currentStepIndex];

  async function handleSubmit(stepId, payload) {
    setSessionSummary((prev) => {
      const updated = structuredClone(prev);
      updated.responses[stepId] = payload;
      return updated;
    });

    // Advance the LangGraph-backed session on the server, using the same
    // transcript we just captured.
    if (sessionId) {
      try {
        const resp = await fetch(`${API_BASE}/api/session/${sessionId}/step`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ transcript: payload.text }),
        });
        if (!resp.ok) {
          // Keep UI usable even if backend step fails.
          console.error("Backend step error", resp.status);
        } else {
          const data = await resp.json();
          setBackendState(data.state);
          const node = data.current_node;
          const idx = demoSteps.findIndex((s) => s.nodeLabel === node);
          if (idx !== -1) {
            setCurrentStepIndex(idx);
          } else if (currentStepIndex < demoSteps.length - 1) {
            setCurrentStepIndex((i) => i + 1);
          }
        }
      } catch (e) {
        console.error("Error calling backend step", e);
        if (currentStepIndex < demoSteps.length - 1) {
          setCurrentStepIndex((i) => i + 1);
        }
      }
    } else if (currentStepIndex < demoSteps.length - 1) {
      // Fallback: purely local progression if no backend session.
      setCurrentStepIndex((i) => i + 1);
    }
  }

  function handleBack() {
    setCurrentStepIndex((i) => (i > 0 ? i - 1 : 0));
  }

  function handleReset() {
    setCurrentStepIndex(0);
    setSessionSummary(makeEmptySessionSummary());
    setStarted(false);
    setSessionId(null);
    setBackendState(null);
  }

  async function handleStart() {
    try {
      const resp = await fetch(`${API_BASE}/api/session`, { method: "POST" });
      if (!resp.ok) {
        console.error("Failed to start backend session", resp.status);
        setStarted(true);
        return;
      }
      const data = await resp.json();
      setSessionId(data.session_id);
      setBackendState(data.state);
      const node = data.current_node;
      const idx = demoSteps.findIndex((s) => s.nodeLabel === node);
      setCurrentStepIndex(idx === -1 ? 0 : idx);
      setStarted(true);
    } catch (e) {
      console.error("Error starting backend session", e);
      setStarted(true);
    }
  }

  return (
    <DemoLayout onReset={handleReset}>
      {!started ? (
        <section className="card step-card">
          <h1 className="step-title">Cititrends Receiving Inspection</h1>
          <p className="helper-text">
            This application guides the associate through each inspection step,
            speaks the questions, captures answers via microphone, sends audio
            to Deepgram for transcription, and drives the LangGraph-powered
            receiving flow.
          </p>
          <button
            type="button"
            className="btn-primary"
            onClick={handleStart}
          >
            Start inspection
          </button>
        </section>
      ) : (
        <StepNavigator
          step={step}
          stepIndex={currentStepIndex}
          totalSteps={demoSteps.length}
          onSubmit={handleSubmit}
          existingResponse={sessionSummary.responses[step.id]}
        />
      )}
      <SummaryPanel
        stepIndex={currentStepIndex}
        totalSteps={demoSteps.length}
        summary={sessionSummary}
        backendState={backendState}
      />
    </DemoLayout>
  );
}

