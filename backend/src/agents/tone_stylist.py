from src.core.models import WorkflowState


class ToneStylistAgent:
    ALLOWED = {"professional", "casual", "assertive", "empathetic"}

    def run(self, state: WorkflowState) -> WorkflowState:
        if state.tone not in self.ALLOWED:
            state.tone = "professional"
        return state
