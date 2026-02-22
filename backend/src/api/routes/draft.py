from fastapi import APIRouter, Depends

from src.auth.security import Principal, enforce_user_scope, get_current_principal
from src.core.config import settings
from src.core.errors import rate_limited, replay_detected
from src.core.models import DraftGenerateRequest, DraftGenerateResponse
from src.db.repositories import get_draft_by_request_id, write_audit_log
from src.db.session import SessionLocal
from src.services.rate_limiter import InMemoryRateLimiter
from src.services.workflow import DraftWorkflowService

router = APIRouter()
workflow = DraftWorkflowService()
rate_limiter = InMemoryRateLimiter(
    max_requests=settings.draft_rate_limit_requests,
    window_seconds=settings.draft_rate_limit_window_seconds,
)


@router.post("/draft/generate", response_model=DraftGenerateResponse)
def generate_draft(
    payload: DraftGenerateRequest,
    principal: Principal = Depends(get_current_principal),
) -> DraftGenerateResponse:
    enforce_user_scope(principal, payload.user_id)
    decision = rate_limiter.check(f"{principal.user_id}:draft_generate")
    if not decision.allowed:
        raise rate_limited("Too many draft generation requests", decision.retry_after_seconds)

    with SessionLocal() as db:
        existing = get_draft_by_request_id(db, payload.request_id)
    if existing is not None:
        raise replay_detected("Duplicate request_id detected")

    response = workflow.run(payload)
    with SessionLocal() as db:
        write_audit_log(
            db,
            request_id=response.request_id,
            actor_user_id=principal.user_id,
            action="draft.generate",
            resource=f"draft://{response.draft_id}",
            decision="allow",
            reason=f"model:{response.model_used}",
        )
        db.commit()
    return response
