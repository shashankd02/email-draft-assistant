from __future__ import annotations

import base64
from dataclasses import dataclass

from openai import OpenAI

from src.core.config import settings


@dataclass
class TTSResult:
    audio_base64: str
    mime_type: str
    provider: str


class TTSProvider:
    def synthesize(self, text: str, persona_id: str | None = None) -> TTSResult:
        raise NotImplementedError


class OpenAITTSProvider(TTSProvider):
    def __init__(self) -> None:
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required for OpenAI TTS provider")
        self.client = OpenAI(api_key=settings.openai_api_key)

    def synthesize(self, text: str, persona_id: str | None = None) -> TTSResult:
        _ = persona_id
        try:
            response = self.client.audio.speech.create(
                model=settings.openai_tts_model,
                voice=settings.openai_tts_voice,
                input=text,
                response_format="mp3",
            )
        except TypeError:
            # Compatibility fallback for older/newer SDK variants.
            response = self.client.audio.speech.create(
                model=settings.openai_tts_model,
                voice=settings.openai_tts_voice,
                input=text,
            )
        audio_bytes = response.read()
        return TTSResult(
            audio_base64=base64.b64encode(audio_bytes).decode("utf-8"),
            mime_type="audio/mpeg",
            provider="openai",
        )


def get_tts_provider() -> TTSProvider:
    if settings.openai_api_key:
        return OpenAITTSProvider()
    if settings.strict_provider_mode:
        raise RuntimeError("No real TTS provider configured. Set OPENAI_API_KEY.")
    raise RuntimeError("TTS provider unavailable")
