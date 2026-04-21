from __future__ import annotations

import hashlib
import re
from pathlib import Path
from uuid import UUID, uuid4

from app.audit.logger import AuditLogger
from app.core.config import Settings
from app.core.exceptions import NotFoundError, ValidationAppError
from app.models.document import Document, ExtractionResult
from app.models.enums import AuditActorType, AuditEventType, CaseStatus, DocumentStatus, ManualReviewActionType, ProcessingStatus
from app.repositories.cases import CaseRepository
from app.repositories.documents import DocumentRepository, ProcessingResultRepository
from app.repositories.manual_review import ManualReviewRepository
from app.schemas.cases import CaseStatusTransitionRequest
from app.schemas.documents import (
    DocumentExtractionField,
    DocumentExtractionResponse,
    DocumentListResponse,
    DocumentResponse,
    DocumentStatusResponse,
    DocumentUploadQueuedResponse,
)
from app.schemas.processing import IDENTITY_DOCUMENT_FIELD_NAMES
from app.services.cases import CaseService


class DocumentService:
    def __init__(
        self,
        document_repository: DocumentRepository,
        result_repository: ProcessingResultRepository,
        review_repository: ManualReviewRepository,
        case_repository: CaseRepository,
        case_service: CaseService,
        audit_logger: AuditLogger,
        settings: Settings,
    ) -> None:
        self.document_repository = document_repository
        self.result_repository = result_repository
        self.review_repository = review_repository
        self.case_repository = case_repository
        self.case_service = case_service
        self.audit_logger = audit_logger
        self.settings = settings

    def upload_document(
        self,
        *,
        case_id: UUID,
        filename: str,
        content_type: str,
        content: bytes,
        document_type: str,
        document_metadata: dict[str, object],
        actor_id: str | None,
    ) -> DocumentResponse:
        case = self.case_repository.get(case_id)
        if case is None:
            raise NotFoundError("Case not found.", error_code="case_not_found")
        if content_type not in self.settings.allowed_upload_mime_types:
            raise ValidationAppError("File MIME type is not allowed.", error_code="mime_type_not_allowed")
        if len(content) > self.settings.max_upload_bytes:
            raise ValidationAppError("File exceeds maximum upload size.", error_code="upload_too_large")
        if not content:
            raise ValidationAppError("Uploaded file is empty.", error_code="empty_upload")

        document_id = uuid4()
        safe_filename = self._safe_filename(filename)
        sha256_digest = hashlib.sha256(content).hexdigest()
        storage_key = f"cases/{case_id}/documents/{document_id}/{safe_filename}"
        storage_path = self.settings.storage_root_path / storage_key
        self._write_local_file(storage_path, content)

        document = Document(
            id=document_id,
            case_id=case_id,
            filename=filename,
            document_type=document_type,
            mime_type=content_type,
            storage_key=storage_key,
            sha256_digest=sha256_digest,
            status=DocumentStatus.STORED,
            file_size_bytes=len(content),
            uploaded_by_user_id=None,
            document_metadata=document_metadata,
            created_by=actor_id,
            updated_by=actor_id,
        )
        self.document_repository.add(document)
        self.audit_logger.record(
            event_type=AuditEventType.DOCUMENT_ADDED,
            actor_type=AuditActorType.USER,
            actor_id=actor_id,
            case_id=case_id,
            entity_type="document",
            entity_id=document_id,
            message="Document uploaded and stored.",
            details={
                "filename": filename,
                "mime_type": content_type,
                "sha256_digest": sha256_digest,
                "storage_key": storage_key,
            },
        )
        self.document_repository.db.commit()
        self.document_repository.db.refresh(document)

        if case.status == CaseStatus.CREATED:
            self.case_service.transition_case(
                case_id=case_id,
                request=CaseStatusTransitionRequest(
                    to_status=CaseStatus.DOCUMENTS_UPLOADED,
                    actor_id=actor_id,
                    reason_code="documents_uploaded",
                ),
        )
        return DocumentResponse.model_validate(document)

    def upload_and_queue_document(
        self,
        *,
        case_id: UUID,
        filename: str,
        content_type: str,
        content: bytes,
        document_type: str,
        document_metadata: dict[str, object],
        actor_id: str | None,
    ) -> DocumentUploadQueuedResponse:
        uploaded = self.upload_document(
            case_id=case_id,
            filename=filename,
            content_type=content_type,
            content=content,
            document_type=document_type,
            document_metadata=document_metadata,
            actor_id=actor_id,
        )
        document = self._get_document(uploaded.id)
        extraction_run = self._create_pending_extraction_run(
            document_id=document.id,
            actor_id=actor_id,
        )
        document.status = DocumentStatus.QUEUED
        document.updated_by = actor_id
        self.result_repository.add_extraction_result(extraction_run)
        self.result_repository.db.flush()
        self.audit_logger.record(
            event_type=AuditEventType.DOCUMENT_QUEUED,
            actor_type=AuditActorType.USER,
            actor_id=actor_id,
            case_id=document.case_id,
            entity_type="document",
            entity_id=document.id,
            message="Document queued for notebook-style GPT document extraction.",
            details={
                "extraction_uuid": str(extraction_run.id),
                "model": self.settings.gpt_model,
                "orchestrator": "langgraph",
            },
        )
        self.document_repository.db.commit()
        self.document_repository.db.refresh(document)
        self.result_repository.db.refresh(extraction_run)
        self._dispatch_processing_task(document.case_id)
        return DocumentUploadQueuedResponse(
            document_uuid=document.id,
            case_uuid=document.case_id,
            extraction_uuid=extraction_run.id,
            status=document.status,
        )

    def list_documents(self, case_id: UUID) -> DocumentListResponse:
        if self.case_repository.get(case_id) is None:
            raise NotFoundError("Case not found.", error_code="case_not_found")
        items = self.document_repository.list_by_case(case_id)
        return DocumentListResponse(
            items=[DocumentResponse.model_validate(document) for document in items],
            total=len(items),
        )

    def get_document_status(self, document_id: UUID) -> DocumentStatusResponse:
        document = self._get_document(document_id)
        extraction = self.result_repository.get_latest_extraction_for_document(document_id)
        return DocumentStatusResponse(
            document_uuid=document.id,
            status=document.status,
            extraction_uuid=extraction.id if extraction else None,
            extraction_status=extraction.status if extraction else None,
            updated_at=document.updated_at,
        )

    def get_document_extraction(self, document_id: UUID) -> DocumentExtractionResponse:
        document = self._get_document(document_id)
        extraction = self.result_repository.get_latest_extraction_for_document(document_id)
        reviewed_payload = self._latest_reviewed_payload(document_id)
        extracted_payload = extraction.extracted_payload if extraction else {}
        fields = [
            DocumentExtractionField(
                field_name=field_name,
                extracted_value=self._string_or_none(extracted_payload.get(field_name)),
                reviewed_value=self._string_or_none(reviewed_payload.get(field_name)) if reviewed_payload else None,
            )
            for field_name in IDENTITY_DOCUMENT_FIELD_NAMES
        ]
        return DocumentExtractionResponse(
            document_uuid=document.id,
            extraction_uuid=extraction.id if extraction else None,
            status=document.status,
            fields=fields,
            extracted_payload=extracted_payload,
            reviewed_payload=reviewed_payload,
            raw_full_text=self._string_or_none(extracted_payload.get("raw_full_text")),
        )

    def _get_document(self, document_id: UUID) -> Document:
        document = self.document_repository.get(document_id)
        if document is None:
            raise NotFoundError("Document not found.", error_code="document_not_found")
        return document

    def _latest_reviewed_payload(self, document_id: UUID) -> dict[str, object] | None:
        action = self.review_repository.get_latest_for_document(
            document_id,
            action_types={ManualReviewActionType.CORRECT_DATA, ManualReviewActionType.APPROVE},
        )
        if action is None:
            return None
        reviewed_payload = action.payload.get("reviewed_payload")
        return reviewed_payload if isinstance(reviewed_payload, dict) else None

    @staticmethod
    def _string_or_none(value: object) -> str | None:
        if value is None:
            return None
        return str(value)

    @staticmethod
    def _safe_filename(filename: str) -> str:
        cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", Path(filename).name).strip("._")
        return cleaned or "document"

    @staticmethod
    def _write_local_file(path: Path, content: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    def _create_pending_extraction_run(
        self,
        *,
        document_id: UUID,
        actor_id: str | None,
    ) -> ExtractionResult:
        """Build a new PENDING ExtractionResult ORM object from the current settings."""
        return ExtractionResult(
            document_id=document_id,
            status=ProcessingStatus.PENDING,
            schema_name=self.settings.llm_schema_version,
            extracted_payload={},
            evidence_refs=[],
            provider_name="openai_responses_gpt",
            model_version=self.settings.gpt_model,
            created_by=actor_id,
            updated_by=actor_id,
        )

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
            self.document_repository.db.commit()
