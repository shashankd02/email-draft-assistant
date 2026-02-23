"use client";

import Link from "next/link";
import { WorkspaceShell } from "@/components/workspace-shell";

const workflowSteps = [
  { id: "01", name: "Input Parser", purpose: "Validate payload and normalize request structure." },
  { id: "02", name: "Intent Guard", purpose: "Reject non-email requests and enforce strict email intent." },
  { id: "03", name: "Context Enrichment", purpose: "Optional web/tool context via MCP with citations." },
  { id: "04", name: "Prompt Refiner", purpose: "Transform raw input into a draft-ready instruction." },
  { id: "05", name: "Personalization", purpose: "Apply user profile preferences and prior context." },
  { id: "06", name: "Tone Stylist", purpose: "Enforce selected tone and communication style." },
  { id: "07", name: "Draft Writer", purpose: "Generate schema-constrained draft with fail-safe fallback." },
  { id: "08", name: "Review Validator", purpose: "Score clarity/tone/factuality and quality checks." },
  { id: "09", name: "Router + Memory", purpose: "Persist thread memory and route retry/fallback outcomes." },
];

export default function WorkflowsPage() {
  return (
    <WorkspaceShell
      title="Agent Workflows"
      subtitle="Detailed workflow stages for intent guard, generation, validation, and memory routing."
      allowGuest
    >
      {() => (
        <div className="grid ops-grid">
          <section className="card">
            <h2>Pipeline View</h2>
            <p className="meta">Visual stage flow with strict guardrails and quality gates.</p>
            <div className="workflow-ribbon">
              {workflowSteps.map((step) => (
                <article key={step.id} className="workflow-node">
                  <span className="workflow-id">{step.id}</span>
                  <h3>{step.name}</h3>
                  <p className="meta">{step.purpose}</p>
                  <Link href={`/architecture-map#lane-agent`} className="workflow-link">
                    View in Architecture Map
                  </Link>
                </article>
              ))}
            </div>
          </section>

          <section className="card">
            <h2>Control Gates</h2>
            <div className="info-grid">
              <article className="info-item">
                <h3>Pre-Generation Gate</h3>
                <p className="meta">Input validation, intent filtering, and safety checks.</p>
              </article>
              <article className="info-item">
                <h3>Generation Gate</h3>
                <p className="meta">Structured output validation, retries, and deterministic fallback.</p>
              </article>
              <article className="info-item">
                <h3>Post-Generation Gate</h3>
                <p className="meta">Quality scoring, observability metrics, and memory persistence.</p>
              </article>
              <article className="info-item">
                <h3>Operational Gate</h3>
                <p className="meta">Rate limiting, replay protection, audit logging, and retention.</p>
              </article>
            </div>
          </section>
        </div>
      )}
    </WorkspaceShell>
  );
}
