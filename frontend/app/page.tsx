"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import Link from "next/link";
import { loginUser, registerUser } from "@/lib/api";
import { showErrorPopup } from "@/lib/error-popup";
import { getRoleFromToken, saveSessionAuth } from "@/lib/session";

type Role = "user" | "admin";
type Mode = "login" | "register";

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<Mode>("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [role, setRole] = useState<Role>("user");
  const [loading, setLoading] = useState(false);
  const [email, setEmail] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [formVersion, setFormVersion] = useState(0);
  const regPasswordRef = useRef<HTMLInputElement | null>(null);
  const regConfirmRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    clearAuthFields();
  }, [mode]);

  function clearAuthFields() {
    setUsername("");
    setPassword("");
    setConfirmPassword("");
    setEmail("");
    setRole("user");
    setError(null);
    setFormVersion((v) => v + 1);
  }

  function clearPasswordFields() {
    setPassword("");
    setConfirmPassword("");
    setError(null);
    if (regPasswordRef.current) regPasswordRef.current.value = "";
    if (regConfirmRef.current) regConfirmRef.current.value = "";
    setFormVersion((v) => v + 1);
  }

  function isPasswordIssue(message: string): boolean {
    return /password|confirm/i.test(message);
  }

  function handleInvalidSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const target = e.target as HTMLInputElement | HTMLSelectElement | null;
    const fieldId = target?.id || "";
    const passwordFieldInvalid = fieldId === "reg-pass" || fieldId === "reg-confirm";
    showErrorPopup("Please complete all required fields and try again.", "Invalid form");
    if (mode === "register" && passwordFieldInvalid) {
      clearPasswordFields();
    } else {
      clearAuthFields();
    }
  }

  async function handleLogin(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);

    setLoading(true);
    try {
      const response = await loginUser(username, password);
      const authenticatedRole = getRoleFromToken(response.access_token) ?? "user";
      saveSessionAuth({
        userId: username,
        role: authenticatedRole,
        token: response.access_token,
        expiresAt: Date.now() + response.expires_in_minutes * 60 * 1000
      });
      router.push("/compose");
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Authentication failed.";
      setError(msg);
      showErrorPopup(msg, "Login failed");
      clearAuthFields();
    } finally {
      setLoading(false);
    }
  }

  function handleRegister(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);

    if (password !== confirmPassword) {
      const msg = "Passwords do not match.";
      setError(msg);
      showErrorPopup(msg, "Registration failed");
      clearPasswordFields();
      return;
    }

    setLoading(true);
    registerUser(username, password, role, email || undefined)
      .then((response) => {
        const authenticatedRole = getRoleFromToken(response.access_token) ?? role;
        saveSessionAuth({
          userId: username,
          role: authenticatedRole,
          token: response.access_token,
          expiresAt: Date.now() + response.expires_in_minutes * 60 * 1000
        });
        router.push("/compose");
      })
      .catch((err) => {
        const msg = err instanceof Error ? err.message : "Registration failed.";
        setError(msg);
        showErrorPopup(msg, "Registration failed");
        if (isPasswordIssue(msg)) {
          clearPasswordFields();
        } else {
          clearAuthFields();
        }
      })
      .finally(() => setLoading(false));
  }

  return (
    <main className="auth-root">
      <section className="auth-shell">
        <aside className="auth-showcase">
          <Image src="/logo-mark.svg" alt="Email Assistant logo" className="auth-logo" width={56} height={56} />
          <p className="eyebrow">Enterprise Agentic Workspace</p>
          <h1>AI Email Assistant</h1>
          <p className="meta">Secure database authentication with production-grade drafting, voice tooling, and evaluation controls.</p>
          <div className="public-links">
            <Link href="/architecture">Architecture</Link>
            <Link href="/architecture-map">Architecture Map</Link>
            <Link href="/workflows">Workflows</Link>
            <Link href="/quality">Quality</Link>
            <Link href="/docs">Docs</Link>
          </div>
        </aside>

        <section className="auth-card">
          <div className="brand-mark" aria-hidden>EA</div>
          <h2>{mode === "login" ? "Welcome back" : "Create account"}</h2>
          <p className="meta">Use your workspace credentials to continue.</p>

          <div className="auth-tabs">
            <button type="button" className={mode === "login" ? "tab active" : "tab"} onClick={() => setMode("login")}>
              Login
            </button>
            <button type="button" className={mode === "register" ? "tab active" : "tab"} onClick={() => setMode("register")}>
              Register
            </button>
          </div>

          {mode === "login" ? (
            <form
              key={`login-${formVersion}`}
              className="stacked-form"
              onSubmit={handleLogin}
              onInvalid={handleInvalidSubmit}
              autoComplete="off"
            >
              <label htmlFor="login-user">Username</label>
              <input id="login-user" value={username} onChange={(e) => setUsername(e.target.value)} required autoComplete="off" />
              <label htmlFor="login-pass">Password</label>
              <input id="login-pass" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required autoComplete="off" />
              <button type="submit" disabled={loading}>{loading ? "Logging in..." : "Login"}</button>
            </form>
          ) : null}

          {mode === "register" ? (
            <form
              key={`register-${formVersion}`}
              className="stacked-form"
              onSubmit={handleRegister}
              onInvalid={handleInvalidSubmit}
              autoComplete="off"
            >
              <label htmlFor="reg-user">Username</label>
              <input id="reg-user" value={username} onChange={(e) => setUsername(e.target.value)} required autoComplete="off" />
              <label htmlFor="reg-email">Email (optional)</label>
              <input id="reg-email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="off" />
              <label htmlFor="reg-pass">Password</label>
              <input
                ref={regPasswordRef}
                id="reg-pass"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="new-password"
              />
              <label htmlFor="reg-confirm">Confirm Password</label>
              <input
                ref={regConfirmRef}
                id="reg-confirm"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                autoComplete="new-password"
              />
              <label htmlFor="reg-role">Role</label>
              <select id="reg-role" value={role} onChange={(e) => setRole(e.target.value as Role)}>
                <option value="user">user</option>
                <option value="admin">admin</option>
              </select>
              <button type="submit" disabled={loading}>{loading ? "Creating account..." : "Register"}</button>
            </form>
          ) : null}

        </section>
      </section>
    </main>
  );
}
