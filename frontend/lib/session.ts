export type SessionAuth = {
  userId: string;
  role: "user" | "admin";
  token: string;
  expiresAt: number;
};

const SESSION_KEY = "email_assistant_auth";

export function saveSessionAuth(auth: SessionAuth): void {
  if (typeof window === "undefined") return;
  window.sessionStorage.setItem(SESSION_KEY, JSON.stringify(auth));
}

function decodeJwtPayload(token: string): Record<string, unknown> | null {
  try {
    const parts = token.split(".");
    if (parts.length < 2) return null;
    const payload = parts[1].replace(/-/g, "+").replace(/_/g, "/");
    const normalized = payload.padEnd(Math.ceil(payload.length / 4) * 4, "=");
    return JSON.parse(atob(normalized)) as Record<string, unknown>;
  } catch {
    return null;
  }
}

export function loadSessionAuth(): SessionAuth | null {
  if (typeof window === "undefined") return null;
  const raw = window.sessionStorage.getItem(SESSION_KEY);
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as SessionAuth;
    if (!parsed?.token) return null;
    const payload = decodeJwtPayload(parsed.token);
    const expSeconds = Number(payload?.exp ?? 0);
    const expMillis = expSeconds > 0 ? expSeconds * 1000 : parsed.expiresAt;
    if (!expMillis || Date.now() >= expMillis) {
      clearSessionAuth();
      return null;
    }
    return { ...parsed, expiresAt: expMillis };
  } catch {
    return null;
  }
}

export function clearSessionAuth(): void {
  if (typeof window === "undefined") return;
  window.sessionStorage.removeItem(SESSION_KEY);
}
