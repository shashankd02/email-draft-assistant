from __future__ import annotations

from datetime import datetime, timedelta
from difflib import SequenceMatcher
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from src.core.models import FeedbackRequest
from src.db.models import AuditLog, Draft, EvalRun, EvalRunItem, FeedbackEvent, JudgeScore, ToolEvent, User, UserProfile, VoicePersona
from src.services.memory_vector import get_vector_memory_service


def ensure_user_exists(db: Session, user_id: str) -> None:
    user = db.get(User, user_id)
    if user is None:
        user = User(id=user_id, email=f"{user_id}@local.dev", role="user")
        db.add(user)
        db.flush()


def get_draft_by_request_id(db: Session, request_id: str) -> Draft | None:
    return db.query(Draft).filter(Draft.request_id == request_id).first()


def list_active_voice_personas(db: Session) -> list[dict[str, Any]]:
    rows = db.query(VoicePersona).filter(VoicePersona.active.is_(True)).order_by(VoicePersona.id.asc()).all()
    return [{"id": row.id, "name": row.name, "provider": row.provider} for row in rows]


def set_default_voice_persona(db: Session, user_id: str, voice_id: int) -> None:
    ensure_user_exists(db, user_id)
    persona = db.query(VoicePersona).filter(VoicePersona.id == voice_id, VoicePersona.active.is_(True)).first()
    if persona is None:
        raise ValueError("Voice persona not found or inactive")
    user = db.get(User, user_id)
    if user is None:
        raise ValueError("User not found")
    user.default_voice_id = voice_id


def get_default_voice_persona_id(db: Session, user_id: str) -> int | None:
    user = db.get(User, user_id)
    if user is None:
        return None
    return user.default_voice_id


def purge_retention_data(
    db: Session,
    *,
    drafts_days: int,
    logs_days: int,
) -> dict[str, int]:
    draft_cutoff = datetime.utcnow() - timedelta(days=max(1, drafts_days))
    logs_cutoff = datetime.utcnow() - timedelta(days=max(1, logs_days))

    old_draft_ids = list(db.scalars(select(Draft.id).where(Draft.created_at < draft_cutoff)).all())
    old_run_ids = list(db.scalars(select(EvalRun.run_id).where(EvalRun.created_at < logs_cutoff)).all())

    deleted_judge_scores = 0
    deleted_feedback_events = 0
    deleted_drafts = 0
    deleted_audit_logs = 0
    deleted_tool_events = 0
    deleted_eval_run_items = 0
    deleted_eval_runs = 0

    if old_draft_ids:
        deleted_judge_scores = db.execute(delete(JudgeScore).where(JudgeScore.draft_id.in_(old_draft_ids))).rowcount or 0
        deleted_feedback_events = db.execute(delete(FeedbackEvent).where(FeedbackEvent.draft_id.in_(old_draft_ids))).rowcount or 0
        deleted_drafts = db.execute(delete(Draft).where(Draft.id.in_(old_draft_ids))).rowcount or 0

    deleted_audit_logs = db.execute(delete(AuditLog).where(AuditLog.created_at < logs_cutoff)).rowcount or 0
    deleted_tool_events = db.execute(delete(ToolEvent).where(ToolEvent.created_at < logs_cutoff)).rowcount or 0

    if old_run_ids:
        deleted_eval_run_items = db.execute(delete(EvalRunItem).where(EvalRunItem.run_id.in_(old_run_ids))).rowcount or 0
        deleted_eval_runs = db.execute(delete(EvalRun).where(EvalRun.run_id.in_(old_run_ids))).rowcount or 0

    return {
        "judge_scores": deleted_judge_scores,
        "feedback_events": deleted_feedback_events,
        "drafts": deleted_drafts,
        "audit_logs": deleted_audit_logs,
        "tool_events": deleted_tool_events,
        "eval_run_items": deleted_eval_run_items,
        "eval_runs": deleted_eval_runs,
    }


def save_draft_and_scores(db: Session, payload: dict[str, Any]) -> None:
    ensure_user_exists(db, payload["user_id"])
    draft = Draft(
        id=payload["draft_id"],
        request_id=payload["request_id"],
        user_id=payload["user_id"],
        intent=payload["intent"],
        tone=payload["tone"],
        draft_text=payload["draft_text"],
        model_used=payload["model_used"],
        fallback_used=payload["fallback_used"],
        latency_ms=payload["latency_ms"],
    )
    db.add(draft)

    scores = payload["judge_scores"]
    score_row = JudgeScore(
        draft_id=payload["draft_id"],
        clarity=scores["clarity"],
        tone_match=scores["tone_match"],
        factuality=scores["factuality"],
        overall=scores["overall"],
        judge_model="gpt-4o",
    )
    db.add(score_row)


def record_feedback(db: Session, payload: FeedbackRequest) -> int:
    ensure_user_exists(db, payload.user_id)
    ratio = SequenceMatcher(None, payload.original_text, payload.final_text).ratio()

    event = FeedbackEvent(
        draft_id=payload.draft_id,
        user_id=payload.user_id,
        action=payload.action,
        feedback_tags=",".join(payload.feedback_tags) if payload.feedback_tags else None,
        diff_ratio=ratio,
    )
    db.add(event)

    profile = db.get(UserProfile, payload.user_id)
    if profile is None:
        profile = UserProfile(user_id=payload.user_id, version=1)
        db.add(profile)
    else:
        profile.version += 1
    memory = get_vector_memory_service()
    memory.upsert_profile_memory(
        payload.user_id,
        text=f"User edited draft from '{payload.original_text[:120]}' to '{payload.final_text[:120]}'",
        source="feedback",
    )
    if payload.feedback_tags:
        memory.upsert_style_preference(payload.user_id, text=";".join(payload.feedback_tags))

    return profile.version


def upsert_profile_fields(db: Session, user_id: str, fields: dict[str, Any]) -> int:
    ensure_user_exists(db, user_id)
    profile = db.get(UserProfile, user_id)
    if profile is None:
        profile = UserProfile(user_id=user_id, version=1, prefs_json=str(fields))
        db.add(profile)
    else:
        profile.version += 1
        profile.prefs_json = str(fields)
    memory = get_vector_memory_service()
    memory.upsert_profile_memory(user_id, text=str(fields), source="profile")
    return profile.version


def write_audit_log(
    db: Session,
    *,
    request_id: str | None,
    actor_user_id: str | None,
    action: str,
    resource: str | None,
    decision: str,
    reason: str | None = None,
) -> None:
    db.add(
        AuditLog(
            request_id=request_id,
            actor_user_id=actor_user_id,
            action=action,
            resource=resource,
            decision=decision,
            reason=reason,
        )
    )


def write_tool_event(
    db: Session,
    *,
    request_id: str | None,
    tool_name: str,
    status: str,
    latency_ms: int | None = None,
    payload_hash: str | None = None,
) -> None:
    db.add(
        ToolEvent(
            request_id=request_id or "unknown",
            tool_name=tool_name,
            status=status,
            latency_ms=latency_ms,
            payload_hash=payload_hash,
        )
    )


def save_eval_run(db: Session, *, run_id: str, actor_user_id: str, dataset: str, summary: dict[str, Any], results: list[dict[str, Any]]) -> None:
    pass_thresholds = summary.get("pass_thresholds", {})
    passed = all(bool(v) for v in pass_thresholds.values()) if pass_thresholds else False
    row = EvalRun(
        run_id=run_id,
        actor_user_id=actor_user_id,
        dataset=dataset,
        total_cases=int(summary.get("total_cases", 0)),
        avg_clarity=float(summary.get("avg_clarity", 0.0)),
        avg_tone_match=float(summary.get("avg_tone_match", 0.0)),
        avg_factuality=float(summary.get("avg_factuality", 0.0)),
        avg_overall=float(summary.get("avg_overall", 0.0)),
        passed=passed,
    )
    db.add(row)

    for item in results:
        scores = item.get("scores", {})
        db.add(
            EvalRunItem(
                run_id=run_id,
                request_id=str(item.get("request_id", "")),
                intent=str(item.get("intent", "")),
                tone=str(item.get("tone", "")),
                clarity=float(scores.get("clarity", 0.0)),
                tone_match=float(scores.get("tone_match", 0.0)),
                factuality=float(scores.get("factuality", 0.0)),
                overall=float(scores.get("overall", 0.0)),
                model_used=str(item.get("model_used", "")),
            )
        )


def list_eval_runs(db: Session, limit: int = 20) -> list[dict[str, Any]]:
    rows = db.query(EvalRun).order_by(EvalRun.created_at.desc()).limit(limit).all()
    output: list[dict[str, Any]] = []
    for row in rows:
        output.append(
            {
                "run_id": row.run_id,
                "actor_user_id": row.actor_user_id,
                "dataset": row.dataset,
                "total_cases": row.total_cases,
                "avg_clarity": row.avg_clarity,
                "avg_tone_match": row.avg_tone_match,
                "avg_factuality": row.avg_factuality,
                "avg_overall": row.avg_overall,
                "passed": row.passed,
                "created_at": row.created_at.isoformat(),
            }
        )
    return output


def get_eval_run_details(db: Session, run_id: str) -> dict[str, Any] | None:
    row = db.query(EvalRun).filter(EvalRun.run_id == run_id).first()
    if row is None:
        return None
    items = db.query(EvalRunItem).filter(EvalRunItem.run_id == run_id).order_by(EvalRunItem.id.asc()).all()
    return {
        "run_id": row.run_id,
        "actor_user_id": row.actor_user_id,
        "dataset": row.dataset,
        "total_cases": row.total_cases,
        "avg_clarity": row.avg_clarity,
        "avg_tone_match": row.avg_tone_match,
        "avg_factuality": row.avg_factuality,
        "avg_overall": row.avg_overall,
        "passed": row.passed,
        "created_at": row.created_at.isoformat(),
        "items": [
            {
                "request_id": item.request_id,
                "intent": item.intent,
                "tone": item.tone,
                "clarity": item.clarity,
                "tone_match": item.tone_match,
                "factuality": item.factuality,
                "overall": item.overall,
                "model_used": item.model_used,
            }
            for item in items
        ],
    }
