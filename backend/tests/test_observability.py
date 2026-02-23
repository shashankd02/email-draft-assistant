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


def test_observability_requires_admin() -> None:
    token = _token("obs-user", role="user")
    res = client.get("/api/v1/observability/metrics", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403


def test_observability_admin_success() -> None:
    token = _token("obs-admin", role="admin")
    res = client.get("/api/v1/observability/metrics", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert "workflow" in body["metrics"]
    assert "agents" in body["metrics"]


def test_observability_alerts_admin_success() -> None:
    token = _token("obs-admin-2", role="admin")
    res = client.get("/api/v1/observability/alerts", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert "alerts" in body
    assert "thresholds" in body
