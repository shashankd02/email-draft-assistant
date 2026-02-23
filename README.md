# AI-Powered Email Assistant

Production-oriented baseline implementation generated from `spec_dev.md` (source of truth).

## Stack
- Frontend: Next.js 14
- Backend: FastAPI + LangGraph-style orchestration scaffold
- Data: PostgreSQL + Chroma (Docker)

## Monorepo Structure
- `backend/` API, agent workflow, MCP stubs, tests
- `frontend/` UI with tone/intent controls and editable draft preview
- `docker-compose.yml` local orchestration for app + data stores
- `spec_dev.md` authoritative architecture specification

## Run (Docker)
Simplest options:
```bash
make start
```
or
```bash
./run-app
```

Manual (equivalent):
```bash
make migrate
make up
```

Services:
- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8002`
- API Docs: `http://localhost:8002/docs`

Stop:
```bash
make stop
```
or
```bash
./stop-app
```

## API Baseline
- `POST /api/v1/auth/token`
- `DELETE /api/v1/auth/me/transcripts`
- `DELETE /api/v1/auth/me`
- `POST /api/v1/draft/generate`
- `POST /api/v1/voice/transcribe`
- `GET /api/v1/voice/personas`
- `POST /api/v1/voice/personas/default`
- `POST /api/v1/draft/feedback`
- `GET /api/v1/health`
- `GET /api/v1/mcp/resources`
- `GET /api/v1/mcp/tools`
- `POST /api/v1/mcp/invoke`
- `POST /api/v1/mcp/resource/read`
- `POST /api/v1/mcp/resource/write`
- `GET /api/v1/evaluation/datasets` (admin)
- `POST /api/v1/evaluation/run` (admin)
- `GET /api/v1/evaluation/runs` (admin)
- `GET /api/v1/evaluation/runs/{run_id}` (admin)
- `POST /api/v1/admin/retention/purge` (admin)
- `POST /api/v1/admin/users/delete` (admin)
- `GET /api/v1/observability/metrics` (admin)
- `GET /api/v1/observability/alerts` (admin)

## Frontend Flow
1. Open `/` for dark-theme authentication page (login/register).
2. Register user in PostgreSQL via `POST /api/v1/auth/register`.
3. Login validates credentials from PostgreSQL via `POST /api/v1/auth/login`, then redirects to `/compose`.
4. Use sidebar navigation to access dedicated pages:
   - `/compose` drafting workspace
   - `/architecture` system architecture summary
   - `/workflows` agent workflow stages
   - `/observability` operational metrics/alerts (admin)
   - `/evaluation` evaluation center (admin tools)
   - `/docs` Swagger/OpenAPI + endpoint map + health
5. Use **Compose Request** panel to generate a draft with authenticated API calls.
6. Edit in **Email Preview** panel and submit feedback via API when needed.
7. In CI, `smoke` job builds containers, applies migrations, and validates auth + draft + MCP endpoints.

## Notes
- Voice transcription uses real providers only (Deepgram/OpenAI) in strict mode.
- Draft generation uses real LLM provider only (`OPENAI_API_KEY` required in strict mode).
- MCP tools implemented: `tool.search_web`, `tool.voice.transcribe`, `tool.voice.speak`, `tool.memory.upsert_profile`.
- MCP memory resources implemented: `memory://user/{user_id}/profile` and `memory://user/{user_id}/threads` (DB-backed).
- Regular users can read anonymized public threads in addition to their own scoped thread memory.
- Evaluation datasets implemented: `core`, `adversarial`, and `voice`.
- Evaluation metrics include judge scores plus BLEU-1 and ROUGE-L summaries (where references exist).
- MCP `tool.search_web` uses Tavily and returns `UPSTREAM_UNAVAILABLE` when search provider is not configured in strict mode.
- Vector memory uses Chroma (HTTP client) with graceful null fallback if unavailable.
- LangSmith tracing hook is available when `LANGSMITH_TRACING=true`.
- Health endpoint now exposes strict-provider readiness (`strict_provider_mode`, `strict_provider_ready`, and per-provider requirement flags).
- Observability endpoint exposes workflow outcomes, fallback/error counters, and per-agent latency percentiles.
- Observability alerts endpoint evaluates p95 latency, fallback rate, provider error rate, and safety failure rate thresholds.
- Database schema is managed by Alembic migrations (`backend/alembic/versions/0001_initial_schema.py` onward).
- Request correlation is enabled via `x-request-id` middleware and response header propagation.
- Draft generation endpoint applies per-user rate limiting (`429 RATE_LIMITED`) for abuse protection.
- Draft generation enforces replay protection on duplicate `request_id` (`409 REPLAY_DETECTED`).
- Deterministic fallback behavior: provider errors/timeouts trigger bounded retries; exhaustion returns `503 UPSTREAM_UNAVAILABLE`.
- Structured-output recovery: draft generation enforces JSON schema, auto-repairs once on schema break, then routes to deterministic safe-template fallback.
- Output safety includes DLP checks for PII patterns when constraints forbid `PII`; violating drafts are blocked.
- MCP invocations are traced into `tool_events` and `audit_logs` for routing/error diagnostics.
- Retention lifecycle supports policy-driven purge of drafts, transcripts, and logs (manual endpoint + scheduler).
- Voice provider priority: Deepgram (if configured) -> OpenAI STT.
- TTS provider: OpenAI TTS.
- Keep all implementation decisions aligned with `spec_dev.md`.

## Git Workflows and Review Automation
- CI workflow (`.github/workflows/ci.yml`)
  - Backend: migrations, compile, tests, eval smoke, security scans.
  - Frontend: install, lint, build, dependency audit.
  - Smoke: containerized auth + draft + MCP endpoint validation.
- PR Review Agent (`.github/workflows/pr-review-agent.yml`)
  - Posts an automated structural review comment on every PR.
  - Flags missing test updates for backend changes.
  - Flags migration changes without docs/spec updates.
  - Flags workflow changes for maintainer attention.
- CODEOWNERS (`.github/CODEOWNERS`)
  - Defines required review ownership for backend, frontend, CI, and specs.
- PR template (`.github/pull_request_template.md`)
  - Enforces consistent summary, validation, risk, and deployment notes.
- Dependency hygiene (`.github/dependabot.yml`)
  - Weekly update PRs for Python, npm, and GitHub Actions.
- Stale management (`.github/workflows/stale.yml`)
  - Auto-labels/closes long-inactive issues/PRs to keep backlog healthy.

## Auth Quick Start
Issue a JWT token:
```bash
curl -X POST http://localhost:8002/api/v1/auth/token \\
  -H "Content-Type: application/json" \\
  -d '{"user_id":"user-001","role":"user","bootstrap_secret":"dev-bootstrap-secret"}'
```

Use the token:
```bash
curl -X POST http://localhost:8002/api/v1/draft/generate \\
  -H "Authorization: Bearer <TOKEN>" \\
  -H "Content-Type: application/json" \\
  -d '{"user_id":"user-001","prompt":"Draft a follow-up","intent":"follow_up","tone":"professional"}'
```
