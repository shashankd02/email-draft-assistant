from __future__ import annotations

from functools import wraps
from typing import Any, Callable

from src.core.config import settings

try:
    from langsmith import traceable as _traceable
except Exception:  # pragma: no cover
    _traceable = None


def traceable(name: str) -> Callable:
    def decorator(func: Callable) -> Callable:
        if not settings.langsmith_tracing or _traceable is None:
            @wraps(func)
            def passthrough(*args: Any, **kwargs: Any):
                return func(*args, **kwargs)

            return passthrough

        traced = _traceable(name=name)(func)

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any):
            return traced(*args, **kwargs)

        return wrapper

    return decorator
