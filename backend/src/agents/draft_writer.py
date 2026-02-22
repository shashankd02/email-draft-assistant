from src.core.models import WorkflowState
from src.services.llm_provider import LLMProvider, get_llm_provider


class DraftWriterAgent:
    def __init__(self, provider: LLMProvider | None = None) -> None:
        self.provider = provider or get_llm_provider()

    def run(self, state: WorkflowState) -> WorkflowState:
        prompt_input = str(state.metadata.get("refined_prompt") or state.prompt)
        result = self.provider.generate_email_draft(
            prompt=prompt_input,
            intent=state.intent,
            tone=state.tone,
            constraints=state.constraints,
            metadata=state.metadata,
        )
        state.selected_model = result.model_used
        state.draft_versions.append(result.draft_text)
        return state
