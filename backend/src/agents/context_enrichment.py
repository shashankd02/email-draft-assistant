from __future__ import annotations

import re

from src.core.models import WorkflowState
from src.services.search_provider import get_search_provider


class ContextEnrichmentAgent:
    CONTEXT_TRIGGERS = (
        r"\bweather\b",
        r"\bforecast\b",
        r"\btemperature\b",
        r"\bnews\b",
        r"\bstock\b",
        r"\bprice\b",
        r"\bscore\b",
        r"\bcompetition\b",
        r"\btoday\b",
        r"\btomorrow\b",
        r"\bthis week\b",
    )

    def _needs_web_context(self, state: WorkflowState) -> bool:
        text = state.prompt.lower()
        if state.metadata.get("force_web_context") is True:
            return True
        return any(re.search(pattern, text) for pattern in self.CONTEXT_TRIGGERS)

    def run(self, state: WorkflowState) -> WorkflowState:
        if state.final_status == "blocked":
            return state
        if not self._needs_web_context(state):
            return state

        try:
            result = get_search_provider().search(query=state.prompt, recency_days=7)
            state.metadata["search_context"] = {
                "citations": result.citations,
                "confidence": result.confidence,
                "provider": result.provider,
            }
            state.context_sources.append(f"web_search:{result.provider}")
        except Exception:
            # Keep generation path available; routing/review will handle quality impact.
            state.context_sources.append("web_search:unavailable")
            state.metadata["search_context"] = {
                "citations": [],
                "confidence": 0.0,
                "provider": "unavailable",
            }
        return state
