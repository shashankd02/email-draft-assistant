from fastapi import APIRouter, Depends

from src.auth.security import Principal, enforce_user_scope, get_current_principal
from src.core.models import FeedbackRequest, FeedbackResponse
from src.db.repositories import record_feedback
from src.db.session import SessionLocal

router = APIRouter()


@router.post("/draft/feedback", response_model=FeedbackResponse)
def submit_feedback(
    payload: FeedbackRequest,
    principal: Principal = Depends(get_current_principal),
) -> FeedbackResponse:
    enforce_user_scope(principal, payload.user_id)
    with SessionLocal() as db:
        version = record_feedback(db, payload)
        db.commit()
    return FeedbackResponse(status="recorded", profile_update_version=version)
