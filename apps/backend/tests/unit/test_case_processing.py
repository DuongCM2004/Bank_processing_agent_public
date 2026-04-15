from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from ops_agent.application.services.case_processing import (
    CaseProcessingService,
    SQLAlchemyCaseProcessingTransitionAuditHook,
)
from ops_agent.application.services.case_workflow import CaseWorkflowService
from ops_agent.domain.shared.enums import (
    AuditEventType,
    CaseStatus,
    DecisionOutcome,
    DocumentStatus,
)
from ops_agent.domain.shared.exceptions import CaseProcessingExecutionError
from ops_agent.infrastructure.db.models import (
    AuditEvent,
    Case,
    ComplianceFinding,
    Decision,
    Document,
    ExtractionResult,
    OCRResult,
    ValidationFinding,
)
from ops_agent.infrastructure.db.repositories.processing_repository import ProcessingRepository
from ops_agent.infrastructure.providers.interfaces import (
    DocumentClassificationProvider,
    ExtractionProvider,
    OCRProvider,
    OCRProviderRequest,
    OCRProviderResult,
    ValidationRulesEngine,
)
from ops_agent.infrastructure.providers.placeholder import (
    PlaceholderDocumentClassificationProvider,
    PlaceholderExtractionProvider,
    PlaceholderOCRProvider,
    PlaceholderValidationRulesEngine,
)
from ops_agent.infrastructure.queue.contracts import InMemoryTaskDispatcher
from ops_agent.infrastructure.storage.local import LocalDocumentStorage


def _build_case_with_document(db_session, *, test_settings, content: bytes, document_type: str = "passport") -> Case:
    storage = LocalDocumentStorage(test_settings.storage.root_path)
    now = datetime.now(UTC)
    case = Case(
        case_reference=f"CASE-{document_type.upper()}-001",
        case_type="kyc_onboarding",
        status=CaseStatus.DOCUMENTS_UPLOADED,
        status_changed_at=now,
        current_queue="document_ops",
        source_channel="manual_upload",
    )
    db_session.add(case)
    db_session.flush()

    stored = storage.store(case_id=case.id, document_id=uuid4(), filename=f"{document_type}.txt", content=content)
    document = Document(
        case_id=case.id,
        filename=f"{document_type}.txt",
        document_type=document_type,
        mime_type="application/pdf",
        storage_key=stored.storage_key,
        sha256_digest=stored.sha256_digest,
        file_size_bytes=stored.size_bytes,
        uploaded_at=now,
        status=DocumentStatus.UPLOADED,
        status_changed_at=now,
        source_channel="manual_upload",
    )
    db_session.add(document)
    db_session.commit()
    db_session.refresh(case)
    return case


def _build_service(
    *,
    db_session,
    test_settings,
    ocr_provider: OCRProvider,
    extraction_provider: ExtractionProvider,
    classification_provider: DocumentClassificationProvider | None = None,
    validation_engine: ValidationRulesEngine | None = None,
    dispatcher=None,
) -> CaseProcessingService:
    repository = ProcessingRepository(db_session)
    workflow_service = CaseWorkflowService(audit_hooks=(SQLAlchemyCaseProcessingTransitionAuditHook(repository),))
    return CaseProcessingService(
        repository=repository,
        workflow_service=workflow_service,
        storage=LocalDocumentStorage(test_settings.storage.root_path),
        ocr_provider=ocr_provider,
        classification_provider=classification_provider or PlaceholderDocumentClassificationProvider(),
        extraction_provider=extraction_provider,
        validation_engine=validation_engine or PlaceholderValidationRulesEngine(),
        processing_settings=test_settings.processing,
        worker_settings=test_settings.worker,
        task_dispatcher=dispatcher,
    )


def test_case_processing_success_path_persists_outputs_and_moves_to_decision_ready(db_session, test_settings) -> None:
    case = _build_case_with_document(
        db_session,
        test_settings=test_settings,
        content=b"Passport No: P1234567\nName: Alice Example",
    )
    dispatcher = InMemoryTaskDispatcher()
    service = _build_service(
        db_session=db_session,
        test_settings=test_settings,
        ocr_provider=PlaceholderOCRProvider(),
        extraction_provider=PlaceholderExtractionProvider(),
        dispatcher=dispatcher,
    )

    task = service.queue_case_for_processing(case_id=case.id, requested_by="queue-dispatcher")
    result = service.process_case(task)

    assert result.final_status == CaseStatus.DECISION_READY
    assert result.manual_review_required is False
    refreshed_case = db_session.get(Case, case.id)
    assert refreshed_case is not None
    assert refreshed_case.status == CaseStatus.DECISION_READY
    assert len(dispatcher.enqueued) == 1
    assert db_session.query(OCRResult).count() == 1
    assert db_session.query(ExtractionResult).count() == 1
    decision = db_session.query(Decision).filter(Decision.case_id == refreshed_case.id).one()
    assert decision.outcome == DecisionOutcome.APPROVED
    event_types = {event.event_type for event in db_session.query(AuditEvent).filter(AuditEvent.case_id == refreshed_case.id).all()}
    assert AuditEventType.OCR_COMPLETED in event_types
    assert AuditEventType.EXTRACTION_COMPLETED in event_types
    assert AuditEventType.DECISION_RECORDED in event_types


def test_case_processing_routes_low_confidence_case_to_manual_review(db_session, test_settings) -> None:
    case = _build_case_with_document(
        db_session,
        test_settings=test_settings,
        content=b"unstructured text with no key fields",
        document_type="bank_statement",
    )
    service = _build_service(
        db_session=db_session,
        test_settings=test_settings,
        ocr_provider=PlaceholderOCRProvider(),
        extraction_provider=PlaceholderExtractionProvider(),
    )

    task = service.queue_case_for_processing(case_id=case.id)
    result = service.process_case(task)

    assert result.final_status == CaseStatus.MANUAL_REVIEW_REQUIRED
    assert result.manual_review_required is True
    refreshed_case = db_session.get(Case, case.id)
    assert refreshed_case is not None
    assert refreshed_case.status == CaseStatus.MANUAL_REVIEW_REQUIRED
    assert db_session.query(ValidationFinding).filter(ValidationFinding.case_id == case.id).count() >= 1
    assert db_session.query(ComplianceFinding).filter(ComplianceFinding.case_id == case.id).count() >= 1
    assert refreshed_case.documents[0].status == DocumentStatus.REVIEW_REQUIRED


class FailingOCRProvider(OCRProvider):
    def process(self, request: OCRProviderRequest) -> OCRProviderResult:
        raise RuntimeError("simulated OCR outage")


def test_case_processing_failure_marks_case_failed_and_supports_retry(db_session, test_settings) -> None:
    case = _build_case_with_document(
        db_session,
        test_settings=test_settings,
        content=b"Passport No: P1234567\nName: Alice Example",
    )
    service = _build_service(
        db_session=db_session,
        test_settings=test_settings,
        ocr_provider=FailingOCRProvider(),
        extraction_provider=PlaceholderExtractionProvider(),
    )

    task = service.queue_case_for_processing(case_id=case.id, attempt_number=1)
    with pytest.raises(CaseProcessingExecutionError):
        service.process_case(task)

    failed_case = db_session.get(Case, case.id)
    assert failed_case is not None
    assert failed_case.status == CaseStatus.FAILED
    assert failed_case.documents[0].status == DocumentStatus.FAILED

    retry_task = service.queue_case_for_processing(case_id=case.id, attempt_number=2)
    retried_case = db_session.get(Case, case.id)
    assert retried_case is not None
    assert retried_case.status == CaseStatus.QUEUED_FOR_PROCESSING
    assert retry_task.attempt_number == 2
