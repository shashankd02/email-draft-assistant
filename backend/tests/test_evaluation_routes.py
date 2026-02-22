from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)


def _issue_token(role: str = "admin") -> str:
    response = client.post(
        "/api/v1/auth/token",
        json={"user_id": "admin-001", "role": role, "bootstrap_secret": "dev-bootstrap-secret"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_eval_datasets_requires_admin() -> None:
    token = _issue_token(role="user")
    response = client.get("/api/v1/evaluation/datasets", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_eval_datasets_admin_success() -> None:
    token = _issue_token(role="admin")
    response = client.get("/api/v1/evaluation/datasets", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    body = response.json()
    names = {d["name"] for d in body["datasets"]}
    assert {"core", "adversarial", "voice"}.issubset(names)
