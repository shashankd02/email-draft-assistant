# AGENTS.md

This file defines how AI agents should operate in this repository.
It is interaction and execution policy only. Product requirements and architecture details belong in spec documents.

## 1) Mission
- Deliver production-quality outcomes on the first pass whenever possible.
- Optimize for correctness, reliability, maintainability, and user experience.
- Prefer clear, robust implementations over clever, fragile solutions.

## 2) Scope Discipline
- Do not duplicate requirements from spec files in this document.
- Use spec documents as requirement inputs, but keep this file focused on agent behavior.
- Do not introduce features, constraints, or assumptions not requested by the user or spec.

## 3) Truthfulness and Anti-Hallucination
- Never invent facts about code, APIs, configs, providers, files, or tests.
- Never report success unless the step was actually executed and verified.
- If uncertain, state uncertainty and verify through code inspection or command output.
- Use exact file references and concrete evidence for technical claims.

## 4) Execution Policy
- Inspect before editing. Reuse existing patterns unless a change is justified.
- Make minimal, targeted changes that solve the root cause.
- Preserve backward compatibility unless breaking change is explicitly approved.
- Do not perform unrelated refactors during focused fixes.

## 5) Engineering Quality Standards
- Critical paths must be production-grade, not mock-dependent.
- Every change should include:
1. Clear implementation delta
2. Validation (tests/checks/build where applicable)
3. Error handling and edge-case behavior
4. Documentation updates when behavior/contracts change
- For schema changes, include migration and rollback path.

## 6) Security and Privacy
- Never commit secrets, tokens, credentials, or private keys.
- Keep `.env` local; maintain examples/templates separately.
- Apply least privilege for access control and data exposure.
- Sanitize user-facing errors; keep sensitive diagnostics in logs.

## 7) Data and Access Controls
- Enforce actor/principal scoping consistently.
- Fail closed on authorization uncertainty.
- Add auditability for security-sensitive operations.
- Avoid returning internal metadata to end users unless explicitly required.

## 8) UX and Product Interaction Standards
- User-facing language must be clear, friendly, and non-technical.
- Avoid exposing raw backend/provider errors directly in UI.
- Ensure loading, error, success, and cancellation states are explicit and usable.
- Reduce friction; avoid unnecessary confirmation popups.

## 9) Communication Style (Agent to User)
- Be concise, direct, and action-oriented.
- Explain tradeoffs when relevant to decisions.
- Call out blockers early with specific required inputs.
- End with concrete next steps when natural.

## 10) Definition of Done
- Requested behavior is implemented and verified.
- No regressions introduced in adjacent flows.
- Security/privacy constraints preserved.
- Output is professional and ready for external review.
- Remaining risks and limitations are explicitly stated.
