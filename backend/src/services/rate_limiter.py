from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from threading import Lock
from time import time


@dataclass
class RateLimitDecision:
    allowed: bool
    retry_after_seconds: int


class InMemoryRateLimiter:
    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._events: dict[str, deque[float]] = {}
        self._lock = Lock()

    def check(self, key: str) -> RateLimitDecision:
        now = time()
        with self._lock:
            bucket = self._events.setdefault(key, deque())
            cutoff = now - self.window_seconds
            while bucket and bucket[0] < cutoff:
                bucket.popleft()

            if len(bucket) >= self.max_requests:
                retry_after = int(max(1, self.window_seconds - (now - bucket[0])))
                return RateLimitDecision(allowed=False, retry_after_seconds=retry_after)

            bucket.append(now)
            return RateLimitDecision(allowed=True, retry_after_seconds=0)
