from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import Field

from app.models.enums import DocumentStatus
from app.schemas.common import APIModel
from app.schemas.processing import IdentityDocumentExtraction, ProcessingStatus


class DocumentResponse(APIModel):
    id: UUID
    case_id: UUID
    filename: str
    document_type: str
    mime_type: str
    storage_key: str
    sha256_digest: str
    status: DocumentStatus
    file_size_bytes: int
    uploaded_at: datetime
    document_metadata: dict[str, object]


class DocumentMetadataRequest(APIModel):
    document_type: str = Field(max_length=80)
    document_metadata: dict[str, object] = Field(default_factory=dict)
    actor_id: str | None = Field(default=None, max_length=128)


class DocumentListResponse(APIModel):
    items: list[DocumentResponse]
    total: int


class DocumentUploadQueuedResponse(APIModel):
    document_uuid: UUID
    case_uuid: UUID
    extraction_uuid: UUID
    status: DocumentStatus


class DocumentStatusResponse(APIModel):
    document_uuid: UUID
    status: DocumentStatus
    extraction_uuid: UUID | None = None
    extraction_status: ProcessingStatus | None = None
    updated_at: datetime


class DocumentExtractionField(APIModel):
    field_name: str
    extracted_value: str | None = None
    reviewed_value: str | None = None


class DocumentExtractionResponse(APIModel):
    document_uuid: UUID
    extraction_uuid: UUID | None
    status: DocumentStatus
    fields: list[DocumentExtractionField]
    extracted_payload: dict[str, object]
    reviewed_payload: dict[str, object] | None = None
    raw_full_text: str | None = None


class DocumentReviewRequest(APIModel):
    action: Literal["edit", "approve", "reject"]
    reviewer_id: str = Field(max_length=128)
    reviewed_payload: IdentityDocumentExtraction | None = None
    comment: str | None = Field(default=None, max_length=1000)


class DocumentReviewResponse(APIModel):
    document_uuid: UUID
    extraction_uuid: UUID | None = None
    status: DocumentStatus
    action_id: UUID
