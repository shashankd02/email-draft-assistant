import re

from src.core.models import WorkflowState


class ReviewValidatorAgent:
    EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
    PHONE_RE = re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")
    SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")

    def run(self, state: WorkflowState) -> WorkflowState:
        latest = state.draft_versions[-1] if state.draft_versions else ""
        clarity = 92.0 if len(latest) > 40 else 70.0
        tone_match = 88.0
        factuality = 86.0 if "http" not in latest else 90.0

        forbidden = [str(item).lower() for item in state.constraints.get("forbidden", [])]
        pii_requested = "pii" in forbidden
        pii_found = any(
            matcher.search(latest) for matcher in (self.EMAIL_RE, self.PHONE_RE, self.SSN_RE)
        )
        if pii_requested and pii_found:
            state.policy_flags.append("pii_leak_detected")
            state.final_status = "blocked"

        state.judge_scores = {
            "clarity": clarity,
            "tone_match": tone_match,
            "factuality": factuality,
            "overall": round((clarity + tone_match + factuality) / 3.0, 2),
        }
        return state
