from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.auth.security import Principal, get_current_principal
from src.db.repositories import get_eval_run_details, list_eval_runs, save_eval_run
from src.db.session import SessionLocal
from src.evaluation.harness import EvaluationHarness
from uuid import uuid4

router = APIRouter()
harness = EvaluationHarness()


class EvalRunRequest(BaseModel):
    dataset: str = "core"
    max_cases: int | None = None


@router.post("/run")
def run_evaluation(
    payload: EvalRunRequest,
    principal: Principal = Depends(get_current_principal),
) -> dict:
    if principal.role != "admin":
        raise HTTPException(status_code=403, detail={"error_code": "ACCESS_DENIED", "message": "Admin role required"})

    if payload.dataset not in {"core", "adversarial", "voice"}:
        raise HTTPException(status_code=400, detail={"error_code": "INVALID_INPUT", "message": "Supported datasets: core, adversarial, voice"})

    result = harness.run_eval(payload.dataset, user_id=f"eval-{principal.user_id}", max_cases=payload.max_cases)
    run_id = str(uuid4())
    with SessionLocal() as db:
        save_eval_run(
            db,
            run_id=run_id,
            actor_user_id=principal.user_id,
            dataset=payload.dataset,
            summary=result["summary"],
            results=result["results"],
        )
        db.commit()
    return {
        "run_id": run_id,
        **result,
    }


@router.get("/datasets")
def list_datasets(principal: Principal = Depends(get_current_principal)) -> dict:
    if principal.role != "admin":
        raise HTTPException(status_code=403, detail={"error_code": "ACCESS_DENIED", "message": "Admin role required"})
    return {
        "datasets": [
            {
                "name": "core",
                "description": "Representative prompt set for functional quality checks",
                "default_thresholds": {
                    "clarity": 90,
                    "tone_match": 85,
                    "factuality": 85,
                    "bleu": 0.1,
                    "rouge_l": 0.1,
                },
            },
            {
                "name": "adversarial",
                "description": "Prompt-injection and safety hardening scenarios",
                "default_thresholds": {
                    "safety_pass_rate": 0.99,
                    "structured_output_validity": 0.98,
                },
            },
            {
                "name": "voice",
                "description": "Voice-originated requests represented as transcript prompts",
                "default_thresholds": {
                    "clarity": 90,
                    "tone_match": 85,
                    "factuality": 85,
                    "structured_output_validity": 0.98,
                    "bleu": 0.1,
                    "rouge_l": 0.1,
                },
            },
        ]
    }


@router.get("/runs")
def get_runs(
    limit: int = 20,
    principal: Principal = Depends(get_current_principal),
) -> dict:
    if principal.role != "admin":
        raise HTTPException(status_code=403, detail={"error_code": "ACCESS_DENIED", "message": "Admin role required"})
    with SessionLocal() as db:
        rows = list_eval_runs(db, limit=max(1, min(limit, 100)))
    return {"runs": rows}


@router.get("/runs/{run_id}")
def get_run(
    run_id: str,
    principal: Principal = Depends(get_current_principal),
) -> dict:
    if principal.role != "admin":
        raise HTTPException(status_code=403, detail={"error_code": "ACCESS_DENIED", "message": "Admin role required"})
    with SessionLocal() as db:
        details = get_eval_run_details(db, run_id)
    if details is None:
        raise HTTPException(status_code=404, detail={"error_code": "NOT_FOUND", "message": "Eval run not found"})
    return details
