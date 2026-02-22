from fastapi import HTTPException


def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=400, detail={"error_code": "INVALID_INPUT", "message": message})


def access_denied(message: str) -> HTTPException:
    return HTTPException(status_code=403, detail={"error_code": "ACCESS_DENIED", "message": message})


def quality_gate_failed(message: str) -> HTTPException:
    return HTTPException(status_code=422, detail={"error_code": "QUALITY_GATE_FAILED", "message": message})


def upstream_unavailable(message: str) -> HTTPException:
    return HTTPException(status_code=503, detail={"error_code": "UPSTREAM_UNAVAILABLE", "message": message})


def rate_limited(message: str, retry_after_seconds: int) -> HTTPException:
    return HTTPException(
        status_code=429,
        detail={
            "error_code": "RATE_LIMITED",
            "message": message,
            "retry_after_seconds": retry_after_seconds,
        },
    )


def replay_detected(message: str) -> HTTPException:
    return HTTPException(status_code=409, detail={"error_code": "REPLAY_DETECTED", "message": message})
