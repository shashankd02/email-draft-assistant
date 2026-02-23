"use client";

import { useCallback, useEffect, useState } from "react";

import { FullscreenLoader } from "@/components/fullscreen-loader";
import { WorkspaceShell } from "@/components/workspace-shell";
import { configureLangSmith, getObservabilityAlerts, getObservabilityMetrics, type ObservabilityAlertsResponse, type ObservabilityMetricsResponse } from "@/lib/api";
import { showErrorPopup, showSuccessPopup } from "@/lib/error-popup";
import type { SessionAuth } from "@/lib/session";

function boolClass(value: boolean): string {
  return value ? "tier-critical" : "tier-excellent";
}

function formatAlertName(name: string): string {
  return name
    .replace(/_/g, " ")
    .replace(/\b\w/g, (m) => m.toUpperCase());
}

function maskUser(userId: string): string {
  if (userId.length <= 3) return userId;
  return `${userId.slice(0, 3)}***`;
}

export default function ObservabilityPage() {
  return (
    <WorkspaceShell
      title="Observability"
      subtitle="Live operational metrics, threshold checks, and system status for production monitoring."
    >
      {(auth) => (auth ? <ObservabilityContent auth={auth} /> : null)}
    </WorkspaceShell>
  );
}

function ObservabilityContent({ auth }: { auth: SessionAuth }) {
  const [metrics, setMetrics] = useState<ObservabilityMetricsResponse | null>(null);
  const [alerts, setAlerts] = useState<ObservabilityAlertsResponse | null>(null);
  const [windowRange, setWindowRange] = useState<"24h" | "7d" | "30d">("24h");
  const [loading, setLoading] = useState(false);
  const [controller, setController] = useState<AbortController | null>(null);
  const [langsmithEnabled, setLangsmithEnabled] = useState(true);
  const [langsmithProject, setLangsmithProject] = useState("email-assistant");
  const [langsmithApiKey, setLangsmithApiKey] = useState("");
  const [savingLangsmith, setSavingLangsmith] = useState(false);

  const loadObservability = useCallback(async (token: string, window: "24h" | "7d" | "30d") => {
    const nextController = new AbortController();
    setController(nextController);
    setLoading(true);
    Promise.all([
      getObservabilityMetrics(token, window, nextController.signal),
      getObservabilityAlerts(token, window, nextController.signal),
    ])
      .then(([metricsResponse, alertsResponse]) => {
        setMetrics(metricsResponse);
        setAlerts(alertsResponse);
        setLangsmithEnabled(metricsResponse.integrations.langsmith.tracing_flag);
        setLangsmithProject(metricsResponse.integrations.langsmith.project || "email-assistant");
      })
      .catch((err) => {
        if (err instanceof Error && err.name === "AbortError") return;
        showErrorPopup(err instanceof Error ? err.message : "Unable to load observability data.", "Observability unavailable");
      })
      .finally(() => {
        setLoading(false);
        setController(null);
      });
  }, []);

  useEffect(() => {
    if (auth.role !== "admin") return;
    void loadObservability(auth.token, windowRange);
  }, [auth.role, auth.token, loadObservability, windowRange]);

  function cancelLoading() {
    controller?.abort();
    setController(null);
    setLoading(false);
  }

  async function handleSaveLangSmith() {
    setSavingLangsmith(true);
    try {
      const result = await configureLangSmith(auth.token, {
        enabled: langsmithEnabled,
        project: langsmithProject.trim() || undefined,
        api_key: langsmithApiKey.trim() || undefined,
      });
      showSuccessPopup(
        result.langsmith.enabled
          ? "LangSmith is enabled for runtime observability."
          : "LangSmith settings were saved, but API key/tracing is incomplete.",
        "LangSmith updated",
      );
      setLangsmithApiKey("");
      await loadObservability(auth.token, windowRange);
    } catch (err) {
      showErrorPopup(err instanceof Error ? err.message : "Unable to save LangSmith settings.", "LangSmith setup failed");
    } finally {
      setSavingLangsmith(false);
    }
  }

  if (auth.role !== "admin") {
    return (
      <section className="card">
        <h2>Observability Access</h2>
        <p className="meta">Admin role is required to view live observability metrics and alerts.</p>
      </section>
    );
  }

  return (
    <div className="grid ops-grid">
      <FullscreenLoader
        open={loading}
        title="Loading observability..."
        subtitle="Fetching live and global metrics."
        onCancel={cancelLoading}
      />

      <section className="card">
        <h2>Global Usage</h2>
        <p className="meta">Cross-user metrics from persisted database records.</p>
        <label htmlFor="window-range">Time Window</label>
        <select
          id="window-range"
          value={windowRange}
          onChange={(e) => setWindowRange(e.target.value as "24h" | "7d" | "30d")}
          disabled={loading}
        >
          <option value="24h">Last 24 hours</option>
          <option value="7d">Last 7 days</option>
          <option value="30d">Last 30 days</option>
        </select>
        {metrics ? (
          <div className="info-grid">
            <article className="info-item">
              <h3>Registered Users</h3>
              <p className="meta">{metrics.global_metrics.totals.registered_users}</p>
            </article>
            <article className="info-item">
              <h3>Total Identities</h3>
              <p className="meta">{metrics.global_metrics.totals.total_identities}</p>
            </article>
            <article className="info-item">
              <h3>Total Drafts</h3>
              <p className="meta">{metrics.global_metrics.totals.drafts}</p>
            </article>
            <article className="info-item">
              <h3>Drafts ({windowRange})</h3>
              <p className="meta">{metrics.global_metrics.activity.drafts_in_window}</p>
            </article>
            <article className="info-item">
              <h3>Active Users ({windowRange})</h3>
              <p className="meta">{metrics.global_metrics.activity.active_users_in_window}</p>
            </article>
            <article className="info-item">
              <h3>Avg Quality</h3>
              <p className="meta">{metrics.global_metrics.quality.avg_overall_score}</p>
            </article>
            <article className="info-item">
              <h3>P95 Latency ({windowRange})</h3>
              <p className="meta">{metrics.global_metrics.latency.p95_latency_ms_in_window} ms</p>
            </article>
            <article className="info-item">
              <h3>Tool Invocations ({windowRange})</h3>
              <p className="meta">{metrics.global_metrics.activity.tool_invocations_in_window}</p>
            </article>
            <article className="info-item">
              <h3>Voice Transcripts ({windowRange})</h3>
              <p className="meta">{metrics.global_metrics.activity.voice_transcripts_in_window}</p>
            </article>
          </div>
        ) : (
          <p className="meta">No observability data available yet.</p>
        )}
      </section>

      <section className="card">
        <h2>Agent Observability Integrations</h2>
        <p className="meta">LangSmith tracing status for agent execution visibility.</p>
        {metrics ? (
          <div className="metrics-grid">
            <div className="metric-chip">
              <span className="metric-chip-label">LangSmith</span>
              <span className={`metric-bubble ${metrics.integrations.langsmith.enabled ? "tier-good" : "tier-warning"}`}>
                {metrics.integrations.langsmith.enabled ? "Enabled" : "Not Configured"}
              </span>
            </div>
          </div>
        ) : null}
        <div className="stacked-form" style={{ marginTop: "0.8rem" }}>
          <label htmlFor="ls-enabled">Enable Tracing</label>
          <select
            id="ls-enabled"
            value={langsmithEnabled ? "yes" : "no"}
            onChange={(e) => setLangsmithEnabled(e.target.value === "yes")}
            disabled={savingLangsmith}
          >
            <option value="yes">Yes</option>
            <option value="no">No</option>
          </select>

          <label htmlFor="ls-project">LangSmith Project</label>
          <input
            id="ls-project"
            value={langsmithProject}
            onChange={(e) => setLangsmithProject(e.target.value)}
            disabled={savingLangsmith}
            placeholder="email-assistant"
          />

          <label htmlFor="ls-api-key">LangSmith API Key (optional update)</label>
          <input
            id="ls-api-key"
            type="password"
            value={langsmithApiKey}
            onChange={(e) => setLangsmithApiKey(e.target.value)}
            disabled={savingLangsmith}
            placeholder="Paste new key to update"
          />
          <button type="button" onClick={() => void handleSaveLangSmith()} disabled={savingLangsmith}>
            {savingLangsmith ? "Saving..." : "Save LangSmith Settings"}
          </button>
          <p className="meta">This updates runtime settings. Keep `backend/.env` updated for persistence after restart.</p>
        </div>
      </section>

      <section className="card">
        <h2>Alert Status</h2>
        <p className="meta">Operational threshold checks.</p>
        {alerts ? (
          <div className="metrics-grid">
            {Object.entries(alerts.alerts).map(([name, value]) => (
              <div key={name} className="metric-chip">
                <span className="metric-chip-label">{formatAlertName(name)}</span>
                <span className={`metric-bubble ${boolClass(Boolean(value))}`}>
                  {value ? "Alert" : "OK"}
                </span>
              </div>
            ))}
          </div>
        ) : null}
      </section>

      <section className="card">
        <h2>Live Runtime Health</h2>
        <p className="meta">Current-process metrics from in-memory runtime telemetry.</p>
        {alerts ? (
          <div className="info-grid">
            <article className="info-item">
              <h3>P95 Latency</h3>
              <p className="meta">{alerts.current.live.p95_latency_ms.toFixed(2)} ms</p>
            </article>
            <article className="info-item">
              <h3>Fallback Rate</h3>
              <p className="meta">{(alerts.current.live.fallback_rate * 100).toFixed(2)}%</p>
            </article>
            <article className="info-item">
              <h3>Provider Error Rate</h3>
              <p className="meta">{(alerts.current.live.provider_error_rate * 100).toFixed(2)}%</p>
            </article>
            <article className="info-item">
              <h3>Safety Failure Rate</h3>
              <p className="meta">{(alerts.current.live.safety_failure_rate * 100).toFixed(2)}%</p>
            </article>
            <article className="info-item">
              <h3>Total Workflows</h3>
              <p className="meta">{alerts.current.live.total_workflows}</p>
            </article>
          </div>
        ) : null}
        <button type="button" onClick={() => void loadObservability(auth.token, windowRange)} disabled={loading}>
          Refresh
        </button>
      </section>

      <section className="card">
        <h2>Recent Draft Activity</h2>
        <p className="meta">Latest application-level events from draft generation workflow.</p>
        {metrics?.recent_activity?.length ? (
          <div className="activity-list">
            {metrics.recent_activity.slice(0, 12).map((item) => (
              <article key={`${item.request_id}-${item.created_at}`} className="info-item">
                <h3>{new Date(item.created_at).toLocaleString()}</h3>
                <p className="meta">
                  User {maskUser(item.user_id)} | {item.intent} | {item.tone} | {item.language.toUpperCase()} | {item.input_mode}
                </p>
                <p className="meta">
                  {item.latency_ms} ms | Score {item.overall_score ?? "n/a"} | {item.fallback_used ? "Fallback used" : "Primary path"}
                </p>
              </article>
            ))}
          </div>
        ) : (
          <p className="meta">No recent draft activity yet.</p>
        )}
      </section>
    </div>
  );
}
