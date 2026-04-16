from __future__ import annotations

import hashlib
import re
from pathlib import Path
from uuid import UUID, uuid4

from app.audit.logger import AuditLogger
from app.core.config import Settings
from app.core.exceptions import NotFoundError, ValidationAppError
from app.models.document import Document
from app.models.enums import AuditActorType, AuditEventType, CaseStatus, DocumentStatus
from app.repositories.cases import CaseRepository
from app.repositories.documents import DocumentRepository
from app.schemas.documents import DocumentListResponse, DocumentResponse
from app.schemas.cases import CaseStatusTransitionRequest
from app.services.cases import CaseService


class DocumentService:
    def __init__(
        self,
        document_repository: DocumentRepository,
        case_repository: CaseRepository,
        case_service: CaseService,
        audit_logger: AuditLogger,
        settings: Settings,
    ) -> None:
        self.document_repository = document_repository
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

    def list_documents(self, case_id: UUID) -> DocumentListResponse:
        if self.case_repository.get(case_id) is None:
            raise NotFoundError("Case not found.", error_code="case_not_found")
        items = self.document_repository.list_by_case(case_id)
        return DocumentListResponse(
            items=[DocumentResponse.model_validate(document) for document in items],
            total=len(items),
        )

    @staticmethod
    def _safe_filename(filename: str) -> str:
        cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", Path(filename).name).strip("._")
        return cleaned or "document"

    @staticmethod
    def _write_local_file(path: Path, content: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

