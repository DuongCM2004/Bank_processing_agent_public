from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from ops_agent.domain.shared.enums import (
    AuditEventType,
    CaseStatus,
    DocumentStatus,
    ManualReviewActionType,
    ProcessingStatus,
)
from ops_agent.infrastructure.db.models import AuditEvent, Case, Document, ExtractionResult, ManualReviewAction


def _seed_review_case(
    db_session,
    *,
    case_status: CaseStatus,
    document_status: DocumentStatus,
    extracted_payload: dict[str, object] | None = None,
) -> tuple[Case, Document, ExtractionResult]:
    now = datetime.now(UTC)
    case = Case(
        case_reference=f"CASE-REVIEW-{uuid4().hex[:8]}",
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
        sha256_digest="a" * 64,
        file_size_bytes=1024,
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
        extracted_payload=extracted_payload or {"document_number": "OLD123"},
        confidence_score=0.95,
        evidence_refs=[{"document_id": str(document.id), "page_number": 1, "metadata": {"field_name": "document_number"}}],
        provider_name="placeholder_extraction",
        processed_at=now,
    )
    db_session.add(extraction_result)
    db_session.commit()
    return case, document, extraction_result


def test_require_manual_review_endpoint_transitions_case_and_records_action(client, db_session) -> None:
    reviewer_id = uuid4()
    case, document, _ = _seed_review_case(
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
    payload = response.json()
    assert payload["case_status"] == "manual_review_required"
    assert payload["action"]["action_type"] == "escalate"

    refreshed_case = db_session.get(Case, case.id)
    refreshed_document = db_session.get(Document, document.id)
    assert refreshed_case is not None and refreshed_case.status == CaseStatus.MANUAL_REVIEW_REQUIRED
    assert refreshed_document is not None and refreshed_document.status == DocumentStatus.REVIEW_REQUIRED

    review_action = db_session.query(ManualReviewAction).filter(ManualReviewAction.case_id == case.id).one()
    assert review_action.action_type == ManualReviewActionType.ESCALATE
    assert review_action.payload["previous_status"] == "decision_ready"


def test_add_manual_review_note_records_reviewer_attribution(client, db_session) -> None:
    reviewer_id = uuid4()
    case, document, _ = _seed_review_case(
        db_session,
        case_status=CaseStatus.MANUAL_REVIEW_REQUIRED,
        document_status=DocumentStatus.REVIEW_REQUIRED,
    )

    response = client.post(
        f"/api/v1/cases/{case.id}/manual-review/notes",
        json={
            "performed_by_user_id": str(reviewer_id),
            "document_id": str(document.id),
            "comment": "Verified signature against supporting record.",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["action_type"] == "add_note"
    assert payload["performed_by_user_id"] == str(reviewer_id)
    assert payload["comment"] == "Verified signature against supporting record."


def test_submit_manual_corrections_preserves_before_after_traceability(client, db_session) -> None:
    reviewer_id = uuid4()
    case, document, extraction_result = _seed_review_case(
        db_session,
        case_status=CaseStatus.MANUAL_REVIEW_REQUIRED,
        document_status=DocumentStatus.REVIEW_REQUIRED,
        extracted_payload={"document_number": "OLD123", "full_name": "Alice Example"},
    )

    response = client.post(
        f"/api/v1/cases/{case.id}/manual-review/corrections",
        json={
            "performed_by_user_id": str(reviewer_id),
            "document_id": str(document.id),
            "comment": "Corrected OCR digit transcription.",
            "corrections": [
                {
                    "extraction_result_id": str(extraction_result.id),
                    "field_name": "document_number",
                    "before_value": "OLD123",
                    "after_value": "NEW123",
                }
            ],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["action"]["action_type"] == "correct_data"
    assert payload["corrections"][0]["before_value"] == "OLD123"
    assert payload["corrections"][0]["after_value"] == "NEW123"

    refreshed_extraction = db_session.get(ExtractionResult, extraction_result.id)
    assert refreshed_extraction is not None
    assert refreshed_extraction.extracted_payload["document_number"] == "NEW123"

    review_action = db_session.query(ManualReviewAction).filter(ManualReviewAction.case_id == case.id).order_by(ManualReviewAction.created_at.desc()).first()
    assert review_action is not None
    assert review_action.payload["corrections"][0]["before_value"] == "OLD123"
    assert review_action.payload["corrections"][0]["after_value"] == "NEW123"


def test_resubmit_manual_review_to_decision_ready_completes_review(client, db_session) -> None:
    reviewer_id = uuid4()
    case, document, _ = _seed_review_case(
        db_session,
        case_status=CaseStatus.MANUAL_REVIEW_REQUIRED,
        document_status=DocumentStatus.REVIEW_REQUIRED,
    )

    response = client.post(
        f"/api/v1/cases/{case.id}/manual-review/resubmit",
        json={
            "performed_by_user_id": str(reviewer_id),
            "document_id": str(document.id),
            "target_status": "decision_ready",
            "comment": "Manual review completed.",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["case_status"] == "decision_ready"
    assert payload["action"]["action_type"] == "confirm_extraction"

    refreshed_case = db_session.get(Case, case.id)
    refreshed_document = db_session.get(Document, document.id)
    assert refreshed_case is not None and refreshed_case.status == CaseStatus.DECISION_READY
    assert refreshed_document is not None and refreshed_document.status == DocumentStatus.EXTRACTION_COMPLETED


def test_resubmit_manual_review_for_reprocessing_records_audit_event(client, db_session) -> None:
    reviewer_id = uuid4()
    case, document, _ = _seed_review_case(
        db_session,
        case_status=CaseStatus.MANUAL_REVIEW_REQUIRED,
        document_status=DocumentStatus.REVIEW_REQUIRED,
    )

    response = client.post(
        f"/api/v1/cases/{case.id}/manual-review/resubmit",
        json={
            "performed_by_user_id": str(reviewer_id),
            "document_id": str(document.id),
            "target_status": "queued_for_processing",
            "comment": "Resubmit for OCR rerun.",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["case_status"] == "queued_for_processing"
    assert payload["action"]["action_type"] == "request_reprocessing"

    audit_events = db_session.query(AuditEvent).filter(AuditEvent.case_id == case.id).all()
    assert any(event.event_type == AuditEventType.MANUAL_REVIEW_ACTION_RECORDED for event in audit_events)
