from __future__ import annotations

from pathlib import Path

import pytest

from tests.fixtures.builders import case_create_payload


pytestmark = pytest.mark.integration


def test_case_creation_returns_expected_mvp_payload(client) -> None:
    response = client.post("/api/v1/cases", json=case_create_payload())

    assert response.status_code == 201
    payload = response.json()
    assert payload["case_type"] == "kyc_onboarding"
    assert payload["status"] == "documents_uploaded"
    assert payload["documents"][0]["filename"] == "passport.pdf"


def test_invalid_workflow_transition_fails_clearly(client) -> None:
    create_response = client.post("/api/v1/cases", json=case_create_payload())
    case_id = create_response.json()["id"]

    response = client.patch(
        f"/api/v1/cases/{case_id}/status",
        json={
            "target_status": "approved",
            "actor_type": "user",
            "actor_id": "reviewer-1",
        },
    )

    assert response.status_code == 409
    error = response.json()["error"]
    assert error["code"] == "invalid_case_transition"
    assert "documents_uploaded" in error["message"]


def test_document_upload_metadata_is_persisted_and_traceable(client, test_settings) -> None:
    create_response = client.post("/api/v1/cases", json=case_create_payload(with_document=False))
    case_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/cases/{case_id}/documents",
        data={
            "document_type": "bank_statement",
            "source_channel": "manual_upload",
            "metadata": '{"source":"branch","currency":"VND"}',
        },
        files={"file": ("statement.pdf", b"fake-pdf-content", "application/pdf")},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["case_id"] == case_id
    assert payload["filename"] == "statement.pdf"
    assert payload["mime_type"] == "application/pdf"
    assert payload["file_size_bytes"] == len(b"fake-pdf-content")
    assert payload["metadata"]["source"] == "branch"
    assert payload["metadata"]["currency"] == "VND"

    stored_path = test_settings.storage.root_path.resolve() / Path(*payload["storage_key"].split("/"))
    assert stored_path.exists()
    assert stored_path.read_bytes() == b"fake-pdf-content"
