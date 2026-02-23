from __future__ import annotations

from collections import Counter, deque
from threading import Lock
from time import time
from typing import Any


def _percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    rank = max(0, min(len(values) - 1, int(round((p / 100.0) * (len(values) - 1)))))
    return round(sorted(values)[rank], 2)


class MetricsStore:
    def __init__(self, max_points: int = 5000) -> None:
        self._lock = Lock()
        self._node_latency_ms: dict[str, deque[float]] = {}
        self._workflow_latency_ms: deque[float] = deque(maxlen=max_points)
        self._workflow_outcomes: Counter[str] = Counter()
        self._fallback_counts: Counter[str] = Counter()
        self._error_counts: Counter[str] = Counter()
        self._updated_at: float = time()
        self._max_points = max_points

    def record_node_timing(self, node: str, latency_ms: float) -> None:
        with self._lock:
            bucket = self._node_latency_ms.get(node)
            if bucket is None:
                bucket = deque(maxlen=self._max_points)
                self._node_latency_ms[node] = bucket
            bucket.append(float(latency_ms))
            self._updated_at = time()

    def record_workflow(
        self,
        *,
        outcome: str,
        latency_ms: float,
        fallback_count: int = 0,
        error_category: str | None = None,
    ) -> None:
        with self._lock:
            self._workflow_latency_ms.append(float(latency_ms))
            self._workflow_outcomes[outcome] += 1
            if fallback_count > 0:
                self._fallback_counts["triggered"] += 1
            else:
                self._fallback_counts["not_triggered"] += 1
            if error_category:
                self._error_counts[error_category] += 1
            self._updated_at = time()

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            workflow_latencies = list(self._workflow_latency_ms)
            node_latency = {
                node: {
                    "count": len(values),
                    "p50_ms": _percentile(list(values), 50),
                    "p95_ms": _percentile(list(values), 95),
                    "p99_ms": _percentile(list(values), 99),
                }
                for node, values in self._node_latency_ms.items()
            }
            return {
                "updated_at_epoch": int(self._updated_at),
                "workflow": {
                    "count": len(workflow_latencies),
                    "p50_ms": _percentile(workflow_latencies, 50),
                    "p95_ms": _percentile(workflow_latencies, 95),
                    "p99_ms": _percentile(workflow_latencies, 99),
                    "outcomes": dict(self._workflow_outcomes),
                    "fallback": dict(self._fallback_counts),
                    "errors": dict(self._error_counts),
                },
                "agents": node_latency,
            }


_METRICS_STORE: MetricsStore | None = None


def get_metrics_store() -> MetricsStore:
    global _METRICS_STORE
    if _METRICS_STORE is None:
        _METRICS_STORE = MetricsStore()
    return _METRICS_STORE

