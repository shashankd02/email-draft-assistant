from __future__ import annotations

import io
from dataclasses import dataclass
from typing import Callable

import httpx
from openai import OpenAI

from src.core.config import settings
from src.core.models import VoiceSegment


@dataclass
class TranscriptionResult:
    transcript: str
    segments: list[VoiceSegment]
    confidence: float
    provider: str


class VoiceProvider:
    async def transcribe(self, audio_bytes: bytes, language: str, mime_type: str = "audio/wav") -> TranscriptionResult:
        raise NotImplementedError


class OpenAIVoiceProvider(VoiceProvider):
    def __init__(self) -> None:
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required for OpenAI voice provider")
        self.client = OpenAI(api_key=settings.openai_api_key)

    async def transcribe(self, audio_bytes: bytes, language: str, mime_type: str = "audio/wav") -> TranscriptionResult:
        # OpenAI SDK call is sync; keeping this adapter async for route compatibility.
        _ = mime_type
        file_obj = io.BytesIO(audio_bytes)
        file_obj.name = "audio.wav"
        result = self.client.audio.transcriptions.create(
            model=settings.openai_stt_model,
            file=file_obj,
            language=language,
        )
        text = getattr(result, "text", "") or ""
        return TranscriptionResult(
            transcript=text,
            segments=[VoiceSegment(speaker="S1", start_ms=0, end_ms=max(1000, len(text) * 40), text=text)],
            confidence=0.92,
            provider="openai",
        )


class DeepgramVoiceProvider(VoiceProvider):
    async def transcribe(self, audio_bytes: bytes, language: str, mime_type: str = "audio/webm") -> TranscriptionResult:
        if not settings.deepgram_api_key:
            raise ValueError("DEEPGRAM_API_KEY is required for Deepgram provider")
        params = {"model": "nova-2", "language": language, "diarize": "true"}
        headers = {
            "Authorization": f"Token {settings.deepgram_api_key}",
            "Content-Type": mime_type or "audio/webm",
        }
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post("https://api.deepgram.com/v1/listen", params=params, headers=headers, content=audio_bytes)
            response.raise_for_status()
            data = response.json()

        channel = ((data.get("results", {}) or {}).get("channels", [{}]) or [{}])[0]
        alternatives = channel.get("alternatives", [{}]) or [{}]
        alt = alternatives[0] if alternatives else {}
        transcript = str(alt.get("transcript", "")).strip()
        words = alt.get("words", []) or []
        segments: list[VoiceSegment] = []
        for word in words[:100]:
            speaker = f"S{int(word.get('speaker', 0)) + 1}" if word.get("speaker") is not None else "S1"
            start_ms = int(float(word.get("start", 0.0)) * 1000)
            end_ms = int(float(word.get("end", 0.0)) * 1000)
            segments.append(VoiceSegment(speaker=speaker, start_ms=start_ms, end_ms=end_ms, text=str(word.get("punctuated_word") or word.get("word") or "")))
        if not segments and transcript:
            segments = [VoiceSegment(speaker="S1", start_ms=0, end_ms=max(1200, len(transcript) * 35), text=transcript)]
        return TranscriptionResult(
            transcript=transcript or "No speech detected.",
            segments=segments,
            confidence=float(alt.get("confidence", 0.85)),
            provider="deepgram",
        )


class RoutingVoiceProvider(VoiceProvider):
    def __init__(self, providers: list[Callable[[], VoiceProvider]]) -> None:
        self._provider_factories = providers

    async def transcribe(self, audio_bytes: bytes, language: str, mime_type: str = "audio/wav") -> TranscriptionResult:
        last_error: Exception | None = None
        for factory in self._provider_factories:
            try:
                provider = factory()
                return await provider.transcribe(audio_bytes, language, mime_type)
            except Exception as exc:  # pragma: no cover - external provider errors
                last_error = exc
                continue
        if last_error is not None:
            raise last_error
        raise RuntimeError("No voice providers configured")


def get_voice_provider() -> VoiceProvider:
    providers: list[Callable[[], VoiceProvider]] = []
    if settings.deepgram_api_key:
        providers.append(lambda: DeepgramVoiceProvider())
    if settings.openai_api_key:
        providers.append(lambda: OpenAIVoiceProvider())
    if not providers and settings.strict_provider_mode:
        raise RuntimeError("No real voice provider configured. Set DEEPGRAM_API_KEY or OPENAI_API_KEY.")
    if not providers:
        raise RuntimeError("Voice provider unavailable")
    return RoutingVoiceProvider(providers)
