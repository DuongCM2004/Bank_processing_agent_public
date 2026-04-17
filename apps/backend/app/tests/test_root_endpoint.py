from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import create_app


def test_root_endpoint_describes_backend_entrypoints() -> None:
    client = TestClient(create_app())

    response = client.get("/")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["api_base"] == "/api/v1"
    assert payload["links"]["health"] == "/api/v1/health"
    assert payload["links"]["docs"] == "/api/v1/docs"
    assert "document upload and listing" in payload["features"]
