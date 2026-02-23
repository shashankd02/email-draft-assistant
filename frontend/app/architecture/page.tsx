"use client";

import Link from "next/link";
import { WorkspaceShell } from "@/components/workspace-shell";

export default function ArchitecturePage() {
  return (
    <WorkspaceShell
      title="System Architecture"
      subtitle="High-level and component-level architecture mapped to the implemented application."
      allowGuest
    >
      {() => (
        <div className="grid ops-grid">
          <section className="card">
            <h2>End-to-End Flow Diagram</h2>
            <p className="meta">User journey, orchestration path, providers, and observability planes.</p>
            <div className="e2e-diagram-shell">
              <svg className="e2e-diagram" viewBox="0 0 1200 290" role="img" aria-label="End to end flow diagram">
                <defs>
                  <marker id="e2e-arrow" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto">
                    <polygon points="0 0, 10 4, 0 8" fill="#8ecfff" />
                  </marker>
                </defs>

                <path d="M 110 95 H 1090" className="e2e-backbone" />

                <g className="e2e-node">
                  <rect x="40" y="58" width="205" height="74" rx="12" />
                  <text x="142" y="88" textAnchor="middle" className="e2e-title">01 User Interaction</text>
                  <text x="142" y="108" textAnchor="middle" className="e2e-sub">Compose input (text/voice)</text>
                </g>

                <g className="e2e-node">
                  <rect x="320" y="58" width="205" height="74" rx="12" />
                  <text x="422" y="88" textAnchor="middle" className="e2e-title">02 API + Guards</text>
                  <text x="422" y="108" textAnchor="middle" className="e2e-sub">Auth, limits, replay checks</text>
                </g>

                <g className="e2e-node">
                  <rect x="600" y="58" width="205" height="74" rx="12" />
                  <text x="702" y="88" textAnchor="middle" className="e2e-title">03 Agent Graph</text>
                  <text x="702" y="108" textAnchor="middle" className="e2e-sub">Parse, refine, write, validate</text>
                </g>

                <g className="e2e-node">
                  <rect x="880" y="58" width="250" height="74" rx="12" />
                  <text x="1005" y="88" textAnchor="middle" className="e2e-title">04 Tools + Providers + Data</text>
                  <text x="1005" y="108" textAnchor="middle" className="e2e-sub">MCP, OpenAI/Deepgram, Postgres/Chroma</text>
                </g>

                <line x1="245" y1="95" x2="335" y2="95" className="e2e-link" markerEnd="url(#e2e-arrow)" />
                <line x1="525" y1="95" x2="615" y2="95" className="e2e-link" markerEnd="url(#e2e-arrow)" />
                <line x1="805" y1="95" x2="895" y2="95" className="e2e-link" markerEnd="url(#e2e-arrow)" />

                <line x1="142" y1="132" x2="142" y2="170" className="e2e-drop" />
                <line x1="422" y1="132" x2="422" y2="170" className="e2e-drop" />
                <line x1="702" y1="132" x2="702" y2="170" className="e2e-drop" />
                <line x1="1005" y1="132" x2="1005" y2="170" className="e2e-drop" />

                <text x="142" y="192" textAnchor="middle" className="e2e-note">UI Layer</text>
                <text x="422" y="192" textAnchor="middle" className="e2e-note">API Layer</text>
                <text x="702" y="192" textAnchor="middle" className="e2e-note">Agent Layer</text>
                <text x="1005" y="192" textAnchor="middle" className="e2e-note">Execution + Data Layer</text>
              </svg>
            </div>
          </section>

          <section className="card">
            <h2>Detailed Interactive Map</h2>
            <p className="meta">Open the dedicated map page for zoomable connected blocks and deep architecture walkthrough.</p>
            <Link href="/architecture-map" className="workflow-link" style={{ width: "fit-content" }}>
              Open Architecture Map
            </Link>
          </section>

          <section className="card">
            <h2>Agent Pipeline</h2>
            <div className="timeline-list">
              <article className="timeline-item">
                <h3>Input Parser + Intent Guard</h3>
                <p className="meta">Rejects non-email inputs and incomplete requests before model usage.</p>
              </article>
              <article className="timeline-item">
                <h3>Context + Prompt Refinement</h3>
                <p className="meta">Enriches context through MCP search and transforms prompt into draft-ready instruction.</p>
              </article>
              <article className="timeline-item">
                <h3>Draft + Validator + Router</h3>
                <p className="meta">Generates structured output, applies safety/quality checks, and routes retry/fallback when needed.</p>
              </article>
            </div>
          </section>

          <section className="card">
            <h2>Data and Control Planes</h2>
            <div className="info-grid">
              <article className="info-item">
                <h3>Control Plane</h3>
                <p className="meta">Auth, policy flags, retry strategy, timeout limits, and role-based access.</p>
              </article>
              <article className="info-item">
                <h3>Data Plane</h3>
                <p className="meta">Drafts, judge scores, transcripts, thread memory, and eval runs in PostgreSQL.</p>
              </article>
              <article className="info-item">
                <h3>Retrieval Plane</h3>
                <p className="meta">Vector context in Chroma for memory and personalization recall.</p>
              </article>
              <article className="info-item">
                <h3>Observability Plane</h3>
                <p className="meta">Live workflow counters + global DB metrics + LangSmith tracing status.</p>
              </article>
            </div>
          </section>
        </div>
      )}
    </WorkspaceShell>
  );
}
