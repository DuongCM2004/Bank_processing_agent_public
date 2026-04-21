from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from app.audit.logger import AuditLogger
from app.core.config import get_settings
from app.db.session import get_session_factory
from app.models.document import Document, ExtractionResult
from app.models.enums import AuditActorType, AuditEventType, CaseStatus, DocumentStatus, ProcessingStatus
from app.providers.base import ProviderDocumentInput
from app.providers.gpt_extraction import GptDocumentExtractionProvider
from app.repositories.audit import AuditEventRepository
from app.repositories.cases import CaseRepository
from app.repositories.documents import DocumentRepository, ProcessingResultRepository
from app.tasks.celery_app import celery_app


@celery_app.task(name="app.tasks.processing.process_case_documents")
def process_case_documents(case_id: str) -> dict[str, object]:
    parsed_case_id = UUID(case_id)
    settings = get_settings()
    session_factory = get_session_factory()
    processed = 0
    failed = 0

    with session_factory() as db:
        case_repository = CaseRepository(db)
        document_repository = DocumentRepository(db)
        result_repository = ProcessingResultRepository(db)
        audit_logger = AuditLogger(AuditEventRepository(db))

        case = case_repository.get(parsed_case_id)
        if case is None:
            return {"case_id": str(parsed_case_id), "status": "failed", "detail": "Case not found."}

        provider = GptDocumentExtractionProvider(settings)
        documents = document_repository.list_by_case(parsed_case_id)
        case.status = CaseStatus.PROCESSING
        case.status_changed_at = datetime.now(UTC)

        for document in documents:
            extraction_run = _latest_or_create_extraction(
                result_repository,
                document,
                schema_name=settings.llm_schema_version,
                model_version=settings.gpt_model,
            )
            try:
                _set_document_status(document, DocumentStatus.PREPROCESSING)
                db.flush()
                _set_document_status(document, DocumentStatus.EXTRACTING)
                extraction_run.status = ProcessingStatus.IN_PROGRESS
                extraction_run.updated_by = "llm-extraction"
                db.flush()

                extraction = provider.extract(
                    ProviderDocumentInput(
                        document_id=document.id,
                        storage_key=document.storage_key,
                        mime_type=document.mime_type,
                    ),
                    raw_text=None,
                )

                _set_document_status(document, DocumentStatus.IN_REVIEW)
                extraction_run.status = ProcessingStatus.COMPLETED
                extraction_run.schema_name = extraction.schema_name
                extraction_run.extracted_payload = extraction.extracted_payload
                extraction_run.confidence_score = extraction.confidence_score
                extraction_run.evidence_refs = extraction.evidence_refs
                extraction_run.provider_job_id = extraction.provider_job_id
                extraction_run.processed_at = datetime.now(UTC)
                extraction_run.provider_name = provider.provider_name
                extraction_run.model_version = extraction.model_version
                extraction_run.updated_by = "llm-extraction"
                audit_logger.record(
                    event_type=AuditEventType.EXTRACTION_COMPLETED,
                    actor_type=AuditActorType.SERVICE,
                    actor_id="llm-extraction",
                    case_id=document.case_id,
                    entity_type="extraction_result",
                    entity_id=extraction_run.id,
                    message="Notebook-style GPT extraction completed and queued for manual review.",
                    details={
                        "document_uuid": str(document.id),
                        "extraction_uuid": str(extraction_run.id),
                        "model": settings.gpt_model,
                        "provider": provider.provider_name,
                        "orchestrator": "langgraph",
                    },
                )
                processed += 1
            except Exception as exc:
                _set_document_status(document, DocumentStatus.FAILED)
                extraction_run.status = ProcessingStatus.FAILED
                extraction_run.updated_by = "llm-extraction"
                audit_logger.record(
                    event_type=AuditEventType.DOCUMENT_FAILED,
                    actor_type=AuditActorType.SERVICE,
                    actor_id="llm-extraction",
                    case_id=document.case_id,
                    entity_type="document",
                    entity_id=document.id,
                    message="Notebook-style GPT extraction failed.",
                    details={
                        "document_uuid": str(document.id),
                        "extraction_uuid": str(extraction_run.id),
                        "error": str(exc),
                    },
                )
                failed += 1

        case.status = CaseStatus.MANUAL_REVIEW_REQUIRED if processed else CaseStatus.FAILED
        case.status_changed_at = datetime.now(UTC)
        db.commit()

    return {
        "case_id": str(parsed_case_id),
        "status": "completed" if processed else "failed",
        "processed": processed,
        "failed": failed,
    }


def _latest_or_create_extraction(
    result_repository: ProcessingResultRepository,
    document: Document,
    schema_name: str,
    model_version: str,
) -> ExtractionResult:
    extraction = result_repository.get_latest_extraction_for_document(document.id)
    if extraction is not None and extraction.status in {ProcessingStatus.PENDING, ProcessingStatus.IN_PROGRESS}:
        return extraction

    extraction = ExtractionResult(
        document_id=document.id,
        status=ProcessingStatus.PENDING,
        schema_name=schema_name,
        extracted_payload={},
        evidence_refs=[],
        provider_name=GptDocumentExtractionProvider.provider_name,
        model_version=model_version,
        created_by="llm-extraction",
        updated_by="llm-extraction",
    )
    result_repository.add_extraction_result(extraction)
    result_repository.db.flush()
    return extraction


def _set_document_status(document: Document, status: DocumentStatus) -> None:
    document.status = status
    document.status_changed_at = datetime.now(UTC)
    document.updated_by = "llm-extraction"
