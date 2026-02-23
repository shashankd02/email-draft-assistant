import asyncio
import contextlib
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import auth, draft, voice, health, feedback, mcp, evaluation, maintenance, observability
from src.core.config import settings
from src.core.observability import RequestContextMiddleware
from src.core.retention_scheduler import retention_scheduler_loop


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = None
    if settings.retention_scheduler_enabled:
        task = asyncio.create_task(retention_scheduler_loop())
    try:
        yield
    finally:
        if task:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task

app = FastAPI(title="AI Email Assistant API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestContextMiddleware)

app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(draft.router, prefix="/api/v1", tags=["draft"])
app.include_router(voice.router, prefix="/api/v1", tags=["voice"])
app.include_router(feedback.router, prefix="/api/v1", tags=["feedback"])
app.include_router(mcp.router, prefix="/api/v1/mcp", tags=["mcp"])
app.include_router(evaluation.router, prefix="/api/v1/evaluation", tags=["evaluation"])
app.include_router(maintenance.router, prefix="/api/v1/admin", tags=["maintenance"])
app.include_router(observability.router, prefix="/api/v1/observability", tags=["observability"])


@app.get("/")
def root() -> dict[str, str]:
    return {"service": "ai-email-assistant", "status": "ok"}
