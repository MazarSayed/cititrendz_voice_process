import React, { useState, useCallback, useEffect, useRef } from "react";
import { DemoLayout } from "./components/DemoLayout.jsx";
import { StepNavigator } from "./components/StepNavigator.jsx";
import { SummaryPanel } from "./components/SummaryPanel.jsx";
import { InspectionPanel } from "./components/InspectionPanel.jsx";
import { CartonTable } from "./components/CartonTable.jsx";
import { demoSteps, makeEmptySessionSummary } from "./demoData.js";

const API_BASE = "http://localhost:8000";
const POLL_SKIP_AFTER_STEP = 6; // Skip poll updates after step so Inspection state stays in sync

export default function App() {
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [sessionSummary, setSessionSummary] = useState(
    makeEmptySessionSummary(),
  );
  const [started, setStarted] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [backendState, setBackendState] = useState(null);
  const [cartons, setCartons] = useState([]);
  // Incremented after every backend response so StepNavigator restarts
  // recording even when the same node is returned (re-prompt / retry).
  const [recordingKey, setRecordingKey] = useState(0);
  const skipNextPollsRef = useRef(0);

  const step = demoSteps[currentStepIndex];

  // Poll session state for real-time updates (every 1s)
  // Skip applying poll result for a few cycles after step response (avoids stale overwrite)
  useEffect(() => {
    if (!sessionId) return;
    const poll = async () => {
      try {
        const resp = await fetch(`${API_BASE}/api/session/${sessionId}/state`);
        if (!resp.ok) return;
        const data = await resp.json();
        if (skipNextPollsRef.current > 0) {
          skipNextPollsRef.current -= 1;
          return;
        }
        setBackendState(data.state || {});
      } catch (e) {
        console.debug("Poll state error", e);
      }
    };
    poll();
    const interval = setInterval(poll, 1000);
    return () => clearInterval(interval);
  }, [sessionId]);

  // Load carton list when PO number becomes available; init PO folder if needed
  useEffect(() => {
    const po = backendState?.po_number;
    if (!po) {
      setCartons([]);
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        // Try to get cartons; if empty, init PO folder to create template
        let resp = await fetch(`${API_BASE}/api/po/${encodeURIComponent(po)}/cartons`);
        if (!resp.ok || cancelled) return;
        let data = await resp.json();
        let list = data.cartons || [];
        if (list.length === 0) {
          resp = await fetch(`${API_BASE}/api/po/${encodeURIComponent(po)}/init`, {
            method: "POST",
          });
          if (resp.ok && !cancelled) {
            data = await resp.json();
            list = data.cartons || [];
          }
        }
        setCartons(list);
      } catch (e) {
        console.debug("Load cartons error", e);
        if (!cancelled) setCartons([]);
      }
    })();
    return () => { cancelled = true; };
  }, [backendState?.po_number]);

  const handleSubmit = useCallback(async (stepId, payload) => {
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
          skipNextPollsRef.current = POLL_SKIP_AFTER_STEP;
          setBackendState(data.state ? { ...data.state } : {});
          const node = data.current_node;
          const idx = demoSteps.findIndex((s) => s.nodeLabel === node);
          if (idx !== -1) {
            setCurrentStepIndex(idx);
          } else {
            setCurrentStepIndex((i) => Math.min(i + 1, demoSteps.length - 1));
          }
        }
      } catch (e) {
        console.error("Error calling backend step", e);
        setCurrentStepIndex((i) => Math.min(i + 1, demoSteps.length - 1));
      } finally {
        // Always bump recordingKey so StepNavigator's useEffect re-runs and
        // starts a fresh recording cycle, whether we advanced or are retrying
        // the same step after a validation failure.
        setRecordingKey((n) => n + 1);
      }
    } else {
      // Fallback: purely local progression if no backend session.
      setCurrentStepIndex((i) => Math.min(i + 1, demoSteps.length - 1));
      setRecordingKey((n) => n + 1);
    }
  }, [sessionId]);

  function handleBack() {
    setCurrentStepIndex((i) => (i > 0 ? i - 1 : 0));
  }

  function handleReset() {
    setCurrentStepIndex(0);
    setSessionSummary(makeEmptySessionSummary());
    setStarted(false);
    setSessionId(null);
    setBackendState(null);
    setCartons([]);
    setRecordingKey(0);
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
      skipNextPollsRef.current = POLL_SKIP_AFTER_STEP;
      setBackendState(data.state || {});
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
        <>
          <StepNavigator
            step={step}
            stepIndex={currentStepIndex}
            totalSteps={demoSteps.length}
            onSubmit={handleSubmit}
            existingResponse={sessionSummary.responses[step.id]}
            recordingKey={recordingKey}
            promptToSpeak={
              backendState?.current_node === step.nodeLabel &&
              backendState?.last_prompt?.text
                ? backendState.last_prompt.text
                : undefined
            }
          />
          {backendState?.current_node === "CARTON_VERIFICATION" && (
            <CartonTable
              poNumber={backendState?.po_number}
              cartons={cartons}
              backendState={backendState}
            />
          )}
        </>
      )}
      <InspectionPanel
        backendState={backendState}
        stepIndex={currentStepIndex}
        totalSteps={demoSteps.length}
        stepLabel={step?.title}
        sessionResponses={sessionSummary.responses}
      />
      <SummaryPanel
        stepIndex={currentStepIndex}
        totalSteps={demoSteps.length}
        summary={sessionSummary}
        backendState={backendState}
      />
      {backendState?.current_node !== "CARTON_VERIFICATION" && (
        <CartonTable
          poNumber={backendState?.po_number}
          cartons={cartons}
          backendState={backendState}
        />
      )}
    </DemoLayout>
  );
}
