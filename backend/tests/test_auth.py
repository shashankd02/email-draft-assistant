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
