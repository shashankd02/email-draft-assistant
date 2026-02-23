from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)


def _token(user_id: str, role: str = "admin") -> str:
    res = client.post(
        "/api/v1/auth/token",
        json={"user_id": user_id, "role": role, "bootstrap_secret": "dev-bootstrap-secret"},
    )
    assert res.status_code == 200
    return res.json()["access_token"]


def test_admin_delete_user_endpoint() -> None:
    user_register = client.post(
        "/api/v1/auth/register",
        json={"username": "to-delete-user", "password": "StrongPass123", "role": "user"},
    )
    assert user_register.status_code == 200

    admin_token = _token("maintenance-admin", role="admin")
    res = client.post(
        "/api/v1/admin/users/delete",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"user_id": "to-delete-user"},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "ok"

