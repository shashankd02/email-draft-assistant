from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.evaluation.harness import EvaluationHarness


def main() -> int:
    harness = EvaluationHarness()
    datasets = ("core", "adversarial", "voice")
    failed: list[str] = []
    report: dict[str, dict] = {}

    for dataset in datasets:
        result = harness.run_eval(dataset, user_id="release-gate", max_cases=3)
        summary = result["summary"]
        report[dataset] = summary
        failed_checks = [name for name, passed in summary["pass_thresholds"].items() if not passed]
        if failed_checks:
            failed.append(f"{dataset}: {', '.join(failed_checks)}")

    print(json.dumps(report, indent=2))
    if failed:
        print("Release gate failed:", "; ".join(failed), file=sys.stderr)
        return 1
    print("Release gate passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
