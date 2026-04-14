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


def test_create_case_creates_review_task_and_audit_trail() -> None:
    response = client.post(
        "/v1/cases",
        json={
            "workflow_type": "kyc_onboarding",
            "priority": "high",
            "review_required": True,
            "customer_reference": "cust-001",
            "documents": [
                {
                    "filename": "passport.pdf",
                    "mime_type": "application/pdf",
                    "source_channel": "ops_upload",
                }
            ],
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["case"]["status"] == "review_required"
    assert payload["review_tasks"][0]["assigned_queue"] == "priority_review"
    assert len(payload["documents"]) == 1

    case_id = payload["case"]["case_id"]
    audit_response = client.get(f"/v1/cases/{case_id}/audit-events")
    assert audit_response.status_code == 200
    assert len(audit_response.json()["items"]) >= 5


def test_claim_correct_revalidate_and_close_flow() -> None:
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

    claim_response = client.post(
        f"/v1/review-tasks/{task_id}/claim",
        json={"reviewer_id": "reviewer-1"},
    )
    assert claim_response.status_code == 200
    assert claim_response.json()["status"] == "claimed"

    correction_response = client.post(
        f"/v1/cases/{case_id}/field-corrections",
        json={
            "reviewer_id": "reviewer-1",
            "corrections": [
                {
                    "field_name": "gross_pay",
                    "new_value": "5000",
                    "reason_code": "reviewer_confirmed",
                    "evidence_refs": [
                        {
                            "document_id": case_payload["documents"][0]["document_id"],
                            "page_number": 1,
                            "text_span": "Gross Pay 5000",
                        }
                    ],
                }
            ],
        },
    )
    assert correction_response.status_code == 200
    assert correction_response.json()["status"] == "corrected"

    revalidate_response = client.post(
        f"/v1/cases/{case_id}/revalidate",
        json={"requested_by": "reviewer-1", "reason_code": "post_correction_review"},
    )
    assert revalidate_response.status_code == 200
    assert revalidate_response.json()["status"] == "validated"

    close_response = client.post(
        f"/v1/cases/{case_id}/close",
        json={"requested_by": "reviewer-1", "outcome": "approved", "reason_code": "manual_approval"},
    )
    assert close_response.status_code == 200
    assert close_response.json()["status"] == "closed"
    assert close_response.json()["final_outcome"] == "approved"


def test_add_document_to_existing_open_case() -> None:
    create_response = client.post(
        "/v1/cases",
        json={
            "workflow_type": "corporate_kyc",
            "priority": "normal",
            "review_required": True,
            "documents": [],
        },
    )
    case_id = create_response.json()["case"]["case_id"]

    add_response = client.post(
        f"/v1/cases/{case_id}/documents",
        json={
            "filename": "certificate_of_incorporation.pdf",
            "mime_type": "application/pdf",
            "source_channel": "ops_upload",
        },
    )

    assert add_response.status_code == 201
    document_id = add_response.json()["document_id"]

    get_document_response = client.get(f"/v1/cases/{case_id}/documents/{document_id}")
    assert get_document_response.status_code == 200
    assert get_document_response.json()["filename"] == "certificate_of_incorporation.pdf"
