from fastapi.testclient import TestClient
from uuid import uuid4

from src.main import app


client = TestClient(app)


def _issue_user_token() -> str:
    response = client.post(
        "/api/v1/auth/token",
        json={"user_id": "draft-user", "role": "user", "bootstrap_secret": "dev-bootstrap-secret"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_replay_request_id_blocked() -> None:
    token = _issue_user_token()
    request_id = f"replay-{uuid4()}"
    payload = {
        "request_id": request_id,
        "user_id": "draft-user",
        "prompt": "Draft a short status update.",
        "intent": "informational",
        "tone": "professional",
        "constraints": {"max_paragraphs": 2, "must_include": [], "forbidden": ["PII"]},
        "metadata": {"recipient_role": "internal", "language": "en"},
    }
    first = client.post("/api/v1/draft/generate", headers={"Authorization": f"Bearer {token}"}, json=payload)
    assert first.status_code == 200

    second = client.post("/api/v1/draft/generate", headers={"Authorization": f"Bearer {token}"}, json=payload)
    assert second.status_code == 409
    assert second.json()["detail"]["error_code"] == "REPLAY_DETECTED"
