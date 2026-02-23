from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {"ok", "degraded"}
    assert "strict_provider_mode" in body
    assert "strict_provider_ready" in body
