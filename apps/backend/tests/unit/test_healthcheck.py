from __future__ import annotations


def test_healthcheck_returns_ok(client) -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "ops-agent-backend"
    assert payload["checks"]["api"] == "ok"
    assert payload["checks"]["database"] == "ok"

