from src.agents.review_validator import ReviewValidatorAgent
from src.core.models import WorkflowState


def test_review_validator_blocks_when_pii_forbidden_and_present() -> None:
    state = WorkflowState(
        request_id="req-1",
        user_id="user-1",
        prompt="draft email",
        intent="informational",
        tone="professional",
        constraints={"forbidden": ["PII"]},
        metadata={},
        draft_versions=["Contact me at user@example.com"],
    )
    reviewed = ReviewValidatorAgent().run(state)
    assert reviewed.final_status == "blocked"
    assert "pii_leak_detected" in reviewed.policy_flags
