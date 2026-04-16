from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.models.enums import ProcessingStatus
from app.schemas.common import APIModel, EvidenceRef


class QueueProcessingRequest(APIModel):
    actor_id: str | None = Field(default=None, max_length=128)
    reason_code: str | None = Field(default="queued_for_processing", max_length=100)


class QueueProcessingResponse(APIModel):
    case_id: UUID
    status: str


class OCRResultResponse(APIModel):
    id: UUID
    document_id: UUID
    status: ProcessingStatus
    raw_text: str | None
    confidence_score: float | None
    provider_name: str
    processed_at: datetime | None


class ExtractionResultCreate(APIModel):
    document_id: UUID
    ocr_result_id: UUID | None = None
    schema_name: str = Field(max_length=120)
    extracted_payload: dict[str, object]
    confidence_score: float | None = Field(default=None, ge=0, le=1)
    evidence_refs: list[EvidenceRef] = Field(default_factory=list)
    provider_name: str = Field(max_length=100)
    model_version: str | None = Field(default=None, max_length=100)


class ExtractionResultResponse(APIModel):
    id: UUID
    document_id: UUID
    status: ProcessingStatus
    schema_name: str
    extracted_payload: dict[str, object]
    confidence_score: float | None
    evidence_refs: list[dict[str, object]]
    provider_name: str
    model_version: str | None
    processed_at: datetime | None

