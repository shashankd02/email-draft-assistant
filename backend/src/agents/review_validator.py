import json
import re

from openai import OpenAI

from src.core.config import settings
from src.core.models import WorkflowState


class ReviewValidatorAgent:
    EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
    PHONE_RE = re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")
    SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")

    def __init__(self) -> None:
        self._client: OpenAI | None = None

    def _client_or_raise(self) -> OpenAI:
        if self._client is not None:
            return self._client
        if not settings.openai_api_key:
            raise RuntimeError("Review validator requires OPENAI_API_KEY in strict mode.")
        self._client = OpenAI(api_key=settings.openai_api_key)
        return self._client

    def _score_with_model(self, state: WorkflowState, latest: str) -> dict[str, float]:
        client = self._client_or_raise()
        citations = list((state.metadata.get("search_context", {}) or {}).get("citations", []))
        system_prompt = (
            "You are a strict email quality reviewer. "
            "Score the draft from 0 to 100 for clarity, tone_match, and factuality. "
            "Use conservative scoring. Return JSON only."
        )
        user_prompt = (
            f"Requested intent: {state.intent}\n"
            f"Requested tone: {state.tone}\n"
            f"Citations available: {citations}\n"
            f"Constraints: {state.constraints}\n"
            f"Draft text:\n{latest}\n\n"
            'Return JSON: {"clarity": number, "tone_match": number, "factuality": number}.'
        )
        response = client.chat.completions.create(
            model=settings.openai_text_model,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        content = response.choices[0].message.content or "{}"
        parsed = json.loads(content)
        clarity = max(0.0, min(100.0, float(parsed.get("clarity", 0.0))))
        tone_match = max(0.0, min(100.0, float(parsed.get("tone_match", 0.0))))
        factuality = max(0.0, min(100.0, float(parsed.get("factuality", 0.0))))
        return {
            "clarity": round(clarity, 2),
            "tone_match": round(tone_match, 2),
            "factuality": round(factuality, 2),
            "overall": round((clarity + tone_match + factuality) / 3.0, 2),
        }

    def _score_with_rules(self, state: WorkflowState, latest: str) -> dict[str, float]:
        length = len(latest.strip())
        paragraph_count = max(1, len([line for line in latest.split("\n") if line.strip()]))
        max_paragraphs = int(state.constraints.get("max_paragraphs", 3))
        clarity = 94.0 if length >= 120 else 90.0 if length >= 60 else 84.0
        if paragraph_count > max_paragraphs:
            clarity -= 8.0

        tone_tokens = {
            "professional": ["dear", "regards", "thank you"],
            "casual": ["hi", "thanks", "let me know"],
            "assertive": ["please", "required", "confirm"],
            "empathetic": ["understand", "appreciate", "sorry"],
        }
        requested_tone = str(state.tone).lower()
        candidates = tone_tokens.get(requested_tone, [])
        lower = latest.lower()
        tone_hits = sum(1 for token in candidates if token in lower)
        tone_match = 78.0 + min(18.0, tone_hits * 6.0)

        citations = list((state.metadata.get("search_context", {}) or {}).get("citations", []))
        has_source = bool(citations)
        factuality = 90.0 if has_source else 85.0
        if "http" in lower and not has_source:
            factuality -= 8.0
        clarity = max(0.0, min(100.0, clarity))
        tone_match = max(0.0, min(100.0, tone_match))
        factuality = max(0.0, min(100.0, factuality))
        overall = (clarity + tone_match + factuality) / 3.0
        return {
            "clarity": round(clarity, 2),
            "tone_match": round(tone_match, 2),
            "factuality": round(factuality, 2),
            "overall": round(overall, 2),
        }

    def _ensemble_scores(self, model_scores: dict[str, float], rule_scores: dict[str, float]) -> dict[str, float]:
        # Weighted ensemble: model judge + deterministic rule judge.
        wm = 0.7
        wr = 0.3
        clarity = (model_scores["clarity"] * wm) + (rule_scores["clarity"] * wr)
        tone = (model_scores["tone_match"] * wm) + (rule_scores["tone_match"] * wr)
        factuality = (model_scores["factuality"] * wm) + (rule_scores["factuality"] * wr)
        return {
            "clarity": round(clarity, 2),
            "tone_match": round(tone, 2),
            "factuality": round(factuality, 2),
            "overall": round((clarity + tone + factuality) / 3.0, 2),
        }

    def run(self, state: WorkflowState) -> WorkflowState:
        if state.final_status in {"blocked", "retry", "upstream_failed"}:
            return state
        latest = state.draft_versions[-1] if state.draft_versions else ""
        if not latest:
            state.policy_flags.append("empty_draft")
            state.final_status = "retry"
            return state

        forbidden = [str(item).lower() for item in state.constraints.get("forbidden", [])]
        pii_requested = "pii" in forbidden
        pii_found = any(
            matcher.search(latest) for matcher in (self.EMAIL_RE, self.PHONE_RE, self.SSN_RE)
        )
        if pii_requested and pii_found:
            state.policy_flags.append("pii_leak_detected")
            state.final_status = "blocked"

        rule_scores = self._score_with_rules(state, latest)
        model_scores = None
        model_error: str | None = None
        try:
            model_scores = self._score_with_model(state, latest)
        except Exception as exc:
            model_error = type(exc).__name__

        if model_scores is not None:
            state.judge_scores = self._ensemble_scores(model_scores, rule_scores)
            state.metadata["judge_components"] = {
                "model_judge": model_scores,
                "rule_judge": rule_scores,
                "ensemble_weights": {"model": 0.7, "rules": 0.3},
            }
        else:
            # Deterministic fallback for test/local flows when model judge is unavailable.
            state.judge_scores = rule_scores
            state.metadata["judge_components"] = {
                "rule_judge": rule_scores,
                "model_judge_error": model_error or "unavailable",
                "ensemble_weights": {"model": 0.0, "rules": 1.0},
            }
        return state
