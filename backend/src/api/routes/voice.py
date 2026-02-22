from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from src.auth.security import Principal, enforce_user_scope, get_current_principal
from src.core.models import VoiceSegment, VoiceTranscribeResponse
from src.db.repositories import get_default_voice_persona_id, list_active_voice_personas, set_default_voice_persona
from src.db.session import SessionLocal
from src.services.voice_provider import get_voice_provider

router = APIRouter()


@router.post("/voice/transcribe", response_model=VoiceTranscribeResponse)
async def transcribe_voice(
    audio_file: UploadFile = File(...),
    user_id: str = Form(...),
    language: str = Form("en"),
    principal: Principal = Depends(get_current_principal),
) -> VoiceTranscribeResponse:
    enforce_user_scope(principal, user_id)
    audio_bytes = await audio_file.read()
    provider = get_voice_provider()
    result = await provider.transcribe(audio_bytes, language, audio_file.content_type or "audio/webm")
    return VoiceTranscribeResponse(
        request_id=str(uuid4()),
        transcript=result.transcript,
        segments=result.segments
        if result.segments
        else [VoiceSegment(speaker="S1", start_ms=0, end_ms=2400, text=result.transcript)],
        confidence=result.confidence,
    )


class SetDefaultVoiceRequest(BaseModel):
    user_id: str
    voice_id: int


@router.get("/voice/personas")
def list_voice_personas(principal: Principal = Depends(get_current_principal)) -> dict:
    with SessionLocal() as db:
        personas = list_active_voice_personas(db)
        default_voice_id = get_default_voice_persona_id(db, principal.user_id)
    return {"personas": personas, "default_voice_id": default_voice_id}


@router.post("/voice/personas/default")
def set_default_voice(
    payload: SetDefaultVoiceRequest,
    principal: Principal = Depends(get_current_principal),
) -> dict:
    enforce_user_scope(principal, payload.user_id)
    with SessionLocal() as db:
        try:
            set_default_voice_persona(db, payload.user_id, payload.voice_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail={"error_code": "NOT_FOUND", "message": str(exc)}) from exc
        db.commit()
    return {"status": "ok", "user_id": payload.user_id, "default_voice_id": payload.voice_id}
