from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str | None] = mapped_column(String(512), nullable=True)
    role: Mapped[str] = mapped_column(String(32), default="user", index=True)
    default_voice_id: Mapped[int | None] = mapped_column(ForeignKey("voice_personas.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class VoicePersona(Base):
    __tablename__ = "voice_personas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), unique=True)
    provider: Mapped[str] = mapped_column(String(64))
    provider_voice_key: Mapped[str] = mapped_column(String(128))
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class UserProfile(Base):
    __tablename__ = "user_profiles"

    user_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.id"), primary_key=True)
    preferred_tone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    organization: Mapped[str | None] = mapped_column(String(255), nullable=True)
    signature: Mapped[str | None] = mapped_column(Text, nullable=True)
    prefs_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Draft(Base):
    __tablename__ = "drafts"
    __table_args__ = (UniqueConstraint("request_id", name="uq_drafts_request_id"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    request_id: Mapped[str] = mapped_column(String(64), index=True)
    user_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.id"), index=True)
    intent: Mapped[str] = mapped_column(String(64))
    tone: Mapped[str] = mapped_column(String(64))
    draft_text: Mapped[str] = mapped_column(Text)
    model_used: Mapped[str] = mapped_column(String(128))
    fallback_used: Mapped[bool] = mapped_column(Boolean, default=False)
    latency_ms: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class JudgeScore(Base):
    __tablename__ = "judge_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    draft_id: Mapped[str] = mapped_column(String(64), ForeignKey("drafts.id"), index=True)
    clarity: Mapped[float] = mapped_column(Float)
    tone_match: Mapped[float] = mapped_column(Float)
    factuality: Mapped[float] = mapped_column(Float)
    overall: Mapped[float] = mapped_column(Float)
    judge_model: Mapped[str] = mapped_column(String(128), default="gpt-4o")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ToolEvent(Base):
    __tablename__ = "tool_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    request_id: Mapped[str] = mapped_column(String(64), index=True)
    tool_name: Mapped[str] = mapped_column(String(128), index=True)
    status: Mapped[str] = mapped_column(String(32))
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    payload_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    request_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    actor_user_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    action: Mapped[str] = mapped_column(String(128))
    resource: Mapped[str | None] = mapped_column(String(255), nullable=True)
    decision: Mapped[str] = mapped_column(String(32))
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class FeedbackEvent(Base):
    __tablename__ = "feedback_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    draft_id: Mapped[str] = mapped_column(String(64), ForeignKey("drafts.id"), index=True)
    user_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.id"), index=True)
    action: Mapped[str] = mapped_column(String(64))
    feedback_tags: Mapped[str | None] = mapped_column(Text, nullable=True)
    diff_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class EvalRun(Base):
    __tablename__ = "eval_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    actor_user_id: Mapped[str] = mapped_column(String(64), index=True)
    dataset: Mapped[str] = mapped_column(String(64))
    total_cases: Mapped[int] = mapped_column(Integer)
    avg_clarity: Mapped[float] = mapped_column(Float)
    avg_tone_match: Mapped[float] = mapped_column(Float)
    avg_factuality: Mapped[float] = mapped_column(Float)
    avg_overall: Mapped[float] = mapped_column(Float)
    passed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class EvalRunItem(Base):
    __tablename__ = "eval_run_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(String(64), ForeignKey("eval_runs.run_id"), index=True)
    request_id: Mapped[str] = mapped_column(String(64))
    intent: Mapped[str] = mapped_column(String(64))
    tone: Mapped[str] = mapped_column(String(64))
    clarity: Mapped[float] = mapped_column(Float)
    tone_match: Mapped[float] = mapped_column(Float)
    factuality: Mapped[float] = mapped_column(Float)
    overall: Mapped[float] = mapped_column(Float)
    model_used: Mapped[str] = mapped_column(String(128))
