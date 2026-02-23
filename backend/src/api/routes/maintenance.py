from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.auth.security import Principal, get_current_principal
from src.core.config import settings
from src.db.repositories import delete_user_data, purge_retention_data
from src.db.session import SessionLocal
from src.services.memory_vector import get_vector_memory_service

router = APIRouter()


class RetentionPurgeRequest(BaseModel):
    drafts_days: int | None = None
    transcripts_days: int | None = None
    logs_days: int | None = None


class UserDeleteRequest(BaseModel):
    user_id: str


@router.post("/retention/purge")
def purge_retention(
    payload: RetentionPurgeRequest,
    principal: Principal = Depends(get_current_principal),
) -> dict:
    if principal.role != "admin":
        raise HTTPException(status_code=403, detail={"error_code": "ACCESS_DENIED", "message": "Admin role required"})

    drafts_days = payload.drafts_days if payload.drafts_days is not None else settings.retention_drafts_days
    transcripts_days = payload.transcripts_days if payload.transcripts_days is not None else settings.retention_transcripts_days
    logs_days = payload.logs_days if payload.logs_days is not None else settings.retention_logs_days
    with SessionLocal() as db:
        deleted = purge_retention_data(db, drafts_days=drafts_days, transcripts_days=transcripts_days, logs_days=logs_days)
        db.commit()
    return {
        "status": "ok",
        "policy_days": {
            "drafts_days": drafts_days,
            "transcripts_days": transcripts_days,
            "logs_days": logs_days,
        },
        "deleted": deleted,
    }


@router.post("/users/delete")
def admin_delete_user(
    payload: UserDeleteRequest,
    principal: Principal = Depends(get_current_principal),
) -> dict:
    if principal.role != "admin":
        raise HTTPException(status_code=403, detail={"error_code": "ACCESS_DENIED", "message": "Admin role required"})
    with SessionLocal() as db:
        deleted = delete_user_data(db, payload.user_id)
        db.commit()
    get_vector_memory_service().delete_user_memory(payload.user_id)
    return {"status": "ok", "user_id": payload.user_id, "deleted": deleted}
