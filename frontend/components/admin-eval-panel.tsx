"use client";

import { useState } from "react";
import { FullscreenLoader } from "@/components/fullscreen-loader";
import { listEvalRuns, runEvaluation, type EvalRunSummary } from "@/lib/api";
import { showErrorPopup, showSuccessPopup } from "@/lib/error-popup";

type Props = {
  token: string;
  role: "user" | "admin";
};

export function AdminEvalPanel({ token, role }: Props) {
  const [maxCases, setMaxCases] = useState(3);
  const [dataset, setDataset] = useState<"core" | "adversarial" | "voice">("core");
  const [running, setRunning] = useState(false);
  const [loadingRuns, setLoadingRuns] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastRunAt, setLastRunAt] = useState<string | null>(null);
  const [runs, setRuns] = useState<EvalRunSummary[]>([]);
  const [controller, setController] = useState<AbortController | null>(null);

  if (role !== "admin") {
    return null;
  }

  async function handleRunEvaluation() {
    if (!token) {
      const msg = "Issue token first.";
      setError(msg);
      showErrorPopup(msg, "Authentication required");
      return;
    }
    const nextController = new AbortController();
    setController(nextController);
    setRunning(true);
    setError(null);
    try {
      const result = await runEvaluation(token, dataset, maxCases, nextController.signal);
      setLastRunAt(new Date().toLocaleString());
      await handleLoadRuns(nextController.signal);
      showSuccessPopup("Evaluation run completed.", "Evaluation done");
    } catch (err) {
      if (err instanceof Error && err.name === "AbortError") return;
      const msg = err instanceof Error ? err.message : "Evaluation run failed";
      setError(msg);
      showErrorPopup(msg, "Evaluation failed");
    } finally {
      setController(null);
      setRunning(false);
    }
  }

  async function handleLoadRuns(signal?: AbortSignal) {
    if (!token) {
      const msg = "Issue token first.";
      setError(msg);
      showErrorPopup(msg, "Authentication required");
      return;
    }
    const nextController = signal ? null : new AbortController();
    if (nextController) setController(nextController);
    setLoadingRuns(true);
    setError(null);
    try {
      const result = await listEvalRuns(token, 10, signal ?? nextController?.signal);
      setRuns(result.runs);
    } catch (err) {
      if (err instanceof Error && err.name === "AbortError") return;
      const msg = err instanceof Error ? err.message : "Failed to load runs";
      setError(msg);
      showErrorPopup(msg, "Load failed");
    } finally {
      if (nextController) setController(null);
      setLoadingRuns(false);
    }
  }

  function cancelCurrentOperation() {
    controller?.abort();
    setController(null);
    setRunning(false);
    setLoadingRuns(false);
  }

  return (
    <section className="card" style={{ marginBottom: "1rem" }}>
      <FullscreenLoader
        open={running || loadingRuns}
        title={running ? "Running evaluation..." : "Loading evaluation runs..."}
        subtitle="Please wait while the platform refreshes quality insights."
        onCancel={cancelCurrentOperation}
      />

      <h2>Admin Evaluation</h2>
      <p className="meta">Run and inspect evaluation snapshots.</p>

      <label htmlFor="maxCases">Max Cases</label>
      <input
        id="maxCases"
        type="number"
        min={1}
        max={20}
        value={maxCases}
        onChange={(e) => setMaxCases(Number(e.target.value || 1))}
      />
      <label htmlFor="evalDataset">Dataset</label>
      <select id="evalDataset" value={dataset} onChange={(e) => setDataset(e.target.value as "core" | "adversarial" | "voice")}>
        <option value="core">core</option>
        <option value="adversarial">adversarial</option>
        <option value="voice">voice</option>
      </select>

      <div style={{ display: "grid", gap: "0.5rem", gridTemplateColumns: "1fr 1fr", marginTop: "0.5rem" }}>
        <button type="button" onClick={handleRunEvaluation} disabled={running}>
          {running ? "Running..." : "Run Evaluation"}
        </button>
        <button type="button" onClick={() => void handleLoadRuns()} disabled={loadingRuns}>
          {loadingRuns ? "Loading..." : "Load Recent Runs"}
        </button>
      </div>

      {lastRunAt ? <p className="meta">Last run completed: {lastRunAt}</p> : null}
      {runs.length > 0 ? (
        <div style={{ marginTop: "0.8rem" }}>
          <h3 style={{ margin: 0, marginBottom: "0.5rem" }}>Recent Runs</h3>
          {runs.map((run) => (
            <div key={run.run_id} style={{ border: "1px solid var(--border)", borderRadius: "8px", padding: "0.6rem", marginBottom: "0.4rem" }}>
              <div className="meta">dataset: {run.dataset} | cases: {run.total_cases}</div>
              <div className="meta">status: {run.passed ? "pass" : "needs attention"} | avg overall: {run.avg_overall}</div>
              <div className="meta">created: {new Date(run.created_at).toLocaleString()}</div>
            </div>
          ))}
        </div>
      ) : null}
    </section>
  );
}
