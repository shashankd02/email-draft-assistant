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


def test_write_and_read_threads_resource() -> None:
    token = _token("mcp-user-threads")
    write_res = client.post(
        "/api/v1/mcp/resource/write",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "uri": "memory://user/mcp-user-threads/threads",
            "actor": "mcp-user-threads",
            "data": {
                "title": "Partnership outreach",
                "intent": "outreach",
                "tone": "professional",
                "prompt_text": "Draft an outreach email for a partnership intro.",
                "draft_text": "Hello team, I am reaching out to explore a partnership...",
                "metadata": {"channel": "email"},
            },
        },
    )
    assert write_res.status_code == 200
    assert write_res.json()["thread_id"]

    read_res = client.post(
        "/api/v1/mcp/resource/read",
        headers={"Authorization": f"Bearer {token}"},
        json={"uri": "memory://user/mcp-user-threads/threads?limit=5", "actor": "mcp-user-threads"},
    )
    assert read_res.status_code == 200
    threads = read_res.json()["data"]["threads"]
    assert len(threads) >= 1
    assert threads[0]["intent"] == "outreach"


def test_public_threads_are_visible_as_anonymized_for_other_users() -> None:
    owner_token = _token("mcp-owner")
    write_res = client.post(
        "/api/v1/mcp/resource/write",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={
            "uri": "memory://user/mcp-owner/threads",
            "actor": "mcp-owner",
            "data": {
                "title": "Public sample",
                "intent": "informational",
                "tone": "professional",
                "prompt_text": "private original prompt",
                "draft_text": "Public-safe draft content",
                "is_public": True,
            },
        },
    )
    assert write_res.status_code == 200

    viewer_token = _token("mcp-viewer")
    read_res = client.post(
        "/api/v1/mcp/resource/read",
        headers={"Authorization": f"Bearer {viewer_token}"},
        json={"uri": "memory://user/mcp-viewer/threads?limit=10&include_public=true", "actor": "mcp-viewer"},
    )
    assert read_res.status_code == 200
    threads = read_res.json()["data"]["threads"]
    public_hits = [t for t in threads if t.get("source") == "public_anonymized"]
    assert len(public_hits) >= 1
    assert public_hits[0]["prompt_text"] is None
