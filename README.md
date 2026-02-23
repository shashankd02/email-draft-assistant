# AI-Powered Email Assistant

This project helps users create clear, tone-aware email drafts quickly using a guided AI workflow.

It is designed as a full end-to-end application with:
- a clean web interface,
- secure login and role-based access,
- backend AI workflow orchestration,
- voice input/output support,
- observability and evaluation dashboards.

`spec_dev.md` is the source of truth for architecture and implementation decisions.

## What This Application Does
- Accepts a drafting request (text or voice)
- Validates that the intent is truly email-related
- Enhances the prompt with context and personalization
- Generates a draft in the selected tone
- Reviews quality and applies fallback logic when needed
- Returns a polished draft for review, copy, playback, and feedback

## Technology Overview
**Frontend**
- Next.js 14, React, TypeScript
- Auth screen + workspace shell
- Pages for compose, architecture, workflows, quality, docs, observability, and evaluation

**Backend**
- FastAPI API with typed request/response contracts
- Multi-step AI workflow service
- MCP endpoints for tools/resources
- Evaluation, observability, and maintenance routes

**Data and Integrations**
- PostgreSQL: users, drafts, logs, and evaluation records
- Chroma: vector memory for profile/thread context
- OpenAI: text generation and text-to-speech
- Deepgram/OpenAI: speech-to-text
- Tavily: web context retrieval
- LangSmith: optional tracing integration

## AI Workflow (Agent Stages)
1. Input Parser: validates and normalizes incoming request fields.
2. Intent Guard: blocks prompts that are not intended for email drafting.
3. Context Enrichment: retrieves external context when applicable.
4. Prompt Refiner: improves prompt clarity and completeness.
5. Personalization: applies profile and memory signals.
6. Tone Stylist: enforces the selected communication tone.
7. Draft Writer: generates the email draft.
8. Review Validator: scores quality dimensions (clarity, tone, factuality).
9. Router + Memory: handles retries/fallback and persists memory updates.

## Visual Diagrams
Architecture and workflow visuals are available in `diagrams/`.

- System Architecture: `diagrams/system-architecture.svg`
- Agent Workflow: `diagrams/agent-workflow.svg`
- End-to-End Request Flow: `diagrams/end-to-end-request-flow.svg`
- Observability + Evaluation Loop: `diagrams/observability-evaluation-loop.svg`

These files can be used directly in presentations and documentation.
PNG exports are also available in the same folder:
- `diagrams/system-architecture.png`
- `diagrams/agent-workflow.png`
- `diagrams/end-to-end-request-flow.png`
- `diagrams/observability-evaluation-loop.png`

## Application URLs
- Web App: `http://localhost:3000`
- Compose: `http://localhost:3000/compose`
- Architecture: `http://localhost:3000/architecture`
- Architecture Map: `http://localhost:3000/architecture-map`
- Workflows: `http://localhost:3000/workflows`
- Quality: `http://localhost:3000/quality`
- API Docs (in app): `http://localhost:3000/docs`
- Swagger (backend): `http://localhost:8002/docs`

## Setup and Run
### Prerequisites
- Docker Desktop (or Docker Engine + Compose plugin)
- Ports available: `3000`, `5432`, `8001`, `8002`

1. Create env files:
```bash
cp backend/.env.example backend/.env
cp frontend/.env.local.example frontend/.env.local
```

2. Add required API keys in `backend/.env`:
- `OPENAI_API_KEY`
- `DEEPGRAM_API_KEY` (recommended for voice transcription)
- `TAVILY_API_KEY` (for web context enrichment)
- `LANGSMITH_API_KEY` (optional)

3. Start all services:
```bash
make start
```

4. Open `http://localhost:3000`, register/login, and start drafting.

To stop:
```bash
make stop
```

### Docker Command Reference
- Start detached + run migrations: `make start`
- Start in foreground (for active logs): `make up`
- Run DB migrations only: `make migrate`
- View logs: `make logs`
- Stop containers (keep data): `make stop`
- Full reset including volumes: `make reset`

### Quick Troubleshooting
- `EADDRINUSE` on port `3000`:
  stop local process on port `3000` or use Docker-only run (`make start`).
- Draft/API calls failing from UI:
  verify `OPENAI_API_KEY` in `backend/.env`, then restart with `make start`.
- Services unhealthy after config updates:
  run `make stop` and `make start` again.
- Stale DB state during evaluation:
  run `make reset`, then `make start`.

## Main API Groups
- Auth: `/api/v1/auth/*`
- Drafting: `/api/v1/draft/*`
- Voice: `/api/v1/voice/*`
- MCP: `/api/v1/mcp/*`
- Evaluation (admin): `/api/v1/evaluation/*`
- Observability (admin): `/api/v1/observability/*`
- Health: `/api/v1/health`

## Key User Features
- Text and voice prompt input
- Multilingual drafting support (English, Spanish, Hindi)
- Tone-controlled output (for example: professional, friendly, assertive)
- Loading overlay with cancellation support
- Draft playback, copy-to-clipboard, and feedback submission

## Admin Features
- Global observability metrics and alerts
- Evaluation datasets and run tracking
- System-level operational insights

## Repository Structure
- `backend/`: APIs, agents, services, DB models, migrations, tests
- `frontend/`: pages, components, styles, client integrations
- `docs/`: assignment and reference documents
- `diagrams/`: architecture and workflow images (`.svg` + `.png`)
- `spec_dev.md`: architecture blueprint and requirements baseline

## Notes
- Diagram assets were moved from `docs/diagrams` to root-level `diagrams/` for easier sharing and presentation use.
