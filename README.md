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
```bash
make migrate
make up
```

Services:
- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8002`
- API Docs: `http://localhost:8002/docs`

## API Baseline
- `POST /api/v1/auth/token`
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

## Frontend Flow
1. Open `/` for dark-theme authentication page (login/register).
2. Register user in PostgreSQL via `POST /api/v1/auth/register`.
3. Login validates credentials from PostgreSQL via `POST /api/v1/auth/login`, then redirects to `/compose`.
4. If admin role is used, run evaluation from **Admin Evaluation** panel.
5. Use **Voice Tools** panel for recording/transcription and readback.
6. Use **Compose Request** panel to generate a draft with authenticated API calls.
7. Edit in **Email Preview** panel and submit feedback via API when needed.
8. In CI, `smoke` job builds containers, applies migrations, and validates auth + draft + MCP endpoints.

## Notes
- Voice transcription uses an OpenAI-first provider adapter with mock fallback when `OPENAI_API_KEY` is not set.
- Draft generation uses an OpenAI-first text provider with local template fallback when `OPENAI_API_KEY` is not set.
- MCP tools implemented: `tool.search_web`, `tool.voice.transcribe`, `tool.voice.speak`, `tool.memory.upsert_profile`.
- Evaluation datasets implemented: `core`, `adversarial`, and `voice`.
- Evaluation metrics include judge scores plus BLEU-1 and ROUGE-L summaries (where references exist).
- MCP `tool.search_web` uses Tavily when `TAVILY_API_KEY` is set, otherwise returns mock results.
- Vector memory uses Chroma (HTTP client) with graceful null fallback if unavailable.
- LangSmith tracing hook is available when `LANGSMITH_TRACING=true`.
- Database schema is managed by Alembic migrations (`backend/alembic/versions/0001_initial_schema.py` onward).
- Request correlation is enabled via `x-request-id` middleware and response header propagation.
- Draft generation endpoint applies per-user rate limiting (`429 RATE_LIMITED`) for abuse protection.
- Draft generation enforces replay protection on duplicate `request_id` (`409 REPLAY_DETECTED`).
- Output safety includes DLP checks for PII patterns when constraints forbid `PII`; violating drafts are blocked.
- MCP invocations are traced into `tool_events` and `audit_logs` for routing/error diagnostics.
- Retention lifecycle endpoint supports policy-driven purge of drafts and logs for compliance maintenance.
- Voice provider priority: Deepgram (if configured) -> OpenAI STT -> Mock.
- TTS provider priority: OpenAI TTS -> Mock.
- Keep all implementation decisions aligned with `spec_dev.md`.

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
