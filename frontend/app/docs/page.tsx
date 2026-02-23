"use client";

import { useEffect, useState } from "react";

import { WorkspaceShell } from "@/components/workspace-shell";
import { getHealth, type HealthResponse } from "@/lib/api";
import { showErrorPopup } from "@/lib/error-popup";

const apiRoot = (process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8002/api/v1").replace(/\/api\/v1\/?$/, "");

const endpointGroups = [
  { group: "Auth", items: ["POST /api/v1/auth/register", "POST /api/v1/auth/login", "POST /api/v1/auth/token"] },
  { group: "Drafting", items: ["POST /api/v1/draft/generate", "POST /api/v1/draft/feedback"] },
  { group: "Voice + MCP", items: ["POST /api/v1/voice/transcribe", "GET /api/v1/mcp/tools", "POST /api/v1/mcp/invoke"] },
  { group: "Evaluation", items: ["GET /api/v1/evaluation/datasets", "POST /api/v1/evaluation/run", "GET /api/v1/evaluation/runs"] },
  { group: "Operations", items: ["GET /api/v1/health", "GET /api/v1/observability/metrics", "GET /api/v1/observability/alerts"] },
];

export default function DocsPage() {
  const [health, setHealth] = useState<HealthResponse | null>(null);

  useEffect(() => {
    getHealth()
      .then(setHealth)
      .catch((err) => {
        showErrorPopup(err instanceof Error ? err.message : "Unable to load health data.", "Health check failed");
      });
  }, []);

  return (
    <WorkspaceShell
      title="API Docs and Operations"
      subtitle="Direct access to Swagger, health readiness, and endpoint map."
      allowGuest
    >
      {() => (
        <div className="grid ops-grid">
          <section className="card">
            <h2>Documentation Links</h2>
            <p className="meta">Open API documentation in a user-friendly view.</p>
            <div className="doc-links">
              <a href={`${apiRoot}/docs`} target="_blank" rel="noreferrer">Swagger UI</a>
            </div>
          </section>

          <section className="card">
            <h2>Service Health</h2>
            {health ? (
              <div className="info-grid">
                <article className="info-item">
                  <h3>Status</h3>
                  <p className="meta">{health.status}</p>
                </article>
                <article className="info-item">
                  <h3>Strict Mode</h3>
                  <p className="meta">{health.strict_provider_mode ? "enabled" : "disabled"}</p>
                </article>
                <article className="info-item">
                  <h3>Strict Ready</h3>
                  <p className="meta">{health.strict_provider_ready ? "yes" : "no"}</p>
                </article>
              </div>
            ) : (
              <p className="meta">Loading health status...</p>
            )}
          </section>

          <section className="card">
            <h2>Endpoint Map</h2>
            <div className="info-grid">
              {endpointGroups.map((group) => (
                <article key={group.group} className="info-item">
                  <h3>{group.group}</h3>
                  {group.items.map((item) => (
                    <p className="meta" key={item}>{item}</p>
                  ))}
                </article>
              ))}
            </div>
          </section>
        </div>
      )}
    </WorkspaceShell>
  );
}
