from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.auth.security import Principal, get_current_principal
from src.core.config import settings
from src.db.repositories import purge_retention_data
from src.db.session import SessionLocal

router = APIRouter()


class RetentionPurgeRequest(BaseModel):
    drafts_days: int | None = None
    logs_days: int | None = None


@router.post("/retention/purge")
def purge_retention(
    payload: RetentionPurgeRequest,
    principal: Principal = Depends(get_current_principal),
) -> dict:
    if principal.role != "admin":
        raise HTTPException(status_code=403, detail={"error_code": "ACCESS_DENIED", "message": "Admin role required"})

    drafts_days = payload.drafts_days if payload.drafts_days is not None else settings.retention_drafts_days
    logs_days = payload.logs_days if payload.logs_days is not None else settings.retention_logs_days
    with SessionLocal() as db:
        deleted = purge_retention_data(db, drafts_days=drafts_days, logs_days=logs_days)
        db.commit()
    return {
        "status": "ok",
        "policy_days": {
            "drafts_days": drafts_days,
            "logs_days": logs_days,
        },
        "deleted": deleted,
    }
