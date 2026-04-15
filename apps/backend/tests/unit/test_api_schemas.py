from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from ops_agent.api.schemas import (
    AuditEventResponse,
    CaseCreateRequest,
    CaseDetailResponse,
    DecisionResponse,
    DocumentUploadMetadataRequest,
    DocumentUploadMetadataResponse,
    ErrorResponse,
    EvidenceReferenceRequest,
    ExtractionResultResponse,
    ManualReviewActionRequest,
    OCRResultResponse,
    ValidationFindingResponse,
    ValidationResultResponse,
)
from ops_agent.domain.shared.enums import (
    AuditActorType,
    AuditEventType,
    CaseStatus,
    DecisionOutcome,
    DecisionType,
    DocumentStatus,
    FindingSeverity,
    FindingStatus,
    ManualReviewActionType,
    ProcessingStatus,
)


def test_case_create_request_supports_nested_documents() -> None:
    request = CaseCreateRequest(
        case_type="kyc_onboarding",
        documents=[
            DocumentUploadMetadataRequest(
                filename="passport.pdf",
                document_type="passport",
                mime_type="application/pdf",
                source_channel="manual_upload",
                sha256_digest="a" * 64,
                storage_key="cases/case-1/passport.pdf",
            )
        ],
    )

    assert request.case_type == "kyc_onboarding"
    assert len(request.documents) == 1
    assert request.documents[0].filename == "passport.pdf"


def test_manual_review_request_supports_evidence_refs() -> None:
    request = ManualReviewActionRequest(
        performed_by_user_id=uuid4(),
        action_type=ManualReviewActionType.CORRECT_DATA,
        payload={"field_name": "customer_name", "new_value": "Jane Doe"},
        evidence_refs=[
            EvidenceReferenceRequest(
                document_id=uuid4(),
                page_number=1,
                text_anchor="Jane D0e",
                extracted_value="Jane Doe",
            )
        ],
    )

    assert request.action_type == ManualReviewActionType.CORRECT_DATA
    assert request.evidence_refs[0].page_number == 1


def test_case_detail_response_embeds_results_and_audit_data() -> None:
    now = datetime.now(UTC)
    case_id = uuid4()
    document_id = uuid4()
    extraction_id = uuid4()

    response = CaseDetailResponse(
        id=case_id,
        case_reference="CASE-0001",
        case_type="kyc_onboarding",
        status=CaseStatus.MANUAL_REVIEW_REQUIRED,
        status_changed_at=now,
        current_queue="document_ops",
        source_channel="manual_upload",
        documents=[
            DocumentUploadMetadataResponse(
                id=document_id,
                case_id=case_id,
                filename="passport.pdf",
                document_type="passport",
                mime_type="application/pdf",
                source_channel="manual_upload",
                storage_key="cases/case-1/passport.pdf",
                sha256_digest="a" * 64,
                file_size_bytes=1024,
                uploaded_at=now,
                status=DocumentStatus.REVIEW_REQUIRED,
                status_changed_at=now,
                created_at=now,
                updated_at=now,
            )
        ],
        ocr_results=[
            OCRResultResponse(
                id=uuid4(),
                document_id=document_id,
                status=ProcessingStatus.COMPLETED,
                raw_text="Passport text",
                confidence_score=0.98,
                provider_name="placeholder",
                created_at=now,
                updated_at=now,
            )
        ],
        extraction_results=[
            ExtractionResultResponse(
                id=extraction_id,
                document_id=document_id,
                status=ProcessingStatus.COMPLETED,
                schema_name="passport_v1",
                extracted_payload={"document_number": "123456789"},
                confidence_score=0.93,
                provider_name="placeholder",
                created_at=now,
                updated_at=now,
            )
        ],
        validation=ValidationResultResponse(
            case_id=case_id,
            validation_findings=[
                ValidationFindingResponse(
                    id=uuid4(),
                    case_id=case_id,
                    document_id=document_id,
                    extraction_result_id=extraction_id,
                    rule_code="name_match_required",
                    field_name="full_name",
                    message="Name requires manual confirmation.",
                    severity=FindingSeverity.WARNING,
                    status=FindingStatus.OPEN,
                    created_at=now,
                    updated_at=now,
                )
            ],
            has_blocking_findings=False,
        ),
        decisions=[
            DecisionResponse(
                id=uuid4(),
                case_id=case_id,
                decision_type=DecisionType.REVIEWER_DECISION,
                outcome=DecisionOutcome.REVIEW_REQUIRED,
                reason_code="manual_confirmation_required",
                created_at=now,
                updated_at=now,
            )
        ],
        audit_events=[
            AuditEventResponse(
                id=uuid4(),
                case_id=case_id,
                actor_type=AuditActorType.USER,
                actor_identifier="reviewer-1",
                event_type=AuditEventType.MANUAL_REVIEW_ACTION_RECORDED,
                summary="Manual review action 'add_note' was recorded.",
                resource_type="case",
                resource_id=case_id,
                occurred_at=now,
                metadata={"action_type": "add_note"},
                created_at=now,
                updated_at=now,
            )
        ],
        created_at=now,
        updated_at=now,
    )

    assert response.status == CaseStatus.MANUAL_REVIEW_REQUIRED
    assert response.documents[0].status == DocumentStatus.REVIEW_REQUIRED
    assert response.extraction_results[0].confidence_score == 0.93
    assert response.validation.validation_findings[0].rule_code == "name_match_required"
    assert response.audit_events[0].event_type == AuditEventType.MANUAL_REVIEW_ACTION_RECORDED


def test_error_response_supports_structured_details() -> None:
    response = ErrorResponse(
        code="request_validation_failed",
        message="Request validation failed.",
        trace_id="trace-123",
        details=[{"field": "documents.0.filename", "issue": "Field required"}],
    )

    assert response.code == "request_validation_failed"
    assert response.details[0].field == "documents.0.filename"
