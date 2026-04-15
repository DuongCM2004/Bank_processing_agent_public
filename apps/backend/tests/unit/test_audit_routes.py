from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from ops_agent.domain.shared.enums import (
    AuditActorType,
    AuditEventType,
    CaseStatus,
    DocumentStatus,
    FindingSeverity,
    FindingStatus,
    ProcessingStatus,
)
from ops_agent.infrastructure.db.models import Case, ComplianceFinding, Document, ExtractionResult


def _seed_decision_case(db_session, *, case_status: CaseStatus, document_status: DocumentStatus) -> tuple[Case, Document, ExtractionResult]:
    now = datetime.now(UTC)
    case = Case(
        case_reference=f"CASE-AUDIT-{uuid4().hex[:8]}",
        case_type="kyc_onboarding",
        status=case_status,
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
        storage_key=f"cases/{case.id}/documents/passport.pdf",
        sha256_digest="d" * 64,
        file_size_bytes=2048,
        uploaded_at=now,
        status=document_status,
        status_changed_at=now,
        source_channel="manual_upload",
    )
    db_session.add(document)
    db_session.flush()

    extraction_result = ExtractionResult(
        document_id=document.id,
        status=ProcessingStatus.COMPLETED,
        schema_name="passport_mvp",
        extracted_payload={"document_number": "ABC123"},
        confidence_score=0.96,
        evidence_refs=[{"document_id": str(document.id), "page_number": 1}],
        provider_name="placeholder_extraction",
        processed_at=now,
    )
    db_session.add(extraction_result)
    db_session.commit()
    return case, document, extraction_result


def test_case_audit_events_route_supports_filters_and_pagination(client) -> None:
    create_response = client.post(
        "/api/v1/cases",
        json={
            "case_type": "kyc_onboarding",
            "source_channel": "manual_upload",
            "current_queue": "document_ops",
            "documents": [
                {
                    "filename": "passport.pdf",
                    "document_type": "passport",
                    "mime_type": "application/pdf",
                    "source_channel": "manual_upload",
                    "sha256_digest": "a" * 64,
                    "storage_key": "cases/test/passport.pdf",
                }
            ],
        },
    )
    case_id = create_response.json()["id"]

    all_events = client.get(f"/api/v1/cases/{case_id}/audit-events", params={"limit": 10, "offset": 0})
    assert all_events.status_code == 200
    all_payload = all_events.json()
    assert all_payload["total"] >= 3
    assert len(all_payload["items"]) >= 3

    filtered = client.get(
        f"/api/v1/cases/{case_id}/audit-events",
        params={"event_type": "status_changed", "limit": 10, "offset": 0},
    )
    assert filtered.status_code == 200
    filtered_payload = filtered.json()
    assert filtered_payload["total"] == 1
    assert filtered_payload["items"][0]["event_type"] == "status_changed"
    assert filtered_payload["items"][0]["summary"] == "Case status changed from 'created' to 'documents_uploaded'."

    paged = client.get(f"/api/v1/cases/{case_id}/audit-events", params={"limit": 1, "offset": 0})
    assert paged.status_code == 200
    paged_payload = paged.json()
    assert paged_payload["limit"] == 1
    assert len(paged_payload["items"]) == 1


def test_document_upload_audit_event_is_structured(client) -> None:
    create_response = client.post(
        "/api/v1/cases",
        json={
            "case_type": "kyc_onboarding",
            "source_channel": "manual_upload",
            "current_queue": "document_ops",
        },
    )
    case_id = create_response.json()["id"]

    upload_response = client.post(
        f"/api/v1/cases/{case_id}/documents",
        data={"document_type": "bank_statement"},
        files={"file": ("statement.pdf", b"fake-pdf-content", "application/pdf")},
    )
    assert upload_response.status_code == 201

    audit_response = client.get(
        f"/api/v1/cases/{case_id}/audit-events",
        params={"event_type": "document_added", "resource_type": "document", "limit": 10, "offset": 0},
    )
    assert audit_response.status_code == 200
    payload = audit_response.json()
    assert payload["total"] == 1
    event = payload["items"][0]
    assert event["summary"] == "Document 'statement.pdf' was uploaded to the case."
    assert event["metadata"]["mime_type"] == "application/pdf"
    assert event["metadata"]["file_size_bytes"] == len(b"fake-pdf-content")


def test_manual_review_audit_event_is_structured(client, db_session) -> None:
    reviewer_id = uuid4()
    case, document, _ = _seed_decision_case(
        db_session,
        case_status=CaseStatus.DECISION_READY,
        document_status=DocumentStatus.EXTRACTION_COMPLETED,
    )

    response = client.post(
        f"/api/v1/cases/{case.id}/manual-review/require",
        json={
            "performed_by_user_id": str(reviewer_id),
            "document_id": str(document.id),
            "comment": "Escalating for human review.",
            "reason_code": "quality_check_required",
        },
    )
    assert response.status_code == 200

    audit_response = client.get(
        f"/api/v1/cases/{case.id}/audit-events",
        params={"event_type": "manual_review_action_recorded", "limit": 10, "offset": 0},
    )
    assert audit_response.status_code == 200
    payload = audit_response.json()
    assert payload["total"] == 1
    event = payload["items"][0]
    assert event["summary"] == "Manual review action 'escalate' was recorded."
    assert event["actor_type"] == AuditActorType.USER.value
    assert event["metadata"]["action_type"] == "escalate"
    assert event["metadata"]["payload"]["target_status"] == "manual_review_required"


def test_decision_audit_event_is_structured(client, db_session) -> None:
    reviewer_id = uuid4()
    case, document, extraction_result = _seed_decision_case(
        db_session,
        case_status=CaseStatus.DECISION_READY,
        document_status=DocumentStatus.EXTRACTION_COMPLETED,
    )
    compliance_finding = ComplianceFinding(
        case_id=case.id,
        document_id=document.id,
        extraction_result_id=extraction_result.id,
        policy_code="kyc-001",
        message="Additional review required before approval.",
        severity=FindingSeverity.WARNING,
        status=FindingStatus.OPEN,
        evidence_refs=[{"document_id": str(document.id), "page_number": 1}],
    )
    db_session.add(compliance_finding)
    db_session.commit()

    response = client.post(
        f"/api/v1/cases/{case.id}/decisions/request-review",
        json={
            "decided_by_user_id": str(reviewer_id),
            "decision_type": "reviewer_decision",
            "reason_code": "supervisor_review_required",
            "rationale": "Further review required.",
            "linked_findings": [{"finding_type": "compliance", "finding_id": str(compliance_finding.id)}],
        },
    )
    assert response.status_code == 200

    audit_response = client.get(
        f"/api/v1/cases/{case.id}/audit-events",
        params={"event_type": "decision_recorded", "limit": 10, "offset": 0},
    )
    assert audit_response.status_code == 200
    payload = audit_response.json()
    assert payload["total"] == 1
    event = payload["items"][0]
    assert event["summary"] == "Decision 'review_required' was recorded for the case."
    assert event["metadata"]["reason_code"] == "supervisor_review_required"
    assert event["metadata"]["linked_findings"] == [
        {"finding_type": "compliance", "finding_id": str(compliance_finding.id)}
    ]
