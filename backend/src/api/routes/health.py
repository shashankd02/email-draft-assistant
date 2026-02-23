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

    llm_provider = "ok" if settings.openai_api_key else "degraded"
    stt_provider = "ok" if (settings.deepgram_api_key or settings.openai_api_key) else "degraded"
    tts_provider = "ok" if settings.openai_api_key else "degraded"
    search_provider = "ok" if settings.tavily_api_key else "degraded"

    strict_requirements = {
        "llm_provider": llm_provider == "ok",
        "stt_provider": stt_provider == "ok",
        "tts_provider": tts_provider == "ok",
        "search_provider": search_provider == "ok",
    }
    strict_ready = all(strict_requirements.values())
    status = "ok"
    if settings.strict_provider_mode and not strict_ready:
        status = "degraded"

    return {
        "status": status,
        "strict_provider_mode": settings.strict_provider_mode,
        "strict_provider_ready": strict_ready,
        "strict_provider_requirements": strict_requirements,
        "dependencies": {
            "postgres": postgres_status,
            "chroma": chroma_status,
            "llm_provider": llm_provider,
            "stt_provider": stt_provider,
            "tts_provider": tts_provider,
            "search_provider": search_provider,
        },
    }
