from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Callable

from openai import OpenAI

from src.core.config import settings


@dataclass
class DraftGenerationResult:
    draft_text: str
    model_used: str
    provider: str


class StructuredOutputError(RuntimeError):
    pass


class LLMProvider:
    def generate_email_draft(
        self,
        *,
        prompt: str,
        intent: str,
        tone: str,
        constraints: dict,
        metadata: dict,
    ) -> DraftGenerationResult:
        raise NotImplementedError


class OpenAILLMProvider(LLMProvider):
    def __init__(self) -> None:
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required for OpenAI LLM provider")
        self.client = OpenAI(api_key=settings.openai_api_key)

    def generate_email_draft(
        self,
        *,
        prompt: str,
        intent: str,
        tone: str,
        constraints: dict,
        metadata: dict,
    ) -> DraftGenerationResult:
        search_context = metadata.get("search_context", {})
        citations = search_context.get("citations", []) if isinstance(search_context, dict) else []
        grounding_note = (
            f"Web context citations available: {citations}\n"
            if citations
            else "No external citations available. Do not invent facts; use neutral wording for unknown details.\n"
        )
        system_prompt = (
            "You are an enterprise email drafting assistant. "
            "Generate concise, clear, and professional email drafts with strict tone control. "
            "Do not include private data or fabricated facts. "
            "If details are missing, keep placeholders instead of guessing. "
            "Return JSON only."
        )
        user_prompt = (
            f"Intent: {intent}\n"
            f"Tone: {tone}\n"
            f"Constraints: {constraints}\n"
            f"Metadata: {metadata}\n"
            f"{grounding_note}"
            f"Request: {prompt}\n\n"
            'Return JSON with this schema exactly: {"draft_text":"<email text>"}'
        )
        raw = self._complete_json(system_prompt, user_prompt)
        parsed = self._parse_structured_draft(raw)
        if parsed is None:
            repair_prompt = (
                "Convert the following content into valid JSON with this exact schema: "
                '{"draft_text":"<email text>"}\n\n'
                f"CONTENT:\n{raw}"
            )
            repaired_raw = self._complete_json(
                "You repair malformed output to strict JSON. Return JSON only.",
                repair_prompt,
            )
            parsed = self._parse_structured_draft(repaired_raw)
            if parsed is None:
                raise StructuredOutputError("Structured output validation failed after one repair attempt.")
        return DraftGenerationResult(draft_text=parsed, model_used=settings.openai_text_model, provider="openai")

    def _complete_json(self, system_prompt: str, user_prompt: str) -> str:
        result = self.client.chat.completions.create(
            model=settings.openai_text_model,
            temperature=0.2,
            timeout=settings.hard_timeout_e2e_seconds,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return (result.choices[0].message.content or "").strip()

    def _parse_structured_draft(self, content: str) -> str | None:
        if not content:
            return None
        try:
            payload = json.loads(content)
        except json.JSONDecodeError:
            return None
        text = str(payload.get("draft_text", "")).strip() if isinstance(payload, dict) else ""
        return text or None


class RoutingLLMProvider(LLMProvider):
    def __init__(self, providers: list[Callable[[], LLMProvider]]) -> None:
        self._provider_factories = providers

    def generate_email_draft(
        self,
        *,
        prompt: str,
        intent: str,
        tone: str,
        constraints: dict,
        metadata: dict,
    ) -> DraftGenerationResult:
        last_error: Exception | None = None
        for factory in self._provider_factories:
            try:
                provider = factory()
                return provider.generate_email_draft(
                    prompt=prompt,
                    intent=intent,
                    tone=tone,
                    constraints=constraints,
                    metadata=metadata,
                )
            except Exception as exc:  # pragma: no cover - provider-specific errors
                last_error = exc
                continue
        if last_error is not None:
            raise last_error
        raise RuntimeError("No LLM providers configured")


def get_llm_provider() -> LLMProvider:
    provider_factories: list[Callable[[], LLMProvider]] = []
    if settings.openai_api_key:
        provider_factories.append(lambda: OpenAILLMProvider())
    if not provider_factories:
        raise RuntimeError("No real LLM provider configured. Set OPENAI_API_KEY.")
    return RoutingLLMProvider(provider_factories)
