export type DraftRequest = {
  user_id: string;
  prompt: string;
  intent: string;
  tone: string;
  constraints: {
    max_paragraphs: number;
    must_include: string[];
    forbidden: string[];
  };
  metadata: {
    recipient_role: string;
    language: string;
  };
};

export type DraftResponse = {
  request_id: string;
  status: string;
  draft_id: string;
  draft_text: string;
  judge_scores: {
    clarity: number;
    tone_match: number;
    factuality: number;
    overall: number;
  };
  model_used: string;
  fallback_used: boolean;
  citations: string[];
  latency_ms: number;
};

export type AuthTokenResponse = {
  access_token: string;
  token_type: string;
  expires_in_minutes: number;
};

export type MCPInvokeResponse = {
  status: string;
  decision: string;
  result?: any;
  message?: string;
};

export type EvalRunSummary = {
  run_id: string;
  actor_user_id: string;
  dataset: string;
  total_cases: number;
  avg_clarity: number;
  avg_tone_match: number;
  avg_factuality: number;
  avg_overall: number;
  passed: boolean;
  created_at: string;
};

export type EvalRunResponse = {
  run_id: string;
  summary: {
    total_cases: number;
    avg_clarity: number;
    avg_tone_match: number;
    avg_factuality: number;
    avg_overall: number;
    pass_thresholds: Record<string, boolean>;
  };
  results: Array<{
    request_id: string;
    intent: string;
    tone: string;
    scores: {
      clarity: number;
      tone_match: number;
      factuality: number;
      overall: number;
    };
    model_used: string;
  }>;
};

const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8002/api/v1";

function authHeader(token: string): HeadersInit {
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`
  };
}

function parseApiErrorMessage(raw: string, fallback: string): string {
  if (!raw) return fallback;
  try {
    const obj = JSON.parse(raw) as { message?: string; detail?: { message?: string } | string };
    if (typeof obj.detail === "string" && obj.detail.trim()) return obj.detail;
    if (typeof obj.detail === "object" && obj.detail?.message) return obj.detail.message;
    if (obj.message) return obj.message;
  } catch {
    // ignore parse errors and sanitize below
  }

  const trimmed = raw.trim();
  if (!trimmed) return fallback;
  if (trimmed.startsWith("{") || trimmed.startsWith("[")) return fallback;
  if (/error_code|traceback|exception|stack|sqlalchemy|httpx/i.test(trimmed)) return fallback;
  return trimmed.length > 180 ? fallback : trimmed;
}

export async function issueToken(userId: string, role: "user" | "admin", bootstrapSecret: string): Promise<AuthTokenResponse> {
  const res = await fetch(`${baseUrl}/auth/token`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      user_id: userId,
      role,
      bootstrap_secret: bootstrapSecret
    })
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(parseApiErrorMessage(text, "Unable to issue token. Please verify your inputs."));
  }

  return (await res.json()) as AuthTokenResponse;
}

export async function registerUser(
  username: string,
  password: string,
  role: "user" | "admin",
  email?: string
): Promise<AuthTokenResponse> {
  const res = await fetch(`${baseUrl}/auth/register`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      username,
      password,
      role,
      email
    })
  });
  const text = await res.text();
  if (!res.ok) {
    throw new Error(parseApiErrorMessage(text, "Registration failed. Please check your details."));
  }
  return JSON.parse(text) as AuthTokenResponse;
}

export async function loginUser(username: string, password: string): Promise<AuthTokenResponse> {
  const res = await fetch(`${baseUrl}/auth/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      username,
      password
    })
  });
  const text = await res.text();
  if (!res.ok) {
    throw new Error(parseApiErrorMessage(text, "Login failed. Please check your username and password."));
  }
  return JSON.parse(text) as AuthTokenResponse;
}

export async function generateDraft(payload: DraftRequest, token: string, signal?: AbortSignal): Promise<DraftResponse> {
  if (!token) {
    throw new Error("No auth token found. Generate token first.");
  }

  const res = await fetch(`${baseUrl}/draft/generate`, {
    method: "POST",
    headers: authHeader(token),
    body: JSON.stringify(payload),
    signal,
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(parseApiErrorMessage(text, "Unable to generate draft right now. Please try again."));
  }

  return (await res.json()) as DraftResponse;
}

export async function invokeMcpTool(
  token: string,
  toolName: string,
  actor: string,
  payload: Record<string, unknown>
): Promise<MCPInvokeResponse> {
  const res = await fetch(`${baseUrl}/mcp/invoke`, {
    method: "POST",
    headers: authHeader(token),
    body: JSON.stringify({
      tool_name: toolName,
      actor,
      payload
    })
  });

  const bodyText = await res.text();
  if (!res.ok) {
    throw new Error(parseApiErrorMessage(bodyText, "This action is unavailable right now. Please try again."));
  }
  return JSON.parse(bodyText) as MCPInvokeResponse;
}

export async function runEvaluation(token: string, dataset: "core" | "adversarial" | "voice", maxCases = 3): Promise<EvalRunResponse> {
  const res = await fetch(`${baseUrl}/evaluation/run`, {
    method: "POST",
    headers: authHeader(token),
    body: JSON.stringify({
      dataset,
      max_cases: maxCases
    })
  });
  const text = await res.text();
  if (!res.ok) {
    throw new Error(parseApiErrorMessage(text, "Evaluation run failed. Please try again."));
  }
  return JSON.parse(text) as EvalRunResponse;
}

export async function listEvalRuns(token: string, limit = 10): Promise<{ runs: EvalRunSummary[] }> {
  const res = await fetch(`${baseUrl}/evaluation/runs?limit=${limit}`, {
    method: "GET",
    headers: authHeader(token)
  });
  const text = await res.text();
  if (!res.ok) {
    throw new Error(parseApiErrorMessage(text, "Unable to load evaluation runs right now."));
  }
  return JSON.parse(text) as { runs: EvalRunSummary[] };
}
