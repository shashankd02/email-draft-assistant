from __future__ import annotations

from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class UserRole(str, Enum):
    admin = "admin"
    user = "user"


class DraftConstraint(BaseModel):
    max_paragraphs: int = 3
    must_include: list[str] = Field(default_factory=list)
    forbidden: list[str] = Field(default_factory=list)


class DraftMetadata(BaseModel):
    recipient_role: str = "general"
    language: str = "en"


class DraftGenerateRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    prompt: str
    intent: str = "informational"
    tone: str = "professional"
    constraints: DraftConstraint = Field(default_factory=DraftConstraint)
    metadata: DraftMetadata = Field(default_factory=DraftMetadata)


class JudgeScores(BaseModel):
    clarity: float
    tone_match: float
    factuality: float

    @property
    def overall(self) -> float:
        return round((self.clarity + self.tone_match + self.factuality) / 3.0, 2)


class DraftGenerateResponse(BaseModel):
    request_id: str
    status: str
    draft_id: str
    draft_text: str
    judge_scores: dict[str, float]
    model_used: str
    fallback_used: bool
    citations: list[str] = Field(default_factory=list)
    latency_ms: int


class FeedbackRequest(BaseModel):
    request_id: str
    draft_id: str
    user_id: str
    action: str
    original_text: str
    final_text: str
    feedback_tags: list[str] = Field(default_factory=list)


class FeedbackResponse(BaseModel):
    status: str
    profile_update_version: int


class VoiceSegment(BaseModel):
    speaker: str
    start_ms: int
    end_ms: int
    text: str


class VoiceTranscribeResponse(BaseModel):
    request_id: str
    transcript: str
    segments: list[VoiceSegment]
    confidence: float


class WorkflowState(BaseModel):
    request_id: str
    user_id: str
    prompt: str
    intent: str
    tone: str
    constraints: dict[str, Any]
    metadata: dict[str, Any]
    context_sources: list[str] = Field(default_factory=list)
    draft_versions: list[str] = Field(default_factory=list)
    judge_scores: dict[str, float] = Field(default_factory=dict)
    fallback_count: int = 0
    selected_model: str = "gpt-4o"
    policy_flags: list[str] = Field(default_factory=list)
    final_status: str = "in_progress"
