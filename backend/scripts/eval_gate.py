from __future__ import annotations

import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.evaluation.harness import EvaluationHarness
from src.core.config import settings


def main() -> int:
    harness = EvaluationHarness()
    datasets = ("core", "adversarial", "voice")
    max_cases_env = os.getenv("EVAL_GATE_MAX_CASES")
    max_cases = int(max_cases_env) if max_cases_env else None
    failed: list[str] = []
    report: dict[str, dict] = {}
    metrics_report: dict[str, dict] = {}
    relaxed_gate = not settings.strict_provider_mode

    for dataset in datasets:
        result = harness.run_eval(dataset, user_id="release-gate", max_cases=max_cases)
        summary = result["summary"]
        metrics = result["metrics"]
        report[dataset] = summary
        metrics_report[dataset] = metrics
        if relaxed_gate:
            # In non-strict mode (CI/local without real providers), only enforce baseline health checks.
            relaxed_checks = {
                "fallback_success_rate": summary["pass_thresholds"].get("fallback_success_rate", True),
            }
            failed_checks = [name for name, passed in relaxed_checks.items() if not passed]
            if failed_checks:
                failed.append(f"{dataset}: {', '.join(failed_checks)}")
        else:
            failed_checks = [name for name, passed in summary["pass_thresholds"].items() if not passed]
            if failed_checks:
                failed.append(f"{dataset}: {', '.join(failed_checks)}")
        if metrics.get("success_count", 0) == 0:
            failed.append(f"{dataset}: no successful cases")
        if metrics.get("fallback_trigger_count", 0) > 0 and metrics.get("fallback_success_rate") is None:
            failed.append(f"{dataset}: fallback metric invalid")

    print(json.dumps({"summary": report, "metrics": metrics_report}, indent=2))
    if failed:
        print("Release gate failed:", "; ".join(failed), file=sys.stderr)
        return 1
    if relaxed_gate:
        print("Release gate passed (relaxed mode: STRICT_PROVIDER_MODE=false)")
    else:
        print("Release gate passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
