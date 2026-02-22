from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from openai import OpenAI

from src.core.config import settings


@dataclass
class DraftGenerationResult:
    draft_text: str
    model_used: str
    provider: str


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
            "If details are missing, keep placeholders instead of guessing."
        )
        user_prompt = (
            f"Intent: {intent}\n"
            f"Tone: {tone}\n"
            f"Constraints: {constraints}\n"
            f"Metadata: {metadata}\n"
            f"{grounding_note}"
            f"Request: {prompt}\n\n"
            "Return only the final email text."
        )
        result = self.client.chat.completions.create(
            model=settings.openai_text_model,
            temperature=0.3,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        text = result.choices[0].message.content or ""
        return DraftGenerationResult(draft_text=text.strip(), model_used=settings.openai_text_model, provider="openai")


class TemplateLLMProvider(LLMProvider):
    def generate_email_draft(
        self,
        *,
        prompt: str,
        intent: str,
        tone: str,
        constraints: dict,
        metadata: dict,
    ) -> DraftGenerationResult:
        opener = {
            "professional": "Dear Team,",
            "casual": "Hi everyone,",
            "assertive": "Team,",
            "empathetic": "Hello team,",
        }.get(tone, "Dear Team,")

        body = (
            f"{opener}\n\n"
            f"I am writing regarding: {prompt}. "
            f"This message is categorized as '{intent}' and follows the requested '{tone}' tone.\n\n"
            "Please review and let me know if you would like any adjustments before sending.\n\n"
            "Best regards,\nYour Name"
        )
        return DraftGenerationResult(draft_text=body, model_used="template-fallback", provider="local")


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
        provider_factories.append(lambda: TemplateLLMProvider())
    return RoutingLLMProvider(provider_factories)
