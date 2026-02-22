"use client";

import { useEffect, useRef, useState } from "react";
import { invokeMcpTool, type DraftResponse } from "@/lib/api";
import { showErrorPopup } from "@/lib/error-popup";

type Props = {
  draft: DraftResponse | null;
  token: string;
  userId: string;
};

function base64ToBlob(base64: string, mimeType: string): Blob {
  const binary = atob(base64);
  const len = binary.length;
  const bytes = new Uint8Array(len);
  for (let i = 0; i < len; i += 1) {
    bytes[i] = binary.charCodeAt(i);
  }
  return new Blob([bytes], { type: mimeType });
}

function formatClock(seconds: number): string {
  if (!Number.isFinite(seconds) || seconds < 0) return "00:00";
  const total = Math.floor(seconds);
  const mm = Math.floor(total / 60).toString().padStart(2, "0");
  const ss = (total % 60).toString().padStart(2, "0");
  return `${mm}:${ss}`;
}

function scoreTierClass(score: number): string {
  if (score >= 90) return "tier-excellent";
  if (score >= 80) return "tier-good";
  if (score >= 70) return "tier-warning";
  return "tier-critical";
}

function timeTierClass(seconds: number): string {
  if (seconds <= 6) return "tier-excellent";
  if (seconds <= 10) return "tier-good";
  if (seconds <= 15) return "tier-warning";
  return "tier-critical";
}

export function DraftPreview({ draft, token, userId }: Props) {
  const [copied, setCopied] = useState(false);
  const [ttsTone, setTtsTone] = useState("professional");
  const [processingTts, setProcessingTts] = useState(false);
  const [playing, setPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [audioSignature, setAudioSignature] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const signature = `${draft?.request_id || draft?.draft_text || ""}::${ttsTone}`;
  const processingSeconds = draft ? Number((draft.latency_ms / 1000).toFixed(2)) : 0;
  const preloadingRef = useRef(false);

  useEffect(() => {
    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
      }
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl);
      }
    };
  }, [audioUrl]);

  useEffect(() => {
    if (!draft) {
      if (audioRef.current) {
        audioRef.current.pause();
      }
      setPlaying(false);
      setCurrentTime(0);
      setDuration(0);
      setAudioSignature(null);
    }
  }, [draft]);

  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.pause();
    }
    setPlaying(false);
    setCurrentTime(0);
    setDuration(0);
    setAudioSignature(null);
  }, [ttsTone, draft?.request_id, draft?.draft_text]);

  useEffect(() => {
    if (!draft?.draft_text?.trim()) return;
    if (preloadingRef.current) return;
    preloadingRef.current = true;
    void ensureTtsAudio(true).finally(() => {
      preloadingRef.current = false;
    });
  }, [draft?.request_id, draft?.draft_text, ttsTone]);

  async function handleCopy() {
    const text = draft?.draft_text?.trim();
    if (!text) return;
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1600);
    } catch {
      showErrorPopup("Could not copy the draft right now.", "Copy failed");
    }
  }

  async function ensureTtsAudio(silent = false): Promise<HTMLAudioElement | null> {
    if (!draft?.draft_text?.trim()) {
      if (!silent) {
        showErrorPopup("Generate a draft first before using text-to-speech.", "No draft available");
      }
      return null;
    }
    if (audioRef.current && audioSignature === signature) {
      return audioRef.current;
    }
    setProcessingTts(true);
    try {
      const result = await invokeMcpTool(token, "tool.voice.speak", userId, {
        request_id: `tts-${Date.now()}`,
        user_id: userId,
        text: draft.draft_text,
        persona_id: ttsTone
      });
      const audioBase64 = String(result.result?.audio_base64 || "");
      const mimeType = String(result.result?.mime_type || "audio/mpeg");
      if (!audioBase64) {
        throw new Error("Audio output was empty.");
      }
      const blob = base64ToBlob(audioBase64, mimeType);
      const nextUrl = URL.createObjectURL(blob);
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl);
      }
      setAudioUrl(nextUrl);

      if (audioRef.current) {
        audioRef.current.pause();
      }
      const audio = new Audio(nextUrl);
      audioRef.current = audio;
      setAudioSignature(signature);
      audio.ontimeupdate = () => setCurrentTime(audio.currentTime || 0);
      audio.onloadedmetadata = () => setDuration(audio.duration || 0);
      audio.onended = () => setPlaying(false);
      audio.onpause = () => setPlaying(false);
      return audio;
    } catch (err) {
      setPlaying(false);
      if (!silent) {
        showErrorPopup(err instanceof Error ? err.message : "Text-to-speech failed.", "Playback error");
      }
      return null;
    } finally {
      setProcessingTts(false);
    }
  }

  async function waitUntilPlayable(audio: HTMLAudioElement): Promise<void> {
    if (audio.readyState >= 2) return;
    await new Promise<void>((resolve) => {
      const onCanPlay = () => {
        audio.removeEventListener("canplay", onCanPlay);
        resolve();
      };
      audio.addEventListener("canplay", onCanPlay, { once: true });
    });
  }

  async function togglePlayPause() {
    let audio = audioRef.current;
    if (!audio || audioSignature !== signature) {
      audio = await ensureTtsAudio();
      if (!audio) return;
    }
    if (playing) {
      audio.pause();
      setPlaying(false);
      return;
    }
    try {
      await waitUntilPlayable(audio);
      await audio.play();
      setPlaying(true);
    } catch {
      showErrorPopup("Playback is not ready yet. Please press Play once more.", "Audio not ready");
      setPlaying(false);
    }
  }

  function stopPlayback() {
    const audio = audioRef.current;
    if (!audio) return;
    audio.pause();
    audio.currentTime = 0;
    setCurrentTime(0);
    setPlaying(false);
  }

  function seekTo(value: number) {
    const audio = audioRef.current;
    if (!audio || !Number.isFinite(value)) return;
    audio.currentTime = value;
    setCurrentTime(value);
  }

  return (
    <section className="card compose-card">
      <h2>Email Preview</h2>
      <p className="meta">Readable output with copy and text-to-speech controls.</p>

      <article className="draft-render" aria-live="polite">
        {draft?.draft_text ? (
          draft.draft_text.split("\n").map((line, idx) => (
            <p key={`${idx}-${line}`}>{line || "\u00a0"}</p>
          ))
        ) : (
          <p className="meta">Generated draft appears here...</p>
        )}
        <button
          type="button"
          className="copy-fab"
          onClick={handleCopy}
          disabled={!draft?.draft_text}
          aria-label="Copy draft to clipboard"
          title={copied ? "Copied" : "Copy to clipboard"}
        >
          {copied ? "✓" : "⧉"}
        </button>
      </article>

      <div className="draft-actions">
        <div className="tts-row">
          <label htmlFor="tts-tone">Voice style</label>
          <select id="tts-tone" value={ttsTone} onChange={(e) => setTtsTone(e.target.value)}>
            <option value="professional">Professional</option>
            <option value="friendly">Friendly</option>
            <option value="narrative">Narrative</option>
            <option value="calm">Calm</option>
          </select>
          <button type="button" onClick={togglePlayPause} disabled={processingTts || !draft?.draft_text}>
            {processingTts ? "Loading..." : playing ? "Pause" : "Play"}
          </button>
          <button type="button" onClick={stopPlayback} disabled={processingTts || !draft?.draft_text}>
            Stop
          </button>
        </div>

        <div className="timeline-row">
          <span className="meta">{formatClock(currentTime)}</span>
          <input
            type="range"
            min={0}
            max={duration || 0}
            value={Math.min(currentTime, duration || 0)}
            step={0.1}
            onChange={(e) => seekTo(Number(e.target.value))}
            disabled={!audioRef.current || !duration}
          />
          <span className="meta">{formatClock(duration)}</span>
        </div>
      </div>

      {draft ? (
        <section className="metrics-grid" aria-label="Draft quality metrics">
          <div className="metric-chip">
            <span className="metric-chip-label">Time</span>
            <span className={`metric-bubble ${timeTierClass(processingSeconds)}`}>{processingSeconds}s</span>
          </div>
          <div className="metric-chip">
            <span className="metric-chip-label">Clarity</span>
            <span className={`metric-bubble ${scoreTierClass(draft.judge_scores.clarity)}`}>{draft.judge_scores.clarity}</span>
          </div>
          <div className="metric-chip">
            <span className="metric-chip-label">Tone</span>
            <span className={`metric-bubble ${scoreTierClass(draft.judge_scores.tone_match)}`}>{draft.judge_scores.tone_match}</span>
          </div>
          <div className="metric-chip">
            <span className="metric-chip-label">Factuality</span>
            <span className={`metric-bubble ${scoreTierClass(draft.judge_scores.factuality)}`}>{draft.judge_scores.factuality}</span>
          </div>
          <div className="metric-chip">
            <span className="metric-chip-label">Overall</span>
            <span className={`metric-bubble ${scoreTierClass(draft.judge_scores.overall)}`}>{draft.judge_scores.overall}</span>
          </div>
        </section>
      ) : null}
    </section>
  );
}
