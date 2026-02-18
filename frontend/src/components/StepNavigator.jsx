import React, { useEffect, useRef, useState } from "react";

const API_BASE = "http://localhost:8000";

export function StepNavigator({ step, stepIndex, totalSteps, onSubmit, existingResponse }) {
  const [transcript, setTranscript] = useState(existingResponse?.text ?? "");
  const [status, setStatus] = useState("idle"); // idle | speaking | recording | transcribing | error
  const [audioSupported, setAudioSupported] = useState(false);
  const abortRef = useRef(false);
  const mediaRecorderRef = useRef(null);

  // When step changes, reset and run: speak prompt -> record -> Deepgram STT.
  useEffect(() => {
    abortRef.current = false;
    setTranscript("");

    const hasAudio =
      typeof navigator !== "undefined" &&
      !!navigator.mediaDevices &&
      !!navigator.mediaDevices.getUserMedia;
    setAudioSupported(hasAudio);

    async function speakThenRecordAndTranscribe() {
      if (!hasAudio) {
        setStatus("error");
        return;
      }

      // 1) Speak the system prompt via backend TTS (Deepgram).
      try {
        setStatus("speaking");
        const resp = await fetch(`${API_BASE}/api/tts`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text: step.systemPrompt }),
        });
        if (!resp.ok) {
          throw new Error(`TTS error: ${resp.status}`);
        }
        const blob = await resp.blob();
        const url = URL.createObjectURL(blob);
        const audio = new Audio(url);
        await new Promise((resolve, reject) => {
          audio.onended = resolve;
          audio.onerror = reject;
          audio.play().catch(reject);
        });
        URL.revokeObjectURL(url);
      } catch (e) {
        console.error(e);
        // Continue to recording even if TTS fails so the flow remains usable.
      }

      if (abortRef.current) return;

      // 2) Capture microphone audio
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const recorder = new MediaRecorder(stream);
        mediaRecorderRef.current = recorder;
        const chunks = [];

        recorder.ondataavailable = (event) => {
          if (event.data && event.data.size > 0) {
            chunks.push(event.data);
          }
        };

        recorder.onstop = async () => {
          stream.getTracks().forEach((t) => t.stop());
          mediaRecorderRef.current = null;

          if (abortRef.current) return;
          if (!chunks.length) {
            setStatus("error");
            return;
          }

          const blob = new Blob(chunks, { type: recorder.mimeType || "audio/webm" });
          setStatus("transcribing");

          try {
            const formData = new FormData();
            formData.append("audio", blob, "turn.webm");

            const resp = await fetch(`${API_BASE}/api/stt`, {
              method: "POST",
              body: formData,
            });

            if (!resp.ok) {
              throw new Error(`STT error: ${resp.status}`);
            }

            const data = await resp.json();
            const text = (data.transcript || "").trim();
            setTranscript(text);
            if (text) {
              setStatus("idle");
              onSubmit(step.id, {
                text,
                at: new Date().toISOString(),
              });
            } else {
              setStatus("error");
            }
          } catch (err) {
            console.error(err);
            setStatus("error");
          }
        };

        setStatus("recording");
        recorder.start();

        // Safety timeout to stop recording after 8 seconds
        setTimeout(() => {
          if (recorder.state === "recording") {
            recorder.stop();
          }
        }, 8000);
      } catch (err) {
        console.error(err);
        setStatus("error");
      }
    }

    speakThenRecordAndTranscribe();

    return () => {
      abortRef.current = true;
      const recorder = mediaRecorderRef.current;
      if (recorder && recorder.state === "recording") {
        try {
          recorder.stop();
        } catch {
          // ignore
        }
      }
      mediaRecorderRef.current = null;
    };
  }, [step.id, step.systemPrompt, onSubmit]);

  const progress = Math.round(((stepIndex + 1) / totalSteps) * 100);

  return (
    <section className="card step-card">
      <div className="step-header">
        <div className="step-pill">
          Step {stepIndex + 1} of {totalSteps}
        </div>
        <div className="step-node-label">{step.nodeLabel}</div>
      </div>

      <div className="progress-track" aria-hidden="true">
        <div className="progress-fill" style={{ width: `${progress}%` }} />
      </div>

      <h1 className="step-title">{step.title}</h1>

      <p className="system-prompt">
        <span className="prompt-label">System</span>
        {step.systemPrompt}
      </p>

      <p className="helper-text">{step.helperText}</p>

      <form className="step-form">
        <div className="voice-status">
          <p className="voice-note">
            System will <strong>speak the question</strong> via Deepgram, then
            capture your answer and send it for transcription.
          </p>
          {!audioSupported && (
            <p className="voice-warning">
              This browser does not allow microphone capture. Use a recent
              version of Chrome and grant microphone permission.
            </p>
          )}
          {audioSupported && (
            <p className="voice-note">
              Status:{" "}
              {status === "speaking" && "Playing question…"}
              {status === "recording" && (
                <strong>Listening… please speak now.</strong>
              )}
              {status === "transcribing" && "Sending audio to Deepgram…"}
              {status === "idle" && transcript && "Captured. Advancing…"}
              {status === "error" &&
                "Something went wrong capturing or transcribing audio."}
            </p>
          )}
        </div>

        {transcript && (
          <>
            <label className="field-label" htmlFor="captured-transcript">
              Transcription
            </label>
            <div
              id="captured-transcript"
              className="input-area input-area--readonly"
            >
              {transcript}
            </div>
          </>
        )}
      </form>
    </section>
  );
}

