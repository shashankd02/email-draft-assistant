from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from src.auth.security import Principal, get_current_principal
from src.core.config import settings
from src.core.metrics import get_metrics_store
from src.db.repositories import get_global_observability_snapshot, list_recent_draft_activity
from src.db.session import SessionLocal

router = APIRouter()

WINDOW_TO_HOURS = {
    "24h": 24,
    "7d": 24 * 7,
    "30d": 24 * 30,
}


class LangSmithConfigRequest(BaseModel):
    enabled: bool
    api_key: str | None = None
    project: str | None = None


@router.get("/metrics")
def get_metrics(
    window: Literal["24h", "7d", "30d"] = Query("24h"),
    principal: Principal = Depends(get_current_principal),
) -> dict:
    if principal.role != "admin":
        raise HTTPException(status_code=403, detail={"error_code": "ACCESS_DENIED", "message": "Admin role required"})
    with SessionLocal() as db:
        global_snapshot = get_global_observability_snapshot(db, window_hours=WINDOW_TO_HOURS[window])
        recent_activity = list_recent_draft_activity(db, limit=20)
    return {
        "status": "ok",
        "window": window,
        "live_metrics": get_metrics_store().snapshot(),
        "global_metrics": global_snapshot,
        "recent_activity": recent_activity,
        "integrations": {
            "langsmith": {
                "enabled": bool(settings.langsmith_tracing and settings.langsmith_api_key),
                "tracing_flag": bool(settings.langsmith_tracing),
                "project": settings.langsmith_project,
                "configured": bool(settings.langsmith_api_key),
            },
        },
    }


@router.get("/alerts")
def get_alerts(
    window: Literal["24h", "7d", "30d"] = Query("24h"),
    principal: Principal = Depends(get_current_principal),
) -> dict:
    if principal.role != "admin":
        raise HTTPException(status_code=403, detail={"error_code": "ACCESS_DENIED", "message": "Admin role required"})
    live_snapshot = get_metrics_store().snapshot()
    workflow = live_snapshot.get("workflow", {})
    outcomes = workflow.get("outcomes", {}) or {}
    errors = workflow.get("errors", {}) or {}
    fallback = workflow.get("fallback", {}) or {}
    total = max(1, int(workflow.get("count", 0)))

    live_p95_ms = float(workflow.get("p95_ms", 0.0))
    live_fallback_rate = float(fallback.get("triggered", 0)) / total
    provider_error_count = int(errors.get("provider_unavailable", 0)) + int(errors.get("draft_provider_error", 0))
    live_provider_error_rate = provider_error_count / total
    safety_fail_count = int(errors.get("jailbreak_detected", 0)) + int(errors.get("pii_leak_detected", 0))
    live_safety_failure_rate = safety_fail_count / total

    with SessionLocal() as db:
        global_snapshot = get_global_observability_snapshot(db, window_hours=WINDOW_TO_HOURS[window])
    global_p95_ms = float(global_snapshot.get("latency", {}).get("p95_latency_ms_in_window", 0.0))
    global_fallback_rate = float(global_snapshot.get("quality", {}).get("fallback_rate", 0.0))

    alerts = {
        "live_p95_latency_breach": live_p95_ms > settings.alert_p95_latency_ms_threshold,
        "global_p95_latency_breach_in_window": global_p95_ms > settings.alert_p95_latency_ms_threshold,
        "live_fallback_rate_spike": live_fallback_rate > settings.alert_fallback_rate_threshold,
        "global_fallback_rate_spike": global_fallback_rate > settings.alert_fallback_rate_threshold,
        "live_provider_error_rate_breach": live_provider_error_rate > settings.alert_provider_error_rate_threshold,
        "live_safety_failure_rate_breach": live_safety_failure_rate > settings.alert_safety_failure_rate_threshold,
    }
    return {
        "status": "ok",
        "thresholds": {
            "p95_latency_ms": settings.alert_p95_latency_ms_threshold,
            "fallback_rate": settings.alert_fallback_rate_threshold,
            "provider_error_rate": settings.alert_provider_error_rate_threshold,
            "safety_failure_rate": settings.alert_safety_failure_rate_threshold,
        },
        "current": {
            "live": {
                "p95_latency_ms": live_p95_ms,
                "fallback_rate": round(live_fallback_rate, 4),
                "provider_error_rate": round(live_provider_error_rate, 4),
                "safety_failure_rate": round(live_safety_failure_rate, 4),
                "total_workflows": total,
                "outcomes": outcomes,
            },
            "global": {
                "window": window,
                "p95_latency_ms_in_window": round(global_p95_ms, 2),
                "fallback_rate": round(global_fallback_rate, 4),
                "totals": global_snapshot.get("totals", {}),
                "activity": global_snapshot.get("activity", {}),
                "quality": global_snapshot.get("quality", {}),
            },
        },
        "alerts": alerts,
    }


@router.post("/integrations/langsmith")
def configure_langsmith(
    payload: LangSmithConfigRequest,
    principal: Principal = Depends(get_current_principal),
) -> dict:
    if principal.role != "admin":
        raise HTTPException(status_code=403, detail={"error_code": "ACCESS_DENIED", "message": "Admin role required"})

    settings.langsmith_tracing = bool(payload.enabled)
    if payload.project:
        settings.langsmith_project = payload.project.strip() or settings.langsmith_project
    if payload.api_key is not None:
        normalized = payload.api_key.strip()
        settings.langsmith_api_key = normalized or None

    return {
        "status": "ok",
        "langsmith": {
            "enabled": bool(settings.langsmith_tracing and settings.langsmith_api_key),
            "tracing_flag": bool(settings.langsmith_tracing),
            "project": settings.langsmith_project,
            "configured": bool(settings.langsmith_api_key),
        },
        "note": "Runtime configuration updated. Persist values in backend/.env for restart durability.",
    }
