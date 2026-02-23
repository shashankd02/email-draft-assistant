"use client";

import { AdminEvalPanel } from "@/components/admin-eval-panel";
import { WorkspaceShell } from "@/components/workspace-shell";

export default function EvaluationPage() {
  return (
    <WorkspaceShell
      title="Evaluation Center"
      subtitle="Dataset-driven quality evaluation for core, adversarial, and voice scenarios."
    >
      {(auth) => (
        auth ? (
        <div className="grid ops-grid">
          <section className="card">
            <h2>Evaluation Overview</h2>
            <p className="meta">
              This panel validates production quality by running controlled datasets and recording score trends.
            </p>
            <div className="info-grid">
              <article className="info-item">
                <h3>Core Dataset</h3>
                <p className="meta">Functional quality checks for standard email drafting requests.</p>
              </article>
              <article className="info-item">
                <h3>Adversarial Dataset</h3>
                <p className="meta">Prompt-injection and safety hardening checks.</p>
              </article>
              <article className="info-item">
                <h3>Voice Dataset</h3>
                <p className="meta">Voice-originated transcript quality and structure checks.</p>
              </article>
            </div>
          </section>
          <AdminEvalPanel token={auth.token} role={auth.role} />
        </div>
        ) : null
      )}
    </WorkspaceShell>
  );
}
