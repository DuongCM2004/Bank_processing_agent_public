from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ops_agent.main import app, repository


client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_repository() -> None:
    repository.cases.clear()
    repository.documents.clear()
    repository.document_versions.clear()
    repository.review_tasks.clear()
    repository.results.clear()
    repository.review_actions.clear()
    repository.audit_events.clear()
    repository.workflow_runs.clear()
    repository.workflow_step_runs.clear()
    repository.extraction_runs.clear()
    repository.validation_runs.clear()
    repository.decisions.clear()


def test_start_processing_for_queued_case_persists_workflow_run() -> None:
    create_response = client.post(
        "/v1/cases",
        json={
            "workflow_type": "bank_statement_ingestion",
            "priority": "normal",
            "review_required": False,
            "documents": [
                {
                    "filename": "statement.pdf",
                    "mime_type": "application/pdf",
                }
            ],
        },
    )
    case_id = create_response.json()["case"]["case_id"]

    process_response = client.post(
        f"/v1/cases/{case_id}/process",
        json={"requested_by": "ops-user-1", "reason_code": "manual_start"},
    )

    assert process_response.status_code == 202
    payload = process_response.json()
    assert payload["case_id"] == case_id
    assert payload["workflow_status"] == "in_progress"
    assert payload["case_status"] == "processing"

    status_response = client.get(f"/v1/cases/{case_id}/status")
    assert status_response.status_code == 200
    status_payload = status_response.json()
    assert status_payload["case_status"] == "processing"
    assert status_payload["workflow_status"] == "in_progress"
    assert status_payload["active_step"] == "ingestion"
    assert status_payload["extraction_status"] == "in_progress"


def test_closing_case_persists_latest_decision() -> None:
    create_response = client.post(
        "/v1/cases",
        json={
            "workflow_type": "income_verification",
            "priority": "normal",
            "review_required": True,
            "documents": [
                {
                    "filename": "payslip.pdf",
                    "mime_type": "application/pdf",
                }
            ],
        },
    )
    case_payload = create_response.json()
    case_id = case_payload["case"]["case_id"]
    task_id = case_payload["review_tasks"][0]["task_id"]

    client.post(f"/v1/review-tasks/{task_id}/claim", json={"reviewer_id": "reviewer-1"})
    close_response = client.post(
        f"/v1/cases/{case_id}/close",
        json={"requested_by": "reviewer-1", "outcome": "approved", "reason_code": "manual_approval"},
    )
    assert close_response.status_code == 200

    decision_response = client.get(f"/v1/cases/{case_id}/decisions/latest")
    assert decision_response.status_code == 200
    decision_payload = decision_response.json()
    assert decision_payload["decision_type"] == "manual_final_decision"
    assert decision_payload["outcome"] == "approved"
    assert decision_payload["reason_code"] == "manual_approval"
