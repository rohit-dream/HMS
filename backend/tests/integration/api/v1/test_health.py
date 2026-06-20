"""Health endpoint integration tests."""

from fastapi import status


def test_liveness(client):
    response = client.get("/api/v1/health")
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["data"]["status"] == "ok"
    assert body["errors"] is None
    assert "request_id" in body["meta"]
    assert response.headers.get("X-Request-ID")


def test_readiness_returns_envelope(client):
    response = client.get("/api/v1/health/ready")
    body = response.json()
    assert "checks" in body["data"]
    assert body["data"]["checks"]["database"] in ("ok", "failed")
    assert response.status_code in (status.HTTP_200_OK, status.HTTP_503_SERVICE_UNAVAILABLE)
