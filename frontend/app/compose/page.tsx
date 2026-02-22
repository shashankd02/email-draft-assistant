"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import { AdminEvalPanel } from "@/components/admin-eval-panel";
import { DraftForm } from "@/components/draft-form";
import { DraftPreview } from "@/components/draft-preview";
import type { DraftResponse } from "@/lib/api";
import { clearSessionAuth, loadSessionAuth, type SessionAuth } from "@/lib/session";

export default function ComposePage() {
  const router = useRouter();
  const [draft, setDraft] = useState<DraftResponse | null>(null);
  const [auth, setAuth] = useState<SessionAuth | null>(null);

  useEffect(() => {
    const session = loadSessionAuth();
    if (!session) {
      router.push("/");
      return;
    }
    setAuth(session);
  }, [router]);

  useEffect(() => {
    if (!auth) return;
    const timer = window.setInterval(() => {
      const current = loadSessionAuth();
      if (!current) {
        router.push("/");
      }
    }, 10000);
    return () => window.clearInterval(timer);
  }, [auth, router]);

  function handleLogout() {
    clearSessionAuth();
    router.push("/");
  }

  if (!auth) {
    return null;
  }

  return (
    <main className="compose-main">
      <header className="workspace-hero">
        <div className="workspace-title">
          <Image src="/logo-mark.svg" alt="Email Assistant logo" className="workspace-logo" width={44} height={44} />
          <div>
            <p className="eyebrow">Agentic Compose Studio</p>
            <h1>AI-Powered Email Assistant</h1>
            <p className="meta">Authenticated as {auth.userId} ({auth.role})</p>
          </div>
        </div>
        <button type="button" className="logout-btn" onClick={handleLogout}>Logout</button>
      </header>

      <AdminEvalPanel token={auth.token} role={auth.role} />

      <div className="grid compose-grid">
        <DraftForm onDraft={setDraft} userId={auth.userId} token={auth.token} />
        <DraftPreview draft={draft} token={auth.token} userId={auth.userId} />
      </div>
    </main>
  );
}
