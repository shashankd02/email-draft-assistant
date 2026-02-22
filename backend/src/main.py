from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import auth, draft, voice, health, feedback, mcp, evaluation, maintenance
from src.core.config import settings
from src.core.observability import RequestContextMiddleware

app = FastAPI(title="AI Email Assistant API", version="0.1.0")

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


@app.get("/")
def root() -> dict[str, str]:
    return {"service": "ai-email-assistant", "status": "ok"}
