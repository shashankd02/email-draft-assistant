from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)


def _token(user_id: str, role: str = "user") -> str:
    res = client.post(
        "/api/v1/auth/token",
        json={"user_id": user_id, "role": role, "bootstrap_secret": "dev-bootstrap-secret"},
    )
    assert res.status_code == 200
    return res.json()["access_token"]


def test_read_policy_resource() -> None:
    token = _token("mcp-user")
    res = client.post(
        "/api/v1/mcp/resource/read",
        headers={"Authorization": f"Bearer {token}"},
        json={"uri": "policy://safety/ruleset", "actor": "mcp-user"},
    )
    assert res.status_code == 200
    assert "block_patterns" in res.json()["data"]


def test_write_and_read_profile_resource() -> None:
    token = _token("mcp-user-2")
    write_res = client.post(
        "/api/v1/mcp/resource/write",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "uri": "memory://user/mcp-user-2/profile",
            "actor": "mcp-user-2",
            "data": {"preferred_tone": "professional"},
        },
    )
    assert write_res.status_code == 200
    read_res = client.post(
        "/api/v1/mcp/resource/read",
        headers={"Authorization": f"Bearer {token}"},
        json={"uri": "memory://user/mcp-user-2/profile", "actor": "mcp-user-2"},
    )
    assert read_res.status_code == 200
    assert read_res.json()["data"]["prefs_json"] is not None
