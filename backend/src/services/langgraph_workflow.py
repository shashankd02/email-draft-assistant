from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from src.agents.draft_writer import DraftWriterAgent
from src.agents.context_enrichment import ContextEnrichmentAgent
from src.agents.input_parser import InputParsingAgent
from src.agents.intent_detection import IntentDetectionAgent
from src.agents.personalization import PersonalizationAgent
from src.agents.prompt_refiner import PromptRefinerAgent
from src.agents.review_validator import ReviewValidatorAgent
from src.agents.router_memory import RoutingMemoryAgent
from src.agents.security_guard import SecurityGuardAgent
from src.agents.tone_stylist import ToneStylistAgent
from src.core.config import settings


class GraphState(TypedDict, total=False):
    request_id: str
    user_id: str
    prompt: str
    intent: str
    tone: str
    constraints: dict[str, Any]
    metadata: dict[str, Any]
    context_sources: list[str]
    draft_versions: list[str]
    judge_scores: dict[str, float]
    fallback_count: int
    selected_model: str
    policy_flags: list[str]
    final_status: str
    total_retries: int


class LangGraphWorkflow:
    def __init__(self) -> None:
        self.input_parser = InputParsingAgent()
        self.intent_detector = IntentDetectionAgent()
        self.tone_stylist = ToneStylistAgent()
        self.personalization = PersonalizationAgent()
        self.context_enrichment = ContextEnrichmentAgent()
        self.prompt_refiner = PromptRefinerAgent()
        self.draft_writer = DraftWriterAgent()
        self.review = ReviewValidatorAgent()
        self.router = RoutingMemoryAgent()
        self.security = SecurityGuardAgent()
        self.graph = self._compile_graph()

    def _compile_graph(self):
        graph = StateGraph(GraphState)

        graph.add_node("n_security", self._security)
        graph.add_node("n_parse", self._parse)
        graph.add_node("n_intent", self._intent)
        graph.add_node("n_tone", self._tone)
        graph.add_node("n_personalize", self._personalize)
        graph.add_node("n_context", self._context)
        graph.add_node("n_refine", self._refine)
        graph.add_node("n_draft", self._draft)
        graph.add_node("n_review", self._review)
        graph.add_node("n_route", self._route)

        graph.set_entry_point("n_security")
        graph.add_conditional_edges("n_security", self._security_decision, {"blocked": END, "continue": "n_parse"})
        graph.add_conditional_edges("n_parse", self._continue_or_block, {"blocked": END, "continue": "n_intent"})
        graph.add_conditional_edges("n_intent", self._continue_or_block, {"blocked": END, "continue": "n_tone"})
        graph.add_edge("n_tone", "n_personalize")
        graph.add_edge("n_personalize", "n_context")
        graph.add_edge("n_context", "n_refine")
        graph.add_edge("n_refine", "n_draft")
        graph.add_edge("n_draft", "n_review")
        graph.add_edge("n_review", "n_route")
        graph.add_conditional_edges(
            "n_route",
            self._route_decision,
            {
                "success": END,
                "retry": "n_draft",
                "quality_failed": END,
                "blocked": END,
            },
        )

        return graph.compile()

    def _to_state_obj(self, state: GraphState):
        from src.core.models import WorkflowState

        return WorkflowState(**state)

    def _to_dict(self, state_obj) -> GraphState:
        data = state_obj.model_dump()
        return data

    def _security(self, state: GraphState) -> GraphState:
        state_obj = self._to_state_obj(state)
        return self._to_dict(self.security.run(state_obj))

    def _parse(self, state: GraphState) -> GraphState:
        state_obj = self._to_state_obj(state)
        return self._to_dict(self.input_parser.run(state_obj))

    def _intent(self, state: GraphState) -> GraphState:
        state_obj = self._to_state_obj(state)
        return self._to_dict(self.intent_detector.run(state_obj))

    def _tone(self, state: GraphState) -> GraphState:
        state_obj = self._to_state_obj(state)
        return self._to_dict(self.tone_stylist.run(state_obj))

    def _personalize(self, state: GraphState) -> GraphState:
        state_obj = self._to_state_obj(state)
        return self._to_dict(self.personalization.run(state_obj))

    def _context(self, state: GraphState) -> GraphState:
        state_obj = self._to_state_obj(state)
        return self._to_dict(self.context_enrichment.run(state_obj))

    def _refine(self, state: GraphState) -> GraphState:
        state_obj = self._to_state_obj(state)
        return self._to_dict(self.prompt_refiner.run(state_obj))

    def _draft(self, state: GraphState) -> GraphState:
        state_obj = self._to_state_obj(state)
        return self._to_dict(self.draft_writer.run(state_obj))

    def _review(self, state: GraphState) -> GraphState:
        state_obj = self._to_state_obj(state)
        return self._to_dict(self.review.run(state_obj))

    def _route(self, state: GraphState) -> GraphState:
        state_obj = self._to_state_obj(state)
        state_obj = self.router.run(state_obj)

        total_retries = state.get("total_retries", 0)
        if state_obj.final_status == "retry":
            total_retries += 1
            if total_retries >= settings.max_total_retries:
                state_obj.final_status = "quality_failed"
        output = self._to_dict(state_obj)
        output["total_retries"] = total_retries
        return output

    def _security_decision(self, state: GraphState) -> str:
        if state.get("final_status") == "blocked":
            return "blocked"
        return "continue"

    def _continue_or_block(self, state: GraphState) -> str:
        if state.get("final_status") == "blocked":
            return "blocked"
        return "continue"

    def _route_decision(self, state: GraphState) -> str:
        status = state.get("final_status", "quality_failed")
        if status in {"success", "retry", "quality_failed", "blocked"}:
            return status
        return "quality_failed"

    def run(self, initial_state: GraphState) -> GraphState:
        return self.graph.invoke(initial_state)
