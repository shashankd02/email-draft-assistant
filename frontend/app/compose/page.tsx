"use client";

import { useState } from "react";
import { DraftForm } from "@/components/draft-form";
import { DraftPreview } from "@/components/draft-preview";
import { WorkspaceShell } from "@/components/workspace-shell";
import type { DraftResponse } from "@/lib/api";

export default function ComposePage() {
  const [draft, setDraft] = useState<DraftResponse | null>(null);

  return (
    <WorkspaceShell
      title="Compose Email Draft"
      subtitle="Strict email intent pipeline with tone control, voice input, and quality scoring."
    >
      {(auth) => (
        auth ? (
        <div className="grid compose-grid">
          <DraftForm onDraft={setDraft} userId={auth.userId} token={auth.token} />
          <DraftPreview draft={draft} token={auth.token} userId={auth.userId} />
        </div>
        ) : null
      )}
    </WorkspaceShell>
  );
}
