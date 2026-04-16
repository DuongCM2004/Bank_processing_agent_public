from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import UploadFile

from ops_agent.api.schemas import DocumentUploadMetadataResponse, DocumentUploadRequest
from ops_agent.application.services.audit import AuditService
from ops_agent.application.services.case_workflow import CaseWorkflowService
from ops_agent.application.services.upload_validation import validate_upload_file
from ops_agent.domain.workflow import CaseTransitionContext
from ops_agent.config import StorageSettings
from ops_agent.domain.shared.enums import AuditActorType, CaseStatus, DocumentStatus
from ops_agent.domain.shared.exceptions import ConflictError, OpsAgentError, ResourceNotFoundError
from ops_agent.infrastructure.db.models import Document
from ops_agent.infrastructure.db.repositories.document_repository import DocumentRepository
from ops_agent.infrastructure.storage.protocols import DocumentStorage


class DocumentUploadService:
    def __init__(
        self,
        *,
        repository: DocumentRepository,
        storage: DocumentStorage,
        storage_settings: StorageSettings,
        workflow_service: CaseWorkflowService,
        audit_service: AuditService,
    ) -> None:
        self._repository = repository
        self._storage = storage
        self._storage_settings = storage_settings
        self._workflow_service = workflow_service
        self._audit_service = audit_service

    async def upload_document(
        self,
        *,
        case_id,
        upload: UploadFile,
        request: DocumentUploadRequest,
    ) -> DocumentUploadMetadataResponse:
        case = self._repository.get_case_by_id(case_id)
        if case is None:
            raise ResourceNotFoundError("Case", str(case_id))
        if case.status not in {CaseStatus.CREATED, CaseStatus.DOCUMENTS_UPLOADED}:
            raise ConflictError(
                f"Document upload is not allowed while case '{case_id}' is in status '{case.status.value}'.",
                error_code="document_upload_not_allowed",
            )

        content = await upload.read()
        try:
            validated_upload = validate_upload_file(
                upload=upload,
                content=content,
                storage_settings=self._storage_settings,
            )
        except OpsAgentError as exc:
            self._audit_rejected_upload(
                case_id=case.id,
                upload=upload,
                request=request,
                reason_code=exc.error_code,
                reason_message=exc.message,
                content_size_bytes=len(content),
            )
            self._repository.commit()
            raise

        document = self._create_document_record(
            case_id=case.id,
            validated_upload=validated_upload,
            request=request,
        )

        document = self._store_and_finalize_upload(
            case=case,
            document=document,
            content=content,
            request=request,
            now=document.uploaded_at,
        )

        return DocumentUploadMetadataResponse(
            id=document.id,
            case_id=document.case_id,
            filename=document.filename,
            document_type=document.document_type,
            mime_type=document.mime_type,
            source_channel=document.source_channel,
            storage_key=document.storage_key,
            sha256_digest=document.sha256_digest,
            file_size_bytes=document.file_size_bytes,
            uploaded_at=document.uploaded_at,
            status=document.status,
            status_changed_at=document.status_changed_at,
            page_count=document.page_count,
            metadata=document.document_metadata,
            created_at=document.created_at,
            updated_at=document.updated_at,
        )

    def _create_document_record(
        self,
        *,
        case_id: uuid.UUID,
        validated_upload: ValidatedUpload,
        request: DocumentUploadRequest,
    ) -> Document:
        now = datetime.now(UTC)
        return Document(
            id=uuid4(),
            case_id=case_id,
            filename=validated_upload.sanitized_filename,
            document_type=request.document_type,
            mime_type=validated_upload.mime_type,
            storage_key="pending",
            sha256_digest="pending",
            file_size_bytes=validated_upload.size_bytes,
            uploaded_at=now,
            status=DocumentStatus.UPLOADED,
            status_changed_at=now,
            source_channel=request.source_channel,
            uploaded_by_user_id=request.uploaded_by_user_id,
            document_metadata=request.metadata,
            created_by=str(request.uploaded_by_user_id) if request.uploaded_by_user_id else None,
            updated_by=str(request.uploaded_by_user_id) if request.uploaded_by_user_id else None,
        )

    def _store_and_finalize_upload(
        self,
        *,
        case,
        document: Document,
        content: bytes,
        request: DocumentUploadRequest,
        now: datetime,
    ) -> Document:
        stored_document = self._storage.store(
            case_id=case.id,
            document_id=document.id,
            filename=document.filename,
            content=content,
        )
        document.storage_key = stored_document.storage_key
        document.sha256_digest = stored_document.sha256_digest
        document.file_size_bytes = stored_document.size_bytes

        self._repository.add_document(document)
        self._audit_service.record_document_uploaded(
            case_id=case.id,
            document_id=document.id,
            actor_user_id=request.uploaded_by_user_id,
            actor_type=AuditActorType.USER if request.uploaded_by_user_id else AuditActorType.SYSTEM,
            actor_identifier=str(request.uploaded_by_user_id) if request.uploaded_by_user_id else "system",
            filename=document.filename,
            mime_type=document.mime_type,
            file_size_bytes=document.file_size_bytes,
            storage_key=document.storage_key,
            occurred_at=now,
        )
        if case.status == CaseStatus.CREATED:
            self._workflow_service.transition(
                case=case,
                to_status=CaseStatus.DOCUMENTS_UPLOADED,
                context=CaseTransitionContext(
                    actor_type=AuditActorType.USER if request.uploaded_by_user_id else AuditActorType.SYSTEM,
                    actor_id=str(request.uploaded_by_user_id) if request.uploaded_by_user_id else "system",
                    reason_code="documents_uploaded",
                    metadata={"document_id": str(document.id), "storage_key": document.storage_key},
                    occurred_at=now,
                ),
            )
        self._repository.commit()
        self._repository.refresh(document)
        return document

    def _audit_rejected_upload(
        self,
        *,
        case_id,
        upload: UploadFile,
        request: DocumentUploadRequest,
        reason_code: str,
        reason_message: str,
        content_size_bytes: int,
    ) -> None:
        now = datetime.now(UTC)
        self._audit_service.record_document_upload_rejected(
            case_id=case_id,
            actor_user_id=request.uploaded_by_user_id,
            actor_type=AuditActorType.USER if request.uploaded_by_user_id else AuditActorType.SYSTEM,
            actor_identifier=str(request.uploaded_by_user_id) if request.uploaded_by_user_id else "system",
            filename=upload.filename,
            mime_type=upload.content_type,
            file_size_bytes=content_size_bytes,
            reason_code=reason_code,
            reason_message=reason_message,
            document_type=request.document_type,
            source_channel=request.source_channel,
            occurred_at=now,
        )


def parse_upload_metadata(raw_metadata: str | None) -> dict[str, str]:
    if not raw_metadata:
        return {}
    try:
        decoded = json.loads(raw_metadata)
    except json.JSONDecodeError as exc:
        raise ConflictError("Upload metadata must be valid JSON.", error_code="invalid_upload_metadata") from exc
    if not isinstance(decoded, dict):
        raise ConflictError("Upload metadata must be a JSON object.", error_code="invalid_upload_metadata")
    normalized: dict[str, str] = {}
    for key, value in decoded.items():
        normalized[str(key)] = str(value)
    return normalized
