from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from ops_agent.api.schemas import DocumentListResponse, DocumentUploadMetadataResponse
from ops_agent.domain.shared.enums import AuditActorType, AuditEventType
from ops_agent.domain.shared.exceptions import DocumentContentUnavailableError, OpsAgentError, ResourceNotFoundError
from ops_agent.infrastructure.db.models import AuditEvent, Document
from ops_agent.infrastructure.db.repositories.document_repository import DocumentRepository
from ops_agent.infrastructure.storage.protocols import DocumentStorage, RetrievedDocument


@dataclass(frozen=True, slots=True)
class ResolvedDocumentDownload:
    document: Document
    stored_document: RetrievedDocument


class DocumentAccessService:
    def __init__(self, *, repository: DocumentRepository, storage: DocumentStorage) -> None:
        self._repository = repository
        self._storage = storage

    def list_case_documents(self, *, case_id: UUID) -> DocumentListResponse:
        self._get_case_or_raise(case_id)
        documents = self._repository.list_case_documents(case_id)
        return DocumentListResponse(
            items=[self._to_metadata_response(document) for document in documents],
            total=len(documents),
        )

    def get_document_metadata(self, *, case_id: UUID, document_id: UUID) -> DocumentUploadMetadataResponse:
        document = self._get_document_or_raise(case_id=case_id, document_id=document_id)
        return self._to_metadata_response(document)

    def prepare_download(
        self,
        *,
        case_id: UUID,
        document_id: UUID,
        downloaded_by_user_id: UUID | None = None,
    ) -> ResolvedDocumentDownload:
        document = self._get_document_or_raise(case_id=case_id, document_id=document_id)
        try:
            stored_document = self._storage.resolve(storage_key=document.storage_key)
        except FileNotFoundError as exc:
            raise DocumentContentUnavailableError(str(document.id)) from exc
        except ValueError as exc:
            raise OpsAgentError(
                "Document storage reference failed integrity validation.",
                error_code="document_storage_integrity_error",
                status_code=500,
            ) from exc

        now = datetime.now(UTC)
        self._repository.add_audit_event(
            AuditEvent(
                case_id=document.case_id,
                actor_user_id=downloaded_by_user_id,
                actor_type=AuditActorType.USER if downloaded_by_user_id else AuditActorType.SYSTEM,
                actor_identifier=str(downloaded_by_user_id) if downloaded_by_user_id else "system",
                event_type=AuditEventType.DOCUMENT_DOWNLOADED,
                resource_type="document",
                resource_id=document.id,
                occurred_at=now,
                details={
                    "filename": document.filename,
                    "mime_type": document.mime_type,
                    "storage_key": document.storage_key,
                    "file_size_bytes": stored_document.size_bytes,
                },
                evidence_refs=[],
                created_by=str(downloaded_by_user_id) if downloaded_by_user_id else None,
                updated_by=str(downloaded_by_user_id) if downloaded_by_user_id else None,
            )
        )
        self._repository.commit()
        return ResolvedDocumentDownload(document=document, stored_document=stored_document)

    def _get_case_or_raise(self, case_id: UUID):
        case = self._repository.get_case_by_id(case_id)
        if case is None:
            raise ResourceNotFoundError("Case", str(case_id))
        return case

    def _get_document_or_raise(self, *, case_id: UUID, document_id: UUID) -> Document:
        self._get_case_or_raise(case_id)
        document = self._repository.get_document_by_id(case_id, document_id)
        if document is None:
            raise ResourceNotFoundError("Document", str(document_id))
        return document

    @staticmethod
    def _to_metadata_response(document: Document) -> DocumentUploadMetadataResponse:
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
