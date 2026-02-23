from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)


def test_issue_token_success() -> None:
    response = client.post(
        "/api/v1/auth/token",
        json={"user_id": "user-001", "role": "user", "bootstrap_secret": "dev-bootstrap-secret"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_issue_token_invalid_secret() -> None:
    response = client.post(
        "/api/v1/auth/token",
        json={"user_id": "user-001", "role": "user", "bootstrap_secret": "invalid"},
    )
    assert response.status_code == 403


def test_mcp_tools_requires_auth() -> None:
    response = client.get("/api/v1/mcp/tools")
    assert response.status_code in (401, 403)


def test_mcp_tools_with_auth() -> None:
    token_response = client.post(
        "/api/v1/auth/token",
        json={"user_id": "user-001", "role": "user", "bootstrap_secret": "dev-bootstrap-secret"},
    )
    token = token_response.json()["access_token"]

    response = client.get(
        "/api/v1/mcp/tools",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert "tools" in response.json()


def test_delete_my_transcripts_and_account() -> None:
    register = client.post(
        "/api/v1/auth/register",
        json={"username": "cleanup-user", "password": "StrongPass123", "role": "user"},
    )
    assert register.status_code == 200
    token = register.json()["access_token"]

    delete_transcripts = client.delete(
        "/api/v1/auth/me/transcripts",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert delete_transcripts.status_code == 200
    assert "deleted_transcripts" in delete_transcripts.json()

    delete_account = client.delete(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert delete_account.status_code == 200
    assert delete_account.json()["status"] == "ok"
