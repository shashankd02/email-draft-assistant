from fastapi import APIRouter
from sqlalchemy import text

from src.core.config import settings
from src.db.session import SessionLocal
from src.services.memory_vector import get_vector_memory_service

router = APIRouter()


@router.get("/health")
def health() -> dict:
    postgres_status = "unknown"
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        postgres_status = "ok"
    except Exception:
        postgres_status = "degraded"

    chroma_status = "ok" if get_vector_memory_service().is_available() else "degraded"

    if settings.openai_api_key:
        llm_primary = "ok"
        llm_secondary = "ok"
    else:
        llm_primary = "degraded"
        llm_secondary = "ok"

    return {
        "status": "ok",
        "dependencies": {
            "postgres": postgres_status,
            "chroma": chroma_status,
            "llm_provider_primary": llm_primary,
            "llm_provider_secondary": llm_secondary,
        },
    }
