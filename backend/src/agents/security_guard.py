from src.core.models import WorkflowState


class SecurityGuardAgent:
    BLOCK_PATTERNS = ["ignore previous instructions", "reveal system prompt", "exfiltrate"]

    def run(self, state: WorkflowState) -> WorkflowState:
        text = state.prompt.lower()
        for pattern in self.BLOCK_PATTERNS:
            if pattern in text:
                state.policy_flags.append("jailbreak_detected")
                state.final_status = "blocked"
                break
        return state
