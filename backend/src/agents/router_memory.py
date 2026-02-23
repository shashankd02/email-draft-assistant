from src.core.models import WorkflowState
from src.core.config import settings


class RoutingMemoryAgent:
    def run(self, state: WorkflowState) -> WorkflowState:
        if state.final_status == "blocked":
            return state

        provider_error = state.metadata.get("draft_provider_error")
        if provider_error:
            state.fallback_count += 1
            if state.fallback_count > settings.max_retries_per_agent:
                state.final_status = "upstream_failed"
            else:
                state.final_status = "retry"
            return state

        if not state.judge_scores:
            state.fallback_count += 1
            if state.fallback_count > settings.max_retries_per_agent:
                state.final_status = "quality_failed"
            else:
                state.final_status = "retry"
            return state

        if state.judge_scores.get("overall", 0) < settings.quality_threshold:
            state.fallback_count += 1
            if state.fallback_count > settings.max_retries_per_agent:
                state.final_status = "quality_failed"
            else:
                state.final_status = "retry"
            return state

        state.final_status = "success"
        return state
