from src.agents.draft_writer import DraftWriterAgent
from src.core.models import WorkflowState
from src.services.llm_provider import LLMProvider, StructuredOutputError


class BrokenStructuredProvider(LLMProvider):
    def generate_email_draft(self, *, prompt: str, intent: str, tone: str, constraints: dict, metadata: dict):
        _ = prompt
        _ = intent
        _ = tone
        _ = constraints
        _ = metadata
        raise StructuredOutputError("malformed json")


def test_schema_break_routes_to_safe_template() -> None:
    state = WorkflowState(
        request_id="req-1",
        user_id="u-1",
        prompt="Draft an outreach email introducing our product.",
        intent="outreach",
        tone="professional",
        constraints={"max_paragraphs": 3, "must_include": [], "forbidden": ["PII"]},
        metadata={"recipient_role": "client", "language": "en"},
    )
    agent = DraftWriterAgent(provider=BrokenStructuredProvider())
    out = agent.run(state)
    assert out.selected_model == "safe-template-fallback"
    assert len(out.draft_versions) == 1
    assert "safe fallback" in out.draft_versions[0].lower()
    assert out.metadata.get("schema_repair_exhausted") is True
    assert "draft_schema_break" in out.policy_flags

