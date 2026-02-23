from src.core.models import WorkflowState
from src.services.llm_provider import LLMProvider, StructuredOutputError, get_llm_provider


class DraftWriterAgent:
    def __init__(self, provider: LLMProvider | None = None) -> None:
        self.provider = provider or get_llm_provider()

    def run(self, state: WorkflowState) -> WorkflowState:
        prompt_input = str(state.metadata.get("refined_prompt") or state.prompt)
        try:
            result = self.provider.generate_email_draft(
                prompt=prompt_input,
                intent=state.intent,
                tone=state.tone,
                constraints=state.constraints,
                metadata=state.metadata,
            )
            state.selected_model = result.model_used
            state.draft_versions.append(result.draft_text)
            state.metadata.pop("draft_provider_error", None)
            state.metadata.pop("schema_repair_exhausted", None)
        except TimeoutError:
            state.policy_flags.append("draft_provider_timeout")
            state.metadata["draft_provider_error"] = "timeout"
            state.final_status = "retry"
        except StructuredOutputError:
            state.policy_flags.append("draft_schema_break")
            state.metadata["schema_repair_exhausted"] = True
            # Safe deterministic fallback to preserve UX and avoid hard failure on formatting issues.
            state.selected_model = "safe-template-fallback"
            state.draft_versions.append(self._safe_template_draft(state))
            state.metadata.pop("draft_provider_error", None)
        except Exception as exc:
            state.policy_flags.append("draft_provider_error")
            state.metadata["draft_provider_error"] = str(type(exc).__name__)
            state.final_status = "retry"
        return state

    def _safe_template_draft(self, state: WorkflowState) -> str:
        recipient = str(state.metadata.get("recipient_role", "recipient")).strip() or "recipient"
        objective = state.prompt.strip() or "the requested topic"
        greeting = "Dear Team," if state.tone == "professional" else "Hello,"
        return (
            f"{greeting}\n\n"
            f"I am reaching out regarding {objective}.\n\n"
            f"This draft is prepared as a safe fallback while preserving your requested '{state.tone}' tone "
            f"for the {recipient} audience.\n\n"
            "Please review and update any placeholders before sending.\n\n"
            "Best regards,\nYour Name"
        )
