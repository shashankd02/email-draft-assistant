from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)


def _user_token() -> str:
    res = client.post(
        "/api/v1/auth/token",
        json={"user_id": "intent-user", "role": "user", "bootstrap_secret": "dev-bootstrap-secret"},
    )
    assert res.status_code == 200
    return res.json()["access_token"]


def test_non_email_prompt_rejected() -> None:
    token = _user_token()
    payload = {
        "user_id": "intent-user",
        "prompt": "what is weather today?",
        "intent": "follow_up",
        "tone": "professional",
        "constraints": {"max_paragraphs": 3, "must_include": [], "forbidden": ["PII"]},
        "metadata": {"recipient_role": "client", "language": "en"},
    }
    res = client.post("/api/v1/draft/generate", headers={"Authorization": f"Bearer {token}"}, json=payload)
    assert res.status_code == 400
    body = res.json()
    assert body["detail"]["error_code"] == "INVALID_INPUT"


def test_small_talk_prompt_rejected() -> None:
    token = _user_token()
    payload = {
        "user_id": "intent-user",
        "prompt": "how are you?",
        "intent": "follow_up",
        "tone": "professional",
        "constraints": {"max_paragraphs": 3, "must_include": [], "forbidden": ["PII"]},
        "metadata": {"recipient_role": "client", "language": "en"},
    }
    res = client.post("/api/v1/draft/generate", headers={"Authorization": f"Bearer {token}"}, json=payload)
    assert res.status_code == 400
    body = res.json()
    assert body["detail"]["error_code"] == "INVALID_INPUT"


def test_random_short_prompt_rejected() -> None:
    token = _user_token()
    payload = {
        "user_id": "intent-user",
        "prompt": "test 123",
        "intent": "informational",
        "tone": "professional",
        "constraints": {"max_paragraphs": 3, "must_include": [], "forbidden": ["PII"]},
        "metadata": {"recipient_role": "client", "language": "en"},
    }
    res = client.post("/api/v1/draft/generate", headers={"Authorization": f"Bearer {token}"}, json=payload)
    assert res.status_code == 400
    body = res.json()
    assert body["detail"]["error_code"] == "INVALID_INPUT"


def test_incomplete_email_request_rejected() -> None:
    token = _user_token()
    payload = {
        "user_id": "intent-user",
        "prompt": "draft email",
        "intent": "informational",
        "tone": "professional",
        "constraints": {"max_paragraphs": 3, "must_include": [], "forbidden": ["PII"]},
        "metadata": {"recipient_role": "client", "language": "en"},
    }
    res = client.post("/api/v1/draft/generate", headers={"Authorization": f"Bearer {token}"}, json=payload)
    assert res.status_code == 400
    body = res.json()
    assert body["detail"]["error_code"] == "INVALID_INPUT"


def test_email_task_with_external_topic_allowed() -> None:
    token = _user_token()
    payload = {
        "user_id": "intent-user",
        "prompt": "Draft an email to my manager about today's weather impact on commute and request remote work.",
        "intent": "informational",
        "tone": "professional",
        "constraints": {"max_paragraphs": 3, "must_include": [], "forbidden": ["PII"]},
        "metadata": {"recipient_role": "manager", "language": "en"},
    }
    res = client.post("/api/v1/draft/generate", headers={"Authorization": f"Bearer {token}"}, json=payload)
    assert res.status_code == 200
