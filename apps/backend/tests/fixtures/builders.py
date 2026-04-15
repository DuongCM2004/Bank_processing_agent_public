from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy.orm import Session

from ops_agent.domain.shared.enums import CaseStatus, DocumentStatus, ProcessingStatus
from ops_agent.infrastructure.db.models import Case, Document, ExtractionResult


def case_create_payload(*, with_document: bool = True) -> dict[str, object]:
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
                "storage_key": f"cases/{uuid4().hex}/passport.pdf",
                "metadata": {"country": "VN"},
            }
        ]
    return payload


def seed_review_case(
    db_session: Session,
    *,
    case_status: CaseStatus = CaseStatus.MANUAL_REVIEW_REQUIRED,
    document_status: DocumentStatus = DocumentStatus.REVIEW_REQUIRED,
    extracted_payload: dict[str, object] | None = None,
) -> tuple[Case, Document, ExtractionResult]:
    now = datetime.now(UTC)
    case = Case(
        case_reference=f"CASE-TEST-{uuid4().hex[:10]}",
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
        sha256_digest="b" * 64,
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
        extracted_payload=extracted_payload or {"document_number": "OLD123", "full_name": "Alice Example"},
        confidence_score=0.93,
        evidence_refs=[{"document_id": str(document.id), "page_number": 1, "metadata": {"field_name": "document_number"}}],
        provider_name="placeholder_extraction",
        processed_at=now,
    )
    db_session.add(extraction_result)
    db_session.commit()
    return case, document, extraction_result
