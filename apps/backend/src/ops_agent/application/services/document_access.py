from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from ops_agent.api.schemas import (
    DocumentExtractionFieldResponse,
    DocumentExtractionResponse,
    DocumentListResponse,
    DocumentReviewRequest,
    DocumentReviewResponse,
    DocumentStatusResponse,
    DocumentUploadMetadataResponse,
)
from ops_agent.domain.shared.enums import AuditActorType, AuditEventType, DocumentStatus
from ops_agent.domain.shared.exceptions import (
    ConflictError,
    DocumentContentUnavailableError,
    OpsAgentError,
    ResourceNotFoundError,
)
from ops_agent.infrastructure.db.models import AuditEvent, Document, ExtractionResult
from ops_agent.infrastructure.db.repositories.document_repository import DocumentRepository
from ops_agent.infrastructure.storage.protocols import DocumentStorage, RetrievedDocument


@dataclass(frozen=True, slots=True)
class ResolvedDocumentDownload:
    document: Document
    stored_document: RetrievedDocument


IDENTITY_EXTRACTION_FIELDS = (
    "document_type",
    "full_name",
    "first_name",
    "last_name",
    "id_number",
    "document_number",
    "date_of_birth",
    "sex",
    "gender",
    "nationality",
    "place_of_birth",
    "issue_date",
    "expiry_date",
    "issuing_authority",
    "address",
    "raw_full_text",
)


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

    def get_document_status(self, *, document_id: UUID) -> DocumentStatusResponse:
        document = self._get_document_by_uuid_or_raise(document_id)
        extraction_result = self._repository.get_latest_extraction_result(document.id)
        return DocumentStatusResponse(
            document_uuid=document.id,
            status=document.status,
            extraction_uuid=extraction_result.id if extraction_result else None,
            extraction_status=extraction_result.status if extraction_result else None,
            updated_at=document.updated_at,
        )

    def get_document_extraction(self, *, document_id: UUID) -> DocumentExtractionResponse:
        document = self._get_document_by_uuid_or_raise(document_id)
        extraction_result = self._repository.get_latest_extraction_result(document.id)
        extracted_payload = dict(extraction_result.extracted_payload) if extraction_result else {}
        return DocumentExtractionResponse(
            document_uuid=document.id,
            extraction_uuid=extraction_result.id if extraction_result else None,
            status=document.status,
            fields=[
                DocumentExtractionFieldResponse(
                    field_name=field_name,
                    extracted_value=self._string_or_none(extracted_payload.get(field_name)),
                    reviewed_value=None,
                )
                for field_name in IDENTITY_EXTRACTION_FIELDS
            ],
            extracted_payload=extracted_payload,
            reviewed_payload=None,
            raw_full_text=self._string_or_none(extracted_payload.get("raw_full_text")),
        )

    def review_document(self, *, document_id: UUID, request: DocumentReviewRequest) -> DocumentReviewResponse:
        document = self._get_document_by_uuid_or_raise(document_id)
        extraction_result = self._repository.get_latest_extraction_result(document.id)
        if extraction_result is None and request.action == "edit":
            raise ConflictError(
                f"Document '{document_id}' has no extraction result to edit.",
                error_code="document_has_no_extraction_result",
            )

        reviewed_payload = request.reviewed_payload.model_dump() if request.reviewed_payload else None
        now = datetime.now(UTC)
        if extraction_result is not None and reviewed_payload is not None and request.action in {"edit", "approve"}:
            extraction_result.extracted_payload = self._canonicalize_reviewed_payload(
                existing_payload=extraction_result.extracted_payload,
                reviewed_payload=reviewed_payload,
            )
            extraction_result.updated_at = now
            extraction_result.updated_by = request.reviewer_id

        if request.action == "approve":
            document.status = DocumentStatus.APPROVED
        elif request.action == "reject":
            document.status = DocumentStatus.REJECTED
        else:
            document.status = DocumentStatus.REVIEW_REQUIRED
        document.status_changed_at = now
        document.updated_at = now
        document.updated_by = request.reviewer_id

        audit_event = self._record_document_review_event(
            document=document,
            extraction_result=extraction_result,
            action=request.action,
            reviewer_id=request.reviewer_id,
            reviewed_payload=reviewed_payload,
            comment=request.comment,
            occurred_at=now,
        )
        self._repository.flush()
        self._repository.commit()
        self._repository.refresh(document)
        self._repository.refresh(audit_event)
        return DocumentReviewResponse(
            document_uuid=document.id,
            extraction_uuid=extraction_result.id if extraction_result else None,
            status=document.status,
            action_id=audit_event.id,
        )

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

    def _get_document_by_uuid_or_raise(self, document_id: UUID) -> Document:
        document = self._repository.get_document_by_uuid(document_id)
        if document is None:
            raise ResourceNotFoundError("Document", str(document_id))
        return document

    def _record_document_review_event(
        self,
        *,
        document: Document,
        extraction_result: ExtractionResult | None,
        action: str,
        reviewer_id: str,
        reviewed_payload: dict[str, object] | None,
        comment: str | None,
        occurred_at: datetime,
    ) -> AuditEvent:
        audit_event = AuditEvent(
            case_id=document.case_id,
            actor_user_id=None,
            actor_type=AuditActorType.USER,
            actor_identifier=reviewer_id,
            event_type=AuditEventType.MANUAL_REVIEW_ACTION_RECORDED,
            summary=f"Document review action '{action}' was recorded.",
            resource_type="document",
            resource_id=document.id,
            occurred_at=occurred_at,
            details={
                "action": action,
                "document_id": str(document.id),
                "extraction_result_id": str(extraction_result.id) if extraction_result else None,
                "reviewed_payload": reviewed_payload,
                "comment": comment,
            },
            evidence_refs=[],
            created_by=reviewer_id,
            updated_by=reviewer_id,
        )
        self._repository.add_audit_event(audit_event)
        return audit_event

    @staticmethod
    def _canonicalize_reviewed_payload(
        *,
        existing_payload: dict[str, object],
        reviewed_payload: dict[str, object],
    ) -> dict[str, object]:
        normalized_payload = dict(existing_payload)
        for field_name in IDENTITY_EXTRACTION_FIELDS:
            value = reviewed_payload.get(field_name)
            normalized_payload[field_name] = DocumentAccessService._string_or_none(value)
        return normalized_payload

    @staticmethod
    def _string_or_none(value: object) -> str | None:
        if value is None:
            return None
        normalized = str(value).strip()
        return normalized or None

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
