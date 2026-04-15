from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

from ops_agent.domain.shared.enums import (
    AuditActorType,
    AuditEventType,
    CaseStatus,
    DocumentStatus,
    ProcessingStatus,
)
from ops_agent.infrastructure.db.models import AuditEvent, Case, Document, ExtractionResult, OCRResult


def _case_payload(*, with_document: bool = True) -> dict[str, object]:
    payload: dict[str, object] = {
        "case_type": "kyc_onboarding",
        "source_channel": "manual_upload",
        "current_queue": "document_ops",
        "metadata": {"journey": "onboarding"},
    }
    if with_document:
        payload["documents"] = [
            {
                "filename": "passport.pdf",
                "document_type": "passport",
                "mime_type": "application/pdf",
                "source_channel": "manual_upload",
                "sha256_digest": "a" * 64,
                "storage_key": "cases/case-1/passport.pdf",
                "metadata": {"country": "VN"},
            }
        ]
    return payload


def test_create_case_returns_created_payload_and_uploaded_status(client) -> None:
    response = client.post("/api/v1/cases", json=_case_payload())

    assert response.status_code == 201
    payload = response.json()
    assert payload["case_type"] == "kyc_onboarding"
    assert payload["status"] == "documents_uploaded"
    assert len(payload["documents"]) == 1
    assert payload["documents"][0]["filename"] == "passport.pdf"


def test_list_cases_supports_status_filter_and_pagination(client) -> None:
    client.post("/api/v1/cases", json=_case_payload(with_document=False))
    client.post("/api/v1/cases", json=_case_payload(with_document=True))

    response = client.get("/api/v1/cases", params={"status": "created", "limit": 10, "offset": 0})

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert len(payload["items"]) == 1
    assert payload["items"][0]["status"] == "created"
    assert payload["items"][0]["document_count"] == 0


def test_get_case_detail_returns_linked_documents_and_results(client, db_session) -> None:
    now = datetime.now(UTC)
    case = Case(
        case_reference="CASE-DETAIL-1",
        case_type="kyc_onboarding",
        status=CaseStatus.DOCUMENTS_UPLOADED,
        status_changed_at=now,
        current_queue="document_ops",
        source_channel="manual_upload",
    )
    db_session.add(case)
    db_session.flush()

    document = Document(
        case_id=case.id,
        filename="passport.pdf",
        document_type="passport",
        mime_type="application/pdf",
        storage_key="cases/detail/passport.pdf",
        sha256_digest="b" * 64,
        file_size_bytes=2048,
        uploaded_at=now,
        status=DocumentStatus.UPLOADED,
        status_changed_at=now,
        source_channel="manual_upload",
    )
    db_session.add(document)
    db_session.flush()

    ocr_result = OCRResult(
        document_id=document.id,
        status=ProcessingStatus.COMPLETED,
        raw_text="OCR text",
        confidence_score=0.97,
        provider_name="placeholder",
        processed_at=now,
    )
    db_session.add(ocr_result)
    db_session.flush()

    extraction_result = ExtractionResult(
        document_id=document.id,
        ocr_result_id=ocr_result.id,
        status=ProcessingStatus.COMPLETED,
        schema_name="passport_v1",
        extracted_payload={"document_number": "123456789"},
        confidence_score=0.91,
        evidence_refs=[{"document_id": str(document.id), "page_number": 1}],
        provider_name="placeholder",
        processed_at=now,
    )
    db_session.add(extraction_result)

    db_session.add(
        AuditEvent(
            case_id=case.id,
            actor_type=AuditActorType.SYSTEM,
            actor_identifier="system",
            event_type=AuditEventType.CASE_CREATED,
            resource_type="case",
            resource_id=case.id,
            occurred_at=now,
            details={"source": "test"},
            evidence_refs=[],
        )
    )
    db_session.commit()

    response = client.get(f"/api/v1/cases/{case.id}/detail")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == str(case.id)
    assert len(payload["documents"]) == 1
    assert len(payload["ocr_results"]) == 1
    assert len(payload["extraction_results"]) == 1
    assert payload["extraction_results"][0]["schema_name"] == "passport_v1"
    assert len(payload["audit_events"]) == 1


def test_update_case_status_uses_safe_workflow_service(client) -> None:
    create_response = client.post("/api/v1/cases", json=_case_payload())
    case_id = create_response.json()["id"]

    valid_response = client.patch(
        f"/api/v1/cases/{case_id}/status",
        json={
            "target_status": "queued_for_processing",
            "actor_type": "service",
            "actor_id": "queue-dispatcher",
            "reason_code": "queued_for_processing",
        },
    )

    assert valid_response.status_code == 200
    assert valid_response.json()["status"] == "queued_for_processing"

    invalid_response = client.patch(
        f"/api/v1/cases/{case_id}/status",
        json={
            "target_status": "approved",
            "actor_type": "user",
            "actor_id": str(uuid4()),
        },
    )

    assert invalid_response.status_code == 409
    error = invalid_response.json()["error"]
    assert error["code"] == "invalid_case_transition"
    assert "queued_for_processing" in error["message"]


def test_upload_document_endpoint_persists_file_and_metadata(client, db_session, test_settings) -> None:
    create_response = client.post("/api/v1/cases", json=_case_payload(with_document=False))
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
    assert payload["metadata"]["currency"] == "VND"

    stored_path = test_settings.storage.root_path.resolve() / Path(*payload["storage_key"].split("/"))
    assert stored_path.exists()
    assert stored_path.read_bytes() == b"fake-pdf-content"

    case = db_session.get(Case, UUID(payload["case_id"]))
    assert case is not None
    assert case.status == CaseStatus.DOCUMENTS_UPLOADED


def test_upload_document_rejects_unsupported_media_type(client) -> None:
    create_response = client.post("/api/v1/cases", json=_case_payload(with_document=False))
    case_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/cases/{case_id}/documents",
        data={"document_type": "bank_statement"},
        files={"file": ("statement.txt", b"plain-text", "text/plain")},
    )

    assert response.status_code == 415
    assert response.json()["error"]["code"] == "unsupported_media_type"


def test_upload_document_rejects_large_payload(client, test_settings) -> None:
    create_response = client.post("/api/v1/cases", json=_case_payload(with_document=False))
    case_id = create_response.json()["id"]
    oversized_content = b"x" * (test_settings.storage.max_upload_bytes + 1)

    response = client.post(
        f"/api/v1/cases/{case_id}/documents",
        data={"document_type": "bank_statement"},
        files={"file": ("statement.pdf", oversized_content, "application/pdf")},
    )

    assert response.status_code == 413
    assert response.json()["error"]["code"] == "payload_too_large"


def test_list_case_documents_returns_uploaded_documents(client) -> None:
    create_response = client.post("/api/v1/cases", json=_case_payload(with_document=False))
    case_id = create_response.json()["id"]

    client.post(
        f"/api/v1/cases/{case_id}/documents",
        data={"document_type": "bank_statement"},
        files={"file": ("statement.pdf", b"fake-pdf-content", "application/pdf")},
    )

    response = client.get(f"/api/v1/cases/{case_id}/documents")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["filename"] == "statement.pdf"


def test_get_case_document_returns_document_metadata(client) -> None:
    create_response = client.post("/api/v1/cases", json=_case_payload(with_document=False))
    case_id = create_response.json()["id"]

    upload_response = client.post(
        f"/api/v1/cases/{case_id}/documents",
        data={"document_type": "bank_statement"},
        files={"file": ("statement.pdf", b"fake-pdf-content", "application/pdf")},
    )
    document_id = upload_response.json()["id"]

    response = client.get(f"/api/v1/cases/{case_id}/documents/{document_id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == document_id
    assert payload["case_id"] == case_id
    assert payload["filename"] == "statement.pdf"


def test_download_document_returns_content_and_emits_audit_event(client, db_session) -> None:
    create_response = client.post("/api/v1/cases", json=_case_payload(with_document=False))
    case_id = create_response.json()["id"]

    upload_response = client.post(
        f"/api/v1/cases/{case_id}/documents",
        data={"document_type": "bank_statement"},
        files={"file": ("statement.pdf", b"fake-pdf-content", "application/pdf")},
    )
    document_payload = upload_response.json()
    document_id = document_payload["id"]

    response = client.get(f"/api/v1/cases/{case_id}/documents/{document_id}/download")

    assert response.status_code == 200
    assert response.content == b"fake-pdf-content"
    assert response.headers["content-type"] == "application/pdf"
    assert "statement.pdf" in response.headers["content-disposition"]

    document_audits = [
        event
        for event in db_session.query(AuditEvent).filter(AuditEvent.resource_id == UUID(document_id)).all()
        if event.event_type == AuditEventType.DOCUMENT_DOWNLOADED
    ]
    assert len(document_audits) == 1
