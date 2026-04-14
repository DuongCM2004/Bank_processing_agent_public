from pathlib import Path
import sys

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from ops_agent.main import app
from tests.testkit import build_case_create_request


def example_integration_review_correction_flow() -> None:
    client = TestClient(app)
    payload = build_case_create_request()
    response = client.post("/v1/cases", json=payload)
    assert response.status_code == 201

    # Expand this example into:
    # claim review task -> submit correction -> revalidate -> audit assertions
