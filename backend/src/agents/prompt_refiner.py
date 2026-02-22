from __future__ import annotations

from src.core.models import WorkflowState


class PromptRefinerAgent:
    def run(self, state: WorkflowState) -> WorkflowState:
        if state.final_status == "blocked":
            return state

        search_context = state.metadata.get("search_context", {}) or {}
        citations = search_context.get("citations", [])
        recipient = str(state.metadata.get("email_target", "")).strip() or state.metadata.get("recipient_role", "recipient")

        refined_lines = [
            "Create a production-ready email draft using this normalized request:",
            f"- User objective: {state.prompt}",
            f"- Intended recipient: {recipient}",
            f"- Intent category: {state.intent}",
            f"- Requested tone: {state.tone}",
            f"- Constraints: {state.constraints}",
            "- Requirements: avoid assumptions, keep unknowns as placeholders, and ensure clear structure.",
        ]
        if citations:
            refined_lines.append(f"- Grounding citations: {citations}")

        state.metadata["refined_prompt"] = "\n".join(refined_lines)
        state.context_sources.append("prompt_refiner")
        return state
