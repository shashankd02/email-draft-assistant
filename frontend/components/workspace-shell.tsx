"use client";

import Image from "next/image";
import Link from "next/link";
import type { Route } from "next";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { clearSessionAuth, loadSessionAuth, type SessionAuth } from "@/lib/session";

type WorkspaceShellProps = {
  title: string;
  subtitle: string;
  children: (auth: SessionAuth | null) => React.ReactNode;
  allowGuest?: boolean;
};

const allNavItems: Array<{ href: Route; label: string; adminOnly?: boolean }> = [
  { href: "/compose", label: "Compose" },
  { href: "/architecture", label: "Architecture" },
  { href: "/architecture-map", label: "Architecture Map" },
  { href: "/workflows", label: "Workflows" },
  { href: "/quality", label: "Quality" },
  { href: "/observability", label: "Observability", adminOnly: true },
  { href: "/evaluation", label: "Evaluation", adminOnly: true },
  { href: "/docs", label: "API Docs" },
];

const apiRoot = (process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8002/api/v1").replace(/\/api\/v1\/?$/, "");

export function WorkspaceShell({ title, subtitle, children, allowGuest = false }: WorkspaceShellProps) {
  const router = useRouter();
  const pathname = usePathname();
  const [auth, setAuth] = useState<SessionAuth | null>(null);

  useEffect(() => {
    const session = loadSessionAuth();
    if (!session && !allowGuest) {
      router.push("/");
      return;
    }
    setAuth(session);
  }, [router, allowGuest]);

  useEffect(() => {
    if (!auth || allowGuest) return;
    const timer = window.setInterval(() => {
      const current = loadSessionAuth();
      if (!current) {
        router.push("/");
      }
    }, 10000);
    return () => window.clearInterval(timer);
  }, [auth, router, allowGuest]);

  function handleLogout() {
    clearSessionAuth();
    router.push("/");
  }

  if (!auth && !allowGuest) return null;
  const navItems = allNavItems.filter((item) => {
    if (item.adminOnly) return auth?.role === "admin";
    return true;
  });

  return (
    <main className="workspace-main">
      <aside className="workspace-sidebar">
        <div className="workspace-brand">
          <Image src="/logo-mark.svg" alt="Email Assistant logo" width={32} height={32} className="workspace-brand-logo" />
          <div>
            <p className="eyebrow">AI Email Assistant</p>
            <p className="workspace-brand-title">Control Center</p>
          </div>
        </div>

        <nav className="workspace-nav">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={pathname === item.href ? "workspace-nav-link active" : "workspace-nav-link"}
            >
              {item.label}
            </Link>
          ))}
        </nav>

        <div className="workspace-sidebar-footer">
          {auth ? (
            <>
              <p className="meta">Signed in as {auth.userId}</p>
              <p className="meta">Role: {auth.role}</p>
              <button type="button" className="logout-btn" onClick={handleLogout}>
                Logout
              </button>
            </>
          ) : (
            <>
              <p className="meta">Guest mode</p>
              <p className="meta">Login for compose, evaluation, and admin controls.</p>
              <button type="button" className="logout-btn" onClick={() => router.push("/")}>
                Login
              </button>
            </>
          )}
        </div>
      </aside>

      <section className="workspace-content">
        <header className="workspace-hero">
          <div className="workspace-title">
            <div>
              <p className="eyebrow">Workspace</p>
              <h1>{title}</h1>
              <p className="meta">{subtitle}</p>
            </div>
          </div>
          <div className="workspace-hero-links">
            <a href={`${apiRoot}/docs`} target="_blank" rel="noreferrer">Swagger</a>
          </div>
        </header>

        {children(auth)}
      </section>
    </main>
  );
}
