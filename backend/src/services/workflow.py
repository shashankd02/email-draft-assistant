from time import perf_counter
from uuid import uuid4

from src.core.errors import access_denied, bad_request, quality_gate_failed, upstream_unavailable
from src.core.metrics import get_metrics_store
from src.core.models import DraftGenerateRequest, DraftGenerateResponse, WorkflowState
from src.db.repositories import save_draft_and_scores
from src.db.session import SessionLocal
from src.services.langgraph_workflow import LangGraphWorkflow
from src.utils.tracing import traceable


class DraftWorkflowService:
    def __init__(self) -> None:
        self.graph_workflow = LangGraphWorkflow()

    @traceable(name="draft_workflow_graph_run")
    def _execute_graph(self, state: WorkflowState) -> WorkflowState:
        final_state_dict = self.graph_workflow.run(
            {
                **state.model_dump(),
                "total_retries": 0,
            }
        )
        return WorkflowState(**{k: v for k, v in final_state_dict.items() if k in WorkflowState.model_fields})

    def run(self, req: DraftGenerateRequest, persist: bool = True) -> DraftGenerateResponse:
        start = perf_counter()
        metrics = get_metrics_store()
        state = WorkflowState(
            request_id=req.request_id,
            user_id=req.user_id,
            prompt=req.prompt,
            intent=req.intent,
            tone=req.tone,
            constraints=req.constraints.model_dump(),
            metadata=req.metadata.model_dump(),
        )
        try:
            state = self._execute_graph(state)
        except Exception:
            latency_ms = int((perf_counter() - start) * 1000)
            metrics.record_workflow(outcome="internal_error", latency_ms=latency_ms, error_category="graph_execution_error")
            raise

        if state.final_status == "blocked":
            latency_ms = int((perf_counter() - start) * 1000)
            metrics.record_workflow(
                outcome="blocked",
                latency_ms=latency_ms,
                fallback_count=state.fallback_count,
                error_category=state.policy_flags[0] if state.policy_flags else "blocked",
            )
            if "not_email_task" in state.policy_flags:
                raise bad_request(
                    "This assistant drafts emails only. Please provide an email request, for example: "
                    "'Draft a professional email to my manager about today's weather impact on commute.'"
                )
            if "insufficient_prompt_context" in state.policy_flags:
                raise bad_request(
                    "Please provide a complete email request with recipient and context. Example: "
                    "'Draft an email to my manager about missing the 9 AM standup due to traffic and request to share updates asynchronously.'"
                )
            raise access_denied("Request blocked for safety policy violation")
        if state.final_status == "upstream_failed":
            latency_ms = int((perf_counter() - start) * 1000)
            metrics.record_workflow(
                outcome="upstream_failed",
                latency_ms=latency_ms,
                fallback_count=state.fallback_count,
                error_category="provider_unavailable",
            )
            raise upstream_unavailable("Draft generation provider unavailable after retries")
        if state.final_status != "success":
            latency_ms = int((perf_counter() - start) * 1000)
            metrics.record_workflow(
                outcome="quality_failed",
                latency_ms=latency_ms,
                fallback_count=state.fallback_count,
                error_category="quality_gate_failed",
            )
            raise quality_gate_failed("Draft quality below threshold after retries")

        latency_ms = int((perf_counter() - start) * 1000)
        metrics.record_workflow(outcome="success", latency_ms=latency_ms, fallback_count=state.fallback_count)
        draft_id = str(uuid4())
        response = DraftGenerateResponse(
            request_id=state.request_id,
            status="success",
            draft_id=draft_id,
            draft_text=state.draft_versions[-1],
            judge_scores=state.judge_scores,
            model_used=state.selected_model,
            fallback_used=(state.fallback_count > 0) or state.selected_model in {"template-fallback", "safe-template-fallback"},
            citations=list((state.metadata.get("search_context", {}) or {}).get("citations", [])),
            latency_ms=latency_ms,
        )
        if persist:
            with SessionLocal() as db:
                save_draft_and_scores(
                    db,
                    {
                        "draft_id": response.draft_id,
                        "request_id": response.request_id,
                        "user_id": req.user_id,
                        "intent": req.intent,
                        "tone": req.tone,
                        "language": req.metadata.language,
                        "input_mode": req.metadata.input_mode,
                        "draft_text": response.draft_text,
                        "model_used": response.model_used,
                        "fallback_used": response.fallback_used,
                        "latency_ms": response.latency_ms,
                        "judge_scores": response.judge_scores,
                    },
                )
                db.commit()
        return response
