# AI-Powered Email Assistant: Enterprise Edition Specification (MASTER)

> **Status**: APPROVED for Development.
> **Version**: 14.0 (Outstanding Architecture Hardening)

## 1. Executive Summary
This document consolidates all approved architecture decisions and serves as the authoritative source of truth for implementation.

**Core Philosophy**:
1.  **Local-First Infrastructure**: Dockerized PostgreSQL and Chroma for controlled and reproducible environments.
2.  **Grading Alignment**:
    *   **MCP Support**: Compliant with Model Context Protocol.
    *   **Evaluation**: Scientific Metrics (BLEU/ROUGE & LLM Judges).
3.  **Strict Security**: Login Required. Scope Enforcement. ACLs.
4.  **Quality Assurance**: Multi-judge evaluation and user confirmation loop.

---

## 2. Confirmed Stack (Locked)

| Layer | Decision | Selection Rationale |
| :--- | :--- | :--- |
| **Frontend** | **Next.js 14 + Shadcn UI** | Modern component-driven UI with production-ready ergonomics. |
| **Backend** | **FastAPI + LangGraph** | Async API layer with explicit state-machine orchestration for agent workflows. |
| **Database** | **PostgreSQL (Docker)** | Durable relational store for users, drafts, audit, and scoring records. |
| **Vector DB** | **ChromaDB (Docker)** | Retrieval memory layer for personalization and prior context reuse. |
| **Search** | **Tavily** | External knowledge retrieval and optional factual grounding. |
| **Observability** | **LangSmith** | Traceability, dataset management, and evaluation visibility. |
| **Voice** | **Deepgram + ElevenLabs** | Speech input/output pipeline for voice-enabled workflows. |

---

## 3. Evaluation & Optimization Strategy (Grading Rubric Aligned)

We use a **Hybrid Evaluation Approach** to ensure reliability.

### 3.1. Metrics Framework
We track quality using both Neural and Rule-Based metrics:
*   **LLM-as-a-Judge**: GPT-4o rates Tone, Coherence, and Factuality (0-100).
*   **Rule-Based Metrics**:
    *   **BLEU/ROUGE**: For comparing summaries against reference texts.
    *   **Regex Checks**: For strict formatting compliance (e.g., "No PII").
    *   **Response Time**: Latency tracking per agent.

### 3.2. Observability Stack
*   **LangSmith**: Primary tool for tracing agent chains and dataset management.
*   **Arize/Helicone**: (Optional Integration) For production monitoring if needed.
*   **Logging**: Structured JSON logs for every decision step.

### 3.3. Optimization Strategy
*   **Prompt Engineering** > Fine-Tuning: Advanced prompting (Chain-of-Thought, Few-Shot) for flexibility and iteration speed.

---

## 4. MCP (Model Context Protocol) Implementation

To ensure high grading on "Routing & MCP" (10%):
*   **MCP Server**: The Backend exposes an MCP-compliant endpoint.
*   **Resource Access**: Agents access `User Memory` and `Templates` as MCP Resources.
*   **Tools**: Search and Voice services are exposed as MCP Tools.

---

## 5. Voice Integration (Voice-First Experience)

We implement a voice-first interface as a core differentiator.

### 5.1. Voice Input (Speech-to-Text)
*   **Service**: **Deepgram Nova-2** (Real-time streaming STT)
*   **Features**:
    *   **Speaker Diarization**: Identifies different speakers in multi-person conversations
    *   **Real-time Transcription**: Low-latency streaming for immediate feedback
    *   **Accuracy**: Industry-leading accuracy for professional contexts

### 5.2. Voice Output (Text-to-Speech)
*   **Service**: **ElevenLabs Turbo v2** (High-fidelity TTS)
*   **Features**:
    *   **Draft Readback**: The assistant can read the generated draft aloud for review
    *   **Low Latency**: Sub-second response time for natural conversation flow
    *   **Natural Prosody**: Human-like intonation and pacing

### 5.3. Voice Persona Library
Users can select from **4 Curated Voice Options**, each optimized for different professional contexts:
1.  **Professional (Default)**: Neutral, authoritative tone for board meetings
2.  **Casual**: Warm, approachable tone for team communications
3.  **Assertive**: Confident, direct tone for negotiations
4.  **Empathetic**: Supportive, understanding tone for sensitive topics

### 5.4. Voice Persistence (Database)
*   **Storage**: User's selected voice preference is saved in PostgreSQL
*   **Schema**: `users.default_voice_id` (FK to `voice_personas` table)
*   **Behavior**: Voice selection persists across sessions and is automatically applied to new drafts

### 5.5. User Journey (Voice-First Workflow)
1.  **Input**: User clicks "Record" → Speaks their request (e.g., "Tell the team I'll be late, keep it casual")
2.  **Processing**: Deepgram transcribes → Intent Agent extracts entities → Planner checks for missing info
3.  **Clarification** (if needed): UI displays "Which meeting?" → User responds via voice or text
4.  **Output**: Draft is generated → ElevenLabs reads it back → User confirms or regenerates

---

## 6. Memory Access Control (ACL)

| Role | Access Scope | Logic |
| :--- | :--- | :--- |
| **Admin** | **Global Read/Write** | Can see their own memory + All User memories. |
| **Regular User** | **Scoped Read/Write** | 1. Can see **Their Own** memory.<br>2. Can see **Anonymized Public Threads**.<br>3. **BLOCKED** from Admin memory. |

---

## 7. Quality Assurance Loop

### 7.1. The Judge Ensemble (Multi-Model Voting)
1.  **Clarity & Grammar** (0-100%).
2.  **Tone Match** (0-100%).
3.  **Factuality** (0-100%).
*   If `Average Score < 85%`: **REJECT** & Auto-Refine.

### 7.2. The User Confirmation Loop
1.  **Draft Presented**: User sees the Email + Confidence Score.
2.  **Highlighting**: Uncertain facts are highlighted.
3.  **Action**: User clicks "Confirm", "Edit", or "Regenerate".

---

## 8. Directory Structure (Monorepo)

```text
email_assistant/
├── backend/                # Python (FastAPI + LangGraph)
│   ├── src/
│   │   ├── core/           # State Machine
│   │   ├── agents/         # MCP Compliant Tools
│   │   ├── evaluation/     # Metrics (BLEU, ROUGE, LLM Judges)
│   │   └── api/            # Endpoints
│   └── Dockerfile
│
├── frontend/               # TypeScript (Next.js)
│   ├── app/                # Pages
│   ├── components/ui/      # Shadcn Components
│   └── Dockerfile
│
├── docker-compose.yml      # Orchestrates Backend + Frontend + DBs
└── README.md
```

---
## 9. Product KPIs, NFRs, and Success Criteria

### 9.1. Business KPIs (from capstone brief, now contractually enforced)
1.  **Draft Time Reduction**: median email drafting time from 15-20 min to **< 2 min**.
2.  **First-Draft Acceptance Rate**: at least **60%** accepted without major edits.
3.  **Tone Alignment**: at least **90%** of outputs score >= 85 by Tone Judge.
4.  **Edit Distance Reduction**: at least **40%** fewer manual edits by week 2.

### 9.2. Non-Functional Requirements (SLOs)
| Dimension | Target |
| :--- | :--- |
| API Availability | >= 99.5% (local demo target: >= 99.0%) |
| End-to-End Draft Latency (text mode) | p50 <= 6s, p95 <= 12s |
| End-to-End Draft Latency (voice mode) | p50 <= 9s, p95 <= 18s |
| Safety Failure Rate (PII leakage / policy violation) | < 1% |
| Fallback Success on upstream failure | >= 95% graceful recovery |

### 9.3. UI Compliance Note (grading compatibility)
`Next.js 14` is the chosen UI stack and fully satisfies Streamlit-equivalent capstone expectations: tone/intent selector, real-time preview, editable draft, and copy/export options.

---
## 10. Canonical Agent Contract Table (Locked)

| Agent | Input Contract | Output Contract | Failure Mode | Owner |
| :--- | :--- | :--- | :--- | :--- |
| Input Parsing Agent | `raw_prompt`, optional metadata | normalized intent payload | malformed prompt | Core NLP |
| Intent Detection Agent | normalized payload | `intent_class`, confidence | low confidence | Core NLP |
| Tone Stylist Agent | intent + tone request | tone plan + style constraints | unsupported tone | Content |
| Draft Writer Agent | context + tone plan + constraints | structured draft | hallucination / format miss | Content |
| Personalization Agent | user profile + prior edits | personalized draft modifiers | missing profile data | Memory |
| Review & Validator Agent | draft + constraints | quality scores + violations | quality below threshold | Quality |
| Routing & Memory Agent | graph state + tool status | next route decision + persistence ops | upstream outage / timeout | Orchestration |
| Security Guard Agent | prompt + draft + tool calls | allow/block + reasons | jailbreak detected | Security |

### 10.1. Shared Graph State Schema (minimum)
`request_id`, `user_id`, `intent`, `tone`, `constraints`, `context_sources`, `draft_versions`, `judge_scores`, `fallback_count`, `selected_model`, `policy_flags`, `final_status`.

---
## 11. Routing, Fallback, and Degradation Matrix

| Condition | Detection | Action | User Experience |
| :--- | :--- | :--- | :--- |
| LLM timeout | > configured timeout | retry once with same model, then switch provider | "Running fallback model..." |
| LLM invalid JSON / schema break | schema validator fail | auto-repair prompt once, else route to safe template generation | warning banner + editable draft |
| Judge score < 85 | quality gate fail | auto-refine loop (max 2 retries) | "Refining for quality..." |
| Tavily unavailable | tool call fail | proceed without web context + factuality warning | "Web validation unavailable" |
| Deepgram failure | STT fail | switch to text input mode | "Voice failed, switched to text" |
| ElevenLabs failure | TTS fail | disable readback; keep text workflow | "Audio preview unavailable" |
| MCP resource denied | ACL check fail | block tool/resource and continue minimal flow | "Permission restricted" |
| Security policy violation | guardrail rule match | hard stop + safe explanation | "Request blocked for safety" |

### 11.1. Hard limits
`max_retries_per_agent = 2`, `max_total_retries = 5`, `hard_timeout_e2e = 30s`.

---
## 12. MCP Contract (Resources, Tools, Auth, Errors)

### 12.1. Resources
1.  `memory://user/{user_id}/profile` (read/write, scoped).
2.  `memory://user/{user_id}/threads` (read/write, scoped).
3.  `templates://email/{template_id}` (read).
4.  `policy://safety/ruleset` (read).

### 12.2. Tools
1.  `tool.search_web(query, recency_days)` -> citations + confidence.
2.  `tool.voice.transcribe(audio_stream)` -> transcript + diarization.
3.  `tool.voice.speak(text, persona_id)` -> audio URL/blob.
4.  `tool.memory.upsert_profile(fields)` -> versioned profile state.

### 12.3. Auth and scopes
JWT session + role scope (`admin`, `user`) + resource-level ACL checks. Every MCP call logs `request_id`, `actor`, `resource`, `decision`.

### 12.4. Error semantics
Standardized MCP error payload: `error_code`, `message`, `retryable`, `fallback_path`.

---
## 13. Evaluation Harness and Release Gates

### 13.1. Evaluation dataset strategy
1.  **Core Dataset**: 100 representative prompts across outreach, follow-up, apology, informational.
2.  **Adversarial Dataset**: 40 prompts for jailbreak, prompt injection, PII leakage.
3.  **Voice Dataset**: 30 spoken requests with noise/accent variations.

### 13.2. Metrics and pass thresholds
| Metric | Threshold |
| :--- | :--- |
| Tone Judge score | >= 85 average |
| Factuality Judge score | >= 85 average |
| Grammar/Clarity Judge score | >= 90 average |
| Safety pass rate | >= 99% |
| Structured output validity | >= 98% |
| Fallback success rate | >= 95% |

### 13.3. Release gates
No release unless all thresholds pass on latest eval run + no P0 bugs + no unresolved security findings.

---
## 14. Observability, Alerting, and Runbooks

### 14.1. Trace model
Distributed trace with `request_id` across frontend action -> API -> LangGraph nodes -> MCP tools -> DB writes.

### 14.2. Required dashboards
1.  Latency by agent/node (p50/p95/p99).
2.  Judge scores over time by intent/tone.
3.  Fallback rates and failure categories.
4.  Cost per request and per model/provider.
5.  Safety violations and blocked requests.

### 14.3. Alerts
1.  p95 latency breach for 15 min.
2.  fallback rate spike > 20%.
3.  safety failure > 1%.
4.  provider error rate > 5%.

### 14.4. Incident runbook (minimum)
Triage -> identify failing node/provider -> switch to fallback profile -> verify recovery -> postmortem with corrective action.

---
## 15. Security, Privacy, and Data Lifecycle

### 15.1. Security controls
1.  Secrets from environment/secret manager only (never hardcoded).
2.  TLS in transit; encrypted storage for sensitive fields.
3.  Prompt injection defense rules before tool execution.
4.  Output DLP checks (emails, phone numbers, identifiers) before final response.
5.  Immutable audit logging for auth, access, and policy decisions.

### 15.2. Privacy and retention
| Data Type | Retention | Deletion |
| :--- | :--- | :--- |
| Transcripts | 30 days (default) | user-initiated delete supported |
| Draft history | 90 days (default) | hard delete + tombstone log |
| Profile memory | until account deletion | full purge on account delete |
| Traces/logs | 30-90 days | policy-based purge |

### 15.3. Consent
Voice capture requires explicit opt-in and clear indicator when recording is active.

---
## 16. Testing, CI/CD, and Deployment

### 16.1. Test pyramid
1.  Unit tests for each agent and schema validator.
2.  Integration tests for LangGraph routing + MCP tools.
3.  End-to-end tests for text and voice workflows.
4.  Regression eval suite using Section 13 datasets.
5.  Fault-injection tests for fallback and timeout behavior.

### 16.2. CI gates
`lint + typecheck + unit + integration + eval-smoke` must pass on every PR.

### 16.3. Deployment model
1.  Environments: `dev`, `stage`, `prod`.
2.  Migration strategy: versioned DB migrations with rollback scripts.
3.  Rollback policy: previous known-good container tag, under 10 minutes target.

---
## 17. Evaluation Traceability Matrix

| Rubric Criterion | Architecture Evidence in this Spec |
| :--- | :--- |
| Functionality | Sections 5, 7, 9, 13 with measurable quality and latency targets |
| Agent Design | Section 10 canonical modular agent contracts |
| Routing & Orchestration | Sections 4, 11, 12 with deterministic route/fallback rules |
| Agent Communication | Section 10 shared state schema + MCP interfaces in Section 12 |
| UX / Usability | Sections 5, 9.3, 11 user-facing degraded modes |
| Routing & Fallback | Section 11 matrix + hard retry/time budgets |
| Error Handling & Logging | Sections 12.4, 14, 15.1 immutable audit trail |
| Documentation | This master spec + README alignment requirement |
| Prompt & Config Documentation | Section 13 eval contracts + Section 12 tool/resource schemas |
| Testing | Section 16 complete test strategy and CI gates |

---
## 18. Implementation Notes (No Scope Removal)

1.  All v13 decisions remain valid and are preserved.
2.  v14 adds operational rigor, measurable acceptance criteria, and production-grade controls.
3.  This document remains the source of truth; implementation details must not contradict locked sections.

---
## 19. API Contract Appendix (Implementation-Ready)

### 19.1. Endpoint: `POST /api/v1/draft/generate`
**Purpose**: Generate email draft from text request.

**Request (JSON)**:
```json
{
  "request_id": "uuid",
  "user_id": "uuid",
  "prompt": "Tell client we need to reschedule to Friday",
  "intent": "follow_up",
  "tone": "professional",
  "constraints": {
    "max_paragraphs": 3,
    "must_include": ["new date", "apology"],
    "forbidden": ["PII"]
  },
  "metadata": {
    "recipient_role": "client",
    "language": "en"
  }
}
```

**Response 200 (JSON)**:
```json
{
  "request_id": "uuid",
  "status": "success",
  "draft_id": "uuid",
  "draft_text": "Dear ...",
  "judge_scores": {
    "clarity": 91,
    "tone_match": 88,
    "factuality": 86,
    "overall": 88.3
  },
  "model_used": "gpt-4o",
  "fallback_used": false,
  "citations": [],
  "latency_ms": 5420
}
```

**Error Responses**:
- `400 INVALID_INPUT`: schema or required field missing.
- `401 UNAUTHORIZED`: invalid auth/session.
- `403 ACCESS_DENIED`: ACL/policy block.
- `422 QUALITY_GATE_FAILED`: retries exhausted under threshold.
- `429 RATE_LIMITED`: per-user/per-IP quota exceeded.
- `503 UPSTREAM_UNAVAILABLE`: model/tool unavailable and fallback exhausted.

### 19.2. Endpoint: `POST /api/v1/voice/transcribe`
**Purpose**: Convert audio to transcript with diarization.

**Request**: multipart/form-data (`audio_file`, `user_id`, optional `language`).

**Response 200**:
```json
{
  "request_id": "uuid",
  "transcript": "Can you draft a follow-up email...",
  "segments": [
    {"speaker": "S1", "start_ms": 0, "end_ms": 2400, "text": "Can you draft..."}
  ],
  "confidence": 0.93
}
```

### 19.3. Endpoint: `POST /api/v1/draft/feedback`
**Purpose**: Learn from user edits for personalization loop.

**Request**:
```json
{
  "request_id": "uuid",
  "draft_id": "uuid",
  "user_id": "uuid",
  "action": "edited",
  "original_text": "Dear ...",
  "final_text": "Hi ...",
  "feedback_tags": ["too_formal", "shorten"]
}
```

**Response 200**:
```json
{
  "status": "recorded",
  "profile_update_version": 12
}
```

### 19.4. Endpoint: `GET /api/v1/health`
**Purpose**: Liveness/readiness and dependency health.

**Response 200**:
```json
{
  "status": "ok",
  "dependencies": {
    "postgres": "ok",
    "chroma": "ok",
    "llm_provider_primary": "ok",
    "llm_provider_secondary": "degraded"
  }
}
```

---
## 20. Data Model and Migration Appendix

### 20.1. Core relational tables (PostgreSQL)
1.  `users(id, email, role, default_voice_id, created_at, updated_at)`
2.  `voice_personas(id, name, provider, provider_voice_key, active)`
3.  `user_profiles(user_id, preferred_tone, organization, signature, prefs_json, version, updated_at)`
4.  `drafts(id, request_id, user_id, intent, tone, draft_text, model_used, fallback_used, latency_ms, created_at)`
5.  `judge_scores(id, draft_id, clarity, tone_match, factuality, overall, judge_model, created_at)`
6.  `tool_events(id, request_id, tool_name, status, latency_ms, payload_hash, created_at)`
7.  `audit_logs(id, request_id, actor_user_id, action, resource, decision, reason, created_at)`
8.  `feedback_events(id, draft_id, user_id, action, feedback_tags, diff_ratio, created_at)`

### 20.2. Indexing strategy
1.  `drafts(user_id, created_at DESC)` for user history views.
2.  `drafts(request_id)` unique for trace correlation.
3.  `judge_scores(draft_id)` for quality analytics joins.
4.  `audit_logs(request_id, created_at)` for security investigations.
5.  `tool_events(request_id, tool_name)` for fallback diagnostics.

### 20.3. Vector memory (Chroma)
Collections:
1.  `profile_memories` keyed by `user_id`.
2.  `draft_memories` keyed by `draft_id` and `intent`.
3.  `style_preferences` keyed by `user_id` and feedback tags.

Metadata required: `user_id`, `source`, `created_at`, `ttl_days`, `embedding_model_version`.

### 20.4. Migration sequencing
1.  Create base identity + role tables.
2.  Create drafting and scoring tables.
3.  Create audit and tool event tables.
4.  Backfill defaults (`default_voice_id`, profile version).
5.  Apply indexes.
6.  Run data validation checks.

### 20.5. Rollback policy
Every forward migration must include a verified down-migration script and backup checkpoint before production apply.

---
## 21. Threat Model Appendix (Security Hardening)

| Threat | Example Scenario | Impact | Control | Residual Risk |
| :--- | :--- | :--- | :--- | :--- |
| Prompt Injection | User asks model to reveal system prompt or secrets | Data leakage | Input sanitization + tool-use policy + allowlist | Medium |
| Tool Exfiltration | Malicious prompt attempts unrestricted web/tool access | Unauthorized data retrieval | MCP scope checks + role ACL + policy engine | Low-Medium |
| PII Leakage | Draft contains sensitive personal/company identifiers | Compliance breach | Output DLP regex + judge safety gate + user warning | Low |
| Auth Bypass | Crafted request with forged user_id | Account compromise | JWT verification + server-side user binding + audit logs | Low |
| Replay Attack | Reuse of previous signed request | Unauthorized action repeat | Nonce/request_id dedupe + expiry checks | Low |
| Provider Outage | Primary model/STT/TTS unavailable | Service disruption | Fallback provider routing + degraded text-only mode | Medium |
| Data Retention Drift | Data stored past policy limits | Policy violation | TTL jobs + periodic retention audits | Low |
| Insider Misuse | Admin accesses unnecessary user data | Privacy breach | Role separation + immutable audit trail + periodic review | Medium |

### 21.1. Security testing requirements
1.  Weekly adversarial prompt suite run.
2.  Pre-release penetration test checklist.
3.  Secrets scanning on every PR.
4.  Dependency vulnerability scan in CI.

---
**Prepared by:** Shashank Dewangan
**Refined by:** AI Coding Assistant (Senior TPM)
