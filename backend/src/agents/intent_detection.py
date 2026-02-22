from src.core.models import WorkflowState


class IntentDetectionAgent:
    KEYWORDS = {
        "follow_up": ["follow up", "follow-up", "checking in"],
        "apology": ["apolog", "sorry"],
        "outreach": ["introduce", "reach out", "connect"],
        "informational": ["update", "inform", "announce", "let", "notify", "tell"],
    }

    def run(self, state: WorkflowState) -> WorkflowState:
        if state.final_status == "blocked":
            return state
        if not state.metadata.get("is_email_task", True):
            state.policy_flags.append("intent_not_email")
            state.final_status = "blocked"
            return state

        text = state.prompt.lower()
        matched_intent: str | None = None
        for intent, keys in self.KEYWORDS.items():
            if any(k in text for k in keys):
                matched_intent = intent
                break
        if matched_intent:
            state.intent = matched_intent
        state.metadata["intent_confidence"] = 0.9 if matched_intent else 0.65
        return state
