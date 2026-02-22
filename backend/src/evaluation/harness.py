from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Any

from fastapi import HTTPException

from src.core.config import settings
from src.core.models import DraftGenerateRequest
from src.services.workflow import DraftWorkflowService


@dataclass
class EvalCase:
    prompt: str
    intent: str
    tone: str
    expected: str = "success"
    reference: str | None = None


@dataclass
class EvalSummary:
    total_cases: int
    avg_clarity: float
    avg_tone_match: float
    avg_factuality: float
    avg_overall: float
    pass_thresholds: dict[str, bool]


def _load_dataset(path: str) -> list[EvalCase]:
    abs_path = Path(path)
    if not abs_path.is_absolute():
        abs_path = Path(__file__).resolve().parents[2] / path

    cases: list[EvalCase] = []
    with abs_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            cases.append(
                EvalCase(
                    prompt=obj["prompt"],
                    intent=obj["intent"],
                    tone=obj["tone"],
                    expected=obj.get("expected", "success"),
                    reference=obj.get("reference"),
                )
            )
    return cases


def _tokens(text: str) -> list[str]:
    return [tok for tok in text.lower().replace("\n", " ").split(" ") if tok]


def _bleu1(candidate: str, reference: str) -> float:
    cand = _tokens(candidate)
    ref = _tokens(reference)
    if not cand or not ref:
        return 0.0
    ref_counts: dict[str, int] = {}
    for tok in ref:
        ref_counts[tok] = ref_counts.get(tok, 0) + 1
    matches = 0
    for tok in cand:
        if ref_counts.get(tok, 0) > 0:
            matches += 1
            ref_counts[tok] -= 1
    return round(matches / max(1, len(cand)), 4)


def _lcs_len(a: list[str], b: list[str]) -> int:
    if not a or not b:
        return 0
    dp = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
    for i in range(1, len(a) + 1):
        for j in range(1, len(b) + 1):
            if a[i - 1] == b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    return dp[len(a)][len(b)]


def _rouge_l(candidate: str, reference: str) -> float:
    cand = _tokens(candidate)
    ref = _tokens(reference)
    if not cand or not ref:
        return 0.0
    lcs = _lcs_len(cand, ref)
    recall = lcs / len(ref)
    precision = lcs / len(cand)
    if recall + precision == 0:
        return 0.0
    return round((2 * recall * precision) / (recall + precision), 4)


class EvaluationHarness:
    def __init__(self, workflow: DraftWorkflowService | None = None) -> None:
        self.workflow = workflow or DraftWorkflowService()

    def _dataset_path(self, dataset: str) -> str:
        mapping = {
            "core": settings.eval_core_dataset_path,
            "adversarial": settings.eval_adversarial_dataset_path,
            "voice": settings.eval_voice_dataset_path,
        }
        if dataset not in mapping:
            raise ValueError(f"Unsupported dataset: {dataset}")
        return mapping[dataset]

    def run_eval(self, dataset: str, user_id: str = "eval-user", max_cases: int | None = None) -> dict[str, Any]:
        cases = _load_dataset(self._dataset_path(dataset))
        if max_cases is not None:
            cases = cases[: max(1, max_cases)]

        results = []
        success_count = 0
        expected_safety_pass_count = 0
        structured_output_valid_count = 0
        fallback_success_count = 0
        fallback_trigger_count = 0
        bleu_scores: list[float] = []
        rouge_l_scores: list[float] = []

        for idx, case in enumerate(cases):
            req = DraftGenerateRequest(
                user_id=user_id,
                prompt=case.prompt,
                intent=case.intent,
                tone=case.tone,
                request_id=f"{dataset}-eval-{idx+1}",
            )
            try:
                response = self.workflow.run(req, persist=False)
                success_count += 1
                if response.fallback_used:
                    fallback_trigger_count += 1
                    fallback_success_count += 1
                is_structured = bool(
                    response.request_id
                    and response.draft_id
                    and response.status == "success"
                    and isinstance(response.judge_scores, dict)
                )
                if is_structured:
                    structured_output_valid_count += 1
                if case.expected == "success":
                    expected_safety_pass_count += 1
                results.append(
                    {
                        "request_id": response.request_id,
                        "intent": case.intent,
                        "tone": case.tone,
                        "expected": case.expected,
                        "status": "success",
                        "scores": response.judge_scores,
                        "model_used": response.model_used,
                        "fallback_used": response.fallback_used,
                    }
                )
                if case.reference:
                    bleu_scores.append(_bleu1(response.draft_text, case.reference))
                    rouge_l_scores.append(_rouge_l(response.draft_text, case.reference))
            except HTTPException as exc:
                detail = exc.detail if isinstance(exc.detail, dict) else {}
                error_code = str(detail.get("error_code", "UNKNOWN"))
                if case.expected == "blocked" and error_code == "ACCESS_DENIED":
                    expected_safety_pass_count += 1
                    structured_output_valid_count += 1
                results.append(
                    {
                        "request_id": req.request_id,
                        "intent": case.intent,
                        "tone": case.tone,
                        "expected": case.expected,
                        "status": "error",
                        "error_code": error_code,
                        "scores": {
                            "clarity": 0.0,
                            "tone_match": 0.0,
                            "factuality": 0.0,
                            "overall": 0.0,
                        },
                        "model_used": "n/a",
                        "fallback_used": False,
                    }
                )

        success_results = [item for item in results if item["status"] == "success"]
        if success_results:
            avg_clarity = round(mean(item["scores"]["clarity"] for item in success_results), 2)
            avg_tone = round(mean(item["scores"]["tone_match"] for item in success_results), 2)
            avg_factuality = round(mean(item["scores"]["factuality"] for item in success_results), 2)
            avg_overall = round(mean(item["scores"]["overall"] for item in success_results), 2)
        else:
            avg_clarity = 0.0
            avg_tone = 0.0
            avg_factuality = 0.0
            avg_overall = 0.0

        total = len(results) if results else 1
        safety_pass_rate = round(expected_safety_pass_count / total, 4)
        structured_output_validity = round(structured_output_valid_count / total, 4)
        fallback_success_rate = 1.0
        if fallback_trigger_count > 0:
            fallback_success_rate = round(fallback_success_count / fallback_trigger_count, 4)
        avg_bleu = round(mean(bleu_scores), 4) if bleu_scores else 0.0
        avg_rouge_l = round(mean(rouge_l_scores), 4) if rouge_l_scores else 0.0

        if dataset == "adversarial":
            pass_thresholds = {
                "clarity": True,
                "tone_match": True,
                "factuality": True,
                "safety_pass_rate": safety_pass_rate >= settings.eval_safety_pass_threshold,
                "structured_output_validity": structured_output_validity >= settings.eval_structured_output_threshold,
                "fallback_success_rate": fallback_success_rate >= settings.eval_fallback_success_threshold,
                "bleu": True,
                "rouge_l": True,
            }
        else:
            pass_thresholds = {
                "clarity": avg_clarity >= settings.eval_clarity_threshold,
                "tone_match": avg_tone >= settings.eval_tone_threshold,
                "factuality": avg_factuality >= settings.eval_factuality_threshold,
                "safety_pass_rate": safety_pass_rate >= settings.eval_safety_pass_threshold,
                "structured_output_validity": structured_output_validity >= settings.eval_structured_output_threshold,
                "fallback_success_rate": fallback_success_rate >= settings.eval_fallback_success_threshold,
                "bleu": avg_bleu >= 0.1,
                "rouge_l": avg_rouge_l >= 0.1,
            }

        return {
            "summary": EvalSummary(
                total_cases=len(results),
                avg_clarity=avg_clarity,
                avg_tone_match=avg_tone,
                avg_factuality=avg_factuality,
                avg_overall=avg_overall,
                pass_thresholds=pass_thresholds,
            ).__dict__,
            "metrics": {
                "dataset": dataset,
                "success_count": success_count,
                "safety_pass_rate": safety_pass_rate,
                "structured_output_validity": structured_output_validity,
                "fallback_success_rate": fallback_success_rate,
                "avg_bleu": avg_bleu,
                "avg_rouge_l": avg_rouge_l,
            },
            "results": results,
        }

    def run_core_eval(self, user_id: str = "eval-user", max_cases: int | None = None) -> dict[str, Any]:
        return self.run_eval("core", user_id=user_id, max_cases=max_cases)
