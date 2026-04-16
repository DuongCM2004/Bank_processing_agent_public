from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.models.enums import DocumentStatus
from app.schemas.common import APIModel


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

