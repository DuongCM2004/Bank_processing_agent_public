from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from app.audit.logger import AuditLogger
from app.core.exceptions import NotFoundError
from app.models.document import ExtractionResult
from app.models.enums import AuditActorType, AuditEventType, CaseStatus, DocumentStatus, ProcessingStatus
from app.repositories.cases import CaseRepository
from app.repositories.documents import DocumentRepository, ProcessingResultRepository
from app.schemas.cases import CaseStatusTransitionRequest
from app.schemas.processing import (
    ExtractionResultCreate,
    ExtractionResultResponse,
    QueueProcessingRequest,
    QueueProcessingResponse,
)
from app.services.cases import CaseService


class ProcessingService:
    def __init__(
        self,
        case_repository: CaseRepository,
        document_repository: DocumentRepository,
        result_repository: ProcessingResultRepository,
        case_service: CaseService,
        audit_logger: AuditLogger,
    ) -> None:
        self.case_repository = case_repository
        self.document_repository = document_repository
        self.result_repository = result_repository
        self.case_service = case_service
        self.audit_logger = audit_logger

    def queue_case_processing(
        self,
        *,
        case_id: UUID,
        request: QueueProcessingRequest,
    ) -> QueueProcessingResponse:
        case = self.case_repository.get(case_id)
        if case is None:
            raise NotFoundError("Case not found.", error_code="case_not_found")
        if case.status != CaseStatus.QUEUED_FOR_PROCESSING:
            self.case_service.transition_case(
                case_id=case_id,
                request=CaseStatusTransitionRequest(
                    to_status=CaseStatus.QUEUED_FOR_PROCESSING,
                    actor_type=AuditActorType.USER,
                    actor_id=request.actor_id,
                    reason_code=request.reason_code,
                ),
            )
        self.audit_logger.record(
            event_type=AuditEventType.PROCESSING_QUEUED,
            actor_type=AuditActorType.USER,
            actor_id=request.actor_id,
            case_id=case_id,
            entity_type="case",
            entity_id=case_id,
            message="Case queued for document processing.",
            details={"queue": "celery", "task": "process_case_documents"},
        )
        self.case_repository.db.commit()
        self._dispatch_processing_task(case_id)
        return QueueProcessingResponse(case_id=case_id, status=CaseStatus.QUEUED_FOR_PROCESSING.value)

    def record_extraction_result(self, request: ExtractionResultCreate) -> ExtractionResultResponse:
        document = self.document_repository.get(request.document_id)
        if document is None:
            raise NotFoundError("Document not found.", error_code="document_not_found")

        result = ExtractionResult(
            document_id=request.document_id,
            ocr_result_id=request.ocr_result_id,
            status=ProcessingStatus.COMPLETED,
            schema_name=request.schema_name,
            extracted_payload=request.extracted_payload.model_dump(mode="json"),
            confidence_score=request.confidence_score,
            evidence_refs=[item.model_dump(mode="json") for item in request.evidence_refs],
            provider_name=request.provider_name,
            processed_at=datetime.now(UTC),
            model_version=request.model_version,
        )
        document.status = DocumentStatus.IN_REVIEW
        document.updated_by = "llm-extraction"
        self.result_repository.add_extraction_result(result)
        self.result_repository.db.flush()
        self.audit_logger.record(
            event_type=AuditEventType.EXTRACTION_COMPLETED,
            actor_type=AuditActorType.SERVICE,
            actor_id="llm-extraction",
            case_id=document.case_id,
            entity_type="extraction_result",
            entity_id=result.id,
            message="LLM document extraction completed and queued for manual review.",
            details={
                "document_uuid": str(document.id),
                "schema_name": request.schema_name,
                "provider_name": request.provider_name,
                "model_version": request.model_version,
            },
        )
        self.result_repository.db.commit()
        self.result_repository.db.refresh(result)
        return ExtractionResultResponse.model_validate(result)

    def _dispatch_processing_task(self, case_id: UUID) -> None:
        try:
            from app.tasks.processing import process_case_documents

            process_case_documents.delay(str(case_id))
        except Exception as exc:
            self.audit_logger.record(
                event_type=AuditEventType.DOCUMENT_FAILED,
                actor_type=AuditActorType.SYSTEM,
                actor_id="task-dispatch",
                case_id=case_id,
                entity_type="case",
                entity_id=case_id,
                message="Document processing task dispatch failed.",
                details={"task": "process_case_documents", "error": str(exc)},
            )
            self.result_repository.db.commit()
