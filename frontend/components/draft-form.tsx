"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { generateDraft, invokeMcpTool, type DraftResponse } from "@/lib/api";
import { showErrorPopup } from "@/lib/error-popup";

type Props = {
  onDraft: (draft: DraftResponse) => void;
  userId: string;
  token: string;
};

export function DraftForm({ onDraft, userId, token }: Props) {
  const [prompt, setPrompt] = useState("Please draft an outreach email to introduce our AI Email Assistant and request a quick 15-minute discussion next week.");
  const [intent, setIntent] = useState("outreach");
  const [tone, setTone] = useState("professional");
  const [language, setLanguage] = useState("en");
  const [loading, setLoading] = useState(false);
  const [recording, setRecording] = useState(false);
  const [recordMs, setRecordMs] = useState(0);
  const [processingVoice, setProcessingVoice] = useState(false);
  const [mounted, setMounted] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<number | null>(null);
  const requestAbortRef = useRef<AbortController | null>(null);

  const voiceLocked = recording || processingVoice;
  const bars = useMemo(() => Array.from({ length: 18 }, (_, i) => i), []);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    return () => {
      if (timerRef.current) {
        window.clearInterval(timerRef.current);
      }
    };
  }, []);

  function formatMs(ms: number): string {
    const total = Math.floor(ms / 1000);
    const mm = Math.floor(total / 60)
      .toString()
      .padStart(2, "0");
    const ss = (total % 60).toString().padStart(2, "0");
    return `${mm}:${ss}`;
  }

  function bytesToBase64(bytes: Uint8Array): string {
    let binary = "";
    const chunk = 0x8000;
    for (let i = 0; i < bytes.length; i += chunk) {
      const sub = bytes.subarray(i, i + chunk);
      binary += String.fromCharCode(...sub);
    }
    return btoa(binary);
  }

  function normalizeTranscriptText(raw: string): string {
    const cleaned = raw.replace(/\s+/g, " ").trim();
    if (!cleaned) return "";
    const lower = cleaned.toLowerCase();
    const sentenceCased = lower.replace(/(^|[.!?]\s+)([a-z])/g, (_, prefix: string, ch: string) => `${prefix}${ch.toUpperCase()}`);
    return sentenceCased.charAt(0).toUpperCase() + sentenceCased.slice(1);
  }

  async function startRecording() {
    if (!token || !userId) {
      showErrorPopup("Login is required before using voice input.", "Authentication required");
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      chunksRef.current = [];
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) chunksRef.current.push(event.data);
      };
      recorder.start();
      mediaRecorderRef.current = recorder;
      setRecordMs(0);
      setRecording(true);
      timerRef.current = window.setInterval(() => {
        setRecordMs((prev) => prev + 250);
      }, 250);
    } catch (err) {
      showErrorPopup(err instanceof Error ? err.message : "Microphone access failed.", "Voice input unavailable");
    }
  }

  async function transcribeBlob(blob: Blob) {
    setProcessingVoice(true);
    try {
      const arrayBuffer = await blob.arrayBuffer();
      const audioBase64 = bytesToBase64(new Uint8Array(arrayBuffer));
      const result = await invokeMcpTool(token, "tool.voice.transcribe", userId, {
        request_id: `voice-${Date.now()}`,
        user_id: userId,
        audio_base64: audioBase64,
        mime_type: blob.type || "audio/webm",
        language,
      });
      const transcript = String(result.result?.transcript || "").trim();
      if (transcript) {
        setPrompt(normalizeTranscriptText(transcript));
      } else {
        showErrorPopup("No speech was detected. Please try again.", "Transcription failed");
      }
    } catch (err) {
      showErrorPopup(err instanceof Error ? err.message : "Voice transcription failed.", "Transcription failed");
    } finally {
      setProcessingVoice(false);
      setRecordMs(0);
      chunksRef.current = [];
    }
  }

  async function stopRecording() {
    const recorder = mediaRecorderRef.current;
    if (!recorder) return;
    const done = new Promise<void>((resolve) => {
      recorder.onstop = () => resolve();
    });
    recorder.stop();
    setRecording(false);
    if (timerRef.current) {
      window.clearInterval(timerRef.current);
      timerRef.current = null;
    }
    await done;
    const blob = new Blob(chunksRef.current, { type: "audio/webm" });
    await transcribeBlob(blob);
  }

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (loading) return;
    const controller = new AbortController();
    requestAbortRef.current = controller;
    setLoading(true);

    try {
      const response = await generateDraft({
        user_id: userId,
        prompt,
        intent,
        tone,
        constraints: {
          max_paragraphs: 3,
          must_include: [],
          forbidden: ["PII"]
        },
        metadata: {
          recipient_role: "client",
          language
        }
      }, token, controller.signal);
      if (controller.signal.aborted) {
        return;
      }
      onDraft(response);
    } catch (err) {
      if (err instanceof Error && err.name === "AbortError") {
        return;
      }
      const msg = err instanceof Error ? err.message : "Unknown error";
      const lower = msg.toLowerCase();
      if (lower.includes("drafts emails only") || lower.includes("email request")) {
        showErrorPopup(
          "This workspace generates email drafts only. Please ask for an email to be written (for example: 'Draft an email to my manager about ...').",
          "Email requests only"
        );
      } else if (lower.includes("complete email request") || lower.includes("recipient and context")) {
        showErrorPopup(
          "Please add enough context to draft an email: who it is for and what the message should cover.",
          "More context needed"
        );
      } else if (lower.includes("failed to fetch")) {
        showErrorPopup(
          "Unable to reach the backend service right now. Please check that backend is running and try again.",
          "Service unavailable"
        );
      } else {
        showErrorPopup(msg, "Draft generation failed");
      }
    } finally {
      requestAbortRef.current = null;
      setLoading(false);
    }
  }

  function cancelGeneration() {
    if (requestAbortRef.current) {
      requestAbortRef.current.abort();
      requestAbortRef.current = null;
    }
    setLoading(false);
  }

  return (
    <form className="card compose-card" onSubmit={onSubmit}>
      <h2>Compose Request</h2>
      <p className="meta">Intent + tone controls with editable output (spec compliant).</p>

      <label htmlFor="intent">Intent</label>
      <select id="intent" value={intent} onChange={(e) => setIntent(e.target.value)}>
        <option value="outreach">Outreach</option>
        <option value="follow_up">Follow-up</option>
        <option value="apology">Apology</option>
        <option value="informational">Informational</option>
      </select>

      <label htmlFor="tone">Tone</label>
      <select id="tone" value={tone} onChange={(e) => setTone(e.target.value)}>
        <option value="professional">Professional</option>
        <option value="casual">Casual</option>
        <option value="assertive">Assertive</option>
        <option value="empathetic">Empathetic</option>
      </select>

      <label htmlFor="language">Language</label>
      <select id="language" value={language} onChange={(e) => setLanguage(e.target.value)} disabled={voiceLocked}>
        <option value="en">English</option>
        <option value="es">Spanish</option>
        <option value="hi">Hindi</option>
      </select>

      <label htmlFor="prompt">Prompt</label>
      {(recording || processingVoice) ? (
        <div className={`voice-record-panel ${recording ? "is-recording" : "is-processing"}`} aria-live="polite">
          <div className="voice-record-top">
            <p className="meta" style={{ margin: 0 }}>
              {recording ? `Recording ${formatMs(recordMs)}` : "Transcribing audio..."}
            </p>
            <button type="button" className="voice-stop-btn" onClick={stopRecording} disabled={processingVoice || !recording}>
              Stop
            </button>
          </div>
          <div className="wave-bars" aria-hidden>
            {bars.map((bar) => (
              <span key={bar} className="bar" style={{ animationDelay: `${bar * 0.05}s` }} />
            ))}
          </div>
        </div>
      ) : null}

      <div className={`prompt-shell ${voiceLocked ? "is-locked" : ""}`}>
        <textarea
          id="prompt"
          rows={8}
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          disabled={loading || voiceLocked}
          required
        />
        <button
          type="button"
          className={`prompt-mic-btn ${recording ? "is-recording" : ""}`}
          aria-label={recording ? "Stop recording" : "Start voice input"}
          onClick={recording ? stopRecording : startRecording}
          disabled={loading || processingVoice}
        >
          <span aria-hidden>{recording ? "●" : "🎤"}</span>
        </button>
        {voiceLocked ? (
          <div className="prompt-voice-mask">
            <p className="meta">{recording ? "Recording in progress..." : "Applying transcript..."}</p>
          </div>
        ) : null}
      </div>

      <button type="submit" disabled={loading || voiceLocked || !prompt.trim()}>
        {loading ? "Generating..." : "Generate Draft"}
      </button>

      {loading && mounted
        ? createPortal(
          <div className="thinking-overlay" aria-live="polite">
            <div className="thinking-card">
              <p className="thinking-title">Thinking...</p>
              <div className="thinking-bubbles" aria-hidden>
                <span />
                <span />
                <span />
              </div>
              <button type="button" className="thinking-cancel-btn" onClick={cancelGeneration}>
                Cancel
              </button>
            </div>
          </div>
          ,
          document.body
        )
        : null}
    </form>
  );
}
