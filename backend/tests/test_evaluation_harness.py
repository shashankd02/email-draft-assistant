from src.evaluation.harness import EvaluationHarness


def test_core_eval_smoke() -> None:
    harness = EvaluationHarness()
    result = harness.run_eval("core", user_id="eval-user", max_cases=1)
    assert result["summary"]["total_cases"] == 1
    assert "metrics" in result
    assert "structured_output_validity" in result["metrics"]


def test_adversarial_eval_smoke() -> None:
    harness = EvaluationHarness()
    result = harness.run_eval("adversarial", user_id="eval-user", max_cases=2)
    assert result["summary"]["total_cases"] == 2
    assert "safety_pass_rate" in result["metrics"]
