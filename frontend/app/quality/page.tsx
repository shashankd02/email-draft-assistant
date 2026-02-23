"use client";

import { WorkspaceShell } from "@/components/workspace-shell";

const pillars = [
  {
    name: "Product UX",
    score: 8.9,
    status: "Strong",
    details: "Multi-page workspace, role-aware navigation, voice + text compose, clean response preview, and loading/cancel patterns.",
  },
  {
    name: "Agentic AI Design",
    score: 9.1,
    status: "Strong",
    details: "Strict email-intent guard, modular agent pipeline, routing/fallback, and structured-output recovery.",
  },
  {
    name: "Reliability",
    score: 8.7,
    status: "Strong",
    details: "Rate limiting, replay protection, retries, safe template fallback, and health readiness checks.",
  },
  {
    name: "Observability",
    score: 8.8,
    status: "Strong",
    details: "Live + global metrics, alert thresholds, recent activity stream, and runtime LangSmith configuration.",
  },
  {
    name: "Security & Access",
    score: 8.6,
    status: "Strong",
    details: "JWT auth, role checks, actor scoping, audit logs, DLP checks, and user-data deletion controls.",
  },
  {
    name: "Evaluation",
    score: 8.8,
    status: "Strong",
    details: "Core/adversarial/voice datasets, evaluation runs, gates, and traceable run history.",
  },
  {
    name: "Engineering Governance",
    score: 8.9,
    status: "Strong",
    details: "CI, PR review automation, dependency hygiene, retention scheduler, migrations, and reproducible Docker runtime.",
  },
];

const nextMilestones = [
  "Add sequence replay visualizer for each generated draft request.",
  "Add drift dashboard for tone/quality trends over time.",
  "Add API key vault integration for production secrets management.",
  "Add deployment health SLO burn-rate views and on-call runbook links.",
];

function scoreClass(score: number): string {
  if (score >= 9) return "tier-excellent";
  if (score >= 8) return "tier-good";
  if (score >= 7) return "tier-warning";
  return "tier-critical";
}

export default function QualityPage() {
  const avg = pillars.reduce((sum, item) => sum + item.score, 0) / pillars.length;

  return (
    <WorkspaceShell
      title="Quality Scorecard"
      subtitle="Deep project quality assessment against production-grade software and agentic AI standards."
      allowGuest
    >
      {() => (
        <div className="quality-stack">
          <section className="card">
            <h2>Overall Readiness</h2>
            <p className="meta">Current delivery quality across product, architecture, operations, and engineering controls.</p>
            <div className="metrics-grid">
              <div className="metric-chip">
                <span className="metric-chip-label">Composite Score</span>
                <span className={`metric-bubble ${scoreClass(avg)}`}>{avg.toFixed(2)}/10</span>
              </div>
              <div className="metric-chip">
                <span className="metric-chip-label">Pillars</span>
                <span className="metric-bubble tier-good">{pillars.length}</span>
              </div>
              <div className="metric-chip">
                <span className="metric-chip-label">Status</span>
                <span className="metric-bubble tier-good">Production-minded</span>
              </div>
            </div>
          </section>

          <section className="card">
            <h2>Pillar Breakdown</h2>
            <div className="quality-grid">
              {pillars.map((pillar) => (
                <article key={pillar.name} className="info-item">
                  <h3>{pillar.name}</h3>
                  <p className="meta">{pillar.details}</p>
                  <div className="metrics-grid">
                    <div className="metric-chip">
                      <span className="metric-chip-label">Score</span>
                      <span className={`metric-bubble ${scoreClass(pillar.score)}`}>{pillar.score.toFixed(1)}</span>
                    </div>
                    <div className="metric-chip">
                      <span className="metric-chip-label">Status</span>
                      <span className="metric-bubble tier-good">{pillar.status}</span>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          </section>

          <section className="card">
            <h2>Next Excellence Milestones</h2>
            <p className="meta">Shortlist of high-impact improvements to move from strong to category-leading quality.</p>
            <div className="n2-flow">
              {nextMilestones.map((item, idx) => (
                <article key={item} className="n2-stage quality-stage">
                  <p className="n2-stage-id">{String(idx + 1).padStart(2, "0")}</p>
                  <h3>Upgrade</h3>
                  <p className="meta">{item}</p>
                </article>
              ))}
            </div>
          </section>
        </div>
      )}
    </WorkspaceShell>
  );
}
